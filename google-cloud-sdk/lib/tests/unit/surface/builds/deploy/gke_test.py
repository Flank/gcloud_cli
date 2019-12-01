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
"""Tests for google3.third_party.py.tests.unit.surface.builds.deploy.gke."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os.path
import subprocess
import uuid

from apitools.base.py import encoding
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.builds.deploy import build_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import times
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class DeployGKETestAlpha(e2e_base.WithMockHttp, sdk_test_base.WithFakeAuth,
                         sdk_test_base.WithTempCWD):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    properties.VALUES.core.project.Set('my-project')
    self.StartPatch('time.sleep')  # To speed up tests with polling

    self.mocked_cloudbuild_v1 = mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'))
    self.mocked_cloudbuild_v1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1.Unmock)
    self.build_msg = core_apis.GetMessagesModule('cloudbuild', 'v1')
    self._step_statuses = self.build_msg.BuildStep.StatusValueValuesEnum
    self._statuses = self.build_msg.Build.StatusValueValuesEnum
    self._sub_options = self.build_msg.BuildOptions.SubstitutionOptionValueValuesEnum

    self.mocked_storage_v1 = mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.mocked_storage_v1.Mock()
    self.addCleanup(self.mocked_storage_v1.Unmock)
    self.storage_msg = core_apis.GetMessagesModule('storage', 'v1')

    self.frozen_time = '2019-07-29T00:05:00.000000Z'
    frozen_time = times.ParseDateTime(self.frozen_time)
    frozen_uuid = uuid.uuid4()
    self.frozen_tgz_filename = '{frozen_time}-{frozen_uuid}.tgz'.format(
        frozen_time=times.GetTimeStampFromDateTime(frozen_time),
        frozen_uuid=frozen_uuid.hex)
    self.frozen_tgz_filepath = 'deploy/source/{}'.format(
        self.frozen_tgz_filename)
    self.StartObjectPatch(times, 'Now', return_value=frozen_time)
    self.StartObjectPatch(uuid, 'uuid4', return_value=frozen_uuid)
    self.StartObjectPatch(os.path, 'getsize', return_value=100)

  def ExpectMessagesForDeploy(self, b_in, b_out, src=True):
    bucket_name = 'my-project_cloudbuild'
    b = self.storage_msg.Bucket(id=bucket_name)
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_msg.StorageBucketsGetRequest(bucket=b.id), response=b)
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_msg.StorageBucketsListRequest(
            project='my-project',
            prefix=b.id,
        ),
        response=self.storage_msg.Buckets(items=[b]))
    if src:
      self.mocked_storage_v1.objects.Insert.Expect(
          self.storage_msg.StorageObjectsInsertRequest(
              bucket=bucket_name,
              name=self.frozen_tgz_filepath,
              object=self.storage_msg.Object(size=100),
          ),
          response=self.storage_msg.Object(
              bucket=bucket_name,
              name=self.frozen_tgz_filepath,
              generation=123,
              size=100,
          ))

    op_metadata = self.build_msg.BuildOperationMetadata(build=b_out)

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.build_msg.CloudbuildProjectsBuildsCreateRequest(
            build=b_in,
            projectId='my-project',
        ),
        response=self.build_msg.Operation(
            metadata=encoding.JsonToMessage(
                self.build_msg.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata))))

  def DefaultInputBuild(self, src=True):
    build = self.build_msg.Build(
        tags=build_util._DEFAULT_TAGS,
        options=self.build_msg.BuildOptions(
            substitutionOption=self._sub_options.ALLOW_LOOSE
        )
    )
    if src:
      build.source = self.build_msg.Source(
          storageSource=self.build_msg.StorageSource(
              bucket='my-project_cloudbuild',
              object=self.frozen_tgz_filepath,
              generation=123,
          ))
    return build

  def DefaultBuildSteps(self, image='gcr.io/test-project/test-image:tag',
                        version='tag', build_and_push=False):
    steps = []
    if build_and_push:
      steps.append(self.build_msg.BuildStep(
          id=build_util._BUILD_BUILD_STEP_ID,
          name='gcr.io/cloud-builders/docker',
          args=[
              'build', '--network', 'cloudbuild', '--no-cache', '-t',
              image, '-f', '${}'.format(build_util._DOCKERFILE_PATH_SUB_VAR),
              '.'
          ],
      ))
      steps.append(self.build_msg.BuildStep(
          id=build_util._PUSH_BUILD_STEP_ID,
          name='gcr.io/cloud-builders/docker',
          args=['push', image]
      ))

    steps.append(self.build_msg.BuildStep(
        id=build_util._PREPARE_DEPLOY_BUILD_STEP_ID,
        name=build_util._GKE_DEPLOY_PROD,
        args=[
            'prepare',
            '--filename=${}'.format(build_util._K8S_YAML_PATH_SUB_VAR),
            '--image={}'.format(image),
            '--app=${}'.format(build_util._APP_NAME_SUB_VAR),
            '--version={}'.format(version),
            '--namespace=${}'.format(build_util._K8S_NAMESPACE_SUB_VAR),
            '--output=output',
            '--annotation=gcb-build-id=$BUILD_ID,${}'.format(
                build_util._K8S_ANNOTATIONS_SUB_VAR),
            '--expose=${}'.format(build_util._EXPOSE_PORT_SUB_VAR)
        ],
    ))
    steps.append(self.build_msg.BuildStep(
        id=build_util._SAVE_CONFIGS_BUILD_STEP_ID,
        name='gcr.io/cloud-builders/gsutil',
        entrypoint='sh',
        args=[
            '-c',
            build_util._SAVE_CONFIGS_SCRIPT
        ],
    ))
    steps.append(self.build_msg.BuildStep(
        id=build_util._APPLY_DEPLOY_BUILD_STEP_ID,
        name=build_util._GKE_DEPLOY_PROD,
        args=[
            'apply',
            '--filename=output/expanded',
            '--namespace=${}'.format(build_util._K8S_NAMESPACE_SUB_VAR),
            '--cluster=${}'.format(build_util._GKE_CLUSTER_SUB_VAR),
            '--location=${}'.format(build_util._GKE_LOCATION_SUB_VAR),
            '--timeout=24h'
        ],
    ))

    return steps

  def DefaultBuildSubstitutions(
      self, app_name='test-image', config='', namespace='default', expose='0',
      cluster='test-cluster', location='us-central1',
      staging_dir='my-project_cloudbuild/deploy/config'):
    return cloudbuild_util.EncodeSubstitutions(
        {
            build_util._DOCKERFILE_PATH_SUB_VAR: 'Dockerfile',
            build_util._APP_NAME_SUB_VAR: app_name,
            build_util._K8S_YAML_PATH_SUB_VAR: config,
            build_util._K8S_NAMESPACE_SUB_VAR: namespace,
            build_util._EXPOSE_PORT_SUB_VAR: expose,
            build_util._GKE_CLUSTER_SUB_VAR: cluster,
            build_util._GKE_LOCATION_SUB_VAR: location,
            build_util._OUTPUT_BUCKET_PATH_SUB_VAR: staging_dir,
            build_util._K8S_ANNOTATIONS_SUB_VAR: ''
        }, self.build_msg
    )

  def DefaultOutputBuild(self, b_in):
    b_out = copy.deepcopy(b_in)

    b_out.createTime = self.frozen_time
    b_out.id = '123-456-789'
    b_out.projectId = 'my-project'
    b_out.status = self._statuses.QUEUED
    b_out.logsBucket = 'gs://my-project_cloudbuild/logs'
    b_out.logUrl = 'mockLogURL'

    return b_out

  def testExistingImage(self):
    b_in = self.DefaultInputBuild(src=False)
    b_in.steps = self.DefaultBuildSteps()
    b_in.substitutions = self.DefaultBuildSubstitutions(
        namespace='test-namespace'
    )

    b_out = self.DefaultOutputBuild(b_in)

    self.ExpectMessagesForDeploy(b_in, b_out, src=False)
    self.Run([
        'builds', 'deploy', 'gke', '--cluster=test-cluster',
        '--location=us-central1', '--namespace=test-namespace',
        '--image=gcr.io/test-project/test-image:tag', '--async'
    ])

  def testExistingImageWithDigest(self):
    b_in = self.DefaultInputBuild(src=False)
    b_in.steps = self.DefaultBuildSteps(
        image='gcr.io/test-project/test-image@sha256:asdfasdf',
        version='version'
    )
    b_in.substitutions = self.DefaultBuildSubstitutions(
        namespace='test-namespace',
        expose='0'
    )

    b_out = self.DefaultOutputBuild(b_in)

    self.ExpectMessagesForDeploy(b_in, b_out, src=False)
    self.Run([
        'builds', 'deploy', 'gke', '--cluster=test-cluster',
        '--location=us-central1', '--namespace=test-namespace',
        '--image=gcr.io/test-project/test-image@sha256:asdfasdf',
        '--app-version=version', '--async'
    ])

  def testInvalidImage(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Image value must be in the gcr.io/* or *.gcr.io/* namespace.'):
      self.Run([
          'builds', 'deploy', 'gke', '--cluster=test-cluster',
          '--location=us-central1', '--image=invalid-image', '--async'
      ])

  def testSourceNotRequired(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Source must not be provided when no Kubernetes configs and no docker '
        'builds are required.'):
      self.Run([
          'builds', 'deploy', 'gke', '.', '--cluster=test-cluster',
          '--location=us-central1',
          '--image=gcr.io/test-project/test-image:tag', '--async'
      ])

  def testTagRequiresSource(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'required to build container image provided by --tag or --tag-default.'
    ):

      self.Run([
          'builds', 'deploy', 'gke', '--cluster=test-cluster',
          '--location=us-central1', '--tag=gcr.io/test-project/test-image:tag',
          '--async'
      ])

  def testInvalidTag(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Tag value must be in the gcr.io/* or *.gcr.io/* namespace.'):
      self.Run([
          'builds', 'deploy', 'gke', '.', '--cluster=test-cluster',
          '--location=us-central1', '--tag=invalid-tag', '--async'
      ])

  def testNoTagWithNoCommitHash(self):
    b_in = self.DefaultInputBuild()
    b_in.steps = self.DefaultBuildSteps(
        image='gcr.io/test-project/test-image',
        version='',
        build_and_push=True
    )
    b_in.substitutions = self.DefaultBuildSubstitutions()

    b_out = self.DefaultOutputBuild(b_in)

    files.MakeDir('source-dir')

    self.StartObjectPatch(
        subprocess,
        'check_output',
        side_effect=('git status', 'no pending changes', ''))

    self.ExpectMessagesForDeploy(b_in, b_out)
    self.Run([
        'builds', 'deploy', 'gke', './source-dir/', '--cluster=test-cluster',
        '--location=us-central1', '--tag=gcr.io/test-project/test-image',
        '--async'
    ])

  def testNoTagWithNotInGitRepo(self):
    b_in = self.DefaultInputBuild()
    b_in.steps = self.DefaultBuildSteps(
        image='gcr.io/test-project/test-image',
        version='',
        build_and_push=True
    )
    b_in.substitutions = self.DefaultBuildSubstitutions()

    b_out = self.DefaultOutputBuild(b_in)

    files.MakeDir('source-dir')

    # Not a Git repo
    self.StartObjectPatch(subprocess, 'check_output', side_effect=OSError)

    self.ExpectMessagesForDeploy(b_in, b_out)
    self.Run([
        'builds', 'deploy', 'gke', './source-dir/', '--cluster=test-cluster',
        '--location=us-central1', '--tag=gcr.io/test-project/test-image',
        '--async'
    ])

  def testDefaultTagWithCommitHash(self):
    b_in = self.DefaultInputBuild()
    b_in.steps = self.DefaultBuildSteps(
        image='gcr.io/$PROJECT_ID/source-dir:shortsha',
        version='shortsha',
        build_and_push=True
    )
    b_in.substitutions = self.DefaultBuildSubstitutions(
        app_name='source-dir'
    )

    b_out = self.DefaultOutputBuild(b_in)

    files.MakeDir('source-dir')

    self.StartObjectPatch(
        subprocess,
        'check_output',
        side_effect=('git status', 'no pending changes', 'shortsha'))

    self.ExpectMessagesForDeploy(b_in, b_out)
    self.Run([
        'builds', 'deploy', 'gke', './source-dir/', '--cluster=test-cluster',
        '--location=us-central1', '--tag-default', '--async'
    ])

  def testDefaultTagWithOverrides(self):
    b_in = self.DefaultInputBuild()
    b_in.steps = self.DefaultBuildSteps(
        image='gcr.io/$PROJECT_ID/name-override:version-override',
        version='version-override',
        build_and_push=True
    )
    b_in.substitutions = self.DefaultBuildSubstitutions(
        app_name='name-override',
    )

    b_in.tags.append('name-override')

    b_out = self.DefaultOutputBuild(b_in)

    self.ExpectMessagesForDeploy(b_in, b_out)
    self.Run([
        'builds', 'deploy', 'gke', '.', '--cluster=test-cluster',
        '--location=us-central1', '--tag-default', '--app-name=name-override',
        '--app-version=version-override', '--async'
    ])

  def testDefaultTagNameRequiresSource(self):
    tarball_path = self.Touch(
        '.', 'source.tgz', contents='pretend this is a valid tarball')

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'No default container image name available. Provide an '
        'app name with --app-name, or provide a valid --tag.'):

      self.Run([
          'builds', 'deploy', 'gke', tarball_path, '--cluster=test-cluster',
          '--location=us-central1', '--tag-default', '--async'
      ])

  def testDefaultTagVersionRequiresGitRepo(self):

    files.MakeDir('source-dir')

    # Not a valid repo
    self.StartObjectPatch(subprocess, 'check_output', side_effect=OSError)

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'No default container image tag available. Provide an app '
        'version with --app-version, or provide a valid --tag.'):

      self.Run([
          'builds', 'deploy', 'gke', './source-dir', '--cluster=test-cluster',
          '--location=us-central1', '--tag-default', '--async'
      ])

  def testDefaultTagVersionRequiresCommitHash(self):

    files.MakeDir('source-dir')

    # No commit hash found
    self.StartObjectPatch(
        subprocess,
        'check_output',
        side_effect=('git status', 'No pending changes', None))

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'No default tag available, no commit sha at HEAD of source repository '
        'available for tag. Provide an app version with --app-version, '
        'or provide a valid --tag.'):

      self.Run([
          'builds', 'deploy', 'gke', './source-dir', '--cluster=test-cluster',
          '--location=us-central1', '--tag-default', '--async'
      ])

  def testVersionBasedOnImageTag(self):
    b_in = self.DefaultInputBuild()
    b_in.steps = self.DefaultBuildSteps(
        image='gcr.io/test-project/test-image:my-tag',
        version='my-tag',
        build_and_push=True
    )
    b_in.substitutions = self.DefaultBuildSubstitutions()

    b_out = self.DefaultOutputBuild(b_in)

    self.ExpectMessagesForDeploy(b_in, b_out)
    self.Run([
        'builds', 'deploy', 'gke', '.', '--cluster=test-cluster',
        '--location=us-central1', '--tag=gcr.io/test-project/test-image:my-tag',
        '--async'
    ])

  def testVersionBasedOnCommitHash(self):
    b_in = self.DefaultInputBuild()
    b_in.steps = self.DefaultBuildSteps(
        image='gcr.io/test-project/test-image@sha256:asdfasdf',
        version='shortsha',
        build_and_push=True
    )
    b_in.substitutions = self.DefaultBuildSubstitutions(
        namespace='test-namespace'
    )

    b_out = self.DefaultOutputBuild(b_in)

    self.StartObjectPatch(
        subprocess,
        'check_output',
        side_effect=('git status', 'no pending changes', 'shortsha'))

    self.ExpectMessagesForDeploy(b_in, b_out)
    self.Run([
        'builds', 'deploy', 'gke', '.', '--cluster=test-cluster',
        '--location=us-central1', '--namespace=test-namespace',
        '--tag=gcr.io/test-project/test-image@sha256:asdfasdf', '--async'
    ])

  def testConfigRequiresSource(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [SOURCE]: required because --config is a '
        'relative path in the source directory.'):

      self.Run([
          'builds', 'deploy', 'gke', '--cluster=test-cluster',
          '--location=us-central1',
          '--image=gcr.io/test-project/test-image:tag',
          '--config=test-config.yaml', '--async'
      ])

  def testDefaultConfig(self):
    b_in = self.DefaultInputBuild()
    b_in.steps = self.DefaultBuildSteps(
        build_and_push=True
    )
    b_in.substitutions = self.DefaultBuildSubstitutions(
        config='test-config.yaml'
    )

    b_out = self.DefaultOutputBuild(b_in)

    self.ExpectMessagesForDeploy(b_in, b_out)
    self.Run([
        'builds', 'deploy', 'gke', '.', '--cluster=test-cluster',
        '--location=us-central1', '--tag=gcr.io/test-project/test-image:tag',
        '--config=test-config.yaml', '--async'
    ])

  def testUserProvidedBucket(self):
    bucket_name = 'test-bucket'

    frozen_file = 'source/{}'.format(self.frozen_tgz_filename)

    b_in = self.DefaultInputBuild(src=False)
    b_in.source = self.build_msg.Source(
        storageSource=self.build_msg.StorageSource(
            bucket=bucket_name,
            object=frozen_file,
            generation=123,
        ))
    b_in.steps = self.DefaultBuildSteps(
        build_and_push=True
    )
    b_in.substitutions = self.DefaultBuildSubstitutions(
        config='test-config.yaml',
        staging_dir=bucket_name
    )

    b_out = self.DefaultOutputBuild(b_in)

    b = self.storage_msg.Bucket(id=bucket_name)
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_msg.StorageBucketsGetRequest(bucket=b.id), response=b)
    self.mocked_storage_v1.objects.Insert.Expect(
        self.storage_msg.StorageObjectsInsertRequest(
            bucket=bucket_name,
            name=frozen_file,
            object=self.storage_msg.Object(size=100),
        ),
        response=self.storage_msg.Object(
            bucket=bucket_name,
            name=frozen_file,
            generation=123,
            size=100,
        ))

    op_metadata = self.build_msg.BuildOperationMetadata(build=b_out)

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.build_msg.CloudbuildProjectsBuildsCreateRequest(
            build=b_in,
            projectId='my-project',
        ),
        response=self.build_msg.Operation(
            metadata=encoding.JsonToMessage(
                self.build_msg.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata))))

    self.Run([
        'builds', 'deploy', 'gke', '.', '--cluster=test-cluster',
        '--location=us-central1', '--tag=gcr.io/test-project/test-image:tag',
        '--config=test-config.yaml', '--async',
        '--gcs-staging-dir=gs://test-bucket'
    ])

  def testUserProvidedBucketWithDir(self):
    bucket_name = 'test-bucket'

    frozen_file = 'my-deploy-dir/source/{}'.format(self.frozen_tgz_filename)

    b_in = self.DefaultInputBuild(src=False)
    b_in.source = self.build_msg.Source(
        storageSource=self.build_msg.StorageSource(
            bucket=bucket_name,
            object=frozen_file,
            generation=123,
        ))
    b_in.steps = self.DefaultBuildSteps(
        build_and_push=True
    )
    b_in.substitutions = self.DefaultBuildSubstitutions(
        config='test-config.yaml',
        staging_dir=bucket_name + '/my-deploy-dir/config'
    )

    b_out = self.DefaultOutputBuild(b_in)

    b = self.storage_msg.Bucket(id=bucket_name)
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_msg.StorageBucketsGetRequest(bucket=b.id), response=b)
    self.mocked_storage_v1.objects.Insert.Expect(
        self.storage_msg.StorageObjectsInsertRequest(
            bucket=bucket_name,
            name=frozen_file,
            object=self.storage_msg.Object(size=100),
        ),
        response=self.storage_msg.Object(
            bucket=bucket_name,
            name=frozen_file,
            generation=123,
            size=100,
        ))

    op_metadata = self.build_msg.BuildOperationMetadata(build=b_out)

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.build_msg.CloudbuildProjectsBuildsCreateRequest(
            build=b_in,
            projectId='my-project',
        ),
        response=self.build_msg.Operation(
            metadata=encoding.JsonToMessage(
                self.build_msg.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata))))

    self.Run([
        'builds', 'deploy', 'gke', '.', '--cluster=test-cluster',
        '--location=us-central1', '--tag=gcr.io/test-project/test-image:tag',
        '--config=test-config.yaml', '--async',
        '--gcs-staging-dir=gs://test-bucket/my-deploy-dir'
    ])

  def testExistingBucketNotOwned(self):
    bucket_name = 'my-project_cloudbuild'
    b = self.storage_msg.Bucket(id=bucket_name)
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_msg.StorageBucketsGetRequest(bucket=b.id), response=b)
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_msg.StorageBucketsListRequest(
            project='my-project',
            prefix=b.id,
        ),
        response=self.storage_msg.Buckets())

    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [--gcs-staging-dir]: A bucket with name '
        'my-project_cloudbuild already exists and is owned by another project. '
        'Specify a bucket using --gcs-staging-dir.'):
      self.Run([
          'builds', 'deploy', 'gke', '--cluster=test-cluster',
          '--location=us-central1', '--namespace=test-namespace',
          '--image=gcr.io/test-project/test-image:tag', '--async'
      ])

  def testSourceFromBucket(self):
    b_in = self.DefaultInputBuild()
    b_in.steps = self.DefaultBuildSteps(
        build_and_push=True
    )
    b_in.substitutions = self.DefaultBuildSubstitutions(
        namespace='test-namespace'
    )

    b_out = self.DefaultOutputBuild(b_in)

    bucket_name = 'my-project_cloudbuild'
    b = self.storage_msg.Bucket(id=bucket_name)
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_msg.StorageBucketsGetRequest(bucket=b.id), response=b)
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_msg.StorageBucketsListRequest(
            project='my-project',
            prefix=b.id,
        ),
        response=self.storage_msg.Buckets(items=[b]))
    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_msg.StorageObjectsRewriteRequest(
            destinationBucket=bucket_name,
            destinationObject=self.frozen_tgz_filepath,
            sourceBucket='source-bucket',
            sourceObject='source.tgz',
        ),
        response=self.storage_msg.RewriteResponse(
            resource=self.storage_msg.Object(
                bucket=bucket_name,
                name=self.frozen_tgz_filepath,
                generation=123,
            ),
            done=True,
        ),
    )

    op_metadata = self.build_msg.BuildOperationMetadata(build=b_out)

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.build_msg.CloudbuildProjectsBuildsCreateRequest(
            build=b_in,
            projectId='my-project',
        ),
        response=self.build_msg.Operation(
            metadata=encoding.JsonToMessage(
                self.build_msg.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata))))

    self.Run([
        'builds', 'deploy', 'gke', 'gs://source-bucket/source.tgz',
        '--cluster=test-cluster', '--location=us-central1',
        '--namespace=test-namespace',
        '--tag=gcr.io/test-project/test-image:tag', '--async'
    ])

  def testSourceFromFile(self):
    b_in = self.DefaultInputBuild()
    b_in.steps = self.DefaultBuildSteps(
        build_and_push=True
    )
    b_in.substitutions = self.DefaultBuildSubstitutions(
        namespace='test-namespace'
    )

    b_out = self.DefaultOutputBuild(b_in)

    tarball_path = self.Touch(
        '.', 'source.tgz', contents='pretend this is a valid tarball')

    self.ExpectMessagesForDeploy(b_in, b_out)

    self.Run([
        'builds', 'deploy', 'gke', tarball_path, '--cluster=test-cluster',
        '--location=us-central1', '--namespace=test-namespace',
        '--tag=gcr.io/test-project/test-image:tag', '--async'
    ])

  def testSourceFromMissingFile(self):
    bucket_name = 'my-project_cloudbuild'
    b = self.storage_msg.Bucket(id=bucket_name)
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_msg.StorageBucketsGetRequest(bucket=b.id), response=b)
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_msg.StorageBucketsListRequest(
            project='my-project',
            prefix=b.id,
        ),
        response=self.storage_msg.Buckets(items=[b]))

    with self.AssertRaisesExceptionMatches(
        exceptions.BadFileException,
        'could not find source [whereissource.tgz]'):
      self.Run([
          'builds', 'deploy', 'gke', 'whereissource.tgz',
          '--cluster=test-cluster', '--location=us-central1',
          '--namespace=test-namespace',
          '--tag=gcr.io/test-project/test-image:tag', '--async'
      ])

  def testSourceFromInvalidFile(self):
    bucket_name = 'my-project_cloudbuild'
    b = self.storage_msg.Bucket(id=bucket_name)
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_msg.StorageBucketsGetRequest(bucket=b.id), response=b)
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_msg.StorageBucketsListRequest(
            project='my-project',
            prefix=b.id,
        ),
        response=self.storage_msg.Buckets(items=[b]))

    source_path = self.Touch(
        '.', 'source.wtf', contents='pretend this is an invalid tarball')

    with self.AssertRaisesExceptionMatches(exceptions.BadFileException,
                                           'Local file'):
      self.Run([
          'builds', 'deploy', 'gke', source_path, '--cluster=test-cluster',
          '--location=us-central1', '--namespace=test-namespace',
          '--tag=gcr.io/test-project/test-image:tag', '--async'
      ])

  def testExposePort(self):
    b_in = self.DefaultInputBuild(src=False)
    b_in.steps = self.DefaultBuildSteps()
    b_in.substitutions = self.DefaultBuildSubstitutions(
        expose='1234'
    )

    b_out = self.DefaultOutputBuild(b_in)

    self.ExpectMessagesForDeploy(b_in, b_out, src=False)
    self.Run([
        'builds', 'deploy', 'gke', '--cluster=test-cluster',
        '--location=us-central1', '--image=gcr.io/test-project/test-image:tag',
        '--expose=1234', '--async'
    ])

  def testBadExposePort(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--expose]: port number is invalid'):
      self.Run([
          'builds', 'deploy', 'gke', '--cluster=test-cluster',
          '--location=us-central1',
          '--image=gcr.io/test-project/test-image:tag', '--expose=-99',
          '--async'
      ])

  def testDeployNoLogUrl(self):
    b_in = self.DefaultInputBuild(src=False)
    b_in.steps = self.DefaultBuildSteps()
    b_in.substitutions = self.DefaultBuildSubstitutions(
        namespace='test-namespace'
    )

    b_out = copy.deepcopy(b_in)
    b_out.createTime = self.frozen_time
    b_out.id = '123-456-789'
    b_out.projectId = 'my-project'
    b_out.status = self._statuses.QUEUED

    self.ExpectMessagesForDeploy(b_in, b_out, src=False)
    self.Run([
        'builds', 'deploy', 'gke', '--cluster=test-cluster',
        '--location=us-central1', '--namespace=test-namespace',
        '--image=gcr.io/test-project/test-image:tag', '--async'
    ])

    self.AssertErrNotContains('To see logs in the Cloud Console')
    self.AssertErrContains('Logs are available in the Cloud Console')

  def testTimeout(self):
    b_in = self.DefaultInputBuild(src=False)
    b_in.steps = self.DefaultBuildSteps()
    b_in.substitutions = self.DefaultBuildSubstitutions(
        namespace='test-namespace')
    b_in.timeout = '62s'

    b_out = self.DefaultOutputBuild(b_in)
    b_out.timeout = '62.000s'

    self.ExpectMessagesForDeploy(b_in, b_out, src=False)
    self.Run([
        'builds', 'deploy', 'gke', '--cluster=test-cluster',
        '--location=us-central1', '--namespace=test-namespace',
        '--image=gcr.io/test-project/test-image:tag', '--async',
        '--timeout=1m2s'
    ])

  def testTimeoutBareSeconds(self):
    b_in = self.DefaultInputBuild(src=False)
    b_in.steps = self.DefaultBuildSteps()
    b_in.substitutions = self.DefaultBuildSubstitutions(
        namespace='test-namespace'
    )

    b_in.timeout = '1234s'

    b_out = self.DefaultOutputBuild(b_in)
    b_out.timeout = '1234.000s'

    self.ExpectMessagesForDeploy(b_in, b_out, src=False)
    self.Run([
        'builds', 'deploy', 'gke', '--cluster=test-cluster',
        '--location=us-central1', '--namespace=test-namespace',
        '--image=gcr.io/test-project/test-image:tag', '--async',
        '--timeout=1234'
    ])

  def testStreamDeploy(self):
    b_in = self.DefaultInputBuild(src=False)
    b_in.steps = self.DefaultBuildSteps()
    b_in.substitutions = self.DefaultBuildSubstitutions()

    b_out = self.DefaultOutputBuild(b_in)

    b_out_working = copy.deepcopy(b_out)
    b_out_working.status = self._statuses.WORKING

    b_out_success = copy.deepcopy(b_out)
    b_out_success.status = self._statuses.SUCCESS

    self.ExpectMessagesForDeploy(b_in, b_out, src=False)

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.build_msg.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=b_out)

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=0-'},
        status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.build_msg.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=b_out_working)

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=44-'},
        status=200,
        body='Here the last line\n')

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.build_msg.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=b_out_success)

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=63-'},
        status=200,
        body='')

    self.Run([
        'builds', 'deploy', 'gke', '--cluster=test-cluster',
        '--location=us-central1', '--image=gcr.io/test-project/test-image:tag'
    ])

    self.AssertOutputContains(
        """\
        Here is some streamed
        data for you to print
        Here the last line
        """,
        normalize_space=True)

  def testStreamDeployButFailure(self):
    b_in = self.DefaultInputBuild(src=False)
    b_in.steps = self.DefaultBuildSteps()
    b_in.substitutions = self.DefaultBuildSubstitutions()

    b_out = self.DefaultOutputBuild(b_in)

    b_out_working = copy.deepcopy(b_out)
    b_out_working.status = self._statuses.WORKING

    b_out_failure = copy.deepcopy(b_out)
    b_out_failure.status = self._statuses.FAILURE

    self.ExpectMessagesForDeploy(b_in, b_out, src=False)

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.build_msg.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=b_out)

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=0-'},
        status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.build_msg.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=b_out_working)

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=44-'},
        status=200,
        body='Here the last line\n')

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.build_msg.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=b_out_failure)

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=63-'},
        status=200,
        body='')

    with self.AssertRaisesExceptionRegexp(core_exceptions.Error, 'FAILURE'):
      self.Run([
          'builds', 'deploy', 'gke', '--cluster=test-cluster',
          '--location=us-central1', '--image=gcr.io/test-project/test-image:tag'
      ])

    self.AssertOutputContains(
        """\
        Here is some streamed
        data for you to print
        Here the last line
        """,
        normalize_space=True)

  def testStreamDeployApplyDeployFailure(self):
    b_in = self.DefaultInputBuild(src=False)
    b_in.steps = self.DefaultBuildSteps()
    b_in.substitutions = self.DefaultBuildSubstitutions()

    b_out = self.DefaultOutputBuild(b_in)

    b_out_working = copy.deepcopy(b_out)
    b_out_working.status = self._statuses.WORKING

    b_out_failure = copy.deepcopy(b_out)
    b_out_failure.steps[-2].status = self._step_statuses.SUCCESS
    b_out_failure.status = self._statuses.FAILURE

    self.ExpectMessagesForDeploy(b_in, b_out, src=False)

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.build_msg.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=b_out)

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=0-'},
        status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.build_msg.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=b_out_working)

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=44-'},
        status=200,
        body='Here the last line\n')

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.build_msg.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=b_out_failure)

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=63-'},
        status=200,
        body='')

    with self.AssertRaisesExceptionRegexp(core_exceptions.Error, 'FAILURE'):
      self.Run([
          'builds', 'deploy', 'gke', '--cluster=test-cluster',
          '--location=us-central1', '--image=gcr.io/test-project/test-image:tag'
      ])

    self.AssertOutputContains(
        """\
        Here is some streamed
        data for you to print
        Here the last line
        """,
        normalize_space=True)
    self.AssertErrContains(
        'You can find the configuration files for this attempt at '
        'gs://my-project_cloudbuild/deploy/config/123-456-789/expanded.')

  def testStreamDeployButTimeout(self):
    b_in = self.DefaultInputBuild(src=False)
    b_in.steps = self.DefaultBuildSteps()
    b_in.substitutions = self.DefaultBuildSubstitutions()

    b_out = self.DefaultOutputBuild(b_in)

    b_out_working = copy.deepcopy(b_out)
    b_out_working.status = self._statuses.WORKING

    b_out_timeout = copy.deepcopy(b_out)
    b_out_timeout.status = self._statuses.TIMEOUT

    self.ExpectMessagesForDeploy(b_in, b_out, src=False)

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.build_msg.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=b_out)

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=0-'},
        status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.build_msg.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=b_out_working)

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=44-'},
        status=200,
        body='Here the last line\n')

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.build_msg.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=b_out_timeout)

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=63-'},
        status=200,
        body='')

    with self.AssertRaisesExceptionRegexp(core_exceptions.Error, 'TIMEOUT'):
      self.Run([
          'builds', 'deploy', 'gke', '--cluster=test-cluster',
          '--location=us-central1', '--image=gcr.io/test-project/test-image:tag'
      ])

    self.AssertOutputContains(
        """\
        Here is some streamed
        data for you to print
        Here the last line
        """,
        normalize_space=True)

if __name__ == '__main__':
  test_case.main()
