# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests of the AppEngine API Client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import build as app_build
from googlecloudsdk.api_lib.app import service_util
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.cloudbuild import logs as cloudbuild_logs
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case
from googlecloudsdk.third_party.appengine.api import appinfo
import mock


class AppEngineApiClientTestBase(sdk_test_base.WithFakeAuth):

  def Project(self):
    return 'fake-project'

  def SetUp(self):
    properties.VALUES.core.project.Set(self.Project())

    api_name = 'appengine'
    api_version = appengine_api_client.AppengineApiClient.ApiVersion()
    beta_api_version = 'v1beta'
    self.mocked_client = apitools_mock.Client(
        apis.GetClientClass(api_name, api_version),
        real_client=apis.GetClientInstance(api_name, api_version, no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

    self.mocked_beta_client = apitools_mock.Client(
        apis.GetClientClass(api_name, beta_api_version),
        real_client=apis.GetClientInstance(
            api_name, beta_api_version, no_http=True))
    self.mocked_beta_client.Mock()
    self.addCleanup(self.mocked_beta_client.Unmock)

    self.messages = apis.GetMessagesModule(api_name, api_version)
    self.beta_messages = apis.GetMessagesModule(api_name, 'v1beta')

    self.client = appengine_api_client.AppengineApiClient(self.mocked_client)
    self.beta_client = appengine_api_client.AppengineApiClient(
        self.mocked_beta_client)

    self.appyaml = appinfo.AppInfoExternal()
    self.appyaml.Set('runtime', 'python27')


class AppEngineApiClientTests(AppEngineApiClientTestBase):
  """Tests of the AppEngine API Client library."""

  def testDeployService(self):
    """Test service deployment using an image name."""
    fake_image = 'fake-image'
    fake_version = 'fake-version'
    self.appyaml.Set('entrypoint', 'ls')

    fake_service = yaml_parsing.ServiceYamlInfo('app.yaml', self.appyaml)
    self.mocked_client.apps_services_versions.Create.Expect(
        request=self.messages.AppengineAppsServicesVersionsCreateRequest(
            parent='apps/fake-project/services/fake-service',
            version=self.messages.Version(
                entrypoint=self.messages.Entrypoint(shell='ls'),
                runtime='python27',
                deployment=self.messages.Deployment(
                    container=self.messages.ContainerInfo(image=fake_image)),
                id=fake_version,
            ),
        ),
        response=self.messages.Operation(done=True))

    fake_build = app_build.BuildArtifact.MakeImageArtifact('fake-image')
    self.client.DeployService('fake-service', fake_version, fake_service,
                              None, fake_build)

  def testDeployServiceWithEnvVars(self):
    """Test service deployment using an image name."""
    fake_image = 'fake-image'
    fake_version = 'fake-version'
    self.appyaml.Set('entrypoint', 'ls')
    variables = appinfo.EnvironmentVariables()
    variables.update({'FOO': 'on', 'BAR': 'true', 'BAZ': '123'})
    self.appyaml.Set('env_variables', variables)

    fake_service = yaml_parsing.ServiceYamlInfo('app.yaml', self.appyaml)
    env_var_message = self.messages.Version.EnvVariablesValue.AdditionalProperty
    self.mocked_client.apps_services_versions.Create.Expect(
        request=self.messages.AppengineAppsServicesVersionsCreateRequest(
            parent='apps/fake-project/services/fake-service',
            version=self.messages.Version(
                entrypoint=self.messages.Entrypoint(shell='ls'),
                runtime='python27',
                deployment=self.messages.Deployment(
                    container=self.messages.ContainerInfo(image=fake_image)),
                id=fake_version,
                envVariables=self.messages.Version.EnvVariablesValue(
                    additionalProperties=[
                        env_var_message(key='BAR', value='true'),
                        env_var_message(key='BAZ', value='123'),
                        env_var_message(key='FOO', value='on')]))),
        response=self.messages.Operation(done=True))

    fake_build = app_build.BuildArtifact.MakeImageArtifact('fake-image')
    self.client.DeployService('fake-service', fake_version, fake_service,
                              None, fake_build)

  def testDeployServiceFromBuildId(self):
    """Test service deployment using an in-progress build ID."""
    fake_build = 'fake-build'
    fake_version = 'fake-version'

    fake_service = yaml_parsing.ServiceYamlInfo('app.yaml', self.appyaml)
    self.mocked_beta_client.apps_services_versions.Create.Expect(
        request=self.beta_messages.AppengineAppsServicesVersionsCreateRequest(
            parent='apps/fake-project/services/fake-service',
            version=self.beta_messages.Version(
                entrypoint=self.beta_messages.Entrypoint(shell=''),
                runtime='python27',
                deployment=self.beta_messages.Deployment(
                    build=self.beta_messages.BuildInfo(
                        cloudBuildId=fake_build)),
                id=fake_version,
            ),
        ),
        response=self.beta_messages.Operation(done=True))

    properties.VALUES.core.project.Set('fake-project')
    cloud_client_mock = mock.MagicMock()
    build_res = resources.REGISTRY.Parse(
        fake_build,
        params={'projectId': 'fake-project'},
        collection='cloudbuild.projects.builds')
    cloud_client_mock = mock.MagicMock()
    self.StartObjectPatch(
        cloudbuild_logs, 'CloudBuildClient', return_value=cloud_client_mock)
    fake_build = app_build.BuildArtifact.MakeBuildIdArtifact(fake_build)
    fake_build.build_op = 'fake_build_op'
    self.beta_client.DeployService('fake-service', fake_version, fake_service,
                                   None, fake_build)
    cloud_client_mock.Stream.assert_called_once_with(build_res)

  def testDeployServiceFromBuildOptions(self):
    """Test service deployment using server-side builds."""
    fake_build = 'fake-build'
    fake_version = 'fake-version'
    manifest = {
        'filea': {'sourceUrl': 'https://storage.googleapis.com/a/b/c.py',
                  'sha1Sum': '123'},
    }
    app_yaml_path = 'yaml.yaml'
    cloud_build_timeout = '333'
    deployment_message = encoding.PyValueToMessage(
        self.beta_messages.Deployment, {'files': manifest,
                                        'cloudBuildOptions': {
                                            'appYamlPath': app_yaml_path,
                                            'cloudBuildTimeout':
                                            cloud_build_timeout,
                                        }})
    fake_service = yaml_parsing.ServiceYamlInfo('app.yaml', self.appyaml)
    op_metadata_warning1 = encoding.MessageToPyValue(
        self.beta_messages.OperationMetadataV1Beta(
            warning=['oh-no!'],
            createVersionMetadata=(
                self.beta_messages.CreateVersionMetadataV1Beta(
                    cloudBuildId='1-2-3-4',)),
        ))
    op_metadata_warning2 = encoding.MessageToPyValue(
        self.beta_messages.OperationMetadataV1Beta(
            warning=['oh-no!', 'it\'s getting worse!'],
            createVersionMetadata=(
                self.beta_messages.CreateVersionMetadataV1Beta(
                    cloudBuildId='1-2-3-4',)),
        ))
    op_metadata_warning1.update({
        '@type': 'type.googleapis.com/google.appengine.OperationMetadataV1Beta'
    })
    op_metadata_warning2.update({
        '@type': 'type.googleapis.com/google.appengine.OperationMetadataV1Beta'
    })
    self.mocked_beta_client.apps_services_versions.Create.Expect(
        request=self.beta_messages.AppengineAppsServicesVersionsCreateRequest(
            parent='apps/fake-project/services/fake-service',
            version=self.beta_messages.Version(
                entrypoint=self.beta_messages.Entrypoint(shell=''),
                runtime='python27',
                deployment=deployment_message,
                id=fake_version,
            ),
        ),
        response=self.beta_messages.Operation(
            name='apps/fake-project/operations/a-b-c-d',
            metadata=encoding.PyValueToMessage(
                self.beta_messages.Operation.MetadataValue,
                op_metadata_warning1,
            )))
    self.mocked_beta_client.apps_operations.Get.Expect(
        request=self.beta_messages.AppengineAppsOperationsGetRequest(
            name='apps/fake-project/operations/a-b-c-d'),
        response=self.beta_messages.Operation(
            metadata=encoding.PyValueToMessage(
                self.beta_messages.Operation.MetadataValue,
                op_metadata_warning2)))
    self.mocked_beta_client.apps_operations.Get.Expect(
        request=self.beta_messages.AppengineAppsOperationsGetRequest(
            name='apps/fake-project/operations/a-b-c-d'),
        response=self.beta_messages.Operation(done=True))

    fake_build = app_build.BuildArtifact.MakeBuildOptionsArtifact({
        'appYamlPath': app_yaml_path,
        'cloudBuildTimeout': cloud_build_timeout,
    })
    properties.VALUES.core.project.Set('fake-project')
    build_res = resources.REGISTRY.Parse(
        '1-2-3-4',
        params={'projectId': 'fake-project'},
        collection='cloudbuild.projects.builds')
    cloud_client_mock = mock.MagicMock()
    self.StartObjectPatch(
        cloudbuild_logs, 'CloudBuildClient', return_value=cloud_client_mock)
    warning_mock = self.StartPropertyPatch(log, 'warning')

    self.beta_client.DeployService('fake-service', fake_version, fake_service,
                                   manifest, fake_build)
    cloud_client_mock.Stream.assert_called_once_with(build_res)
    warning_mock.assert_has_calls(
        [mock.call('oh-no!\n'),
         mock.call('it\'s getting worse!\n')],
        any_order=True)

  def testCreateVersion(self):
    fake_build = app_build.BuildArtifact.MakeBuildIdArtifact('fake-build')
    fake_image = app_build.BuildArtifact.MakeImageArtifact('fake-image')
    fake_service = yaml_parsing.ServiceYamlInfo('app.yaml', self.appyaml)
    self.appyaml.Set('entrypoint', 'ls')

    image_version_expected = self.messages.Version(
        entrypoint=self.messages.Entrypoint(shell='ls'),
        runtime='python27',
        deployment=self.messages.Deployment(
            container=self.messages.ContainerInfo(image='fake-image')))

    image_version_result = self.client._CreateVersionResource(
        fake_service, None, None, fake_image)

    self.assertEqual(image_version_result, image_version_expected)

    # buildId deployments are only supported in the v1beta and v1alpha Admin API
    # versions currently, so use the v1beta client and messages.
    build_version_expected = self.beta_messages.Version(
        entrypoint=self.beta_messages.Entrypoint(shell='ls'),
        runtime='python27',
        deployment=self.beta_messages.Deployment(
            build=self.beta_messages.BuildInfo(cloudBuildId='fake-build')))

    build_version_result = self.beta_client._CreateVersionResource(
        fake_service, None, None, fake_build)

    self.assertEqual(build_version_result, build_version_expected)

  def testDeployService_WithExtraConfigs(self):
    fake_image = 'fake-image'
    fake_version = 'fake-version'
    self.appyaml.Set('entrypoint', 'ls')

    extra_config_settings = {
        'cloud_build_timeout': '50',
    }

    beta_settings = appinfo.BetaSettings()
    # This value is here to test that existing beta_settings value are not
    # over-written
    beta_settings['foo'] = 'bar'
    self.appyaml.beta_settings = beta_settings
    fake_service = yaml_parsing.ServiceYamlInfo('app.yaml', self.appyaml)

    prop = self.messages.Version.BetaSettingsValue.AdditionalProperty
    beta_settings = self.messages.Version.BetaSettingsValue(
        additionalProperties=[
            prop(key='cloud_build_timeout', value='50'),
            prop(key='foo', value='bar'),
        ])
    self.mocked_client.apps_services_versions.Create.Expect(
        request=self.messages.AppengineAppsServicesVersionsCreateRequest(
            parent='apps/fake-project/services/fake-service',
            version=self.messages.Version(
                entrypoint=self.messages.Entrypoint(shell='ls'),
                runtime='python27',
                deployment=self.messages.Deployment(
                    container=self.messages.ContainerInfo(image=fake_image)),
                id=fake_version,
                betaSettings=beta_settings),),
        response=self.messages.Operation(done=True))

    fake_build = app_build.BuildArtifact.MakeImageArtifact('fake-image')
    self.client.DeployService('fake-service', fake_version, fake_service, None,
                              fake_build,
                              extra_config_settings)


class AppEngineApiClientVersionTests(AppEngineApiClientTestBase):
  """Tests for the version-related methods of the App Engine API client."""

  def testDeleteVersion(self):
    version_name = 'apps/{}/services/my-service/versions/my-version'.format(
        self.Project())
    self.mocked_client.apps_services_versions.Delete.Expect(
        self.messages.AppengineAppsServicesVersionsDeleteRequest(
            name=version_name),
        self.messages.Operation(done=True))
    self.client.DeleteVersion('my-service', 'my-version')

  def testListInstancesWhenDeletedRaceCondition(self):
    """Test ListInstances when a version is deleted midway."""
    # Versions can be deleted between getting the list of versions, and
    # requesting their instance information. If this happens, we should
    # gracefully remove the version from the list.
    version_1 = version_util.Version.FromResourcePath(
        'fake-project/fake-svc/fake-ver1')
    version_2 = version_util.Version.FromResourcePath(
        'fake-project/fake-svc/fake-ver2')
    version_3 = version_util.Version.FromResourcePath(
        'fake-project/fake-svc/fake-ver3')
    versions = [version_1, version_2, version_3]

    self.mocked_client.apps_services_versions_instances.List.Expect(
        request=self.messages.AppengineAppsServicesVersionsInstancesListRequest(
            parent='apps/fake-project/services/fake-svc/versions/fake-ver1',
            pageSize=100),
        response=self.messages.ListInstancesResponse(instances=[
            self.messages.Instance(
                name='apps/fake-project/services/fake-svc/versions/fake-ver1/instances/fake-inst1'
            ),
            self.messages.Instance(
                name='apps/fake-project/services/fake-svc/versions/fake-ver1/instances/fake-inst2'
            )
        ]))
    self.mocked_client.apps_services_versions_instances.List.Expect(
        request=self.messages.AppengineAppsServicesVersionsInstancesListRequest(
            parent='apps/fake-project/services/fake-svc/versions/fake-ver2',
            pageSize=100),
        exception=apitools_exceptions.HttpNotFoundError(None, None, None))
    self.mocked_client.apps_services_versions_instances.List.Expect(
        request=self.messages.AppengineAppsServicesVersionsInstancesListRequest(
            parent='apps/fake-project/services/fake-svc/versions/fake-ver3',
            pageSize=100),
        response=self.messages.ListInstancesResponse(instances=[
            self.messages.Instance(
                name='apps/fake-project/services/fake-svc/versions/fake-ver3/instances/fake-inst1'
            ),
            self.messages.Instance(
                name='apps/fake-project/services/fake-svc/versions/fake-ver3/instances/fake-inst2'
            )
        ]))
    expected_instances = [
        'apps/fake-project/services/fake-svc/versions/fake-ver1/instances/fake-inst1',
        'apps/fake-project/services/fake-svc/versions/fake-ver1/instances/fake-inst2',
        'apps/fake-project/services/fake-svc/versions/fake-ver3/instances/fake-inst1',
        'apps/fake-project/services/fake-svc/versions/fake-ver3/instances/fake-inst2'
    ]

    instances = self.client.ListInstances(versions)
    readable_instances = [instance.instance.name for instance in instances]
    self.assertEqual(readable_instances, expected_instances)

  def testListVersionsWhenDeletedRaceCondition(self):
    """Test ListVersions when a service is deleted midway."""
    # Services can be deleted between getting the list of services, and
    # requesting their version information. If this happens, we should
    # gracefully remove the service from the list.
    service_1 = service_util.Service.FromResourcePath('fake-project/fake-svc1')
    service_2 = service_util.Service.FromResourcePath('fake-project/fake-svc2')
    service_3 = service_util.Service.FromResourcePath('fake-project/fake-svc3')
    services = [service_1, service_2, service_3]

    self.mocked_client.apps_services_versions.List.Expect(
        request=self.messages.AppengineAppsServicesVersionsListRequest(
            parent='apps/fake-project/services/fake-svc1', pageSize=100),
        response=self.messages.ListVersionsResponse(versions=[
            self.messages.Version(
                name='apps/fake-project/services/fake-svc1/versions/fake-ver1'),
            self.messages.Version(
                name='apps/fake-project/services/fake-svc1/versions/fake-ver2')
        ]))
    self.mocked_client.apps_services_versions.List.Expect(
        request=self.messages.AppengineAppsServicesVersionsListRequest(
            parent='apps/fake-project/services/fake-svc2', pageSize=100),
        exception=apitools_exceptions.HttpNotFoundError(None, None, None))
    self.mocked_client.apps_services_versions.List.Expect(
        request=self.messages.AppengineAppsServicesVersionsListRequest(
            parent='apps/fake-project/services/fake-svc3', pageSize=100),
        response=self.messages.ListVersionsResponse(versions=[
            self.messages.Version(
                name='apps/fake-project/services/fake-svc3/versions/fake-ver1'),
            self.messages.Version(
                name='apps/fake-project/services/fake-svc3/versions/fake-ver2')
        ]))
    expected_versions = [
        'apps/fake-project/services/fake-svc1/versions/fake-ver1',
        'apps/fake-project/services/fake-svc1/versions/fake-ver2',
        'apps/fake-project/services/fake-svc3/versions/fake-ver1',
        'apps/fake-project/services/fake-svc3/versions/fake-ver2'
    ]

    versions = self.client.ListVersions(services)
    readable_versions = [version.version.name for version in versions]
    self.assertEqual(readable_versions, expected_versions)


class AppEngineApiClientPatchTests(AppEngineApiClientTestBase):
  """Tests for patch-functionality such as dispatch rules update."""

  def testUpdateDispatchRules(self):
    rules = [
        {'domain': 'abc.xyz', 'path': 'do', 'service': 's'},
        {'domain': '*', 'path': 'dont', 'service': 's2'},
    ]
    rules_message = [
        self.messages.UrlDispatchRule(domain='abc.xyz', path='do', service='s'),
        self.messages.UrlDispatchRule(domain='*', path='dont', service='s2'),
    ]
    self.mocked_client.apps.Patch.Expect(
        request=self.messages.AppengineAppsPatchRequest(
            name='apps/fake-project',
            application=self.messages.Application(
                dispatchRules=rules_message),
            updateMask='dispatchRules,'),
        response=self.messages.Operation(done=True))
    self.client.UpdateDispatchRules(rules)


if __name__ == '__main__':
  test_case.main()
