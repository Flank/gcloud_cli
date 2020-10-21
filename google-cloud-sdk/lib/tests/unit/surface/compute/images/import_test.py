# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resources import InvalidResourceException
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import daisy_test_base
from tests.lib.surface.compute.images import test_resources

_DEFAULT_TIMEOUT = '6984s'


class ImageImportTest(daisy_test_base.DaisyBaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.source_disk = 'gs://31dd/source-image.vmdk'
    self.https_source_disk = ('https://storage.googleapis.com/'
                              '31dd/source-image.vmdk')
    self.local_source_disk = self.Touch(
        self.temp_path, 'source-image.vmdk', contents='diskcontents')
    self.local_source_disk_size = os.path.getsize(self.local_source_disk)
    self.source_image = 'source-image'
    self.image_name = 'my-image'
    self.destination_image = 'my-translated-image'
    self.import_workflow = '../workflows/image_import/import_image.wf.json'
    self.builder = daisy_utils._DEFAULT_BUILDER_DOCKER_PATTERN.format(
        executable=daisy_utils._IMAGE_IMPORT_BUILDER_EXECUTABLE,
        docker_image_tag=daisy_utils._DEFAULT_BUILDER_VERSION)
    self.tags = ['gce-daisy', 'gce-daisy-image-import']

  def GetCopiedSource(self, regionalized=True, daisy_bucket_name=None):
    return ('gs://{0}/tmpimage/12345678-'
            '1234-5678-1234-567812345678-source-image.vmdk'.format(
                daisy_bucket_name or
                self.GetScratchBucketName(regionalized=regionalized)))

  def GetImportStepForGSFile(self):
    import_vars = []
    daisy_utils.AppendArg(import_vars, 'source_file', self.GetCopiedSource())
    daisy_utils.AppendBoolArg(import_vars, 'data_disk')
    daisy_utils.AppendArg(
        import_vars, 'scratch_bucket_gcs_path',
        'gs://{0}/'.format(self.GetScratchBucketNameWithRegion()))
    daisy_utils.AppendArg(import_vars, 'timeout', _DEFAULT_TIMEOUT)
    daisy_utils.AppendArg(import_vars, 'client_id', 'gcloud')
    daisy_utils.AppendArg(import_vars, 'image_name', self.image_name)
    daisy_utils.AppendArg(import_vars, 'client_version',
                          config.CLOUD_SDK_VERSION)
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars,
        name=self.GetBuilder(region=self.GetScratchBucketRegion()))

  def GetImportStepForNonGSFile(self):
    import_vars = []
    daisy_utils.AppendArg(import_vars, 'source_file',
                          self.GetCopiedSource(regionalized=False))
    daisy_utils.AppendBoolArg(import_vars, 'data_disk')
    daisy_utils.AppendArg(
        import_vars, 'scratch_bucket_gcs_path',
        'gs://{0}/'.format(self.GetScratchBucketNameWithoutRegion()))
    daisy_utils.AppendArg(import_vars, 'timeout', _DEFAULT_TIMEOUT)
    daisy_utils.AppendArg(import_vars, 'client_id', 'gcloud')
    daisy_utils.AppendArg(import_vars, 'image_name', self.image_name)
    daisy_utils.AppendArg(import_vars, 'client_version',
                          config.CLOUD_SDK_VERSION)
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars,
        name=self.GetBuilder())

  def GetDaisyImportTranslateStep(self):
    return self.GetNetworkStepForImport(zone='')

  def GetNetworkStepForImport(self,
                              network=None,
                              subnet=None,
                              zone='my-region-c',
                              from_image=False,
                              storage_location='',
                              family=None,
                              description=None,
                              sysprep_windows=False,
                              daisy_bucket_name=None):
    import_vars = []
    if from_image:
      daisy_utils.AppendArg(import_vars, 'source_image', self.source_image)
    else:
      daisy_utils.AppendArg(
          import_vars, 'source_file',
          self.GetCopiedSource(
              regionalized=True, daisy_bucket_name=daisy_bucket_name))

    daisy_utils.AppendArg(import_vars, 'os', 'ubuntu-1604')
    if zone:
      daisy_utils.AppendArg(import_vars, 'zone', zone)
    if storage_location:
      daisy_utils.AppendArg(import_vars, 'storage_location', storage_location)

    daisy_utils.AppendArg(
        import_vars, 'scratch_bucket_gcs_path', 'gs://{0}/'.format(
            daisy_bucket_name or
            self.GetScratchBucketName(not from_image or storage_location,
                                      storage_location if from_image else '')))

    daisy_utils.AppendArg(import_vars, 'timeout', _DEFAULT_TIMEOUT)
    daisy_utils.AppendArg(import_vars, 'client_id', 'gcloud')
    daisy_utils.AppendArg(import_vars, 'image_name', self.image_name)

    if subnet:
      daisy_utils.AppendArg(import_vars, 'subnet', subnet)

    if network:
      daisy_utils.AppendArg(import_vars, 'network', network)

    if description:
      daisy_utils.AppendArg(import_vars, 'description', description)

    if family:
      daisy_utils.AppendArg(import_vars, 'family', family)

    if sysprep_windows:
      daisy_utils.AppendBoolArg(import_vars, 'sysprep_windows')

    daisy_utils.AppendArg(import_vars, 'client_version',
                          config.CLOUD_SDK_VERSION)
    region = ''
    if storage_location and from_image:
      region = storage_location
    elif not from_image:
      region = 'my-region'
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars, name=self.GetBuilder(zone=zone, region=region))

  def AddStorageRewriteMock(self, daisy_bucket_name=None):
    destination_bucket = daisy_bucket_name or self.GetScratchBucketNameWithRegion(
    )

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
            bucket=self.GetScratchBucketNameWithoutRegion(),
            name=('tmpimage/12345678-1234-5678-1234-567812345678'
                  '-source-image.vmdk'),
            object=storage_msgs.Object(size=file_size)),
        response=response,
        exception=exception)

  def testCommonCase(self):
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetDaisyImportTranslateStep())
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testCommonCaseNoTranslate(self):
    self.PrepareDaisyMocksWithRegionalBucket(self.GetImportStepForGSFile())
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

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
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetImportStepForGSFile())
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1}
             --data-disk
             """.format(self.image_name, self.https_source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testTranslateFromImage(self):
    translate_workflow = 'ubuntu/translate_ubuntu_1604.wf.json'
    daisy_step = self.GetImportStepForTranslateFromImage(translate_workflow)
    self.PrepareDaisyMocksWithDefaultBucket(daisy_step)

    self.Run("""
             compute images import --source-image {0}
             --os ubuntu-1604 {1}
             """.format(self.source_image, self.destination_image))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testTranslateWithCustomWorkflow(self):
    translate_workflow = 'ubuntu/translate_ubuntu_1604_custom.wf.json'
    daisy_step = self.GetImportStepForTranslateFromImage(translate_workflow)

    self.PrepareDaisyMocksWithDefaultBucket(daisy_step)

    self.Run("""
             compute images import --source-image {0}
             --custom-workflow ubuntu/translate_ubuntu_1604_custom.wf.json
             {1}
             """.format(self.source_image, self.destination_image))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def GetImportStepForTranslateFromImage(self, translate_workflow):
    default_translate_workflow = 'ubuntu/translate_ubuntu_1604.wf.json'
    import_vars = []
    daisy_utils.AppendArg(import_vars, 'source_image', self.source_image)
    if default_translate_workflow != translate_workflow:
      daisy_utils.AppendArg(import_vars, 'custom_translate_workflow',
                            translate_workflow)
    else:
      daisy_utils.AppendArg(import_vars, 'os', 'ubuntu-1604')
    daisy_utils.AppendArg(
        import_vars, 'scratch_bucket_gcs_path',
        'gs://{0}/'.format(self.GetScratchBucketNameWithoutRegion()))
    daisy_utils.AppendArg(import_vars, 'timeout', _DEFAULT_TIMEOUT)
    daisy_utils.AppendArg(import_vars, 'client_id', 'gcloud')
    daisy_utils.AppendArg(import_vars, 'image_name', self.destination_image)
    daisy_utils.AppendArg(import_vars, 'client_version',
                          config.CLOUD_SDK_VERSION)
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars, name=self.GetBuilder())

  def testAsync(self):
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetDaisyImportTranslateStep(),
        async_flag=True)
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1} --async
             --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertErrContains('Created [https://cloudbuild.googleapis.com/'
                           'v1/projects/my-project/builds/1234]')

  def testDescription(self):
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetNetworkStepForImport(zone='',
                                     description='custom ubuntu image'))
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             --description="custom ubuntu image"
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testFamily(self):
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetNetworkStepForImport(zone='', family='ubuntu'))
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             --family ubuntu
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testSysprepFlagIsPropagated(self):
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetNetworkStepForImport(sysprep_windows=True))
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks(source_file_bucket_check=False)

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             --zone my-region-c
             --sysprep-windows
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testSysprepFlagHasNegative(self):
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetNetworkStepForImport(sysprep_windows=False))
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks(source_file_bucket_check=False)

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             --zone my-region-c
             --no-sysprep-windows
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testTimeoutFlag(self):
    # Daisy timeout 2% sooner than Argo.
    daisy_import_step = self.GetImportStepForTimeoutTest(59)
    self.PrepareDaisyMocksWithRegionalBucket(daisy_import_step, timeout='60s')
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1} --timeout 1m
             --data-disk
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testLongTimeoutFlag(self):
    # Daisy timeout 5m sooner than Argo.
    daisy_import_step = self.GetImportStepForTimeoutTest(21300)
    self.PrepareDaisyMocksWithRegionalBucket(
        daisy_import_step, timeout='21600s')
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1} --timeout 6h
             --data-disk
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def GetImportStepForTimeoutTest(self, timeout):
    import_vars = []
    daisy_utils.AppendArg(import_vars, 'source_file', self.GetCopiedSource())
    daisy_utils.AppendBoolArg(import_vars, 'data_disk')
    daisy_utils.AppendArg(
        import_vars, 'scratch_bucket_gcs_path',
        'gs://{0}/'.format(self.GetScratchBucketNameWithRegion()))
    daisy_utils.AppendArg(import_vars, 'timeout', '{}s'.format(timeout))
    daisy_utils.AppendArg(import_vars, 'client_id', 'gcloud')
    daisy_utils.AppendArg(import_vars, 'image_name', self.image_name)
    daisy_utils.AppendArg(import_vars, 'client_version',
                          config.CLOUD_SDK_VERSION)
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars,
        name=self.GetBuilder(region=self.GetScratchBucketRegion()))

  def testLogLocationDir(self):
    self.doTestLogLocation('gs://foo/bar')
    self.doTestLogLocation('https://storage.googleapis.com/foo/bar')

  def testLogLocationDirTrailingSlash(self):
    self.doTestLogLocation('gs://foo/bar/')
    self.doTestLogLocation('https://storage.googleapis.com/foo/bar/')

  def testLogLocationBucketOnly(self):
    self.doTestLogLocation('gs://foo')
    self.doTestLogLocation('https://storage.googleapis.com/foo')

  def doTestLogLocation(self, log_location):
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetImportStepForGSFile(), log_location=log_location)
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1} --log-location {2}
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

    self._ExpectServiceUsage()
    self._ExpectIamRolesGet(
        is_import=True, permissions=missing_permissions, skip_compute=True)

    get_request = self.crm_v1_messages \
        .CloudresourcemanagerProjectsGetIamPolicyRequest(
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(
                options=self.crm_v1_messages.GetPolicyOptions(
                    requestedPolicyVersion=
                    iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
            resource='my-project')
    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        request=get_request,
        response=missing_permissions,
    )
    self.PrepareDaisyBucketMocksWithRegion()

    scratch_bucket_name = self.GetScratchBucketNameWithRegion()
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
    self.prepareArtifactRegistryMocks()

    with self.assertRaises(console_io.UnattendedPromptError):
      self.Run("""
               compute images import {0}
               --source-file {1} --os ubuntu-1604
               """.format(self.image_name, self.source_disk))

  def testAllowFailedServiceAccountPermissionModification(self):
    actual_permissions = self.crm_v1_messages.Policy(bindings=[
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_USER),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR),
    ])
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetDaisyImportTranslateStep(), permissions=actual_permissions)
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    # mock for 2 service accounts.
    for _ in range(2):
      self.mocked_crm_v1.projects.GetIamPolicy.Expect(
          request=(
              self.crm_v1_messages
              .CloudresourcemanagerProjectsGetIamPolicyRequest(
                  getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(
                      options=self.crm_v1_messages.GetPolicyOptions(
                          requestedPolicyVersion=iam_util
                          .MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
                  resource='my-project')),
          response=self.permissions,
      )
      self.mocked_crm_v1.projects.SetIamPolicy.Expect(
          self.crm_v1_messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
              resource='my-project',
              setIamPolicyRequest=self.crm_v1_messages.SetIamPolicyRequest(
                  policy=self.permissions,),
          ),
          exception=api_exceptions.HttpForbiddenError('response', 'content',
                                                      'url'))
    self.Run("""
             compute images import {0}
             --source-file {1} --quiet
             --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains(
        """\
        [import-image] output
        """, normalize_space=True)

  def testAllowFailedIamGetRoles(self):
    self.PrepareDaisyBucketMocksWithRegion()
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()
    self._ExpectServiceUsage()

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    get_request = self.crm_v1_messages \
      .CloudresourcemanagerProjectsGetIamPolicyRequest(
          getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(
              options=self.crm_v1_messages.GetPolicyOptions(
                  requestedPolicyVersion=
                  iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
          resource='my-project')
    actual_permissions = self.crm_v1_messages.Policy(bindings=[])
    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        request=get_request,
        response=actual_permissions,
    )

    self.mocked_iam_v1.roles.Get.Expect(
        self.iam_v1_messages.IamRolesGetRequest(
            name=daisy_utils.ROLE_COMPUTE_ADMIN),
        exception=api_exceptions.HttpForbiddenError('response', 'content',
                                                    'url'))
    self.mocked_iam_v1.roles.Get.Expect(
        self.iam_v1_messages.IamRolesGetRequest(
            name=daisy_utils.ROLE_COMPUTE_STORAGE_ADMIN),
        exception=api_exceptions.HttpForbiddenError('response', 'content',
                                                    'url'))

    # Called once for each missed service account role.
    self._ExpectAddIamPolicyBinding(5)

    self._ExpectCloudBuild(self.GetDaisyImportTranslateStep())

    self.Run("""
             compute images import {0}
             --source-file {1} --quiet
             --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains(
        """\
        [import-image] output
        """, normalize_space=True)

  def testEditorPermissionIsSufficientForComputeAccount(self):
    actual_permissions = self.crm_v1_messages.Policy(bindings=[
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_COMPUTE_ADMIN),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_USER),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR),
        self.crm_v1_messages.Binding(
            members=[
                'serviceAccount:123456-compute@developer.gserviceaccount.com'
            ],
            role=daisy_utils.ROLE_EDITOR),
    ])
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetDaisyImportTranslateStep(),
        permissions=actual_permissions
    )
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1} --quiet
             --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testCustomRolePermissionIsSufficientForComputeAccount(self):
    actual_permissions = self.crm_v1_messages.Policy(bindings=[
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_COMPUTE_ADMIN),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_USER),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR),
        self.crm_v1_messages.Binding(
            members=[
                'serviceAccount:123456-compute@developer.gserviceaccount.com'
            ],
            role='roles/custom'),
    ])
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetDaisyImportTranslateStep(),
        permissions=actual_permissions
    )
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1} --quiet
             --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def prepareArtifactRegistryMocks(self,
                                   source_file_bucket_check=True,
                                   location='',
                                   regionalized=True):
    pass

  def testAddMissingPermissions(self):
    actual_permissions = self.crm_v1_messages.Policy(bindings=[
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_COMPUTE_ADMIN),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR),
        self.crm_v1_messages.Binding(
            members=[
                'serviceAccount:123456-compute@developer.gserviceaccount.com'
            ],
            role=daisy_utils.ROLE_COMPUTE_STORAGE_ADMIN),
    ])
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetDaisyImportTranslateStep(),
        permissions=actual_permissions
    )
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    # Called once for each missed service account role.
    self._ExpectAddIamPolicyBinding(2)

    self.Run("""
             compute images import {0}
             --source-file {1} --quiet
             --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testUploadLocalFile(self):
    self.PrepareDaisyMocksWithDefaultBucket(
        self.GetImportStepForNonGSFile())
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
    self.PrepareDaisyMocksWithDefaultBucket(
        self.GetImportStepForNonGSFile())
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
    daisy_bucket_name = self.GetScratchBucketNameWithRegion()
    source_disk = 'gs://31dd/{0}'.format(source_disk_file_name)
    copied_source = ('gs://{0}/tmpimage/12345678-'
                     '1234-5678-1234-567812345678-source-image.ova'
                     .format(daisy_bucket_name))

    daisy_import_translate_step = self.GetImportStepForWarnOnOva(
        copied_source, daisy_bucket_name)
    self.PrepareDaisyMocksWithRegionalBucket(daisy_import_translate_step)

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
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             """.format(self.image_name, source_disk))

    self.AssertErrContains('The specified input file may contain more than '
                           'one virtual disk.')
    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def GetImportStepForWarnOnOva(self, copied_source, daisy_bucket_name):
    import_vars = []
    daisy_utils.AppendArg(import_vars, 'source_file', copied_source)
    daisy_utils.AppendArg(import_vars, 'os', 'ubuntu-1604')
    daisy_utils.AppendArg(
        import_vars, 'scratch_bucket_gcs_path',
        'gs://{0}/'.format(daisy_bucket_name))
    daisy_utils.AppendArg(import_vars, 'timeout', _DEFAULT_TIMEOUT)
    daisy_utils.AppendArg(import_vars, 'client_id', 'gcloud')
    daisy_utils.AppendArg(import_vars, 'image_name', self.image_name)
    daisy_utils.AppendArg(import_vars, 'client_version',
                          config.CLOUD_SDK_VERSION)
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars,
        name=self.GetBuilder(region=self.GetScratchBucketRegion()))

  def testGcloudBailsWhenFileUploadFails(self):
    self.PrepareDaisyBucketMocksWithoutRegion()
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
    import_and_translate_step_with_zone = self.GetImportStepForZoneFlagTest()

    self.PrepareDaisyMocksWithRegionalBucket(
        import_and_translate_step_with_zone)
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks(
        source_file_bucket_check=False, location='us-west1')

    cmd = 'compute images import {0} --source-file {1} --os ubuntu-1604'
    if add_zone_cli_arg:
      cmd += ' --zone us-west1-c'

    self.Run(cmd.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def GetImportStepForZoneFlagTest(self):
    import_vars = []
    daisy_utils.AppendArg(import_vars, 'source_file', self.GetCopiedSource())
    daisy_utils.AppendArg(import_vars, 'os', 'ubuntu-1604')
    daisy_utils.AppendArg(import_vars, 'zone', 'us-west1-c')
    daisy_utils.AppendArg(
        import_vars, 'scratch_bucket_gcs_path',
        'gs://{0}/'.format(self.GetScratchBucketNameWithRegion()))
    daisy_utils.AppendArg(import_vars, 'timeout', _DEFAULT_TIMEOUT)
    daisy_utils.AppendArg(import_vars, 'client_id', 'gcloud')
    daisy_utils.AppendArg(import_vars, 'image_name', self.image_name)
    daisy_utils.AppendArg(import_vars, 'client_version',
                          config.CLOUD_SDK_VERSION)

    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars, name=self.GetBuilder(zone='us-west1-c'))

  def GetBuilder(self, zone='', region=''):
    if self.builder:
      return self.builder
    return daisy_utils._DEFAULT_BUILDER_DOCKER_PATTERN.format(
        executable=daisy_utils._IMAGE_IMPORT_BUILDER_EXECUTABLE,
        docker_image_tag=daisy_utils._DEFAULT_BUILDER_VERSION)

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
    self.PrepareDaisyBucketMocksWithoutRegion()

    with self.AssertRaisesToolExceptionRegexp(
        '.+does not support compressed archives.+'):
      self.Run("""
               compute images import {0}
               --data-disk
               --source-file my-cool-file.tar.gz
               """.format(self.image_name))

  def testNoGooglePackagesInstall(self):
    import_step = self.GetImportStepForNoGooglePackageInstall()
    self.PrepareDaisyMocksWithRegionalBucket(import_step)
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604 --no-guest-environment
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def GetImportStepForNoGooglePackageInstall(self):
    import_vars = []
    daisy_utils.AppendArg(import_vars, 'source_file', self.GetCopiedSource())
    daisy_utils.AppendArg(import_vars, 'os', 'ubuntu-1604')
    daisy_utils.AppendArg(
        import_vars, 'scratch_bucket_gcs_path',
        'gs://{0}/'.format(self.GetScratchBucketNameWithRegion()))
    daisy_utils.AppendArg(import_vars, 'timeout', _DEFAULT_TIMEOUT)
    daisy_utils.AppendArg(import_vars, 'client_id', 'gcloud')
    daisy_utils.AppendArg(import_vars, 'image_name', self.image_name)
    daisy_utils.AppendBoolArg(import_vars, 'no_guest_environment')
    daisy_utils.AppendArg(import_vars, 'client_version',
                          config.CLOUD_SDK_VERSION)
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars,
        name=self.GetBuilder(region=self.GetScratchBucketRegion()))

  def testNonGcsHttpsUriFails(self):
    """Ensure that only "https://" URLs that point to GCS are accepted."""
    with self.assertRaises(InvalidResourceException):
      self.Run("""
        compute images import {0} --source-file {1} --data-disk
        """.format(self.image_name,
                   'https://example.com/not-a-gcs-bucket/file.vmdk'))

  def testDaisyUsesZoneConfigProperty(self):
    properties.VALUES.compute.zone.Set('us-west1-c')
    self.doZoneFlagTest(add_zone_cli_arg=False)

  def doNetworkTestSuccess(self,
                           daisy_step,
                           cmd,
                           regionalized=True,
                           from_image=False,
                           zone_included=False,
                           scratch_bucket_location='',
                           wrapper_location=''):
    if regionalized:
      self.PrepareDaisyMocksWithRegionalBucket(
          daisy_step,
          match_source_file_region=not from_image,
          scratch_bucket_location=scratch_bucket_location)
      if not from_image:
        self.AddStorageRewriteMock()
    else:
      self.PrepareDaisyMocksWithDefaultBucket(daisy_step)
    self.prepareArtifactRegistryMocks(
        source_file_bucket_check=not from_image and not zone_included,
        regionalized=regionalized or zone_included,
        location=wrapper_location)
    self.Run(cmd)
    self.AssertOutputContains('[import-image] output', normalize_space=True)

  def testNetworkFlag(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(
            network=self.network, zone=''), """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --network {2}
        """.format(self.image_name, self.source_disk, self.network))

  def testSubnetFlag(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(network=self.network, subnet=self.subnet),
        """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --network {2} --subnet {3} --zone my-region-c
        """.format(self.image_name, self.source_disk, self.network,
                   self.subnet),
        zone_included=True)

  def testSubnetFlagZoneAndRegionNotSpecified(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(subnet=self.subnet, zone=''),
        """
             compute images import {0} --source-file {1} --os ubuntu-1604
             --subnet {2}
             """.format(self.image_name, self.source_disk, self.subnet))

  def testSubnetFlagZoneAsProperty(self):
    properties.VALUES.compute.zone.Set('my-region-c')
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(network=self.network, subnet=self.subnet),
        """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --network {2} --subnet {3}
        """.format(self.image_name, self.source_disk, self.network,
                   self.subnet),
        zone_included=True)

  def testSubnetFlagRegionAsProperty(self):
    properties.VALUES.compute.region.Set('my-region')
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(
            network=self.network, subnet=self.subnet, zone=''),
        """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --network {2} --subnet {3}
        """.format(
            self.image_name, self.source_disk, self.network, self.subnet))

  def testNetworkFlagFromImage(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(
            network=self.network, zone='', from_image=True),
        """
        compute images import {0} --source-image {1} --os ubuntu-1604
        --network {2}
        """.format(
            self.image_name, self.source_image, self.network),
        regionalized=False, from_image=True)

  def testSubnetFlagFromImage(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(
            network=self.network, subnet=self.subnet, from_image=True),
        """
        compute images import {0} --source-image {1} --os ubuntu-1604
        --network {2} --subnet {3} --zone my-region-c
        """.format(self.image_name, self.source_image, self.network,
                   self.subnet),
        regionalized=False,
        from_image=True,
        zone_included=True)

  def testScratchBucketCreatedInSourceRegion(self):
    import_step = self.GetNetworkStepForImport(zone='')

    self.PrepareDaisyMocks(
        import_step, timeout='7200s', log_location=None, permissions=None,
        async_flag=False, is_import=True)
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(bucket='31dd'),
        response=self.storage_v1_messages.Bucket(
            name='31dd',
            storageClass='REGIONAL',
            location=self.GetScratchBucketRegion()
        ),
    )

    daisy_bucket_name = self.GetScratchBucketNameWithRegion()
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=daisy_bucket_name),
        exception=api_exceptions.HttpNotFoundError(None, None, None))

    daisy_bucket = self.storage_v1_messages.Bucket(
        kind='storage#bucket',
        name=daisy_bucket_name,
        location=self.GetScratchBucketRegion(),
    )
    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=daisy_bucket,
            project='my-project',
        ),
        response=self.storage_v1_messages.Bucket(id=daisy_bucket_name))
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_v1_messages.StorageBucketsListRequest(
            project='my-project',
            prefix=daisy_bucket_name,
        ),
        response=self.storage_v1_messages.Buckets(
            items=[self.storage_v1_messages.Bucket(id=daisy_bucket_name)]))

    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testScratchBucketCreatedEvenIfDefaultAlreadyExistsInAnotherProject(self):
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(bucket='31dd'),
        response=self.storage_v1_messages.Bucket(
            name='31dd',
            storageClass='REGIONAL',
            location=self.GetScratchBucketRegion()
        ),
    )

    daisy_bucket_name = self.GetScratchBucketNameWithRegion()
    daisy_bucket = self.storage_v1_messages.Bucket(
        kind='storage#bucket',
        name=daisy_bucket_name,
        location=self.GetScratchBucketRegion(),
    )

    # Bucket exists when searched by name and is accessible
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=daisy_bucket_name),
        response=daisy_bucket)

    # But, it's not in the current project
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_v1_messages.StorageBucketsListRequest(
            project='my-project',
            prefix=daisy_bucket_name,
        ),
        response=self.storage_v1_messages.Buckets(items=[]))

    # Try another, slightly different bucket name
    daisy_utils.bucket_random_suffix_override = '12345678'
    daisy_bucket_name = '{0}-{1}'.format(
        daisy_bucket_name, daisy_utils.bucket_random_suffix_override)

    daisy_bucket = self.storage_v1_messages.Bucket(
        kind='storage#bucket',
        name=daisy_bucket_name,
        location=self.GetScratchBucketRegion(),
    )

    # Doesn't exist
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=daisy_bucket_name),
        exception=api_exceptions.HttpNotFoundError(None, None, None))
    # Create it
    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=daisy_bucket,
            project='my-project',
        ),
        response=self.storage_v1_messages.Bucket(id=daisy_bucket_name))
    # Make sure it's in the current project
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_v1_messages.StorageBucketsListRequest(
            project='my-project',
            prefix=daisy_bucket_name,
        ),
        response=self.storage_v1_messages.Buckets(
            items=[self.storage_v1_messages.Bucket(id=daisy_bucket_name)]))

    self.AddStorageRewriteMock(daisy_bucket_name=daisy_bucket_name)
    self.prepareArtifactRegistryMocks()

    import_step = self.GetNetworkStepForImport(
        zone='', daisy_bucket_name=daisy_bucket_name)
    self.PrepareDaisyMocks(
        import_step, timeout='7200s', log_location=None, permissions=None,
        async_flag=False, is_import=True)

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testFailOnAllScratchBucketsExistInAnotherProject(self):
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(bucket='31dd'),
        response=self.storage_v1_messages.Bucket(
            name='31dd',
            storageClass='REGIONAL',
            location=self.GetScratchBucketRegion()
        ),
    )

    daisy_bucket_name = self.GetScratchBucketNameWithRegion()
    daisy_bucket = self.storage_v1_messages.Bucket(
        kind='storage#bucket',
        name=daisy_bucket_name,
        location=self.GetScratchBucketRegion(),
    )

    # Bucket exists when searched by name and is accessible
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=daisy_bucket_name),
        response=daisy_bucket)

    # But, it's not in the current project
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_v1_messages.StorageBucketsListRequest(
            project='my-project',
            prefix=daisy_bucket_name,
        ),
        response=self.storage_v1_messages.Buckets(items=[]))

    # Try another, slightly different bucket name
    daisy_utils.bucket_random_suffix_override = '12345678'
    daisy_bucket_name = '{0}-{1}'.format(
        daisy_bucket_name, daisy_utils.bucket_random_suffix_override)

    daisy_bucket = self.storage_v1_messages.Bucket(
        kind='storage#bucket',
        name=daisy_bucket_name,
        location=self.GetScratchBucketRegion(),
    )
    for _ in range(10):
      # This one also exists
      self.mocked_storage_v1.buckets.Get.Expect(
          self.storage_v1_messages.StorageBucketsGetRequest(
              bucket=daisy_bucket_name),
          response=daisy_bucket)
      # Also in another project
      self.mocked_storage_v1.buckets.List.Expect(
          self.storage_v1_messages.StorageBucketsListRequest(
              project='my-project',
              prefix=daisy_bucket_name,
          ),
          response=self.storage_v1_messages.Buckets(items=[]))

    with self.AssertRaisesExceptionMatches(
        daisy_utils.DaisyBucketCreationException,
        r'Unable to create a temporary bucket `my-project-daisy-bkt-my-region` needed for the operation to proceed as it exists in another project.'
    ):
      self.Run("""
                 compute images import {0}
                 --source-file {1} --os ubuntu-1604
                 """.format(self.image_name, self.source_disk))

  def testSourceFileBucketOnlyGCSPath(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        r'Invalid value for [source-file]: must be a path to an object in Google Cloud Storage'
    ):
      self.Run("""
                 compute images import {0}
                 --source-file gs://bucket --os ubuntu-1604
                 """.format(self.image_name))

  def testStorageLocationFlagFromGCSFileZoneSpecified(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(
            storage_location='storage-region', zone='zone-region-c'),
        """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --zone zone-region-c --storage-location storage-region
        """.format(self.image_name, self.source_disk),
        zone_included=True,
        wrapper_location='zone-region')

  def testStorageLocationFlagFromGCSFileZoneNotSpecified(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(
            storage_location='storage-region', zone=''),
        """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --storage-location storage-region
        """.format(self.image_name, self.source_disk),
        zone_included=False,
        wrapper_location='my-region')

  def testStorageLocationFlagFromImage(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(
            network=self.network,
            from_image=True,
            storage_location='storage-region'),
        """
        compute images import {0} --source-image {1} --os ubuntu-1604
        --network {2} --storage-location storage-region --zone my-region-c
        """.format(self.image_name, self.source_image, self.network),
        regionalized=True,
        from_image=True,
        zone_included=True,
        scratch_bucket_location='storage-region')


class ImageImportTestBeta(ImageImportTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    super(ImageImportTestBeta, self).SetUp()
    self.builder = ''

  def prepareArtifactRegistryMocks(self,
                                   source_file_bucket_check=True,
                                   location='',
                                   regionalized=True):
    region = self.GetScratchBucketRegion().lower() if not location else location
    if source_file_bucket_check:
      self.mocked_storage_v1.buckets.Get.Expect(
          self.storage_v1_messages.StorageBucketsGetRequest(bucket='31dd'),
          response=self.storage_v1_messages.Bucket(
              name='31dd', storageClass='REGIONAL', location=region),
      )
    if regionalized:
      location = 'projects/compute-image-tools/locations/{}'.format(region)
      repo_name = '{}/repositories/wrappers'.format(location)
      package_name = '{}/packages/gce_vm_image_import'.format(repo_name)

      msgs = self.mocked_artifacts_v1beta2_messages
      self.mocked_artifacts_v1beta2.projects_locations.List.Expect(
          msgs.ArtifactregistryProjectsLocationsListRequest(
              name='projects/compute-image-tools'),
          response=msgs.ListLocationsResponse(
              locations=[msgs.Location(name=location, locationId=region)]))

      self.mocked_artifacts_v1beta2.projects_locations_repositories.Get.Expect(
          msgs.ArtifactregistryProjectsLocationsRepositoriesGetRequest(
              name=repo_name),
          response=msgs.Repository(
              name=repo_name,
              format=msgs.Repository.FormatValueValuesEnum.DOCKER))

      self.mocked_artifacts_v1beta2.projects_locations_repositories_packages.Get.Expect(
          msgs.ArtifactregistryProjectsLocationsRepositoriesPackagesGetRequest(
              name=package_name),
          response=msgs.Package(name=package_name))

  def GetBuilder(self,
                 zone='',
                 region='',
                 tag=daisy_utils._DEFAULT_BUILDER_VERSION):
    if self.builder:
      return self.builder

    builder_region = ''

    if zone:
      builder_region = daisy_utils.GetRegionFromZone(zone).lower()
    elif region:
      builder_region = region.lower()

    if builder_region:
      return daisy_utils._REGIONALIZED_BUILDER_DOCKER_PATTERN.format(
          executable=daisy_utils._IMAGE_IMPORT_BUILDER_EXECUTABLE,
          region=builder_region,
          docker_image_tag=tag)
    else:
      return daisy_utils._DEFAULT_BUILDER_DOCKER_PATTERN.format(
          executable=daisy_utils._IMAGE_IMPORT_BUILDER_EXECUTABLE,
          docker_image_tag=tag)

  def testWindowsByolMapping(self):
    target_workflow = '../workflows/image_import/import_from_image.wf.json'
    translate_workflow = 'windows/translate_windows_7_x64_byol.wf.json'
    daisy_step = self.GetImportStepForWindowsByolMapping(target_workflow,
                                                         translate_workflow)

    self.PrepareDaisyMocksWithDefaultBucket(daisy_step)

    self.Run("""
             compute images import --source-image {0}
             --os windows-7-x64-byol
             {1}
             """.format(self.source_image, self.destination_image))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testDockerImageTag(self):
    self.testCommonCase()

    self.builder = self.GetBuilder(tag='latest', region='my-region')
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetDaisyImportTranslateStep())
    self.AddStorageRewriteMock()
    self.prepareArtifactRegistryMocks()

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             --docker-image-tag latest
             """.format(self.image_name, self.source_disk))
    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def GetImportStepForWindowsByolMapping(
      self, target_workflow, translate_workflow):
    import_vars = []
    daisy_utils.AppendArg(import_vars, 'source_image', self.source_image)
    daisy_utils.AppendArg(import_vars, 'os', 'windows-7-x64-byol')
    daisy_utils.AppendArg(
        import_vars, 'scratch_bucket_gcs_path',
        'gs://{0}/'.format(self.GetScratchBucketNameWithoutRegion()))
    daisy_utils.AppendArg(import_vars, 'timeout', _DEFAULT_TIMEOUT)
    daisy_utils.AppendArg(import_vars, 'client_id', 'gcloud')
    daisy_utils.AppendArg(import_vars, 'image_name', self.destination_image)
    daisy_utils.AppendArg(import_vars, 'client_version',
                          config.CLOUD_SDK_VERSION)
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars, name=self.GetBuilder())


if __name__ == '__main__':
  test_case.main()
