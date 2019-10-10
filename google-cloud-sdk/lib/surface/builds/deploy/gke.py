# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Build and deploy to Google Kubernetes Engine command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os.path
import uuid

from apitools.base.py import encoding
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import logs as cb_logs
from googlecloudsdk.api_lib.cloudbuild import snapshot
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.builds.deploy import git
from googlecloudsdk.command_lib.cloudbuild import execution
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.util import times

import six

_ALLOWED_SOURCE_EXT = ['.zip', '.tgz', '.gz']

_GKE_DEPLOY_PROD = 'gcr.io/cloud-builders/gke-deploy:stable'
_CLOUD_BUILD_DEPLOY_TAGS = [
    'gcp-cloud-build-deploy', 'gcp-cloud-build-deploy-gcloud'
]
_SUGGESTED_CONFIGS_PATH = 'gs://{0}/config/{1}/suggested'
_EXPANDED_CONFIGS_PATH = 'gs://{0}/config/{1}/expanded'
_COPY_AUDIT_FILES_SCRIPT = '''
set -e

gsutil cp -r output/suggested {0}
echo "Copied suggested base configs to {0}"
gsutil cp -r output/expanded {1}
echo "Copied expanded configs to {1}"
'''.format(
    _SUGGESTED_CONFIGS_PATH.format('{0}', '$BUILD_ID'),
    _EXPANDED_CONFIGS_PATH.format('{0}', '$BUILD_ID')
)

# Build step IDs
_BUILD_BUILD_STEP_ID = 'Build'
_PUSH_BUILD_STEP_ID = 'Push'
_PREPARE_DEPLOY_BUILD_STEP_ID = 'Prepare deploy'
_SAVE_CONFIGS_BUILD_STEP_ID = 'Save configs'
_APPLY_DEPLOY_BUILD_STEP_ID = 'Apply deploy'


class FailedDeployException(core_exceptions.Error):
  """Exception for builds that did not succeed."""

  def __init__(self, build):
    super(FailedDeployException, self).__init__(
        'failed to build or deploy: build {id} completed with status "{status}"'
        .format(id=build.id, status=build.status))


class DeployGKE(base.Command):
  """Build and deploy to a target Google Kubernetes Engine cluster."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        'source',
        nargs='?',
        help='Location of the source and configs to build and deploy. The '
        '`--config` option, if provided, is a relative path in the source '
        'directory. The location can be a directory on a local disk or a '
        'gzipped archive file (.tar.gz) in Google Cloud Storage.')
    docker = parser.add_mutually_exclusive_group(required=True)
    docker.add_argument(
        '--tag',
        help="""
        Tag to use with a 'docker build' image creation. Cloud Build runs a
        remote 'docker build -t $TAG .' command, where $TAG is the tag provided
        by this flag. The tag must be in the gcr.io/* or *.gcr.io/* namespaces.
        If you specify a tag in this command, your source must include a
        Dockerfile. For instructions on building using a Dockerfile see
        https://cloud.google.com/cloud-build/docs/quickstart-docker.

        If you would like a default tag to build with, supply the flag
         `--tag-default`.
        """)
    docker.add_argument(
        '--tag-default',
        action='store_true',
        help="""
        Default tag to use with a 'docker build' image creation. Cloud Build
        runs a remote 'docker build -t $TAG .' command, where $TAG is the tag,
        in the format 'gcr.io/$PROJECT_ID/<source directory>:$SHORT_SHA'.

        Your source must include a Dockerfile. For instructions on building
        using a Dockerfile see
        https://cloud.google.com/cloud-build/docs/quickstart-docker.
        """)
    docker.add_argument(
        '--image',
        help='Existing container image to deploy. If set, Cloud Build deploys '
        'the container image to the target Kubernetes cluster. The image must '
        'be in the gcr.io/* or *.gcr.io/* namespaces.')
    parser.add_argument(
        '--gcs-staging-dir',
        help="""
        Path to the Google Cloud Storage subdirectory into which to copy the
        source and configs (suggested base and expanded Kubernetes YAML files)
        that are used to stage and deploy your app. If the bucket in this path
        doesn't exist, Cloud Build creates it.

        If this field is not set, the source and configs are written to
        'gs://[PROJECT_ID]_cloudbuild/deploy', where source is written to the
        'source' sub-directory and configs are written to the 'config'
        sub-directory.
        """)
    parser.add_argument(
        '--app-name',
        help='If specified, the following label is added to the Kubernetes '
        "manifests: 'app.kubernetes.io/name: APP_NAME'. Defaults to the "
        'container image name provided by `--image` or `--tag` without the tag, '
        "e.g. 'my-app' for 'gcr.io/my-project/my-app:1.0.0'.")
    parser.add_argument(
        '--app-version',
        help='If specified, the following label is added to the Kubernetes '
        "manifests: 'app.kubernetes.io/version: APP_VERSION'. Defaults to the "
        'container image tag provided by `--image` or `--tag`. If no image tag '
        'is provided and `SOURCE` is a valid git repository, defaults to the '
        'short revision hash of the HEAD commit.')
    parser.add_argument(
        '--cluster',
        help='Name of the target cluster to deploy to.',
        required=True)
    parser.add_argument(
        '--location',
        help='Region or zone of the target cluster to deploy to.',
        required=True)
    parser.add_argument(
        '--namespace',
        default='default',
        help='Namespace of the target cluster to deploy to. If this field is '
        "not set, the 'default' namespace is used.")
    parser.add_argument(
        '--config',
        help="""
        Path to the Kubernetes YAML, or directory containing multiple
        Kubernetes YAML files, used to deploy the container image,
        relative to SOURCE. The files must reference the provided container
        image or tag.

        If this field is not set, a default Deployment config and Horizontal
        Pod Autoscaler config are used to deploy the image.
        """)
    parser.add_argument(
        '--timeout',
        help='Maximum time a build is run before it times out. For example, '
        '"2h15m5s" is 2 hours, 15 minutes, and 5 seconds. If you '
        'do not specify a unit, seconds is assumed. Overrides the default '
        'builds/timeout property value for this command invocation.',
        action=actions.StoreProperty(properties.VALUES.builds.timeout),
    )
    parser.add_argument(
        '--expose',
        type=int,
        help='Port that the deployed application listens to. If set, a '
        "Kubernetes Service of type 'LoadBalancer' is created with a "
        'single TCP port mapping that exposes this port.')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.

    Raises:
      FailedDeployException: If the build is completed and not 'SUCCESS'.
    """

    client = cloudbuild_util.GetClientInstance()
    messages = cloudbuild_util.GetMessagesModule()

    build_config = self._CreateBuildFromArgs(args, messages)

    # Start the build
    project = properties.VALUES.core.project.Get(required=True)
    op = client.projects_builds.Create(
        messages.CloudbuildProjectsBuildsCreateRequest(
            build=build_config, projectId=project))
    log.debug('submitting build: ' + repr(build_config))

    json = encoding.MessageToJson(op.metadata)
    build = encoding.JsonToMessage(messages.BuildOperationMetadata, json).build

    build_ref = resources.REGISTRY.Create(
        collection='cloudbuild.projects.builds',
        projectId=build.projectId,
        id=build.id)

    log.status.Print('Starting Cloud Build to build and deploy to the target '
                     'Google Kubernetes Engine cluster...\n')

    log.CreatedResource(build_ref)
    if build.logUrl:
      log.status.Print(
          'Logs are available at [{log_url}].'.format(log_url=build.logUrl))
    else:
      log.status.Print('Logs are available in the Cloud Console.')

    if args.async_:
      return

    mash_handler = execution.MashHandler(
        execution.GetCancelBuildHandler(client, messages, build_ref))

    # Otherwise, logs are streamed from GCS.
    with execution_utils.CtrlCSection(mash_handler):
      build = cb_logs.CloudBuildClient(client, messages).Stream(build_ref)

    if build.status == messages.Build.StatusValueValuesEnum.TIMEOUT:
      log.status.Print(
          'Your build and deploy timed out. Use the [--timeout=DURATION] flag '
          'to change the timeout threshold.')

    suggested_configs_path = _SUGGESTED_CONFIGS_PATH.format(
        self.staging_path, build.id)
    expanded_configs_path = _EXPANDED_CONFIGS_PATH.format(
        self.staging_path, build.id)

    if build.status != messages.Build.StatusValueValuesEnum.SUCCESS:
      save_configs_build_step = next((
          x for x in build.steps if x.id == _SAVE_CONFIGS_BUILD_STEP_ID
      ), None)

      status = save_configs_build_step.status
      if status == messages.BuildStep.StatusValueValuesEnum.SUCCESS:
        log.status.Print(
            'You can find the configuration files for this attempt at {}.'
            .format(expanded_configs_path)
        )
      raise FailedDeployException(build)

    log.status.Print(
        'Successfully deployed to your Google Kubernetes Engine cluster.\n\n'
        'You can find the configuration files of the deployed Kubernetes '
        'objects stored at {expanded}.\n\n'
        'You can also find suggested base Kubernetes configuration files '
        'at {suggested}.'.format(
            expanded=expanded_configs_path,
            suggested=suggested_configs_path))
    return

  def _CreateBuildFromArgs(self, args, messages):
    """Creates the Cloud Build config from the arguments.

    Args:
      args: argsparse object from the DeployGKE command.
      messages: Cloud Build messages module.

    Returns:
      messages.Build, the Cloud Build config.
    """
    build = messages.Build(steps=[], tags=_CLOUD_BUILD_DEPLOY_TAGS)

    if args.app_name:
      build.tags.append(args.app_name)

    build_timeout = properties.VALUES.builds.timeout.Get()

    if build_timeout is not None:
      try:
        # A bare number is interpreted as seconds.
        build_timeout_secs = int(build_timeout)
      except ValueError:
        build_timeout_duration = times.ParseDuration(build_timeout)
        build_timeout_secs = int(build_timeout_duration.total_seconds)
      build.timeout = six.text_type(build_timeout_secs) + 's'

    if args.source is None:
      if args.tag or args.tag_default:
        raise c_exceptions.RequiredArgumentException(
            'SOURCE',
            'required to build container image provided by --tag or --tag-default.'
        )
      if args.config:
        raise c_exceptions.RequiredArgumentException(
            'SOURCE', 'required because --config is a relative path in the '
            'source directory.')

    if args.source and args.image and not args.config:
      raise c_exceptions.InvalidArgumentException(
          'SOURCE', 'Source should not be provided when no Kubernetes '
          'configs and no docker builds are required.')

    if args.tag_default:
      if args.app_name:
        default_name = args.app_name
      elif os.path.isdir(args.source):
        default_name = os.path.basename(os.path.abspath(args.source))
      else:
        raise c_exceptions.InvalidArgumentException(
            '--tag-default',
            'No default container image name available. Please provide an '
            'app name with --app-name, or provide a valid --tag.')

      if args.app_version:
        default_tag = args.app_version
      elif git.IsGithubRepository(
          args.source) and not git.HasPendingChanges(args.source):
        default_tag = git.GetShortGitHeadRevision(args.source)
        if not default_tag:
          raise c_exceptions.InvalidArgumentException(
              '--tag-default',
              'No default tag available, no commit sha at HEAD of source '
              'repository available for tag. Please provide an app version '
              'with --app-version, or provide a valid --tag.')
      else:
        raise c_exceptions.InvalidArgumentException(
            '--tag-default',
            'No default container image tag available. Please provide an app '
            'version with --app-version, or provide a valid --tag.')

      args.tag = 'gcr.io/$PROJECT_ID/{name}:{tag}'.format(
          name=default_name, tag=default_tag)

    if args.tag:
      if (properties.VALUES.builds.check_tag.GetBool() and
          'gcr.io/' not in args.tag):
        raise c_exceptions.InvalidArgumentException(
            '--tag',
            'Tag value must be in the gcr.io/* or *.gcr.io/* namespace.')
      build.steps.append(
          messages.BuildStep(
              id=_BUILD_BUILD_STEP_ID,
              name='gcr.io/cloud-builders/docker',
              args=[
                  'build', '--network', 'cloudbuild', '--no-cache', '-t',
                  args.tag, '.'
              ],
          ))
      build.steps.append(
          messages.BuildStep(
              id=_PUSH_BUILD_STEP_ID,
              name='gcr.io/cloud-builders/docker', args=['push', args.tag]))

    if args.image and (properties.VALUES.builds.check_tag.GetBool() and
                       'gcr.io/' not in args.image):
      raise c_exceptions.InvalidArgumentException(
          '--image',
          'Image value must be in the gcr.io/* or *.gcr.io/* namespace.')

    if args.expose and args.expose < 0:
      raise c_exceptions.InvalidArgumentException('EXPOSE',
                                                  'port number is invalid')

    self._StageSourceAndConfigFiles(args, messages, build)

    image = args.image if args.image else args.tag

    prepare_deploy_step = messages.BuildStep(
        id=_PREPARE_DEPLOY_BUILD_STEP_ID,
        name=_GKE_DEPLOY_PROD,
        args=[
            'prepare',
            '--image={}'.format(image),
            '--namespace={}'.format(args.namespace),
            '--output=output',
            '--annotation=gcb-build-id=$BUILD_ID',
        ],
    )
    image_name = image.split('/')[-1]
    image_with_digest = image_name.split('@')
    image_with_tag = image_name.split(':')
    if args.app_name:
      prepare_deploy_step.args.append('--app={}'.format(args.app_name))
    else:
      if len(image_with_digest) > 1:
        prepare_deploy_step.args.append('--app={}'.format(image_with_digest[0]))
      else:
        prepare_deploy_step.args.append('--app={}'.format(image_with_tag[0]))

    if args.app_version:
      prepare_deploy_step.args.append('--version={}'.format(args.app_version))
    elif len(image_with_digest) == 1 and len(image_with_tag) > 1:
      prepare_deploy_step.args.append('--version={}'.format(image_with_tag[1]))
    elif args.source:
      if git.IsGithubRepository(
          args.source) and not git.HasPendingChanges(args.source):
        short_sha = git.GetShortGitHeadRevision(args.source)
        if short_sha:
          prepare_deploy_step.args.append('--version={}'.format(short_sha))

    if args.config:
      prepare_deploy_step.args.append('--filename={}'.format(args.config))
    if args.expose:
      prepare_deploy_step.args.append('--expose={}'.format(args.expose))

    # Append before the gsutil copy step
    build.steps.insert(-1, prepare_deploy_step)

    apply_deploy_step = messages.BuildStep(
        id=_APPLY_DEPLOY_BUILD_STEP_ID,
        name=_GKE_DEPLOY_PROD,
        args=[
            'apply',
            '--filename=output/expanded',
            '--namespace={}'.format(args.namespace),
            '--cluster={}'.format(args.cluster),
            '--location={}'.format(args.location)
        ],
    )
    if build.timeout is not None:
      apply_deploy_step.args.append('--timeout={}'.format(build.timeout))

    # Append after the gsutil copy step
    build.steps.append(apply_deploy_step)

    return build

  def _StageSourceAndConfigFiles(self, args, messages, build):
    """Stages the source and config files in a staging Google Cloud Storage bucket.

    Args:
      args: argsparse object from the DeployGKE command.
      messages: Cloud Build messages module.
      build: Cloud Build config.
    """

    project = properties.VALUES.core.project.Get(required=True)
    safe_project = project.replace(':', '_')
    safe_project = safe_project.replace('.', '_')
    # The string 'google' is not allowed in bucket names.
    safe_project = safe_project.replace('google', 'elgoog')

    gcs_client = storage_api.StorageClient()

    default_bucket_name = '{}_cloudbuild'.format(safe_project)

    gcs_staging_dir_name = (
        args.gcs_staging_dir if args.gcs_staging_dir else
        'gs://{}/deploy'.format(default_bucket_name))

    try:
      gcs_staging_dir = resources.REGISTRY.Parse(
          gcs_staging_dir_name, collection='storage.objects')
      gcs_staging_dir_obj = gcs_staging_dir.object
    except resources.WrongResourceCollectionException:
      gcs_staging_dir = resources.REGISTRY.Parse(
          gcs_staging_dir_name, collection='storage.buckets')
      gcs_staging_dir_obj = None

    gcs_client.CreateBucketIfNotExists(gcs_staging_dir.bucket)

    if args.gcs_staging_dir is None:
      # Check that the default bucket is also owned by the project (b/33046325)
      bucket_list_req = gcs_client.messages.StorageBucketsListRequest(
          project=project, prefix=default_bucket_name)
      bucket_list = gcs_client.client.buckets.List(bucket_list_req)

      if not any(
          bucket.id == default_bucket_name for bucket in bucket_list.items):
        raise c_exceptions.RequiredArgumentException(
            '--gcs-staging-dir',
            'A bucket with name {} already exists and is owned by '
            'another project. Specify a bucket using '
            '--gcs-staging-dir.'.format(default_bucket_name))

    if args.source:
      suffix = '.tgz'
      if args.source.startswith('gs://') or os.path.isfile(args.source):
        _, suffix = os.path.splitext(args.source)

      staged_source = 'source/{stamp}-{uuid}{suffix}'.format(
          stamp=times.GetTimeStampFromDateTime(times.Now()),
          uuid=uuid.uuid4().hex,
          suffix=suffix,
      )

      if gcs_staging_dir_obj:
        staged_source = gcs_staging_dir_obj + '/' + staged_source
      gcs_source_staging = resources.REGISTRY.Create(
          collection='storage.objects',
          bucket=gcs_staging_dir.bucket,
          object=staged_source)

      staged_source_obj = None

      if args.source.startswith('gs://'):
        gcs_source = resources.REGISTRY.Parse(
            args.source, collection='storage.objects')
        staged_source_obj = gcs_client.Rewrite(gcs_source, gcs_source_staging)
      else:
        if not os.path.exists(args.source):
          raise c_exceptions.BadFileException(
              'could not find source [{src}]'.format(src=args.source))
        elif os.path.isdir(args.source):
          source_snapshot = snapshot.Snapshot(args.source)
          size_str = resource_transform.TransformSize(
              source_snapshot.uncompressed_size)
          log.status.Print(
              'Creating temporary tarball archive of {num_files} file(s)'
              ' totalling {size} before compression.'.format(
                  num_files=len(source_snapshot.files), size=size_str))
          staged_source_obj = source_snapshot.CopyTarballToGCS(
              gcs_client, gcs_source_staging)
        elif os.path.isfile(args.source):
          unused_root, ext = os.path.splitext(args.source)
          if ext not in _ALLOWED_SOURCE_EXT:
            raise c_exceptions.BadFileException(
                'Local file [{src}] is none of '.format(src=args.source) +
                ', '.join(_ALLOWED_SOURCE_EXT))
          log.status.Print('Uploading local file [{src}] to '
                           '[gs://{bucket}/{object}].'.format(
                               src=args.source,
                               bucket=gcs_source_staging.bucket,
                               object=gcs_source_staging.object,
                           ))
          staged_source_obj = gcs_client.CopyFileToGCS(args.source,
                                                       gcs_source_staging)

      build.source = messages.Source(
          storageSource=messages.StorageSource(
              bucket=staged_source_obj.bucket,
              object=staged_source_obj.name,
              generation=staged_source_obj.generation,
          ))

    if gcs_staging_dir_obj:
      staging_path = gcs_staging_dir.bucket + '/' + gcs_staging_dir_obj
    else:
      staging_path = gcs_staging_dir.bucket

    # TODO(b/139489312): Revisit when implementing `gcloud builds configure
    #  gke`, since it will require refactoring this entire file.
    #  This is the easiest way to propagate staging_path up for now.
    self.staging_path = staging_path

    build.steps.append(
        messages.BuildStep(
            id=_SAVE_CONFIGS_BUILD_STEP_ID,
            name='gcr.io/cloud-builders/gsutil',
            entrypoint='sh',
            args=[
                '-c',
                _COPY_AUDIT_FILES_SCRIPT.format(staging_path)
            ],
        ))
    return
