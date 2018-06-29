# Copyright 2018 Google Inc. All Rights Reserved.
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
from __future__ import unicode_literals
import uuid

from apitools.base.py import encoding
from apitools.base.py.testing import mock as client_mocker

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import e2e_base
from tests.lib import sdk_test_base


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

    self.mocked_servicemanagement_v1 = client_mocker.Client(
        core_apis.GetClientClass('servicemanagement', 'v1'))
    self.mocked_servicemanagement_v1.Mock()
    self.addCleanup(self.mocked_servicemanagement_v1.Unmock)
    self.servicemanagement_v1_messages = core_apis.GetMessagesModule(
        'servicemanagement', 'v1')

    self.uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    self.uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')

    properties.VALUES.core.project.Set('my-project')
    self._statuses = self.cloudbuild_v1_messages.Build.StatusValueValuesEnum

    self.project = self.crm_v1_messages.Project(
        projectId='my-project', projectNumber=123456)
    admin_permissions_binding = self.crm_v1_messages.Binding(
        members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
        role='roles/compute.admin')
    iam_permissions_binding = self.crm_v1_messages.Binding(
        members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
        role='roles/iam.serviceAccountActor')
    self.permissions = self.crm_v1_messages.Policy(
        bindings=[admin_permissions_binding, iam_permissions_binding])
    self.services = self.servicemanagement_v1_messages.ListServicesResponse(
        services=[self.servicemanagement_v1_messages.ManagedService(
            serviceName='cloudbuild.googleapis.com')]
    )
    self.tags = ['gce-daisy']

  def PrepareDaisyMocks(self, daisy_step, timeout='7200s', log_location=None,
                        permissions=None, async_flag=False):
    if log_location:
      buildin_logs_bucket = 'gs://{0}'.format(log_location)
    else:
      buildin_logs_bucket = None
    buildin = self.cloudbuild_v1_messages.Build(
        steps=[daisy_step],
        tags=self.tags,
        logsBucket=buildin_logs_bucket,
        timeout=timeout,
    )

    if log_location:
      buildout_logs_bucket = 'gs://{0}'.format(log_location)
    else:
      buildout_logs_bucket = 'gs://my-project_cloudbuild/logs'
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

    if not async_flag:
      self.AddHTTPResponse(
          'https://storage.googleapis.com/{0}/log-1234.txt'.format(
              log_location or 'my-project_cloudbuild/logs'),
          request_headers={'Range': 'bytes=0-'}, status=200,
          body='Here is some streamed\ndata for you to print\n')

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
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

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
        ),
        response=permissions or self.permissions,
    )

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )
