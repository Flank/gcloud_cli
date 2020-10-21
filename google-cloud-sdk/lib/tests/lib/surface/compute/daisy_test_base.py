# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Base module for testing commands that call Daisy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
import uuid

from apitools.base.py import encoding
from apitools.base.py.testing import mock as client_mocker

from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import properties
from tests.lib import e2e_base
from tests.lib import sdk_test_base
import mock

_DEFAULT_TIMEOUT = '6984s'


class DaisyBaseTest(e2e_base.WithMockHttp, sdk_test_base.SdkBase):
  """Base class for tests that call Daisy."""

  def SetUp(self):
    self.mocked_cloudbuild_v1 = client_mocker.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'),
    )
    self.mocked_cloudbuild_v1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1.Unmock)
    self.cloudbuild_v1_messages = core_apis.GetMessagesModule(
        'cloudbuild', 'v1')

    self.mocked_storage_v1 = client_mocker.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.mocked_storage_v1.Mock()
    self.addCleanup(self.mocked_storage_v1.Unmock)
    self.storage_v1_messages = core_apis.GetMessagesModule(
        'storage', 'v1')

    self.mocked_crm_v1 = client_mocker.Client(
        core_apis.GetClientClass('cloudresourcemanager', 'v1'))
    self.mocked_crm_v1.Mock()
    self.addCleanup(self.mocked_crm_v1.Unmock)
    self.crm_v1_messages = core_apis.GetMessagesModule(
        'cloudresourcemanager', 'v1')

    self.mocked_iam_v1 = client_mocker.Client(
        core_apis.GetClientClass('iam', 'v1'))
    self.mocked_iam_v1.Mock()
    self.addCleanup(self.mocked_iam_v1.Unmock)
    self.iam_v1_messages = core_apis.GetMessagesModule(
        'iam', 'v1')

    self.mocked_serviceusage_v1 = client_mocker.Client(
        core_apis.GetClientClass('serviceusage', 'v1'))
    self.mocked_serviceusage_v1.Mock()
    self.addCleanup(self.mocked_serviceusage_v1.Unmock)
    self.serviceusage_v1_messages = core_apis.GetMessagesModule(
        'serviceusage', 'v1')

    self.mocked_compute_client_v1 = client_mocker.Client(
        core_apis.GetClientClass('compute', 'v1'),
        real_client=core_apis.GetClientInstance('compute', 'v1', no_http=True))
    self.mocked_compute_client_v1.Mock()
    self.addCleanup(self.mocked_compute_client_v1.Unmock)
    self.compute_v1_messages = core_apis.GetMessagesModule(
        'compute', 'v1')

    self.mocked_artifacts_v1beta2 = client_mocker.Client(
        core_apis.GetClientClass('artifactregistry', 'v1beta2'))
    self.mocked_artifacts_v1beta2.Mock()
    self.addCleanup(self.mocked_artifacts_v1beta2.Unmock)
    self.mocked_artifacts_v1beta2_messages = core_apis.GetMessagesModule(
        'artifactregistry', 'v1beta2')

    make_requests_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.MakeRequests',
        autospec=True)
    self.addCleanup(make_requests_patcher.stop)
    self.make_requests = make_requests_patcher.start()

    def MakeRequests(*_, **kwargs):
      if False:  # pylint: disable=using-constant-test, generator mock
        yield
      # We check to see if the image we are importing to already exists,
      # so in the default case, the image should not exist.
      kwargs['errors'].append((404, 'Not Found'))

    self.make_requests.side_effect = MakeRequests

    self.permissions = self.crm_v1_messages.Policy(bindings=[
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_COMPUTE_ADMIN),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_USER),
        self.crm_v1_messages.Binding(
            members=[
                'serviceAccount:123456-compute@developer.gserviceaccount.com'
            ],
            role=daisy_utils.ROLE_COMPUTE_STORAGE_ADMIN),
        self.crm_v1_messages.Binding(
            members=[
                'serviceAccount:123456-compute@developer.gserviceaccount.com'
            ],
            role=daisy_utils.ROLE_STORAGE_OBJECT_VIEWER),
    ])

    self.uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    self.uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')

    properties.VALUES.core.project.Set('my-project')
    self._statuses = self.cloudbuild_v1_messages.Build.StatusValueValuesEnum

    self.project = self.crm_v1_messages.Project(
        projectId='my-project', projectNumber=123456)

    self.tags = ['gce-daisy']
    self.network = 'my-network'
    self.subnet = 'my-subnet'

  def PrepareDaisyMocks(self, daisy_step, timeout='7200s', log_location=None,
                        permissions=None, async_flag=False, is_import=True):
    self._ExpectCloudBuild(daisy_step, log_location, timeout, async_flag)
    if not is_import:
      self.permissions = self.crm_v1_messages.Policy(bindings=[
          self.crm_v1_messages.Binding(
              members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
              role=daisy_utils.ROLE_COMPUTE_ADMIN),
          self.crm_v1_messages.Binding(
              members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
              role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR),
          self.crm_v1_messages.Binding(
              members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
              role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_USER),
          self.crm_v1_messages.Binding(
              members=[
                  'serviceAccount:123456-compute@developer.gserviceaccount.com',
              ],
              role=daisy_utils.ROLE_COMPUTE_STORAGE_ADMIN),
          self.crm_v1_messages.Binding(
              members=[
                  'serviceAccount:123456-compute@developer.gserviceaccount.com',
              ],
              role=daisy_utils.ROLE_STORAGE_OBJECT_ADMIN),
      ])

    self._ExpectServiceUsage()

    permissions = self.permissions if permissions is None else permissions
    self._ExpectIamRolesGet(is_import, permissions)

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
    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        request=get_request,
        response=permissions,
    )

  def _ExpectCloudBuild(self, daisy_step, log_location=None, timeout='7200s',
                        async_flag=False):
    log_bucket_dir = ''
    if log_location:
      if self.IsGCSBucketPath(log_location):
        log_location = log_location.rstrip('/')
      log_bucket_dir = self.TrimGCSPathProtocolPrefix(log_location)
      buildin_logs_bucket = 'gs://{0}'.format(log_bucket_dir)
      buildout_logs_bucket = buildin_logs_bucket
    else:
      buildin_logs_bucket = None
      buildout_logs_bucket = 'gs://my-project_cloudbuild/logs'

    buildin = self.cloudbuild_v1_messages.Build(
        steps=[daisy_step],
        tags=self.tags,
        logsBucket=buildin_logs_bucket,
        timeout=timeout,
    )
    buildout = self.cloudbuild_v1_messages.Build(
        id='1234',
        projectId='my-project',
        steps=[daisy_step],
        tags=self.tags,
        status=self._statuses.SUCCESS,
        logsBucket=buildout_logs_bucket,
        timeout=timeout,
    )
    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=buildout,
    )
    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=buildin,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata)))
    )
    if not async_flag:
      self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
          self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
              id='1234',
              projectId='my-project',
          ),
          response=buildout,
      )
    if not async_flag:
      self.AddHTTPResponse(
          'https://storage.googleapis.com/{0}/log-1234.txt'.format(
              log_bucket_dir or 'my-project_cloudbuild/logs'),
          request_headers={'Range': 'bytes=0-'}, status=200,
          body=('Cloudbuild output\n[import-image] output\n'
                '[image-export] output\n[import-ovf] output\n'
                '[windows-upgrade] output'))

  def _ExpectIamRolesGet(self, is_import, permissions=None, skip_compute=False):
    if is_import:
      self.required_cloudbuild_service_account_roles = (
          daisy_utils.IMPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT)
      self.required_compute_service_account_roles = (
          daisy_utils.IMPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT)
    else:
      self.required_cloudbuild_service_account_roles = (
          daisy_utils.EXPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT)
      self.required_compute_service_account_roles = (
          daisy_utils.EXPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT)

    applied_cloudbuild_service_account_roles = set()
    applied_compute_service_account_roles = set()
    permissions = permissions or self.permissions
    for binding in permissions.bindings:
      if binding.members[0] == (
          'serviceAccount:123456@cloudbuild.gserviceaccount.com'):
        applied_cloudbuild_service_account_roles.add(binding.role)
      elif binding.members[0] == (
          'serviceAccount:123456-compute@developer.gserviceaccount.com'):
        applied_compute_service_account_roles.add(binding.role)

    # roles.Get will be called twice: 1 for expected roles, 1 for applied roles.
    permission_string = 'permission{0}.{1}'
    if not self.required_cloudbuild_service_account_roles.issubset(
        applied_cloudbuild_service_account_roles):
      for role in sorted(self.required_cloudbuild_service_account_roles):
        self.mocked_iam_v1.roles.Get.Expect(
            self.iam_v1_messages.IamRolesGetRequest(name=role),
            response=self.iam_v1_messages.Role(includedPermissions=[
                permission_string.format(1, role),
                permission_string.format(2, role),
            ]))
      for role in sorted(applied_cloudbuild_service_account_roles):
        self.mocked_iam_v1.roles.Get.Expect(
            self.iam_v1_messages.IamRolesGetRequest(name=role),
            response=self.iam_v1_messages.Role(
                includedPermissions=[
                    permission_string.format(1, role),
                    permission_string.format(2, role),
                ]))
    skip_compute = skip_compute or applied_compute_service_account_roles == {
        daisy_utils.ROLE_EDITOR,
    }
    if (not skip_compute and
        not self.required_compute_service_account_roles.issubset(
            applied_compute_service_account_roles)):
      for role in sorted(self.required_compute_service_account_roles):
        self.mocked_iam_v1.roles.Get.Expect(
            self.iam_v1_messages.IamRolesGetRequest(name=role),
            response=self.iam_v1_messages.Role(includedPermissions=[
                permission_string.format(3, role),
                permission_string.format(4, role),
            ]))
      if applied_compute_service_account_roles == {'roles/custom'}:
        included_permissions = []
        for role in self.required_compute_service_account_roles:
          included_permissions.append(permission_string.format(3, role))
          included_permissions.append(permission_string.format(4, role))
        self.mocked_iam_v1.roles.Get.Expect(
            self.iam_v1_messages.IamRolesGetRequest(name='roles/custom'),
            response=self.iam_v1_messages.Role(
                includedPermissions=included_permissions))
      else:
        for role in sorted(applied_compute_service_account_roles):
          self.mocked_iam_v1.roles.Get.Expect(
              self.iam_v1_messages.IamRolesGetRequest(name=role),
              response=self.iam_v1_messages.Role(includedPermissions=[
                  permission_string.format(3, role),
                  permission_string.format(4, role),
              ]))
    return permissions

  def _ExpectAddIamPolicyBinding(self, count_missed_roles):
    for _ in range(count_missed_roles):
      get_request = self.crm_v1_messages \
        .CloudresourcemanagerProjectsGetIamPolicyRequest(
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(
                options=self.crm_v1_messages.GetPolicyOptions(
                    requestedPolicyVersion=
                    iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
            resource='my-project')
      self.mocked_crm_v1.projects.GetIamPolicy.Expect(
          request=get_request,
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

  def _ExpectServiceUsage(self, build_enabled=True, compute_enabled=True):
    state_type = self.serviceusage_v1_messages.GoogleApiServiceusageV1Service.StateValueValuesEnum
    self.mocked_serviceusage_v1.services.Get.Expect(
        self.serviceusage_v1_messages.ServiceusageServicesGetRequest(
            name='projects/my-project/services/cloudbuild.googleapis.com',),
        response=self.serviceusage_v1_messages.GoogleApiServiceusageV1Service(
            state=state_type.ENABLED
            if build_enabled else state_type.DISABLED,))
    if build_enabled:
      self.mocked_serviceusage_v1.services.Get.Expect(
          self.serviceusage_v1_messages.ServiceusageServicesGetRequest(
              name='projects/my-project/services/logging.googleapis.com',),
          response=self.serviceusage_v1_messages.GoogleApiServiceusageV1Service(
              state=state_type.ENABLED,))
    if build_enabled:
      self.mocked_serviceusage_v1.services.Get.Expect(
          self.serviceusage_v1_messages.ServiceusageServicesGetRequest(
              name='projects/my-project/services/compute.googleapis.com',),
          response=self.serviceusage_v1_messages.GoogleApiServiceusageV1Service(
              state=state_type.ENABLED
              if compute_enabled else state_type.DISABLED,))

  def PrepareDaisyMocksWithRegionalBucket(
      self, daisy_step, timeout='7200s', log_location=None, permissions=None,
      async_flag=False, is_import=True, match_source_file_region=True,
      scratch_bucket_location=''):
    self.PrepareDaisyMocks(daisy_step, timeout, log_location, permissions,
                           async_flag, is_import)
    self.PrepareDaisyBucketMocksWithRegion(
        match_source_file_region=match_source_file_region,
        scratch_bucket_location=scratch_bucket_location)

  def PrepareDaisyMocksWithDefaultBucket(
      self,
      daisy_step,
      timeout='7200s',
      log_location=None,
      permissions=None,
      async_flag=False,
      is_import=True):
    self.PrepareDaisyMocks(daisy_step, timeout, log_location, permissions,
                           async_flag, is_import)
    self.PrepareDaisyBucketMocksWithoutRegion()

  def PrepareDaisyBucketMocksWithRegion(self,
                                        match_source_file_region=True,
                                        scratch_bucket_location=''):
    if match_source_file_region:
      self.mocked_storage_v1.buckets.Get.Expect(
          self.storage_v1_messages.StorageBucketsGetRequest(bucket='31dd'),
          response=self.storage_v1_messages.Bucket(
              name='31dd',
              storageClass='REGIONAL',
              location='MY-REGION'
          ),
      )

    daisy_bucket_name = self.GetScratchBucketNameWithRegion(
        scratch_bucket_location=scratch_bucket_location)
    daisy_bucket = self.storage_v1_messages.Bucket(
        id=daisy_bucket_name,
        location=self.GetScratchBucketRegion(
            scratch_bucket_location=scratch_bucket_location))
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=daisy_bucket_name),
        response=daisy_bucket)
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_v1_messages.StorageBucketsListRequest(
            project='my-project',
            prefix=daisy_bucket.id,
        ),
        response=self.storage_v1_messages.Buckets(items=[daisy_bucket]))

  def PrepareDaisyBucketMocksWithoutRegion(self):
    daisy_bucket_name = self.GetScratchBucketNameWithoutRegion()
    daisy_bucket = self.storage_v1_messages.Bucket(id=daisy_bucket_name)
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=daisy_bucket_name),
        response=daisy_bucket)
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_v1_messages.StorageBucketsListRequest(
            project='my-project',
            prefix=daisy_bucket.id,
        ),
        response=self.storage_v1_messages.Buckets(items=[daisy_bucket]))

  def GetNetworkStep(self, workflow, daisy_vars, operation, regionalized,
                     network=None, subnet=None, include_zone=True,
                     include_empty_network=False):
    network_vars = ''
    if subnet:
      network_vars += ',{0}_subnet=regions/my-region/subnetworks/{1}'.format(
          operation, subnet)

    if network:
      network_vars += ',{0}_network=global/networks/{1}'.format(
          operation, network)
    elif include_empty_network:
      network_vars += ',{0}_network='.format(operation)

    daisy_vars = daisy_vars.format(network_vars)

    args = [
        '-gcs_path=gs://{0}/'.format(
            self.GetScratchBucketName(regionalized)),
        '-default_timeout={0}'.format(_DEFAULT_TIMEOUT),
        daisy_vars,
        workflow,
    ]
    if include_zone:
      args.insert(0, '-zone=my-region-c')

    return self.cloudbuild_v1_messages.BuildStep(args=args, name=self.builder)

  @staticmethod
  def GetScratchBucketNameWithRegion(scratch_bucket_location=''):
    return (
        'my-project-daisy-bkt-' +
        DaisyBaseTest.GetScratchBucketRegion(scratch_bucket_location).lower())

  @staticmethod
  def GetScratchBucketNameWithoutRegion():
    return 'my-project-daisy-bkt'

  @staticmethod
  def GetScratchBucketName(regionalized, scratch_bucket_location=''):
    if regionalized:
      return DaisyBaseTest.GetScratchBucketNameWithRegion(
          scratch_bucket_location)
    else:
      return DaisyBaseTest.GetScratchBucketNameWithoutRegion()

  @staticmethod
  def GetScratchBucketRegion(scratch_bucket_location=''):
    if scratch_bucket_location:
      return scratch_bucket_location
    return 'MY-REGION'

  @staticmethod
  def IsGCSBucketPath(path):
    return re.match('^gs://([^/]*)/?$', path) or re.match(
        '^https://storage.googleapis.com/([^/]*)/?$', path)

  @staticmethod
  def TrimGCSPathProtocolPrefix(path):
    return path.replace('gs://',
                        '').replace('https://storage.googleapis.com/', '')
