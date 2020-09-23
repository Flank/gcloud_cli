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

import base64
import copy
import os.path
import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.auth import auth_util
from googlecloudsdk.command_lib.code import flags
from googlecloudsdk.command_lib.code import local

from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.calliope import util as calliope_test_util
import mock
import six

IAM_MESSAGE_MODULE = core_apis.GetMessagesModule('iam', 'v1')
CRM_MESSAGE_MODULE = core_apis.GetMessagesModule('cloudresourcemanager', 'v1')


class TestDataType(local.DataObject):
  NAMES = ['a', 'b', 'c']


class DataObjectTest(test_case.TestCase):

  def testDataObject(self):
    obj = TestDataType(a=4, b=5, c=6)

    self.assertEqual(obj.a, 4)
    self.assertEqual(obj.b, 5)
    self.assertEqual(obj.c, 6)

  def testDataObjectMissingB(self):
    obj = TestDataType(a=4, c=6)

    self.assertEqual(obj.a, 4)
    self.assertIsNone(obj.b)
    self.assertEqual(obj.c, 6)

  def testInvalidNames(self):
    with self.assertRaises(ValueError):
      TestDataType(a=4, d=7)


class IamTest(cli_test_base.CliTestBase, test_case.WithInput):

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

  def testCreateDevelopmentServiceAccountNoEditorRole(self):
    self.mock_iam_client.projects_serviceAccounts.Get.Expect(
        mock.ANY,
        exception=apitools_exceptions.HttpNotFoundError('', '', ''),
        enable_type_checking=False)

    service_account_msg = IAM_MESSAGE_MODULE.ServiceAccount(
        displayName='Serverless Local Development Service Account')
    create_account_request = IAM_MESSAGE_MODULE.CreateServiceAccountRequest(
        accountId='my-id', serviceAccount=service_account_msg)
    request = IAM_MESSAGE_MODULE.IamProjectsServiceAccountsCreateRequest(
        name='projects/project-id',
        createServiceAccountRequest=create_account_request)

    self.mock_iam_client.projects_serviceAccounts.Create.Expect(
        request, response=IAM_MESSAGE_MODULE.ServiceAccount())

    self.WriteInput('n')

    self.assertEqual(
        local.CreateDevelopmentServiceAccount(
            'my-id@project-id.iam.gserviceaccount.com'),
        'projects/project-id/serviceAccounts/my-id@'
        'project-id.iam.gserviceaccount.com')

  def testCreateDevelopmentServiceAccount(self):
    self.mock_iam_client.projects_serviceAccounts.Get.Expect(
        mock.ANY,
        exception=apitools_exceptions.HttpNotFoundError('', '', ''),
        enable_type_checking=False)

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
    self.mock_iam_client.projects_serviceAccounts.Get.Expect(
        mock.ANY,
        response=IAM_MESSAGE_MODULE.ServiceAccount(),
        enable_type_checking=False)

    self.assertEqual(
        local.CreateDevelopmentServiceAccount(
            'id-exists@project-id.iam.gserviceaccount.com'),
        'projects/project-id/serviceAccounts/id-exists@'
        'project-id.iam.gserviceaccount.com')

  def testAppengineServiceAccountExists(self):
    self.mock_iam_client.projects_serviceAccounts.Get.Expect(
        mock.ANY,
        response=IAM_MESSAGE_MODULE.ServiceAccount(),
        enable_type_checking=False)

    self.assertEqual(
        local.CreateDevelopmentServiceAccount(
            'my-project.google.com@appspot.gserviceaccount.com'),
        'projects/my-project/serviceAccounts/'
        'my-project.google.com@appspot.gserviceaccount.com')

  def testAppengineServiceAccountMissing(self):
    self.mock_iam_client.projects_serviceAccounts.Get.Expect(
        mock.ANY,
        exception=apitools_exceptions.HttpNotFoundError('', '', ''),
        enable_type_checking=False)

    with self.assertRaises(ValueError):
      local.CreateDevelopmentServiceAccount(
          'my-project.google.com@appspot.gserviceaccount.com')

  def testComputeServiceAccountExists(self):
    self.mock_iam_client.projects_serviceAccounts.Get.Expect(
        mock.ANY,
        response=IAM_MESSAGE_MODULE.ServiceAccount(),
        enable_type_checking=False)

    self.mock_crm_client.projects.Get.Expect(
        mock.ANY,
        response=CRM_MESSAGE_MODULE.Project(
            projectId=six.ensure_binary('my-project')),
        enable_type_checking=False)

    self.assertEqual(
        local.CreateDevelopmentServiceAccount(
            '1234-compute@developer.gserviceaccount.com'),
        'projects/my-project/serviceAccounts/'
        '1234-compute@developer.gserviceaccount.com')

  def testComputeServiceAccountMissing(self):
    self.mock_iam_client.projects_serviceAccounts.Get.Expect(
        mock.ANY,
        exception=apitools_exceptions.HttpNotFoundError('', '', ''),
        enable_type_checking=False)

    with self.assertRaises(ValueError):
      local.CreateDevelopmentServiceAccount(
          'my-project.google.com@appspot.gserviceaccount.com')

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

      self.assertEqual(local.CreateServiceAccountKey('lalala'), 'blah')
      mock_write.assert_called_with(mock.ANY, b'blah')

  def testEncodeServiceAccountKey(self):
    secret = local.LocalDevelopmentSecretSpec(six.ensure_binary('monkey'))
    self.assertEqual(secret['data']['local_development_service_account.json'],
                     'bW9ua2V5')

  def testUserCancelsCreateKey(self):
    with mock.patch.object(os.path, 'exists') as mock_exists:
      mock_exists.return_value = False

      self.WriteInput('n')
      with self.assertRaises(console_io.OperationCancelledError):
        local.CreateServiceAccountKey('lalala')

  def testAddSecret(self):
    yaml_text = textwrap.dedent("""\
    apiVersion: v1
    kind: Deployment
    metadata:
      name: my-service
    labels:
      service: my-service
    spec:
      template:
        spec:
          containers:
          - name: my-service-container
            image: image-name
            env:
            - name: PORT
              value: "8080"
            ports:
            - containerPort: 8080
    """)
    deployment = yaml.load(yaml_text)
    credential_generator = local.CredentialGenerator(lambda: None)
    credential_generator.ModifyDeployment(deployment)
    credential_generator.ModifyContainer(
        deployment['spec']['template']['spec']['containers'][0])

    expected_yaml_text = textwrap.dedent("""\
    apiVersion: v1
    kind: Deployment
    metadata:
      name: my-service
    labels:
      service: my-service
    spec:
      template:
        spec:
          containers:
          - name: my-service-container
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
    self.assertEqual(deployment, yaml.load(expected_yaml_text))

  def testCreateSecret(self):
    credential_generator = local.CredentialGenerator(lambda: 'abcdef')

    configs = credential_generator.CreateConfigs()

    expected = {
        'apiVersion': 'v1',
        'data': {
            'local_development_service_account.json':
                six.ensure_text(base64.b64encode(six.ensure_binary('abcdef')))
        },
        'kind': 'Secret',
        'metadata': {
            'name': 'local-development-credential'
        },
        'type': 'Opaque'
    }
    self.assertEqual(configs, [expected])


class GetUserCredentialTest(test_case.TestCase):

  def testADCNotPresent(self):
    with mock.patch.object(auth_util, 'GetADCAsJson') as get_adc:
      get_adc.return_value = None

      with self.assertRaises(local.ADCMissingError):
        local.GetUserCredential()


class EnvironmentVariables(test_case.TestCase):

  def testAddEnvironmentVariables(self):
    deployment = local.CreateDeployment('my-service', 'my-image')
    before_env_list = copy.copy(
        deployment['spec']['template']['spec']['containers'][0]['env'])

    env_vars = {'a': 'b', 'c': 'd'}

    local.AddEnvironmentVariables(deployment, 'my-service-container', env_vars)
    env_list = deployment['spec']['template']['spec']['containers'][0]['env']

    expected_env_list = before_env_list + [{
        'name': 'a',
        'value': 'b'
    }, {
        'name': 'c',
        'value': 'd'
    }]
    six.assertCountEqual(self, env_list, expected_env_list)


def MakeFakeAbsPath(cwd):

  def FakeAbsPath(path):
    if os.path.isabs(path):
      return path
    return os.path.join(cwd, path)

  return FakeAbsPath


class SettingsTest(test_case.WithInput):

  def SetUp(self):
    self.parser = calliope_test_util.ArgumentParser()
    flags.CommonFlags(self.parser)

  def testServiceNameUnderscoreToDash(self):

    with mock.patch.object(files, 'GetCWD') as mock_getcwd, \
         mock.patch.object(os.path, 'abspath') as mock_abspath, \
         mock.patch.object(properties.VALUES.core.project, 'Get',
                           return_value='my-project'), \
        mock.patch.object(os.path, 'exists', return_value=True):
      mock_getcwd.return_value = '/current/working_directory'
      mock_abspath.side_effect = MakeFakeAbsPath('/current/working_directory')

      args = self.parser.parse_args([])
      settings = local.Settings.FromArgs(args)

    self.assertEqual(settings.service_name, 'working-directory')
    self.assertEqual(settings.image, 'gcr.io/my-project/working-directory')

  def testImageNameNoProject(self):

    with mock.patch.object(files, 'GetCWD') as mock_getcwd, \
         mock.patch.object(os.path, 'abspath') as mock_abspath, \
         mock.patch.object(properties.VALUES.core.project, 'Get',
                           return_value=None), \
        mock.patch.object(os.path, 'exists', return_value=True):
      mock_getcwd.return_value = '/current/working_directory'
      mock_abspath.side_effect = MakeFakeAbsPath('/current/working_directory')

      args = self.parser.parse_args([])
      settings = local.Settings.FromArgs(args)

    self.assertEqual(settings.image, 'working-directory')

  def testDockerFileNotInCWD(self):
    properties.VALUES.core.project.Set('my-project')

    with mock.patch.object(files, 'GetCWD') as mock_getcwd:
      with mock.patch.object(os.path, 'abspath') as mock_abspath:
        mock_getcwd.return_value = '/current/working_directory'
        mock_abspath.side_effect = MakeFakeAbsPath('/current/working_directory')

        args = self.parser.parse_args(
            ['--dockerfile=/notcurrent/working_directory/Dockerfile'])

        with self.assertRaisesRegex(
            local.InvalidLocationError,
            'Dockerfile must be located in the build context directory'):
          local.Settings.FromArgs(args)


class CloudSqlProxyGeneratorTest(test_case.TestCase):

  def testAddCloudSqlSidecar(self):
    yaml_text = textwrap.dedent("""\
    apiVersion: v1
    kind: Deployment
    metadata:
      name: my-service
    labels:
      service: my-service
    spec:
      template:
        spec:
          containers:
          - name: my-service-container
            image: image-name
            env:
            - name: PORT
              value: "8080"
            ports:
            - containerPort: 8080
    """)
    deployment = yaml.load(yaml_text)

    code_generator = local.CloudSqlProxyGenerator(
        ['my-sql-instance', 'your-sql-instance'], local.SecretInfo())
    code_generator.ModifyDeployment(deployment)
    code_generator.ModifyContainer(
        deployment['spec']['template']['spec']['containers'][0])

    expected_yaml_text = textwrap.dedent("""\
    apiVersion: v1
    kind: Deployment
    metadata:
      name: my-service
    labels:
      service: my-service
    spec:
      template:
        spec:
          containers:
          - name: my-service-container
            image: image-name
            env:
            - name: PORT
              value: "8080"
            ports:
            - containerPort: 8080
            volumeMounts:
            - name: cloudsql
              mountPath: /cloudsql
              readOnly: true
          - name: cloud-sql-proxy
            image: 'gcr.io/cloudsql-docker/gce-proxy:1.16'
            command:
            - '/cloud_sql_proxy'
            args:
            - '-dir=/cloudsql'
            - '-instances=my-sql-instance,your-sql-instance'
            - '-credential_file=/etc/local_development_credential/local_development_service_account.json'
            volumeMounts:
            - name: cloudsql
              mountPath: /cloudsql
          volumes:
          - name: cloudsql
            emptyDir: {}
    """)
    self.assertEqual(deployment, yaml.load(expected_yaml_text))


class CreateBuilderTest(test_case.TestCase):

  def SetUp(self):
    self.parser = calliope_test_util.ArgumentParser()
    flags.CommonFlags(self.parser)

  def testAppengineBuilder(self):
    args = self.parser.parse_args(['--appengine'])

    with files.TemporaryDirectory() as temp_dir:
      app_yaml = 'runtime: python37'
      files.WriteFileContents(os.path.join(temp_dir, 'app.yaml'), app_yaml)

      self.assertEqual(
          local._CreateBuilder(args, temp_dir),
          local.BuildpackBuilder(
              builder='gcr.io/gae-runtimes/buildpacks/python37/builder:argo_current',
              trust=True,
              devmode=False))

  def testUntrustedBuilder(self):
    args = self.parser.parse_args(['--builder=my-builder:latest'])

    self.assertEqual(
        local._CreateBuilder(args, files.GetCWD()),
        local.BuildpackBuilder(
            builder='my-builder:latest', trust=False, devmode=False))

  def testTrustedDevmodeBuilder(self):
    args = self.parser.parse_args(['--builder=gcr.io/buildpack/builder:v1'])

    self.assertEqual(
        local._CreateBuilder(args, files.GetCWD()),
        local.BuildpackBuilder(
            builder='gcr.io/buildpack/builder:v1', trust=True, devmode=True))

  def testDockerfile(self):
    with files.TemporaryDirectory() as temp_dir:
      dockerfile = os.path.join(temp_dir, 'Dockerfile')
      files.WriteFileContents(dockerfile, '')

      args = self.parser.parse_args(['--dockerfile=' + dockerfile])

      self.assertEqual(
          local._CreateBuilder(args, temp_dir),
          local.DockerfileBuilder(dockerfile=dockerfile))

  def testDockerfileNotInContext(self):
    with files.TemporaryDirectory() as temp_dir, \
         files.TemporaryDirectory() as temp_dir2, \
         self.assertRaises(local.InvalidLocationError):
      dockerfile = os.path.join(temp_dir, 'Dockerfile')
      files.WriteFileContents(dockerfile, '')
      args = self.parser.parse_args(['--dockerfile=' + dockerfile])

      local._CreateBuilder(args, temp_dir2)

  def testDockerfileMissing(self):
    with files.TemporaryDirectory() as temp_dir:
      args = self.parser.parse_args(
          ['--dockerfile=' + os.path.join(temp_dir, 'Dockerfile')])

      with self.assertRaises(local.InvalidLocationError):
        local._CreateBuilder(args, temp_dir)
