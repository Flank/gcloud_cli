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
    self.builder = daisy_utils._IMAGE_IMPORT_BUILDER.format(
        daisy_utils._DEFAULT_BUILDER_VERSION)
    self.tags = ['gce-daisy', 'gce-daisy-image-import']

  def GetCopiedSource(self, regionalized=True):
    return ('gs://{0}/tmpimage/12345678-'
            '1234-5678-1234-567812345678-source-image.vmdk'.
            format(self.GetScratchBucketName(regionalized=regionalized)))

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
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars, name=self.builder)

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
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars, name=self.builder)

  def GetDaisyImportTranslateStep(self):
    return self.GetNetworkStepForImport(include_zone=False)

  def GetNetworkStepForImport(self, network=None, subnet=None,
                              include_zone=True, from_image=False,
                              include_storage_location=False,
                              family=None, description=None,
                              sysprep_windows=False):

    import_vars = []

    if from_image:
      daisy_utils.AppendArg(import_vars, 'source_image', self.source_image)
    else:
      daisy_utils.AppendArg(import_vars, 'source_file',
                            self.GetCopiedSource(regionalized=True))

    daisy_utils.AppendArg(import_vars, 'os', 'ubuntu-1604')

    if include_zone:
      daisy_utils.AppendArg(import_vars, 'zone', 'my-region-c')

    if include_storage_location:
      daisy_utils.AppendArg(import_vars, 'storage_location', 'my-region')

    daisy_utils.AppendArg(
        import_vars, 'scratch_bucket_gcs_path',
        'gs://{0}/'.format(self.GetScratchBucketName(
            not from_image or include_storage_location)))

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

    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars, name=self.builder)

  def AddStorageRewriteMock(self):
    destination_bucket = self.GetScratchBucketNameWithRegion()

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
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars, name=self.builder)

  def testAsync(self):
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetDaisyImportTranslateStep(),
        async_flag=True)
    self.AddStorageRewriteMock()

    self.Run("""
             compute images import {0}
             --source-file {1} --async
             --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertErrContains('Created [https://cloudbuild.googleapis.com/'
                           'v1/projects/my-project/builds/1234]')

  def testDescription(self):
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetNetworkStepForImport(include_zone=False,
                                     description='custom ubuntu image'))
    self.AddStorageRewriteMock()

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
        self.GetNetworkStepForImport(include_zone=False, family='ubuntu'))
    self.AddStorageRewriteMock()

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             --family ubuntu
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testTimeoutFlag(self):
    # Daisy timeout 2% sooner than Argo.
    daisy_import_step = self.GetImportStepForTimeoutTest(59)
    self.PrepareDaisyMocksWithRegionalBucket(daisy_import_step, timeout='60s')
    self.AddStorageRewriteMock()

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
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars, name=self.builder)

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
    self.Run("""
             compute images import {0}
             --source-file {1} --quiet
             --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

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
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars, name=self.builder)

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
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars, name=self.builder)

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
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars, name=self.builder)

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

  def doNetworkTestSuccess(
      self, daisy_step, cmd, regionalized=True, from_image=False):
    if regionalized:
      self.PrepareDaisyMocksWithRegionalBucket(
          daisy_step, match_source_file_region=not from_image)
      if not from_image:
        self.AddStorageRewriteMock()
    else:
      self.PrepareDaisyMocksWithDefaultBucket(daisy_step)
    self.Run(cmd)
    self.AssertOutputContains('[import-image] output', normalize_space=True)

  def testNetworkFlag(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(
            network=self.network, include_zone=False), """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --network {2}
        """.format(self.image_name, self.source_disk, self.network))

  def testSubnetFlag(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(
            network=self.network, subnet=self.subnet), """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --network {2} --subnet {3} --zone my-region-c
        """.format(
            self.image_name, self.source_disk, self.network, self.subnet))

  def testSubnetFlagZoneAndRegionNotSpecified(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(subnet=self.subnet, include_zone=False),
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
        """.format(
            self.image_name, self.source_disk, self.network, self.subnet))

  def testSubnetFlagRegionAsProperty(self):
    properties.VALUES.compute.region.Set('my-region')
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(
            network=self.network, subnet=self.subnet, include_zone=False),
        """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --network {2} --subnet {3}
        """.format(
            self.image_name, self.source_disk, self.network, self.subnet))

  def testNetworkFlagFromImage(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(
            network=self.network, include_zone=False, from_image=True),
        """
        compute images import {0} --source-image {1} --os ubuntu-1604
        --network {2}
        """.format(
            self.image_name, self.source_image, self.network),
        regionalized=False)

  def testSubnetFlagFromImage(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(
            network=self.network, subnet=self.subnet,
            include_zone=True, from_image=True),
        """
        compute images import {0} --source-image {1} --os ubuntu-1604
        --network {2} --subnet {3} --zone my-region-c
        """.format(
            self.image_name, self.source_image, self.network, self.subnet),
        regionalized=False)

  def testScratchBucketCreatedInSourceRegion(self):
    import_step = self.GetNetworkStepForImport(include_zone=False)

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

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                kind='storage#bucket',
                name=daisy_bucket_name,
                location=self.GetScratchBucketRegion(),

            ),
            project='my-project',
        ),
        response=self.storage_v1_messages.Bucket(id=daisy_bucket_name))

    self.AddStorageRewriteMock()

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

  def testSourceFileBucketOnlyGCSPath(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        r'Invalid value for [source-file]: must be a path to an object in Google Cloud Storage'
    ):
      self.Run("""
                 compute images import {0}
                 --source-file gs://bucket --os ubuntu-1604
                 """.format(self.image_name))

  def testStorageLocationFlagFromGCSFile(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(include_zone=True,
                                     include_storage_location=True),
        """
        compute images import {0} --source-file {1} --os ubuntu-1604
        --zone my-region-c --storage-location my-region
        """.format(
            self.image_name, self.source_disk))

  def testStorageLocationFlagFromImage(self):
    self.doNetworkTestSuccess(
        self.GetNetworkStepForImport(
            network=self.network, include_zone=True, from_image=True,
            include_storage_location=True),
        """
        compute images import {0} --source-image {1} --os ubuntu-1604
        --network {2} --storage-location my-region --zone my-region-c
        """.format(
            self.image_name, self.source_image, self.network),
        regionalized=True, from_image=True)


class ImageImportTestBeta(ImageImportTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testSysprepFlagIsPropagated(self):
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetNetworkStepForImport(sysprep_windows=True))
    self.AddStorageRewriteMock()

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

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             --zone my-region-c
             --no-sysprep-windows
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        [import-image] output
        """, normalize_space=True)

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
    self.builder = daisy_utils._IMAGE_IMPORT_BUILDER.format(
        daisy_utils._DEFAULT_BUILDER_VERSION)
    self.testCommonCase()

    self.builder = daisy_utils._IMAGE_IMPORT_BUILDER.format('latest')
    self.PrepareDaisyMocksWithRegionalBucket(
        self.GetDaisyImportTranslateStep())
    self.AddStorageRewriteMock()
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
    return self.cloudbuild_v1_messages.BuildStep(
        args=import_vars, name=self.builder)


if __name__ == '__main__':
  test_case.main()
