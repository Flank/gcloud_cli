# -*- coding: utf-8 -*- #
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
"""Tests for the images import subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resources import InvalidResourceException
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import daisy_test_base
from tests.lib.surface.compute import test_resources

_DEFAULT_TIMEOUT = '7056s'


class ImageImportTest(daisy_test_base.DaisyBaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.regionalized = False

  def SetUp(self):
    self.source_disk = 'gs://31dd/source-image.vmdk'
    self.https_source_disk = ('https://storage.googleapis.com/'
                              '31dd/source-image.vmdk')
    self.local_source_disk = self.Touch(
        self.temp_path, 'source-image.vmdk', contents='diskcontents')
    self.local_source_disk_size = os.path.getsize(self.local_source_disk)
    self.source_image = 'my-image'
    self.image_name = self.source_image
    self.destination_image = 'my-translated-image'
    self.import_workflow = '../workflows/image_import/import_image.wf.json'
    self.daisy_builder = 'gcr.io/compute-image-tools/daisy:release'

  def GetCopiedSource(self, regionalized=True):
    return ('gs://{0}/tmpimage/12345678-'
            '1234-5678-1234-567812345678-source-image.vmdk'.
            format(self.GetScratchBucketName(regionalized=regionalized)))

  def GetDaisyImportStep(self, regionalized=True):
    return self.cloudbuild_v1_messages.BuildStep(
        args=[
            '-gcs_path=gs://{0}/'.format(
                self.GetScratchBucketName(regionalized=regionalized)),
            '-default_timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-variables=image_name={0},source_disk_file={1}'.format(
                self.image_name,
                self.GetCopiedSource(regionalized=regionalized)),
            self.import_workflow,
        ],
        name=self.daisy_builder,
    )

  def GetDaisyImportTranslateStep(self, regionalized=True):
    return self.GetNetworkStep(include_zone=False)

  def GetNetworkStep(self, network=None, subnet=None, include_zone=True,
                     include_empty_network=False):
    daisy_vars_template = (
        '-variables=image_name={0},source_disk_file={1},translate_workflow={2}')
    daisy_vars = daisy_vars_template.format(
        self.image_name,
        self.GetCopiedSource(
            regionalized=self.regionalized),
        'ubuntu/translate_ubuntu_1604.wf.json')
    return super(ImageImportTest, self).GetNetworkStep(
        workflow='../workflows/image_import/import_and_translate.wf.json',
        daisy_vars=daisy_vars, operation=daisy_utils.ImageOperation.IMPORT,
        network=network, subnet=subnet, include_zone=include_zone,
        include_empty_network=include_empty_network)

  def AddStorageRewriteMock(self, regionalized=True):
    destination_bucket = self.GetScratchBucketName(regionalized=regionalized)

    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_v1_messages.StorageObjectsRewriteRequest(
            destinationBucket=destination_bucket,
            destinationObject=('tmpimage/12345678-1234-5678-1234-567812345678'
                               '-source-image.vmdk'),
            sourceBucket='31dd',
            sourceObject='source-image.vmdk',
        ),
        response=self.storage_v1_messages.RewriteResponse(
            resource=self.storage_v1_messages.Object(
                bucket=destination_bucket,
                name='source-image.vmdk',
                generation=123,
            ),
            done=True,
        ),
    )

  def AddStorageUploadMock(self, file_size=None, error=False):
    file_size = file_size or self.local_source_disk_size
    storage_msgs = self.mocked_storage_v1.MESSAGES_MODULE

    response = storage_msgs.Object(size=file_size)
    exception = None
    if error:
      response = None
      exception = http_error.MakeHttpError()

    self.mocked_storage_v1.objects.Insert.Expect(
        storage_msgs.StorageObjectsInsertRequest(
            bucket=self.GetScratchBucketName(regionalized=False),
            name=('tmpimage/12345678-1234-5678-1234-567812345678'
                  '-source-image.vmdk'),
            object=storage_msgs.Object(size=file_size)),
        response=response,
        exception=exception)

  def testCommonCase(self):
    self.PrepareDaisyMocks(
        self.GetDaisyImportTranslateStep(regionalized=self.regionalized),
        regionalized=self.regionalized)
    self.AddStorageRewriteMock(regionalized=self.regionalized)

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testCommonCaseNoTranslate(self):
    self.PrepareDaisyMocks(
        self.GetDaisyImportStep(regionalized=self.regionalized),
        regionalized=self.regionalized)
    self.AddStorageRewriteMock(regionalized=self.regionalized)

    self.Run("""
             compute images import {0}
             --source-file {1}
             --data-disk
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testHttpsLinkToGcsImage(self):
    """Make sure https:// URIs are converted correctly to gs:// ones.

    This test should behave *exactly* like the test above
    (testCommonCaseNoTranslate). gcloud ought to recognize a URI like
    https://storage.googleapis.com/bucket/image.vmdk and translate it to
    gs://bucket/image.vmdk automatically.
    """
    self.PrepareDaisyMocks(
        self.GetDaisyImportStep(regionalized=self.regionalized),
        regionalized=self.regionalized)
    self.AddStorageRewriteMock(regionalized=self.regionalized)

    self.Run("""
             compute images import {0}
             --source-file {1}
             --data-disk
             """.format(self.image_name, self.https_source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testNonGcsHttpsUriFails(self):
    """Ensure that only "https://" URLs that point to GCS are accepted."""

    # Old code (currently for BETA and GA) created Daisy scratch bucket even
    # if file path is not a valid GCS path. The new code first checks path
    # validity before creating Daisy scratch bucket, thus these mocks are
    # not needed.
    self.PrepareDaisyBucketMocks(regionalized=self.regionalized)

    with self.assertRaises(InvalidResourceException):
      self.Run("""
               compute images import {0}
               --source-file {1}
               --data-disk
               """.format(self.image_name,
                          'https://example.com/not-a-gcs-bucket/file.vmdk'))

  def testTranslateFromImage(self):
    target_workflow = '../workflows/image_import/import_from_image.wf.json'
    translate_workflow = 'ubuntu/translate_ubuntu_1604.wf.json'
    daisy_step = self.cloudbuild_v1_messages.BuildStep(
        args=[
            '-gcs_path=gs://{0}/'.format(
                self.GetScratchBucketName(regionalized=False)),
            '-default_timeout={0}'.format(_DEFAULT_TIMEOUT),
            ('-variables=image_name={0},'
             'translate_workflow={1},'
             'source_image=global/images/{2}').format(
                 self.destination_image,
                 translate_workflow,
                 self.source_image),
            target_workflow,
        ],
        name=self.daisy_builder,
    )
    self.PrepareDaisyMocks(daisy_step, regionalized=False)

    self.Run("""
             compute images import --source-image {0}
             --os ubuntu-1604 {1}
             """.format(self.source_image, self.destination_image))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testTranslateWithCustomWorkflow(self):
    target_workflow = '../workflows/image_import/import_from_image.wf.json'
    translate_workflow = 'ubuntu/translate_ubuntu_1604_custom.wf.json'
    daisy_step = self.cloudbuild_v1_messages.BuildStep(
        args=[
            '-gcs_path=gs://{0}/'.format(
                self.GetScratchBucketName(regionalized=False)),
            '-default_timeout={0}'.format(_DEFAULT_TIMEOUT),
            ('-variables=image_name={0},'
             'translate_workflow={1},'
             'source_image=global/images/{2}').format(
                 self.destination_image,
                 translate_workflow,
                 self.source_image),
            target_workflow,
        ],
        name=self.daisy_builder,
    )

    self.PrepareDaisyMocks(daisy_step, regionalized=False)

    self.Run("""
             compute images import --source-image {0}
             --custom-workflow ubuntu/translate_ubuntu_1604_custom.wf.json
             {1}
             """.format(self.source_image, self.destination_image))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testAsync(self):
    self.PrepareDaisyMocks(
        self.GetDaisyImportTranslateStep(regionalized=self.regionalized),
        async_flag=True, regionalized=self.regionalized)
    self.AddStorageRewriteMock(regionalized=self.regionalized)

    self.Run("""
             compute images import {0}
             --source-file {1} --async
             --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertErrContains('Created [https://cloudbuild.googleapis.com/'
                           'v1/projects/my-project/builds/1234]')

  def testTimeoutFlag(self):
    daisy_import_step = self.cloudbuild_v1_messages.BuildStep(
        args=[
            '-gcs_path=gs://{0}/'.format(
                self.GetScratchBucketName(regionalized=self.regionalized)),
            '-default_timeout=59s',  # Daisy timeout 2% sooner than Argo.
            '-variables=image_name={0},source_disk_file={1}'
            .format(self.image_name,
                    self.GetCopiedSource(regionalized=self.regionalized)),
            self.import_workflow,
        ],
        name=self.daisy_builder,
    )
    self.PrepareDaisyMocks(
        daisy_import_step, timeout='60s', regionalized=self.regionalized)
    self.AddStorageRewriteMock(regionalized=self.regionalized)

    self.Run("""
             compute images import {0}
             --source-file {1} --timeout 1m
             --data-disk
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testLongTimeoutFlag(self):
    daisy_import_step = self.cloudbuild_v1_messages.BuildStep(
        args=[
            '-gcs_path=gs://{0}/'.format(
                self.GetScratchBucketName(regionalized=self.regionalized)),
            '-default_timeout=21300s',  # Daisy timeout 5m sooner than Argo.
            '-variables=image_name={0},source_disk_file={1}'
            .format(self.image_name,
                    self.GetCopiedSource(regionalized=self.regionalized)),
            self.import_workflow,
        ],
        name=self.daisy_builder,
    )
    self.PrepareDaisyMocks(
        daisy_import_step, timeout='21600s', regionalized=self.regionalized)
    self.AddStorageRewriteMock(regionalized=self.regionalized)

    self.Run("""
             compute images import {0}
             --source-file {1} --timeout 6h
             --data-disk
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testLogLocation(self):
    log_location = 'foo/bar'
    self.PrepareDaisyMocks(
        self.GetDaisyImportStep(regionalized=self.regionalized),
        log_location=log_location, regionalized=self.regionalized)
    self.AddStorageRewriteMock(regionalized=self.regionalized)

    self.Run("""
             compute images import {0}
             --source-file {1} --log-location gs://{2}
             --data-disk
             """.format(self.image_name, self.source_disk, log_location))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testExitOnMissingPermissions(self):
    missing_permissions = self.crm_v1_messages.Policy(
        bindings=[],
    )
    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
        ),
        response=missing_permissions,
    )
    self.PrepareDaisyBucketMocks(regionalized=self.regionalized)

    scratch_bucket_name = self.GetScratchBucketName(
        regionalized=self.regionalized)
    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_v1_messages.StorageObjectsRewriteRequest(
            destinationBucket=scratch_bucket_name,
            destinationObject=('tmpimage/12345678-1234-5678-1234-567812345678'
                               '-source-image.vmdk'),
            sourceBucket='31dd',
            sourceObject='source-image.vmdk',
        ),
        response=self.storage_v1_messages.RewriteResponse(
            resource=self.storage_v1_messages.Object(
                bucket=scratch_bucket_name,
                name='source-image.vmdk',
                generation=123,
            ),
            done=True,
        ),
    )

    with self.assertRaises(console_io.UnattendedPromptError):
      self.Run("""
               compute images import {0}
               --source-file {1} --os ubuntu-1604
               """.format(self.image_name, self.source_disk))

  def testAddMissingPermissions(self):
    admin_permissions_binding = self.crm_v1_messages.Binding(
        members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
        role='roles/compute.admin',
    )

    missing_permissions = self.crm_v1_messages.Policy(
        bindings=[admin_permissions_binding],
    )
    self.PrepareDaisyMocks(
        self.GetDaisyImportTranslateStep(regionalized=self.regionalized),
        permissions=missing_permissions, regionalized=self.regionalized
    )
    self.AddStorageRewriteMock(regionalized=self.regionalized)

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project'),
        response=self.permissions,
    )

    self.mocked_crm_v1.projects.SetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource='my-project',
            setIamPolicyRequest=self.crm_v1_messages.SetIamPolicyRequest(
                policy=self.permissions,
            ),
        ),
        response=self.permissions,
    )

    self.Run("""
             compute images import {0}
             --source-file {1} --quiet
             --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testUploadLocalFile(self):
    self.PrepareDaisyMocks(
        self.GetDaisyImportStep(regionalized=False), regionalized=False)
    self.AddStorageUploadMock()

    self.Run("""
             compute images import {0}
             --source-file {1}
             --data-disk
             """.format(self.image_name, self.local_source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testUploadLocalFileWithSpacesInPath(self):
    """The same as the last test, except with spaces in the file path."""
    path_with_spaces = 'my cool directory/source image.vmdk'
    temp_file_path = self.Touch(
        self.temp_path,
        path_with_spaces,
        contents='diskcontents',
        makedirs=True)
    temp_file_size = os.path.getsize(temp_file_path)
    self.PrepareDaisyMocks(
        self.GetDaisyImportStep(regionalized=False), regionalized=False)
    self.AddStorageUploadMock(file_size=temp_file_size)

    self.Run("""
             compute images import {0}
             --source-file "{1}"
             --data-disk
             """.format(self.image_name, temp_file_path))

    self.AssertOutputContains("""\
        """, normalize_space=True)

  def testWarnOnOva(self):
    source_disk_file_name = 'source-image.ova'
    daisy_bucket_name = self.GetScratchBucketName(
        regionalized=self.regionalized)
    source_disk = 'gs://31dd/{0}'.format(source_disk_file_name)
    copied_source = ('gs://{0}/tmpimage/12345678-'
                     '1234-5678-1234-567812345678-source-image.ova'
                     .format(daisy_bucket_name))

    daisy_import_translate_step = self.cloudbuild_v1_messages.BuildStep(
        args=[
            '-gcs_path=gs://{0}/'.format(daisy_bucket_name),
            '-default_timeout={0}'.format(_DEFAULT_TIMEOUT),
            ('-variables=image_name={0},'
             'source_disk_file={1},'
             'translate_workflow={2}').format(
                 self.image_name, copied_source,
                 'ubuntu/translate_ubuntu_1604.wf.json'),
            '../workflows/image_import/import_and_translate.wf.json',
        ],
        name=self.daisy_builder,
    )
    self.PrepareDaisyMocks(
        daisy_import_translate_step, source_disk=source_disk_file_name,
        regionalized=self.regionalized)

    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_v1_messages.StorageObjectsRewriteRequest(
            destinationBucket=daisy_bucket_name,
            destinationObject=('tmpimage/12345678-1234-5678-1234-567812345678'
                               '-source-image.ova'),
            sourceBucket='31dd',
            sourceObject='source-image.ova',
        ),
        response=self.storage_v1_messages.RewriteResponse(
            resource=self.storage_v1_messages.Object(
                bucket=daisy_bucket_name,
                name='source-image.ova',
                generation=123,
            ),
            done=True,
        ),
    )

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             """.format(self.image_name, source_disk))

    self.AssertErrContains('The specified input file may contain more than '
                           'one virtual disk.')
    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testGcloudBailsWhenFileUploadFails(self):
    self.PrepareDaisyBucketMocks(regionalized=False)
    self.AddStorageUploadMock(error=True)

    with self.assertRaises(storage_api.UploadError):
      self.Run("""
               compute images import {0}
               --source-file {1}
               --data-disk
               """.format(self.image_name, self.local_source_disk))

  def testDaisyUsesZoneArg(self):
    self.doZoneFlagTest()

  def doZoneFlagTest(self, add_zone_cli_arg=True):
    scratch_bucket_name = self.GetScratchBucketName(
        regionalized=self.regionalized)

    import_and_translate_step_with_zone = self.cloudbuild_v1_messages.BuildStep(  # pylint: disable=line-too-long
        args=[
            '-zone=us-west1-c',
            '-gcs_path=gs://{0}/'.format(scratch_bucket_name),
            '-default_timeout={0}'.format(_DEFAULT_TIMEOUT),
            ('-variables=image_name={0},'
             'source_disk_file={1},'
             'translate_workflow={2}').format(
                 self.image_name,
                 self.GetCopiedSource(regionalized=self.regionalized),
                 'ubuntu/translate_ubuntu_1604.wf.json'),
            '../workflows/image_import/import_and_translate.wf.json'
        ],
        name=self.daisy_builder,
    )

    self.PrepareDaisyMocks(
        import_and_translate_step_with_zone, regionalized=self.regionalized)
    self.AddStorageRewriteMock(self.regionalized)

    cmd = 'compute images import {0} --source-file {1} --os ubuntu-1604'
    if add_zone_cli_arg:
      cmd += ' --zone us-west1-c'

    self.Run(cmd.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testMissingSource(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--source-file | --source-image) must be specified.'):
      self.Run("""
               compute images import {0} --os ubuntu-1604
               """.format(self.destination_image))

  def testMissingNoTranslateOrOsFlags(self):
    with self.AssertRaisesArgumentErrorMatches(
        ('Exactly one of (--custom-workflow | --data-disk | --os) '
         'must be specified.')):
      self.Run("""
               compute images import --source-file {0} {1}
               """.format(self.source_image, self.destination_image))

  def testInvalidImageNames(self):
    invalid_names = ['test-',
                     'Hello',
                     '4image',
                     'my_image',
                     ('this-is-a-very-long-image-name-that-is-longer-than'
                      '-64-characters-but-otherwise-ok'),
                    ]
    for name in invalid_names:
      with self.AssertRaisesExceptionRegexp(exceptions.InvalidArgumentException,
                                            'Name must start with a lowercase'):
        self.Run("""
                 compute images import {0}
                 --source-file {1} --os ubuntu-1604
                 """.format(name, self.source_disk))

  def testExistingImage(self):
    self.make_requests.side_effect = iter([
        [test_resources.IMAGES[0]],
    ])

    name = 'my-image'
    error = r'The image \[{0}\] already exists'.format(name)

    with self.AssertRaisesExceptionRegexp(
        exceptions.InvalidArgumentException, error):
      self.Run("""
               compute images import {0}
               --source-file {1} --os ubuntu-1604
               """.format(name, self.source_disk))

  def testTarGzFile(self):
    self.PrepareDaisyBucketMocks(regionalized=False)

    with self.AssertRaisesToolExceptionRegexp(
        '.+does not support compressed archives.+'):
      self.Run("""
               compute images import {0}
               --data-disk
               --source-file my-cool-file.tar.gz
               """.format(self.image_name))

  def testUploadLocalFileGsutil(self):
    properties.VALUES.storage.use_gsutil.Set(True)
    mocked_run_gsutil_command = self.StartPatch(
        'googlecloudsdk.api_lib.storage.storage_util.RunGsutilCommand',
        return_value=0)

    self.PrepareDaisyMocks(
        self.GetDaisyImportStep(regionalized=False), regionalized=False)
    self.Run("""
             compute images import {0}
             --source-file {1}
             --data-disk
             """.format(self.image_name, self.local_source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

    # Expect exactly one call to "gsutil cp <local file> <GCS URI>".
    mocked_run_gsutil_command.assert_called_once_with(
        'cp',
        [self.local_source_disk, self.GetCopiedSource(regionalized=False)]
    )


class ImageImportTestBeta(ImageImportTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.regionalized = False


class ImageImportTestAlpha(ImageImportTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.regionalized = True

  def SetUp(self):
    self.tags = ['gce-daisy', 'gce-daisy-image-import']

  def testNoGooglePackagesInstall(self):
    daisy_import_translate_no_google_packages_step = (
        self.cloudbuild_v1_messages.BuildStep(
            args=[
                '-gcs_path=gs://{0}/'.format(self.GetScratchBucketName()),
                '-default_timeout={0}'.format(_DEFAULT_TIMEOUT),
                ('-variables=image_name={0},'
                 'source_disk_file={1},'
                 'translate_workflow={2},'
                 'install_gce_packages=false').format(
                     self.image_name, self.GetCopiedSource(),
                     'ubuntu/translate_ubuntu_1604.wf.json'),
                '../workflows/image_import/import_and_translate.wf.json',
            ],
            name=self.daisy_builder,)
    )
    self.PrepareDaisyMocks(daisy_import_translate_no_google_packages_step)
    self.AddStorageRewriteMock()

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604 --no-guest-environment
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testNonGcsHttpsUriFails(self):
    """Ensure that only "https://" URLs that point to GCS are accepted."""
    with self.assertRaises(InvalidResourceException):
      self.Run("""
               compute images import {0} --source-file {1} --data-disk
               """.format(
                   self.image_name,
                   'https://example.com/not-a-gcs-bucket/file.vmdk'))

  def testDaisyUsesZoneConfigProperty(self):
    properties.VALUES.compute.zone.Set('us-west1-c')
    self.doZoneFlagTest(add_zone_cli_arg=False)

  def doNetworkTestSuccess(self, daisy_step, cmd):
    self.PrepareDaisyMocks(daisy_step, regionalized=self.regionalized)
    self.AddStorageRewriteMock(regionalized=self.regionalized)
    self.Run(cmd)
    self.AssertOutputContains('[import-image] output', normalize_space=True)

  def testNetworkFlag(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStep(network=self.network, include_zone=False),
        """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --network {2}
        """.format(self.image_name, self.source_disk, self.network))

  def testSubnetFlag(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStep(network=self.network, subnet=self.subnet),
        """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --network {2} --subnet {3} --zone my-region-c
        """.format(
            self.image_name, self.source_disk, self.network, self.subnet))

  def testSubnetFlagNetworkVariableClearedIfNetworkFlagNotSpecified(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStep(
            network='', include_empty_network=True, subnet=self.subnet),
        """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --subnet {2} --zone my-region-c
        """.format(
            self.image_name, self.source_disk, self.subnet))

  def testSubnetFlagZoneAndRegionNotSpecified(self):
    error = r'Region or zone should be specified.'
    self.PrepareDaisyBucketMocks(regionalized=self.regionalized)
    self.AddStorageRewriteMock(regionalized=self.regionalized)

    with self.AssertRaisesExceptionRegexp(
        daisy_utils.SubnetException, error):
      self.Run("""
             compute images import {0} --source-file {1} --os ubuntu-1604
             --subnet {2}
             """.format(self.image_name, self.source_disk, self.subnet))

  def testSubnetFlagZoneAsProperty(self):
    properties.VALUES.compute.zone.Set('my-region-c')
    self.doNetworkTestSuccess(
        self.GetNetworkStep(network=self.network, subnet=self.subnet),
        """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --network {2} --subnet {3}
        """.format(
            self.image_name, self.source_disk, self.network, self.subnet))

  def testSubnetFlagRegionAsProperty(self):
    properties.VALUES.compute.region.Set('my-region')
    self.doNetworkTestSuccess(
        self.GetNetworkStep(
            network=self.network, subnet=self.subnet, include_zone=False),
        """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --network {2} --subnet {3}
        """.format(
            self.image_name, self.source_disk, self.network, self.subnet))

if __name__ == '__main__':
  test_case.main()
