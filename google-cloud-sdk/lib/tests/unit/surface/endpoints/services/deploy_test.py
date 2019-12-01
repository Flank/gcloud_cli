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

"""Unit tests for endpoints services deploy command.

Under certain conditions, various services will be enabled in the process of
running deploy commands.

If servicemanagement.googleapis is disabled, gcloud will detect this when
requests are made and offer to enable it. This is built into gcloud's API
client, rather than the deploy command proper, and as such is NOT tested in
these tests.

When a service is created for the first time, after a successful deployment, the
deploy command will first enable endpoints.googleapis (which is a meta-service
that enables several other services which may or may not already be enabled) as
well as enabling the produced service. Failures to enable these services will be
detected and the user notified.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from apitools.base.py.extra_types import JsonObject
from apitools.base.py.extra_types import JsonValue
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.endpoints import config_reporter
from googlecloudsdk.api_lib.endpoints import exceptions
from googlecloudsdk.api_lib.endpoints import services_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import http_encoding
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.endpoints import unit_test_base

import six
from six.moves import range
import six.moves.urllib.error
import six.moves.urllib.parse
import six.moves.urllib.request


SERVICE_NAME = 'service-name.googleapis.com'
SERVICE_VERSION = 'service-config-version-1'
TITLE = 'The title of my swagger spec or google service config APIs!'
CONFIG_TEMPLATE = """
{
     "title": "%s",
     "name": "%s"
}
"""
TEST_CONFIG = http_encoding.Encode(CONFIG_TEMPLATE % (TITLE, SERVICE_NAME))
TEST_SWAGGER = http_encoding.Encode("""
{
   "swagger": "2.0",
   "host": "%s",
   "title": "%s"
}
""" % (SERVICE_NAME, TITLE))
TEST_SWAGGER_YAML = http_encoding.Encode("""
---
  title: "%s"
  host: "%s"
  swagger: "2.0"
""" % (TITLE, SERVICE_NAME))
TEST_SERVICE_CONFIG_YAML = http_encoding.Encode("""
---
  type: google.api.Service
  name: "%s"
  title: "%s"
""" % (SERVICE_NAME, TITLE))
TEST_SERVICE_CONFIG_2_YAML = http_encoding.Encode("""
---
  type: google.api.Service
  name: foobar
  http:
    rules:
    - selector: endpoints.examples.bookstore.Bookstore.ListShelves
      get: /v1/shelves
""")
TEST_RAW_PROTO = http_encoding.Encode("""
syntax = "proto3";
service Bookstore {
  rpc GetShelf(GetShelfRequest) returns (Shelf) {}
}
""")
TEST_SERVICE_CONFIG_NO_TYPE_YAML = http_encoding.Encode("""
---
  name: "%s"
  title: "%s"
""" % (SERVICE_NAME, TITLE))

ENABLED = True
DISABLED = False

# Shorten these names for better readability
FILE_TYPES = (services_util.GetMessagesModule().ConfigFile.
              FileTypeValueValuesEnum)

CONFIG_CREATE_REQUEST = (services_util.GetMessagesModule().
                         ServicemanagementServicesConfigsCreateRequest)

SUBMIT_REQUEST = (services_util.GetMessagesModule().
                  ServicemanagementServicesConfigsSubmitRequest)


class EndpointsDeployTest(unit_test_base.EV1UnitTestBase, test_case.WithInput):
  """Unit tests for endpoints services deploy command."""

  def PreSetUp(self):
    self.su_services_messages = core_apis.GetMessagesModule(
        'serviceusage', 'v1')
    self.su_mocked_client = mock.Client(
        core_apis.GetClientClass('serviceusage', 'v1'),
        real_client=core_apis.GetClientInstance(
            'serviceusage', 'v1', no_http=True))
    self.su_mocked_client.Mock()
    self.addCleanup(self.su_mocked_client.Unmock)

  def SetUp(self):
    prop = self.services_messages.Operation.ResponseValue.AdditionalProperty
    self.op = self.services_messages.Operation
    self.operation_name = 'operation-12345-67890'
    self.operation = self.op(
        name=self.operation_name,
        done=False,
        response=self.op.ResponseValue(additionalProperties=[
            prop(key='producerProjectId',
                 value=JsonValue(string_value=self.PROJECT_NAME)),
            prop(key='serviceName', value=JsonValue(string_value=SERVICE_NAME)),
            prop(key='serviceConfig', value=JsonValue(
                object_value=JsonObject(properties=[JsonObject.Property(
                    key='id', value=JsonValue(string_value=SERVICE_VERSION))])))
        ])
    )
    self.completed_operation = self.op(
        name=self.operation_name,
        done=True,
        response=self.op.ResponseValue(additionalProperties=[
            prop(key='serviceName', value=JsonValue(string_value=SERVICE_NAME)),
            prop(key='serviceConfig', value=JsonValue(
                object_value=JsonObject(properties=[JsonObject.Property(
                    key='id', value=JsonValue(string_value=SERVICE_VERSION))])))
        ])
    )
    self.usage_settings = self.services_messages.UsageSettings(
        consumerEnableStatus=(self.services_messages.UsageSettings.
                              ConsumerEnableStatusValueValuesEnum.ENABLED)
    )
    self.project_settings = self.services_messages.ProjectSettings(
        usageSettings=self.usage_settings)

    self._config_file_path = self.Touch(
        self.temp_path, name='service.json', contents=TEST_CONFIG)
    self._config_yaml_file_path = self.Touch(
        self.temp_path, name='service.yaml',
        contents=TEST_SERVICE_CONFIG_NO_TYPE_YAML)
    self._swagger_file_path = self.Touch(
        self.temp_path, name='swagger.json', contents=TEST_SWAGGER)
    self._swagger_yaml_file_path = self.Touch(
        self.temp_path, name='swagger.yaml', contents=TEST_SWAGGER_YAML)

    self.blank_config_report_response = (
        self.services_messages.GenerateConfigReportResponse(
            serviceName=SERVICE_NAME,
            id='MyConfigReport',
            changeReports=[],
            diagnostics=[]))

    self.alpha = False
    self.beta = False
    self.base_cmd = 'endpoints services deploy'

  def _AssertManagementUrlDisplayed(self, service=SERVICE_NAME, project=None):
    # Assert that we printed out the Endpoints Management UI link for a
    # successful deployment.
    project = project or self.PROJECT_NAME
    self.AssertErrContains(
        'To manage your API, go to: '
        'https://console.cloud.google.com/endpoints/api/'
        '{service}/overview?project={project}'.format(
            service=six.moves.urllib.parse.quote(service),
            project=six.moves.urllib.parse.quote(project)))

  def _MockServiceGetCall(self, service_name, project_name=None):
    self.mocked_client.services.Get.Expect(
        request=self.services_messages.ServicemanagementServicesGetRequest(
            serviceName=service_name
        ),
        response=(self.services_messages.ManagedService(
            serviceName=service_name, producerProjectId=project_name)))

  def _MockServiceRolloutCreate(self, service_name, service_version):
    traffic = self.services_messages.TrafficPercentStrategy
    rollout = self.services_messages.Rollout(
        serviceName=service_name,
        trafficPercentStrategy=traffic(
            percentages=(traffic.PercentagesValue(
                additionalProperties=[
                    (traffic.PercentagesValue.AdditionalProperty(
                        key='service-config-version-1',
                        value=100.0))]))))
    # These class names are reminding me uncomfortably of Java.
    rcr = self.services_messages.ServicemanagementServicesRolloutsCreateRequest
    self.mocked_client.services_rollouts.Create.Expect(
        request=rcr(rollout=rollout, serviceName=service_name),
        response=self.completed_operation)

  def _WaitForPushAdvisorReport(self, service_name, service_version, result):
    if self.beta or self.alpha:
      reporter = config_reporter.ConfigReporter(service_name)
      reporter.new_config.SetConfigId(service_version)
      reporter.old_config.SetConfigUseDefaultId()
      self.ExpectConfigReportRequest(reporter, result)

  def _WaitForBlankPushAdvisorReport(self, service_name, service_version):
    self._WaitForPushAdvisorReport(service_name, service_version,
                                   self.blank_config_report_response)

  def testDeployFailsOnMissingFile(self):
    with self.assertRaisesRegex(
        calliope_exceptions.BadFileException,
        r'Could not open service config file \[missing-file\]'):
      self.Run('{0} missing-file'.format(self.base_cmd))

  def testDeployFailsOnBadFileExceptionErrors(self):
    self._config_file_path = self.Touch(
        self.temp_path, name='file-with-no-extension', contents=TEST_CONFIG)
    with self.assertRaisesRegex(
        calliope_exceptions.BadFileException,
        'Could not determine the content type of file'):
      self.Run('{0} {1}'.format(self.base_cmd, self._config_file_path))

    self._config_file_path = self.Touch(
        self.temp_path,
        name='file-with-bad-contents.json',
        contents='!foo-bar-contents!')
    with self.assertRaisesRegex(
        calliope_exceptions.BadFileException,
        'Could not read JSON or YAML from service config file'):
      self.Run('{0} {1}'.format(self.base_cmd, self._config_file_path))

    self._config_file_path = self.Touch(
        self.temp_path,
        name='valid-json-but-no-api-spec-in-contents.json',
        contents='{"foo": "bar"}')
    with self.assertRaisesRegex(
        calliope_exceptions.BadFileException,
        'Unable to parse Open API, or Google Service Configuration '):
      self.Run('{0} {1}'.format(self.base_cmd, self._config_file_path))

    self._config_file_path = self._config_file_path = self.Touch(
        self.temp_path, name='service.json', contents=TEST_CONFIG)
    with self.assertRaisesRegex(
        calliope_exceptions.BadFileException,
        'Ambiguous input. Found normalized service configuration in file'):
      self.Run('{0} {1} {2}'.format(self.base_cmd,
                                    self._swagger_file_path,
                                    self._config_file_path))

  def testDeployMultipleSwaggerFilesAtOnce(self):
    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # Mock the SubmitSourceConfig API call.
    self.mocked_client.services_configs.Submit.Expect(
        request=(SUBMIT_REQUEST(
            serviceName=SERVICE_NAME,
            submitConfigSourceRequest=(
                self.services_messages.SubmitConfigSourceRequest(
                    configSource=self.services_messages.ConfigSource(
                        files=[
                            self.services_messages.ConfigFile(
                                fileContents=six.binary_type(TEST_SWAGGER_YAML),
                                filePath=os.path.basename(
                                    self._swagger_yaml_file_path),
                                fileType=FILE_TYPES.OPEN_API_YAML),
                            self.services_messages.ConfigFile(
                                fileContents=six.binary_type(TEST_SWAGGER_YAML),
                                filePath=os.path.basename(
                                    self._swagger_yaml_file_path),
                                fileType=FILE_TYPES.OPEN_API_YAML)
                        ]),
                    validateOnly=False)))),
        response=self.operation
    )
    submit_response = {
        'serviceConfig': {'id': SERVICE_VERSION, 'name': SERVICE_NAME},
        'diagnostics': [
            {
                'kind': 'WARNING',
                'location': 'foo',
                'message': 'diagnostic warning message bar'
            }
        ]
    }
    self.MockOperationWait(self.operation_name, submit_response)

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    # Mock the Service Rollout creation.
    self._MockServiceRolloutCreate(SERVICE_NAME, SERVICE_VERSION)
    self.MockOperationWait(self.operation_name)

    # A Get call is required to generate the management url
    self._MockServiceGetCall(SERVICE_NAME, self.PROJECT_NAME)

    self.Run('{0} {1} {2}'.format(self.base_cmd,
                                  self._swagger_yaml_file_path,
                                  self._swagger_yaml_file_path))
    self.AssertErrContains('WARNING: foo: diagnostic warning message bar')
    self.AssertErrContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    self._AssertManagementUrlDisplayed()

  def testDeployMultipleProtoYamlFilesAtOnce(self):
    proto_binary = b'`1234568908@#%*@(#*$ !!! binary-foo!!! %!@#!%@!#$!@#$'
    yaml_file = self.Touch(self.temp_path, name='bookstore.yaml',
                           contents=TEST_SERVICE_CONFIG_YAML)
    yaml_file_2 = self.Touch(self.temp_path, name='bookstore_config.yaml',
                             contents=TEST_SERVICE_CONFIG_2_YAML)
    proto_file = self.Touch(
        self.temp_path, name='bookstore.descriptor', contents=proto_binary)

    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # Mock the SubmitSourceConfig API call.
    self.mocked_client.services_configs.Submit.Expect(
        request=(SUBMIT_REQUEST(
            serviceName=SERVICE_NAME,
            submitConfigSourceRequest=(
                self.services_messages.SubmitConfigSourceRequest(
                    configSource=self.services_messages.ConfigSource(
                        files=[
                            self.services_messages.ConfigFile(
                                fileContents=six.binary_type(proto_binary),
                                filePath=os.path.basename(proto_file),
                                fileType=FILE_TYPES.FILE_DESCRIPTOR_SET_PROTO),
                            self.services_messages.ConfigFile(
                                fileContents=six.binary_type(
                                    TEST_SERVICE_CONFIG_YAML),
                                filePath=os.path.basename(yaml_file),
                                fileType=FILE_TYPES.SERVICE_CONFIG_YAML),
                            self.services_messages.ConfigFile(
                                fileContents=six.binary_type(
                                    TEST_SERVICE_CONFIG_2_YAML),
                                filePath=os.path.basename(yaml_file_2),
                                fileType=FILE_TYPES.SERVICE_CONFIG_YAML)
                        ]),
                    validateOnly=False)))),
        response=self.operation
    )
    submit_response = {
        'serviceConfig': {'id': SERVICE_VERSION, 'name': SERVICE_NAME},
        'diagnostics': [
            {
                'kind': 'WARNING',
                'location': 'foo',
                'message': 'diagnostic warning message bar'
            }
        ]
    }
    self.MockOperationWait(self.operation_name, submit_response)

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    # Mock the Service Rollout creation.
    self._MockServiceRolloutCreate(SERVICE_NAME, SERVICE_VERSION)
    self.MockOperationWait(self.operation_name)

    # A Get call is required to generate the management url
    self._MockServiceGetCall(SERVICE_NAME, self.PROJECT_NAME)

    self.Run('{0} {1} {2} {3}'.format(
        self.base_cmd, proto_file, yaml_file, yaml_file_2))
    self.AssertErrContains('WARNING: foo: diagnostic warning message bar')
    self.AssertErrContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    self._AssertManagementUrlDisplayed()

  def testDeployWithRawProtoFiles(self):
    # Verify that the deploy command correctly accepts raw proto files as input.
    raw_proto_file = self.Touch(self.temp_path, name='bookstore.proto',
                                contents=TEST_RAW_PROTO)
    yaml_file = self.Touch(self.temp_path, name='bookstore.yaml',
                           contents=TEST_SERVICE_CONFIG_YAML)

    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # Mock the SubmitSourceConfig API call.
    self.mocked_client.services_configs.Submit.Expect(
        request=(SUBMIT_REQUEST(
            serviceName=SERVICE_NAME,
            submitConfigSourceRequest=(
                self.services_messages.SubmitConfigSourceRequest(
                    configSource=self.services_messages.ConfigSource(
                        files=[
                            self.services_messages.ConfigFile(
                                fileContents=six.binary_type(
                                    TEST_SERVICE_CONFIG_YAML),
                                filePath=os.path.basename(yaml_file),
                                fileType=FILE_TYPES.SERVICE_CONFIG_YAML),
                            self.services_messages.ConfigFile(
                                fileContents=six.binary_type(TEST_RAW_PROTO),
                                filePath=os.path.basename(raw_proto_file),
                                fileType=FILE_TYPES.PROTO_FILE)
                        ]),
                    validateOnly=False)))),
        response=self.operation
    )
    submit_response = {
        'serviceConfig': {'id': SERVICE_VERSION, 'name': SERVICE_NAME},
        'diagnostics': [
            {
                'kind': 'WARNING',
                'location': 'foo',
                'message': 'diagnostic warning message bar'
            }
        ]
    }
    self.MockOperationWait(self.operation_name, submit_response)

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    # Mock the Service Rollout creation.
    self._MockServiceRolloutCreate(SERVICE_NAME, SERVICE_VERSION)
    self.MockOperationWait(self.operation_name)

    # A Get call is required to generate the management url
    self._MockServiceGetCall(SERVICE_NAME, self.PROJECT_NAME)

    self.Run('{0} {1} {2}'.format(
        self.base_cmd, yaml_file, raw_proto_file))
    self.AssertErrContains('WARNING: foo: diagnostic warning message bar')
    self.AssertErrContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    # TODO(b/77867100): remove after deprecation period.
    self.AssertErrContains(
        'Support for uploading uncompiled .proto files is deprecated and will '
        'soon be removed. Use compiled descriptor sets (.pb) instead.')

    self._AssertManagementUrlDisplayed()

  def testServicesDeployNewServiceConfig(self):
    config_to_deploy = self.services_messages.Service(
        name=SERVICE_NAME,
        producerProjectId=self.PROJECT_NAME,
        title=TITLE)

    # The service does not exist yet, so it is created first.
    self.mocked_client.services.Get.Expect(
        request=self.services_messages.ServicemanagementServicesGetRequest(
            serviceName=SERVICE_NAME,
        ),
        exception=http_error.MakeHttpError(code=403)
    )
    managed_service = self.services_messages.ManagedService(
        serviceName=SERVICE_NAME,
        producerProjectId=self.PROJECT_NAME,
    )
    self.mocked_client.services.Create.Expect(
        request=managed_service,
        response=self.services_messages.Operation(name='operations/myop')
    )
    self.MockOperationWait('myop')

    # The service configuration resource is created.
    self.mocked_client.services_configs.Create.Expect(
        request=CONFIG_CREATE_REQUEST(
            serviceName=SERVICE_NAME,
            service=config_to_deploy,
        ),
        response=self.services_messages.Service(
            name=SERVICE_NAME,
            producerProjectId=self.PROJECT_NAME,
            title=TITLE,
            id=SERVICE_VERSION,  # this id is set by the server
        ),
    )

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    # Mock the Service Rollout creation.
    self._MockServiceRolloutCreate(SERVICE_NAME, SERVICE_VERSION)
    self.MockOperationWait(self.operation_name)

    # The produced service is enabled here because the service was created.
    self._expectEnableService(SERVICE_NAME, self.PROJECT_NAME,
                              self.operation_name)

    # A Get call is required to generate the management url
    self._MockServiceGetCall(SERVICE_NAME, self.PROJECT_NAME)

    self.Run('{0} {1}'.format(self.base_cmd, self._config_file_path))

    # Assert that we had to auto-enable the service, since it was not yet
    # enabled.
    self.AssertLogContains('Enabling service [{0}] on project [{1}]...'.format(
        SERVICE_NAME, self.PROJECT_NAME))

    self.AssertErrContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    self._AssertManagementUrlDisplayed()

  def testServicesDeployNewServiceConfigEnablementFailure(self):
    # This test is basically the same as the previous one, except enabling
    # the Endpoints meta-service and the produced service will fail.
    config_to_deploy = self.services_messages.Service(
        name=SERVICE_NAME,
        producerProjectId=self.PROJECT_NAME,
        title=TITLE)

    # The service does not exist yet, so it is created first.
    self.mocked_client.services.Get.Expect(
        request=self.services_messages.ServicemanagementServicesGetRequest(
            serviceName=SERVICE_NAME,
        ),
        exception=http_error.MakeHttpError(code=403)
    )
    managed_service = self.services_messages.ManagedService(
        serviceName=SERVICE_NAME,
        producerProjectId=self.PROJECT_NAME,
    )
    self.mocked_client.services.Create.Expect(
        request=managed_service,
        response=self.services_messages.Operation(name='operations/myop')
    )
    self.MockOperationWait('myop')

    # The service configuration resource is created.
    self.mocked_client.services_configs.Create.Expect(
        request=CONFIG_CREATE_REQUEST(
            serviceName=SERVICE_NAME,
            service=config_to_deploy,
        ),
        response=self.services_messages.Service(
            name=SERVICE_NAME,
            producerProjectId=self.PROJECT_NAME,
            title=TITLE,
            id=SERVICE_VERSION,  # this id is set by the server
        ),
    )

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    # Mock the Service Rollout creation.
    self._MockServiceRolloutCreate(SERVICE_NAME, SERVICE_VERSION)
    self.MockOperationWait(self.operation_name)

    # The produced service is enabled here because the service was created.
    self._expectEnableService(SERVICE_NAME, self.PROJECT_NAME, None,
                              http_error.MakeHttpError(code=403))

    # A Get call is required to generate the management url
    self._MockServiceGetCall(SERVICE_NAME, self.PROJECT_NAME)

    self.Run('{0} {1}'.format(self.base_cmd, self._config_file_path))

    # Assert that we had to auto-enable the service, since it was not yet
    # enabled.
    self.AssertLogContains('Enabling service [{0}] on project [{1}]...'.format(
        SERVICE_NAME, self.PROJECT_NAME))

    # This is an abbreviation of the full error message
    # in AttemptToEnableService()
    self.AssertErrContains(
        'Attempted to enable service [{0}]'.format(SERVICE_NAME))

    self.AssertErrContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    self._AssertManagementUrlDisplayed()

  def testServicesDeployGoogleServiceConfig(self):
    config_to_deploy = self.services_messages.Service(
        name=SERVICE_NAME,
        producerProjectId=self.PROJECT_NAME,
        title=TITLE)

    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # The service configuration resource is created.
    self.mocked_client.services_configs.Create.Expect(
        request=CONFIG_CREATE_REQUEST(
            serviceName=SERVICE_NAME,
            service=config_to_deploy,
        ),
        response=self.services_messages.Service(
            name=SERVICE_NAME,
            producerProjectId=self.PROJECT_NAME,
            title=TITLE,
            id=SERVICE_VERSION,  # this id is set by the server
        ),
    )

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    # Mock the Service Rollout creation.
    self._MockServiceRolloutCreate(SERVICE_NAME, SERVICE_VERSION)
    self.MockOperationWait(self.operation_name)

    # A Get call is required to generate the management url
    self._MockServiceGetCall(SERVICE_NAME, self.PROJECT_NAME)

    self.Run('{0} {1}'.format(self.base_cmd, self._config_file_path))

    self.AssertErrContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    self._AssertManagementUrlDisplayed()

  def testServicesDeployGoogleServiceConfigYaml(self):
    config_to_deploy = self.services_messages.Service(
        name=SERVICE_NAME,
        producerProjectId=self.PROJECT_NAME,
        title=TITLE)

    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # The service configuration resource is created.
    self.mocked_client.services_configs.Create.Expect(
        request=CONFIG_CREATE_REQUEST(
            serviceName=SERVICE_NAME,
            service=config_to_deploy,
        ),
        response=self.services_messages.Service(
            name=SERVICE_NAME,
            producerProjectId=self.PROJECT_NAME,
            title=TITLE,
            id=SERVICE_VERSION,  # this id is set by the server
        ),
    )

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    # Mock the Service Rollout creation.
    self._MockServiceRolloutCreate(SERVICE_NAME, SERVICE_VERSION)
    self.MockOperationWait(self.operation_name)

    # A Get call is required to generate the management url
    self._MockServiceGetCall(SERVICE_NAME, self.PROJECT_NAME)

    self.Run('{0} {1}'.format(self.base_cmd, self._config_yaml_file_path))

    self.AssertErrContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    self._AssertManagementUrlDisplayed()

  def testServicesDeployGoogleServiceConfigAlreadyEnabled(self):
    config_to_deploy = self.services_messages.Service(
        name=SERVICE_NAME,
        producerProjectId=self.PROJECT_NAME,
        title=TITLE)

    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # The service configuration resource is created.
    self.mocked_client.services_configs.Create.Expect(
        request=CONFIG_CREATE_REQUEST(
            serviceName=SERVICE_NAME,
            service=config_to_deploy,
        ),
        response=self.services_messages.Service(
            name=SERVICE_NAME,
            producerProjectId=self.PROJECT_NAME,
            title=TITLE,
            id=SERVICE_VERSION,  # this id is set by the server
        ),
    )

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    # Mock the Service Rollout creation.
    self._MockServiceRolloutCreate(SERVICE_NAME, SERVICE_VERSION)
    self.MockOperationWait(self.operation_name)

    # A Get call is required to generate the management url
    self._MockServiceGetCall(SERVICE_NAME, self.PROJECT_NAME)

    self.Run('{0} {1}'.format(self.base_cmd, self._config_file_path))

    self.AssertErrContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    self._AssertManagementUrlDisplayed()

  def testServicesDeployGoogleServiceConfigAsync(self):
    config_to_deploy = self.services_messages.Service(
        name=SERVICE_NAME,
        producerProjectId=self.PROJECT_NAME,
        title=TITLE)

    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # The service configuration resource is created.
    self.mocked_client.services_configs.Create.Expect(
        request=CONFIG_CREATE_REQUEST(
            serviceName=SERVICE_NAME,
            service=config_to_deploy,
        ),
        response=self.services_messages.Service(
            name=SERVICE_NAME,
            producerProjectId=self.PROJECT_NAME,
            title=TITLE,
            id=SERVICE_VERSION,  # this id is set by the server
        ),
    )

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    # Mock the Service Rollout creation.
    self._MockServiceRolloutCreate(SERVICE_NAME, SERVICE_VERSION)

    # A Get call is required to generate the management url
    self._MockServiceGetCall(SERVICE_NAME, self.PROJECT_NAME)

    self.Run('{0} --async {1}'.format(self.base_cmd,
                                      self._config_file_path))

    self.AssertErrNotContains('Waiting for async operation')

    expected_cmd = ('gcloud endpoints operations wait '
                    '{0}'.format(self.operation_name))
    self.AssertErrContains(
        'Asynchronous operation is in progress... '
        'Use the following command to wait for its '
        'completion:\n {0}'.format(expected_cmd))

    self.AssertErrContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    self._AssertManagementUrlDisplayed()

  def testServicesDeployYamlSwaggerConfig(self):
    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # Mock the SubmitSourceConfig API call.
    self.mocked_client.services_configs.Submit.Expect(
        request=(SUBMIT_REQUEST(
            serviceName=SERVICE_NAME,
            submitConfigSourceRequest=(
                self.services_messages.SubmitConfigSourceRequest(
                    configSource=self.services_messages.ConfigSource(
                        files=[self.services_messages.ConfigFile(
                            fileContents=six.binary_type(TEST_SWAGGER_YAML),
                            filePath=os.path.basename(
                                self._swagger_yaml_file_path),
                            fileType=FILE_TYPES.OPEN_API_YAML)]),
                    validateOnly=False)))),
        response=self.operation
    )
    submit_response = {
        'serviceConfig': {'id': SERVICE_VERSION, 'name': SERVICE_NAME},
        'diagnostics': [
            {
                'kind': 'WARNING',
                'location': 'foo',
                'message': 'diagnostic warning message bar'
            }
        ]
    }
    self.MockOperationWait(self.operation_name, submit_response)

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    # Mock the Service Rollout creation.
    self._MockServiceRolloutCreate(SERVICE_NAME, SERVICE_VERSION)
    self.MockOperationWait(self.operation_name)

    # A Get call is required to generate the management url
    self._MockServiceGetCall(SERVICE_NAME, self.PROJECT_NAME)

    self.Run('{0} {1}'.format(
        self.base_cmd, self._swagger_yaml_file_path))
    self.AssertErrContains('WARNING: foo: diagnostic warning message bar')
    self.AssertErrContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    self._AssertManagementUrlDisplayed()

  def testServicesDeployJSONSwaggerConfig(self):
    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # Mock the SubmitSourceConfig API call.
    self.mocked_client.services_configs.Submit.Expect(
        request=(SUBMIT_REQUEST(
            serviceName=SERVICE_NAME,
            submitConfigSourceRequest=(
                self.services_messages.SubmitConfigSourceRequest(
                    configSource=self.services_messages.ConfigSource(
                        files=[self.services_messages.ConfigFile(
                            fileContents=six.binary_type(TEST_SWAGGER),
                            filePath=os.path.basename(
                                self._swagger_file_path),
                            fileType=FILE_TYPES.OPEN_API_YAML)]),
                    validateOnly=False)))),
        response=self.operation
    )
    submit_response = {'serviceConfig': {
        'id': SERVICE_VERSION, 'name': SERVICE_NAME}}
    self.MockOperationWait(self.operation_name, submit_response)

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    # Mock the Service Rollout creation.
    self._MockServiceRolloutCreate(SERVICE_NAME, SERVICE_VERSION)
    self.MockOperationWait(self.operation_name)

    # A Get call is required to generate the management url
    self._MockServiceGetCall(SERVICE_NAME, self.PROJECT_NAME)

    self.Run('{0} {1}'.format(self.base_cmd, self._swagger_file_path))

    self.AssertErrContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    self.AssertErrContains(
        'Waiting for async operation {0} to complete...'.format(
            self.operation_name))

    expected_cmd = ('gcloud endpoints operations describe '
                    '{0}'.format(self.operation_name))
    self.AssertErrContains(
        'Operation finished successfully. '
        'The following command can describe '
        'the Operation details:\n {0}'.format(expected_cmd))

    self._AssertManagementUrlDisplayed()

  def testServicesDeployCrossProject(self):
    # This test covers deploying to a service in another project, which is
    # permitted when the service already exists. However, we want to display
    # the correct Management URL when we do this.

    project_name = 'one-' + self.PROJECT_NAME + '-another'

    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # Mock the SubmitSourceConfig API call.
    self.mocked_client.services_configs.Submit.Expect(
        request=(SUBMIT_REQUEST(
            serviceName=SERVICE_NAME,
            submitConfigSourceRequest=(
                self.services_messages.SubmitConfigSourceRequest(
                    configSource=self.services_messages.ConfigSource(
                        files=[self.services_messages.ConfigFile(
                            fileContents=six.binary_type(TEST_SWAGGER),
                            filePath=os.path.basename(
                                self._swagger_file_path),
                            fileType=FILE_TYPES.OPEN_API_YAML)]),
                    validateOnly=False)))),
        response=self.operation
    )
    submit_response = {'serviceConfig': {
        'id': SERVICE_VERSION, 'name': SERVICE_NAME}}
    self.MockOperationWait(self.operation_name, submit_response)

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    # Mock the Service Rollout creation.
    self._MockServiceRolloutCreate(SERVICE_NAME, SERVICE_VERSION)
    self.MockOperationWait(self.operation_name)

    # A Get call is required to generate the management url
    self._MockServiceGetCall(SERVICE_NAME, project_name)

    self.Run('{0} {1}'.format(self.base_cmd, self._swagger_file_path))

    self.AssertErrContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    self.AssertErrContains(
        'Waiting for async operation {0} to complete...'.format(
            self.operation_name))

    expected_cmd = ('gcloud endpoints operations describe '
                    '{0}'.format(self.operation_name))
    self.AssertErrContains(
        'Operation finished successfully. '
        'The following command can describe '
        'the Operation details:\n {0}'.format(expected_cmd))

    self._AssertManagementUrlDisplayed(project=project_name)

  def testServicesDeployNoServiceVersion(self):
    config_to_deploy = self.services_messages.Service(
        name=SERVICE_NAME,
        producerProjectId=self.PROJECT_NAME,
        title=TITLE)

    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # The service configuration resource is created.
    self.mocked_client.services_configs.Create.Expect(
        request=CONFIG_CREATE_REQUEST(
            serviceName=SERVICE_NAME,
            service=config_to_deploy,
        ),
        # This response is malformed because it does not contain a service
        # version
        response=self.services_messages.Service(
            name=SERVICE_NAME,
            producerProjectId=self.PROJECT_NAME,
            title=TITLE,
            id=None
        ),
    )

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidConditionError,
        'Failed to retrieve Service Configuration Id'):
      self.Run('{0} {1}'.format(self.base_cmd, self._config_file_path))

  def testServicesDeployServiceConfigValidateOnly(self):
    with self.AssertRaisesExceptionMatches(
        core_exceptions.Error,
        'The --validate-only flag is not supported when using normalized '
        'service configs as input.'):
      self.Run('{0} {1} --validate-only'.format(
          self.base_cmd, self._config_file_path))

    # Assert that we did not auto-enable the service, since this is a
    # validate-only run
    self.AssertLogNotContains(
        'Enabling service [{0}] on project [{1}]...'.format(
            SERVICE_NAME, self.PROJECT_NAME))

    # Assert that we did not print out the actual uploaded success message,
    # since this is a validate-only run
    self.AssertErrNotContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    # Assert that we did not print out the Endpoints Management UI link,
    # since this is a validate-only run
    self.AssertErrNotContains('To manage your API, go to:')

  def testServicesDeployJSONSwaggerConfigValidateOnly(self):
    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # Mock the SubmitSourceConfig API call.
    self.mocked_client.services_configs.Submit.Expect(
        request=(SUBMIT_REQUEST(
            serviceName=SERVICE_NAME,
            submitConfigSourceRequest=(
                self.services_messages.SubmitConfigSourceRequest(
                    configSource=self.services_messages.ConfigSource(
                        files=[self.services_messages.ConfigFile(
                            fileContents=six.binary_type(TEST_SWAGGER),
                            filePath=os.path.basename(
                                self._swagger_file_path),
                            fileType=FILE_TYPES.OPEN_API_YAML)]),
                    validateOnly=True)))),
        response=self.operation
    )
    submit_response = {'serviceConfig': {
        'id': SERVICE_VERSION, 'name': SERVICE_NAME}}
    self.MockOperationWait(self.operation_name, submit_response)

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    self.Run('{0} {1} --validate-only'.format(
        self.base_cmd, self._swagger_file_path))

    # Make sure the uploaded status message does not print out, since this is
    # a validate-only run.
    self.AssertErrNotContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    # Assert that we did not print out the Endpoints Management UI link,
    # since this is a validate-only run
    self.AssertErrNotContains('To manage your API, go to:')

    self.AssertErrContains(
        'Waiting for async operation {0} to complete...'.format(
            self.operation_name))

    expected_cmd = ('gcloud endpoints operations describe '
                    '{0}'.format(self.operation_name))
    self.AssertErrContains(
        'Operation finished successfully. '
        'The following command can describe '
        'the Operation details:\n {0}'.format(expected_cmd))

  def testServicesDeployValidateOnlyNewServiceNonInteractive(self):
    # The service does not exist yet, so it is created first.
    self.mocked_client.services.Get.Expect(
        request=self.services_messages.ServicemanagementServicesGetRequest(
            serviceName=SERVICE_NAME,
        ),
        exception=http_error.MakeHttpError(code=403)
    )

    with self.AssertRaisesExceptionMatches(
        core_exceptions.Error,
        'The service {0} must exist in order to '
        'validate the configuration. To create the service in project '
        '{1}, rerun the command without the --validate-only flag.'.format(
            SERVICE_NAME, self.PROJECT_NAME)):
      self.Run('{0} {1} --validate-only'.format(
          self.base_cmd, self._swagger_file_path))

    # Make sure the uploaded status message does not print out, since this is
    # a validate-only run.
    self.AssertErrNotContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    # Assert that we did not print out the Endpoints Management UI link,
    # since this is a validate-only run
    self.AssertErrNotContains('To manage your API, go to:')

    self.AssertErrContains('must exist in order to validate')
    self.AssertErrContains('To create the service')
    self.AssertErrContains(SERVICE_NAME)
    self.AssertErrContains(self.PROJECT_NAME)

  def testServicesDeployValidateOnlyNewServiceInteractiveYes(self):
    self.StartObjectPatch(console_io, 'CanPrompt', return_value=True)

    # The service does not exist yet, so it is created first.
    self.mocked_client.services.Get.Expect(
        request=self.services_messages.ServicemanagementServicesGetRequest(
            serviceName=SERVICE_NAME,
        ),
        exception=http_error.MakeHttpError(code=403)
    )
    managed_service = self.services_messages.ManagedService(
        serviceName=SERVICE_NAME,
        producerProjectId=self.PROJECT_NAME,
    )
    self.mocked_client.services.Create.Expect(
        request=managed_service,
        response=self.services_messages.Operation(name='operations/myop')
    )
    self.MockOperationWait('myop')

    # Mock the SubmitSourceConfig API call.
    self.mocked_client.services_configs.Submit.Expect(
        request=(SUBMIT_REQUEST(
            serviceName=SERVICE_NAME,
            submitConfigSourceRequest=(
                self.services_messages.SubmitConfigSourceRequest(
                    configSource=self.services_messages.ConfigSource(
                        files=[self.services_messages.ConfigFile(
                            fileContents=six.binary_type(TEST_SWAGGER),
                            filePath=os.path.basename(
                                self._swagger_file_path),
                            fileType=FILE_TYPES.OPEN_API_YAML)]),
                    validateOnly=True)))),
        response=self.operation
    )
    submit_response = {'serviceConfig': {
        'id': SERVICE_VERSION, 'name': SERVICE_NAME}}
    self.MockOperationWait(self.operation_name, submit_response)

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)
    self.WriteInput('yes')

    self.Run('{0} {1} --validate-only'.format(
        self.base_cmd, self._swagger_file_path))

    # Make sure the uploaded status message does not print out, since this is
    # a validate-only run.
    self.AssertErrNotContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    # Assert that we did not print out the Endpoints Management UI link,
    # since this is a validate-only run
    self.AssertErrNotContains('To manage your API, go to:')

    self.AssertErrContains('must exist')
    self.AssertErrContains('Do you want to create the service')
    self.AssertErrContains(SERVICE_NAME)
    self.AssertErrContains(self.PROJECT_NAME)

  def testServicesDeployValidateOnlyNewServiceInteractiveNo(self):
    self.StartObjectPatch(console_io, 'CanPrompt', return_value=True)

    # The service does not exist yet, so it is created first.
    self.mocked_client.services.Get.Expect(
        request=self.services_messages.ServicemanagementServicesGetRequest(
            serviceName=SERVICE_NAME,
        ),
        exception=http_error.MakeHttpError(code=403)
    )
    self.WriteInput('no')

    self.Run('{0} {1} --validate-only'.format(
        self.base_cmd, self._swagger_file_path))

    # Make sure the uploaded status message does not print out, since this is
    # a validate-only run.
    self.AssertErrNotContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    # Assert that we did not print out the Endpoints Management UI link,
    # since this is a validate-only run
    self.AssertErrNotContains('To manage your API, go to:')

    self.AssertErrContains('must exist')
    self.AssertErrContains('Do you want to create the service')
    self.AssertErrContains(SERVICE_NAME)
    self.AssertErrContains(self.PROJECT_NAME)

  def testServicesDeployYamlSwaggerConfigValidateOnly(self):
    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # Mock the SubmitSourceConfig API call.
    self.mocked_client.services_configs.Submit.Expect(
        request=(SUBMIT_REQUEST(
            serviceName=SERVICE_NAME,
            submitConfigSourceRequest=(
                self.services_messages.SubmitConfigSourceRequest(
                    configSource=self.services_messages.ConfigSource(
                        files=[self.services_messages.ConfigFile(
                            fileContents=six.binary_type(TEST_SWAGGER_YAML),
                            filePath=os.path.basename(
                                self._swagger_yaml_file_path),
                            fileType=FILE_TYPES.OPEN_API_YAML)]),
                    validateOnly=True)))),
        response=self.operation
    )
    submit_response = {
        'serviceConfig': {'id': SERVICE_VERSION, 'name': SERVICE_NAME},
        'diagnostics': [
            {
                'kind': 'WARNING',
                'location': 'foo',
                'message': 'diagnostic warning message bar'
            }
        ]
    }
    self.MockOperationWait(self.operation_name, submit_response)

    # Wait for Push Advisor report (no warnings)
    self._WaitForBlankPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION)

    self.Run('{0} {1} --validate-only'.format(
        self.base_cmd, self._swagger_yaml_file_path))

    # Assert that we did not print out the actual uploaded success message,
    # since this is a validate-only run
    self.AssertErrNotContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    # Assert that we did not print out the Endpoints Management UI link,
    # since this is a validate-only run
    self.AssertErrNotContains('To manage your API, go to:')

    self.AssertErrContains('WARNING: foo: diagnostic warning message bar')

  def testServicesDeployRaisesExceptionOnDiagnosticErrors(self):
    # Test with one diagnostic ERROR as well as several
    for num_errors in range(1, 3):
      # The service already exists, so it is not created again.
      self._MockServiceGetCall(SERVICE_NAME)

      # Mock the SubmitSourceConfig API call.
      self.mocked_client.services_configs.Submit.Expect(
          request=(SUBMIT_REQUEST(
              serviceName=SERVICE_NAME,
              submitConfigSourceRequest=(
                  self.services_messages.SubmitConfigSourceRequest(
                      configSource=self.services_messages.ConfigSource(
                          files=[self.services_messages.ConfigFile(
                              fileContents=six.binary_type(TEST_SWAGGER_YAML),
                              filePath=os.path.basename(
                                  self._swagger_yaml_file_path),
                              fileType=FILE_TYPES.OPEN_API_YAML)]),
                      validateOnly=False)))),
          response=self.operation
      )
      submit_response = {
          'serviceConfig': {'id': SERVICE_VERSION, 'name': SERVICE_NAME},
          'diagnostics': [
              {
                  'kind': 'WARNING',
                  'location': 'foo',
                  'message': 'diagnostic warning message bar'
              }
          ] + [
              {
                  'kind': 'ERROR',
                  'location': 'foo{n}'.format(n=n),
                  'message': 'diagnostic error message bar{n}'.format(n=n)
              }
              for n in range(2, 2 + num_errors)
          ]
      }
      self.MockOperationWait(self.operation_name, submit_response)

      with self.AssertRaisesExceptionMatches(
          exceptions.ServiceDeployErrorException,
          '{n} diagnostic error{s} found in service configuration deployment. '
          'See log for details.'.format(n=num_errors,
                                        s='s' if num_errors > 1 else '')):
        self.Run('{0} {1}'.format(
            self.base_cmd, self._swagger_yaml_file_path))
      self.AssertErrContains('WARNING: foo: diagnostic warning message bar')
      for n in range(2, 2 + num_errors):
        self.AssertErrContains(
            'ERROR: foo{n}: diagnostic error message bar{n}'.format(n=n))

  def _expectEnableService(self, service, project, operation, exception=None):
    if exception:
      self.su_mocked_client.services.Enable.Expect(
          request=self.su_services_messages.ServiceusageServicesEnableRequest(
              name='projects/%s/services/%s' % (project, service),),
          exception=exception,
      )
    else:
      self.su_mocked_client.services.Enable.Expect(
          request=self.su_services_messages.ServiceusageServicesEnableRequest(
              name='projects/%s/services/%s' % (project, service),),
          response=self.su_services_messages.Operation(
              name=operation,
              done=False,
          ))
      self.su_mocked_client.operations.Get.Expect(
          request=self.su_services_messages.ServiceusageOperationsGetRequest(
              name=operation),
          response=self.su_services_messages.Operation(
              name=operation,
              done=True,
          ))


class EndpointsBetaDeployTest(EndpointsDeployTest):
  """Unit tests for endpoints services beta deploy command."""

  def SetUp(self):
    self.alpha = False
    self.beta = True
    self.base_cmd = 'beta endpoints services deploy'

  def _deployServiceConfigWithAdvisorResult(self, push_advisor_result,
                                            force=False):
    config_to_deploy = self.services_messages.Service(
        name=SERVICE_NAME,
        producerProjectId=self.PROJECT_NAME,
        title=TITLE)

    # The service already exists, so it is not created again.
    self._MockServiceGetCall(SERVICE_NAME)

    # The service configuration resource is created.
    self.mocked_client.services_configs.Create.Expect(
        request=CONFIG_CREATE_REQUEST(
            serviceName=SERVICE_NAME,
            service=config_to_deploy,
        ),
        response=self.services_messages.Service(
            name=SERVICE_NAME,
            producerProjectId=self.PROJECT_NAME,
            title=TITLE,
            id=SERVICE_VERSION,  # this id is set by the server
        ),
    )

    # Wait for Push Advisor report (with a warning)
    self._WaitForPushAdvisorReport(SERVICE_NAME, SERVICE_VERSION,
                                   result=push_advisor_result)

    # If forcing the deployment, make sure the rest of the commands complete
    if force:
      # Mock the Service Rollout creation.
      self._MockServiceRolloutCreate(SERVICE_NAME, SERVICE_VERSION)
      self.MockOperationWait(self.operation_name)

      # A Get call is required to generate the management url
      self._MockServiceGetCall(SERVICE_NAME, self.PROJECT_NAME)

    cmd = '{0} {1}'.format(self.base_cmd, self._config_file_path)
    if force:
      cmd += ' --force'
    self.Run(cmd)

  def testServicesDeployServiceConfigWithAdvisorWarnings(self):
    push_advisor_result = self.CreateGenerateConfigReportResponse(
        service_name=SERVICE_NAME)
    self._deployServiceConfigWithAdvisorResult(push_advisor_result)

    # Verify that the warning log messages appear
    self.AssertLogContains('oldValue #1')
    self.AssertLogContains('newValue #1')
    self.AssertLogContains('Advice #1')
    self.AssertLogContains('Advice found for changes in the new service config')

  def testServicesDeployServiceConfigWithAdvisorWarningsForced(self):
    push_advisor_result = self.CreateGenerateConfigReportResponse(
        service_name=SERVICE_NAME)
    self._deployServiceConfigWithAdvisorResult(push_advisor_result,
                                               force=True)

    # Verify that the warning log messages appear
    self.AssertLogContains('oldValue #1')
    self.AssertLogContains('newValue #1')
    self.AssertLogContains('Advice #1')
    self.AssertLogContains('Advice found for changes in the new service '
                           'config, but proceeding anyway because --force is '
                           'set...')

    self.AssertErrContains(
        ('Service Configuration [{0}] uploaded for service [{1}]').format(
            SERVICE_VERSION, SERVICE_NAME))

    self._AssertManagementUrlDisplayed()

  def testServicesDeployServiceConfigWithManyAdvisorWarnings(self):
    num_changes = 10
    push_advisor_result = self.CreateGenerateConfigReportResponse(
        service_name=SERVICE_NAME, num_changes=num_changes)
    self._deployServiceConfigWithAdvisorResult(push_advisor_result)

    # Verify that the warning log messages appear
    for n in range(3):
      self.AssertLogContains('oldValue #{0}'.format(n+1))
      self.AssertLogContains('newValue #{0}'.format(n+1))
    self.AssertLogContains('Advice #1')
    self.AssertLogContains('{0} total changes with advice found, check config '
                           'report file for full list.'.format(num_changes))
    self.AssertLogContains('Advice found for changes in the new service config')


class EndpointsAlphaDeployTest(EndpointsBetaDeployTest):
  """Unit tests for endpoints services alpha deploy command."""

  def SetUp(self):
    self.alpha = True
    self.beta = True
    self.base_cmd = 'alpha endpoints services deploy'


if __name__ == '__main__':
  test_case.main()
