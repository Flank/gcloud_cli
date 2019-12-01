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
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os.path
import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.local import local
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from tests.lib import test_case
import mock
import six

IAM_MESSAGE_MODULE = core_apis.GetMessagesModule('iam', 'v1')
CRM_MESSAGE_MODULE = core_apis.GetMessagesModule('cloudresourcemanager', 'v1')


class IamTest(test_case.WithInput):

  def SetUp(self):
    self.mock_iam_client = apitools_mock.Client(
        core_apis.GetClientClass('iam', 'v1'))
    self.mock_iam_client.Mock()
    self.addCleanup(self.mock_iam_client.Unmock)

    self.mock_crm_client = apitools_mock.Client(
        core_apis.GetClientClass('cloudresourcemanager', 'v1'))
    self.mock_crm_client.Mock()
    self.addCleanup(self.mock_crm_client.Unmock)

    def MockGetClientInstance(api_name, version):
      if api_name == 'iam' and version == 'v1':
        return self.mock_iam_client
      if api_name == 'cloudresourcemanager' and version == 'v1':
        return self.mock_crm_client
      return None

    self.StartObjectPatch(
        core_apis, 'GetClientInstance', side_effect=MockGetClientInstance)

  def testCreateDevelopmentServiceAccount(self):
    service_account_msg = IAM_MESSAGE_MODULE.ServiceAccount(
        displayName='Serverless Local Development Service Account')
    create_account_request = IAM_MESSAGE_MODULE.CreateServiceAccountRequest(
        accountId='my-id', serviceAccount=service_account_msg)
    request = IAM_MESSAGE_MODULE.IamProjectsServiceAccountsCreateRequest(
        name='projects/project-id',
        createServiceAccountRequest=create_account_request)

    self.mock_iam_client.projects_serviceAccounts.Create.Expect(
        request, response=IAM_MESSAGE_MODULE.ServiceAccount())

    self.mock_crm_client.projects.GetIamPolicy.Expect(
        CRM_MESSAGE_MODULE.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='project-id'),
        response=CRM_MESSAGE_MODULE.Policy())

    self.mock_crm_client.projects.SetIamPolicy.Expect(
        CRM_MESSAGE_MODULE.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource='project-id',
            setIamPolicyRequest=CRM_MESSAGE_MODULE.SetIamPolicyRequest(
                policy=CRM_MESSAGE_MODULE.Policy(bindings=[
                    CRM_MESSAGE_MODULE.Binding(
                        members=[
                            'serviceAccount:my-id@'
                            'project-id.iam.gserviceaccount.com',
                        ],
                        role='roles/editor',
                    ),
                ]),)),
        response=CRM_MESSAGE_MODULE.Policy(bindings=[
            CRM_MESSAGE_MODULE.Binding(
                members=[
                    'serviceAccount:my-id@'
                    'project-id.iam.gserviceaccount.com',
                ],
                role='roles/editor',
            ),
        ]))

    self.assertEqual(
        local.CreateDevelopmentServiceAccount(
            'my-id@project-id.iam.gserviceaccount.com'),
        'projects/project-id/serviceAccounts/my-id@'
        'project-id.iam.gserviceaccount.com')

  def testServiceAccountAlreadyExists(self):
    self.mock_iam_client.projects_serviceAccounts.Create.Expect(
        mock.ANY,
        exception=apitools_exceptions.HttpConflictError('', '', ''),
        enable_type_checking=False)

    self.mock_crm_client.projects.GetIamPolicy.Expect(
        CRM_MESSAGE_MODULE.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='project-id'),
        response=CRM_MESSAGE_MODULE.Policy())

    self.mock_crm_client.projects.SetIamPolicy.Expect(
        CRM_MESSAGE_MODULE.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource='project-id',
            setIamPolicyRequest=CRM_MESSAGE_MODULE.SetIamPolicyRequest(
                policy=CRM_MESSAGE_MODULE.Policy(bindings=[
                    CRM_MESSAGE_MODULE.Binding(
                        members=[
                            'serviceAccount:id-exists@'
                            'project-id.iam.gserviceaccount.com',
                        ],
                        role='roles/editor',
                    ),
                ]),)),
        response=CRM_MESSAGE_MODULE.Policy(bindings=[
            CRM_MESSAGE_MODULE.Binding(
                members=[
                    'serviceAccount:id-exists@'
                    'project-id.iam.gserviceaccount.com',
                ],
                role='roles/editor',
            ),
        ]))
    self.assertEqual(
        local.CreateDevelopmentServiceAccount(
            'id-exists@project-id.iam.gserviceaccount.com'),
        'projects/project-id/serviceAccounts/id-exists@'
        'project-id.iam.gserviceaccount.com')

  def testBindingAlreadyExists(self):
    self.mock_iam_client.projects_serviceAccounts.Create.Expect(
        mock.ANY,
        exception=apitools_exceptions.HttpConflictError('', '', ''),
        enable_type_checking=False)

    self.mock_crm_client.projects.GetIamPolicy.Expect(
        mock.ANY,
        response=CRM_MESSAGE_MODULE.Policy(bindings=[
            CRM_MESSAGE_MODULE.Binding(
                members=[
                    'serviceAccount:id-exists@'
                    'project-id.iam.gserviceaccount.com',
                ],
                role='roles/editor',
            ),
        ]),
        enable_type_checking=False)

    # Assure SetIamPolicy is not called
    local.CreateDevelopmentServiceAccount(
        'id-exists@project-id.iam.gserviceaccount.com')

  def testUseCachedKey(self):
    patch_read = mock.patch.object(files, 'ReadFileContents')
    patch_exists = mock.patch.object(os.path, 'exists')

    with patch_read as mock_read, patch_exists as mock_exists:
      mock_exists.return_Value = True
      mock_read.return_value = 'BlahBlah'

      self.assertEqual(local.CreateServiceAccountKey('lalala'), 'BlahBlah')

  def testCreateServiceAccountKey(self):
    create_key_request = (
        IAM_MESSAGE_MODULE.IamProjectsServiceAccountsKeysCreateRequest(
            name='lalala',
            createServiceAccountKeyRequest=IAM_MESSAGE_MODULE
            .CreateServiceAccountKeyRequest(
                privateKeyType=IAM_MESSAGE_MODULE.CreateServiceAccountKeyRequest
                .PrivateKeyTypeValueValuesEnum.TYPE_GOOGLE_CREDENTIALS_FILE)))
    self.mock_iam_client.projects_serviceAccounts_keys.Create.Expect(
        create_key_request,
        response=IAM_MESSAGE_MODULE.ServiceAccountKey(privateKeyData=b'blah'))

    patch_write = mock.patch.object(files, 'WriteFileContents')
    patch_exists = mock.patch.object(os.path, 'exists')

    with patch_write as mock_write, patch_exists as mock_exists:
      mock_exists.return_value = False

      self.assertEqual(local.CreateServiceAccountKey('lalala'), b'blah')
      mock_write.assert_called_with(mock.ANY, b'blah')

  def testUserCancelsCreateKey(self):
    with mock.patch.object(os.path, 'exists') as mock_exists:
      mock_exists.return_value = False

      self.WriteInput('n')
      with self.assertRaises(console_io.OperationCancelledError):
        local.CreateServiceAccountKey('lalala')

  def testAddSecret(self):
    yaml_text = textwrap.dedent("""\
    apiVersion: v1
    kind: Pod
    metadata:
      name: my-service
    labels:
      service: my-service
    spec:
      containers:
      - name: my-service}-container
        image: image-name
        env:
        - name: PORT
          value: "8080"
        ports:
        - containerPort: 8080
    """)
    configs = list(yaml.load_all(yaml_text))
    local.AddServiceAccountSecret(configs)

    expected_yaml_text = textwrap.dedent("""\
    apiVersion: v1
    kind: Pod
    metadata:
      name: my-service
    labels:
      service: my-service
    spec:
      containers:
      - name: my-service}-container
        image: image-name
        env:
        - name: PORT
          value: "8080"
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: /etc/local_development_credential/local_development_service_account.json
        ports:
        - containerPort: 8080
        volumeMounts:
        - mountPath: /etc/local_development_credential
          name: local-development-credential
          readOnly: true
      volumes:
      - name: local-development-credential
        secret:
          secretName: local-development-credential
    """)
    six.assertCountEqual(self, configs, list(yaml.load_all(expected_yaml_text)))
