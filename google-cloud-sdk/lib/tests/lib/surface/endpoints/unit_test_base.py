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

"""Base for Endpoints V1 unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

from apitools.base.py import encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

import mock as third_party_mock
from six.moves import range


class EV1UnitTestBase(sdk_test_base.WithFakeAuth,
                      sdk_test_base.WithLogCapture,
                      cli_test_base.CliTestBase):
  """Base class for Endpoints unit tests."""

  PROJECT_NAME = None
  DEFAULT_SERVICE_NAME = 'service-name.googleapis.com'

  def PreSetUp(self):
    EV1UnitTestBase.PROJECT_NAME = self.Project()
    self.services_messages = core_apis.GetMessagesModule(
        'servicemanagement', 'v1')

  def SetUp(self):
    properties.VALUES.core.project.Set(self.PROJECT_NAME)

    self.services_client = core_apis.GetClientInstance(
        'servicemanagement', 'v1', no_http=True)
    # Mock out the service management API
    self.mocked_client = mock.Client(
        core_apis.GetClientClass('servicemanagement', 'v1'),
        real_client=core_apis.GetClientInstance(
            'servicemanagement', 'v1', no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

    # Mock out time.sleep calls in operation polling
    self.time_mock = self.StartObjectPatch(time, 'time')
    self.sleep_mock = self.StartObjectPatch(time, 'sleep')

  def CreateServiceConfig(self, name=None, config_id=None):
    name = name if name else self.DEFAULT_SERVICE_NAME
    config_id = config_id if config_id else '2016-01-01R1'
    return self.services_messages.Service(
        name=name,
        id=config_id)

  def CreateService(self, identifier=None, service_config=None):
    """Helper function to create a simple service.

    Args:
      identifier: Optional string to act as service title and prepend to name.
      service_config: Optional service config to attach to returned service.

    Returns:
      Service with name and serviceConfig set.
    """
    name = ('%s.googleapis.com' %
            identifier if identifier else self.DEFAULT_SERVICE_NAME)
    if not service_config:
      service_config = self.CreateServiceConfig()
    return self.services_messages.ManagedService(
        serviceName=name,
        serviceConfig=service_config)

  def MockOperationWait(self, op_name, response_dict=None,
                        final_error_code=None):
    response = None
    if response_dict:
      response = encoding.DictToMessage(
          response_dict, self.services_messages.Operation.ResponseValue)

    # First, expect a call where the op is not yet done
    self.mocked_client.operations.Get.Expect(
        request=self.services_messages.ServicemanagementOperationsGetRequest(
            operationsId=op_name
        ),
        response=self.services_messages.Operation(
            name=op_name,
            done=False,
            response=response,
        )
    )

    # Then, expect a call where the op has now completed
    self.mocked_client.operations.Get.Expect(
        request=self.services_messages.ServicemanagementOperationsGetRequest(
            operationsId=op_name
        ),
        response=self.services_messages.Operation(
            name=op_name,
            done=True,
            error=(self.services_messages.Status(code=final_error_code)
                   if final_error_code else None),
            response=response,
        )
    )

  def CompareToDefaultChangeReport(self):
    self.AssertOutputMatches(
        'configChanges:\n'
        '- changeType: MODIFIED\n'
        '  element: auditing\n'
        '  newValue: newValue\n'
        '  oldValue: oldValue\n')

  def CreateGenerateConfigReportResponse(self, service_name=None,
                                         num_changes=1, num_advices=1):
    advices = [
        self.services_messages.Advice(description='Advice #{0}'.format(n+1))
        for n in range(num_advices)]
    config_changes = [
        self.services_messages.ConfigChange(
            advices=advices,
            element='auditing',
            oldValue='oldValue #{0}'.format(n+1),
            newValue='newValue #{0}'.format(n+1),
            changeType=(self.services_messages.ConfigChange.
                        ChangeTypeValueValuesEnum.MODIFIED))
        for n in range(num_changes)]
    change_report = self.services_messages.ChangeReport(
        configChanges=config_changes)

    return self.services_messages.GenerateConfigReportResponse(
        changeReports=[change_report],
        diagnostics=[],
        id='MyConfigReport',
        serviceName=service_name or self.DEFAULT_SERVICE_NAME)

  def ExpectConfigReportRequest(self, reporter, mocked_response=None):
    success = self.services_messages.Rollout.StatusValueValuesEnum.SUCCESS
    percentages_value = (self.services_messages.TrafficPercentStrategy
                         .PercentagesValue)
    prop = percentages_value.AdditionalProperty

    active_config_ids = ['service_config_1', 'service_config_2']

    percentages = [
        prop(key=i, value=100. / len(active_config_ids))
        for i in active_config_ids
    ]

    req = self.services_messages.ServicemanagementServicesRolloutsListRequest(
        serviceName=self.DEFAULT_SERVICE_NAME,
        pageSize=1)

    mocked_rollout = self.services_messages.Rollout(
        rolloutId='rollout1',
        status=success,
        serviceName=self.DEFAULT_SERVICE_NAME,
        trafficPercentStrategy=self.services_messages.TrafficPercentStrategy(
            percentages=percentages_value(additionalProperties=percentages)
        ),
    )

    self.mocked_client.services_rollouts.List.Expect(
        request=req,
        response=self.services_messages.ListServiceRolloutsResponse(
            rollouts=[mocked_rollout])
    )

    # Patch GetActiveServiceConfigIdsForService to return the mocked
    # active_config_ids. Otherwise, the client will attempt to call the
    # backend to find the active config IDs, and the ordering of the calls
    # will differ from what is expected, and UnexpectedRequestExceptions
    # will be raised.
    with third_party_mock.patch(
        'googlecloudsdk.api_lib.endpoints.services_util'
        '.GetActiveServiceConfigIdsForService',
        return_value=active_config_ids):
      self.mocked_client.services.GenerateConfigReport.Expect(
          request=reporter.ConstructRequestMessage(),
          response=(mocked_response or
                    self.CreateGenerateConfigReportResponse(
                        service_name=reporter.service)))
