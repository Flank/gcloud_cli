# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Import image command."""

import os.path
import uuid

from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.images import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

_OS_CHOICES = {'debian-8': 'debian/translate_debian_8.wf.json',
               'debian-9': 'debian/translate_debian_9.wf.json',
               'centos-6': 'enterprise_linux/translate_centos_6.wf.json',
               'centos-7': 'enterprise_linux/translate_centos_7.wf.json',
               'rhel-6': 'enterprise_linux/translate_rhel_6_licensed.wf.json',
               'rhel-7': 'enterprise_linux/translate_centos_7_licensed.wf.json',
               'rhel-6-byol': 'enterprise_linux/translate_rhel_6_byol.wf.json',
               'rhel-7-byol': 'enterprise_linux/translate_rhel_7_byol.wf.json',
               'ubuntu-1404': 'ubuntu/translate_ubuntu_1404.wf.json',
               'ubuntu-1604': 'ubuntu/translate_ubuntu_1604.wf.json',
               'windows-2008r2': 'windows/translate_windows_2008_r2.wf.json',
               'windows-2012r2': 'windows/translate_windows_2012_r2.wf.json',
               'windows-2016': 'windows/translate_windows_2016.wf.json',
              }
_WORKFLOW_DIR = '../workflows/image_import/'
_IMPORT_WORKFLOW = _WORKFLOW_DIR + 'import_image.wf.json'
_IMPORT_AND_TRANSLATE_WORKFLOW = _WORKFLOW_DIR + 'import_and_translate.wf.json'
_WORKFLOWS_URL = ('https://github.com/GoogleCloudPlatform/compute-image-tools/'
                  'tree/master/daisy_workflows/image_import')


def _IsLocalFile(file_name):
  return not (file_name.startswith('gs://') or
              file_name.startswith('https://'))


def _UploadToGcs(async, local_path, daisy_bucket, image_uuid):
  """Uploads a local file to GCS. Returns the gs:// URI to that file."""
  file_name = os.path.basename(local_path).replace(' ', '-')
  dest_path = 'gs://{0}/tmpimage/{1}-{2}'.format(
      daisy_bucket, image_uuid, file_name)
  log.status.Print('\nCopying [{0}] to [{1}]'.format(local_path, dest_path))
  if async:
    log.status.Print('Once completed, your image will be imported from Cloud'
                     ' Storage asynchronously.')
  storage_util.RunGsutilCommand('cp', [local_path, dest_path])
  return dest_path


def _CopyToScratchBucket(source_uri, image_uuid, storage_client, daisy_bucket):
  """Copy image from source_uri to daisy scratch bucket."""
  image_file = os.path.basename(source_uri)
  dest_uri = 'gs://{0}/tmpimage/{1}-{2}'.format(
      daisy_bucket, image_uuid, image_file)
  src_object = resources.REGISTRY.Parse(source_uri,
                                        collection='storage.objects')
  dest_object = resources.REGISTRY.Parse(dest_uri,
                                         collection='storage.objects')
  log.status.Print('\nCopying [{0}] to [{1}]'.format(source_uri, dest_uri))
  storage_client.Rewrite(src_object, dest_object)
  return dest_uri


def _GetTranslateWorkflow(args):
  if args.os:
    return _OS_CHOICES[args.os]
  return args.custom_workflow


def _MakeGcsUri(uri):
  obj_ref = resources.REGISTRY.Parse(uri)
  return 'gs://{0}/{1}'.format(obj_ref.bucket, obj_ref.object)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Import(base.CreateCommand):
  """Import a Google Compute Engine image."""

  @staticmethod
  def Args(parser):
    Import.DISK_IMAGE_ARG = flags.MakeDiskImageArg()
    Import.DISK_IMAGE_ARG.AddArgument(parser, operation_type='create')

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        '--source-file',
        help=("""A local file, or the Google Cloud Storage URI of the virtual
              disk file to import. For example: ``gs://my-bucket/my-image.vmdk''
              or ``./my-local-image.vmdk''"""),
    )
    flags.SOURCE_IMAGE_ARG.AddArgument(source, operation_type='translate')

    workflow = parser.add_mutually_exclusive_group(required=True)
    workflow.add_argument(
        '--os',
        choices=sorted(_OS_CHOICES.keys()),
        help='Specifies the OS of the image being translated.'
    )
    workflow.add_argument(
        '--translate',
        default=True,
        action='store_true',
        help=('Import the disk without making it bootable or installing Google '
              'tools on it.')
    )
    workflow.add_argument(
        '--custom-workflow',
        help=("""\
              Specifies a custom workflow to use for the image translate.
              Workflow should be relative to the image_import directory here:
              []({0}). For example: ``{1}''""".format(
                  _WORKFLOWS_URL, _OS_CHOICES[sorted(_OS_CHOICES.keys())[0]])),
        hidden=True
    )

    daisy_utils.AddCommonDaisyArgs(parser)
    parser.display_info.AddCacheUpdater(flags.ImagesCompleter)

  def Run(self, args):
    log.warning('Importing image, this may take up to 1 hour.')

    storage_client = storage_api.StorageClient()
    daisy_bucket = daisy_utils.GetAndCreateDaisyBucket(
        storage_client=storage_client)
    image_uuid = uuid.uuid4()

    variables = ['image_name={}'.format(args.image_name)]
    if args.source_image:
      # If we're starting from an image, then we've already imported it.
      workflow = '{0}{1}'.format(_WORKFLOW_DIR, _GetTranslateWorkflow(args))
      ref = resources.REGISTRY.Parse(
          args.source_image,
          collection='compute.images',
          params={'project': properties.VALUES.core.project.GetOrFail})
      # source_name should be of the form 'global/images/image-name'.
      source_name = ref.RelativeName()[len(ref.Parent().RelativeName() + '/'):]
      variables.append('source_image={}'.format(source_name))
    else:
      # Get the image into the scratch bucket, wherever it is now.
      if _IsLocalFile(args.source_file):
        gcs_uri = _UploadToGcs(args.async, args.source_file,
                               daisy_bucket, image_uuid)
      else:
        source_file = _MakeGcsUri(args.source_file)
        gcs_uri = _CopyToScratchBucket(source_file, image_uuid,
                                       storage_client, daisy_bucket)

      # Import and (maybe) translate from the scratch bucket.
      variables.append('source_disk_file={}'.format(gcs_uri))
      if args.translate:
        workflow = _IMPORT_AND_TRANSLATE_WORKFLOW
        variables.append(
            'translate_workflow={}'.format(_GetTranslateWorkflow(args)))
      else:
        workflow = _IMPORT_WORKFLOW

    return daisy_utils.RunDaisyBuild(args, workflow, ','.join(variables),
                                     daisy_bucket=daisy_bucket)

Import.detailed_help = {
    'brief': 'Import a Google Compute Engine image',
    'DESCRIPTION': """\
        *{command}* imports Virtual Disk images, such as VMWare VMDK files
        and VHD files, into Google Compute Engine.

        Importing images involves 3 steps:
        *  Upload the virtual disk file to Google Cloud Storage.
        *  Import the image to Google Compute Engine.
        *  Translate the image to make a bootable image.
        This command will perform all three of these steps as necessary,
        depending on the input arguments specified by the user.

        This command uses the `--os` flag to choose the appropriate translation.
        You can omit the translation step using the `--no-translate` flag.
        """,
}
