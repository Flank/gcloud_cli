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

"""Base for Services V1 unit tests."""

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
from six.moves import range


class SV1UnitTestBase(sdk_test_base.WithFakeAuth,
                      sdk_test_base.WithLogCapture,
                      cli_test_base.CliTestBase):
  """Base class for Services unit tests."""

  PROJECT_NAME = None
  DEFAULT_SERVICE_NAME = 'service-name.googleapis.com'

  def PreSetUp(self):
    SV1UnitTestBase.PROJECT_NAME = self.Project()
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
        id=config_id
    )

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
        serviceConfig=service_config
    )

  def MockOperationWait(self, op_name, response_dict=None,
                        final_error_code=None):
    response = None
    if response_dict:
      response = encoding.DictToMessage(
          response_dict,
          self.services_messages.Operation.ResponseValue)

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


NETWORK_URL_FORMAT = 'projects/%s/global/networks/%s'


class SNUnitTestBase(sdk_test_base.WithFakeAuth, sdk_test_base.WithLogCapture,
                     cli_test_base.CliTestBase):
  """Base class for service networking unit tests."""

  PROJECT_NAME = 'fake-project'
  PROJECT_NUMBER = 12481632

  def PreSetUp(self):
    self.services_messages = core_apis.GetMessagesModule(
        'servicenetworking', 'v1beta')

  def SetUp(self):
    properties.VALUES.core.project.Set(self.PROJECT_NAME)

    # Mock out the service networking API
    self.mocked_client = mock.Client(
        core_apis.GetClientClass('servicenetworking', 'v1beta'),
        real_client=core_apis.GetClientInstance(
            'servicenetworking', 'v1beta', no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.service = 'service-name.googleapis.com'

  def ExpectCreateConnection(self, network, ranges, operation, error=None):
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=operation, done=False)
    self.mocked_client.services_connections.Create.Expect(
        self.services_messages.
        ServicenetworkingServicesConnectionsCreateRequest(
            parent='services/%s' % self.service,
            connection=self.services_messages.Connection(
                network=NETWORK_URL_FORMAT % (self.PROJECT_NUMBER, network),
                reservedPeeringRanges=ranges)),
        op,
        exception=error)

  def ExpectOperation(self, name, poll_count=2, error=None):
    for _ in range(poll_count):
      op = self.services_messages.Operation(name=name, done=False)
      self.mocked_client.operations.Get.Expect(
          request=self.services_messages.ServicenetworkingOperationsGetRequest(
              name=name),
          response=op)
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=name, done=True)
    self.mocked_client.operations.Get.Expect(
        self.services_messages.ServicenetworkingOperationsGetRequest(name=name),
        op,
        exception=error)

  def ExpectListConnections(self, network, conns, error=None):
    if error:
      resp = None
    else:
      resp = self.services_messages.ListConnectionsResponse(connections=conns)
    self.mocked_client.services_connections.List.Expect(
        self.services_messages.ServicenetworkingServicesConnectionsListRequest(
            parent='services/%s' % self.service,
            network=NETWORK_URL_FORMAT % (self.PROJECT_NUMBER, network)),
        resp,
        exception=error)


class SUUnitTestBase(sdk_test_base.WithFakeAuth, sdk_test_base.WithLogCapture,
                     cli_test_base.CliTestBase):
  """Base class for service usage unit tests."""

  PROJECT_NAME = 'fake-project'
  DEFAULT_SERVICE_NAME = 'service-name.googleapis.com'
  DEFAULT_SERVICE_NAME_2 = 'service-name-1.googleapis.com'

  def PreSetUp(self):
    self.services_messages = core_apis.GetMessagesModule('serviceusage', 'v1')

  def SetUp(self):
    properties.VALUES.core.project.Set(self.PROJECT_NAME)

    # Mock out the service networking API
    self.mocked_client = mock.Client(
        core_apis.GetClientClass('serviceusage', 'v1'),
        real_client=core_apis.GetClientInstance(
            'serviceusage', 'v1', no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

  def ExpectEnableApiCall(self, operation, error=None):
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=operation, done=False)
    self.mocked_client.services.Enable.Expect(
        self.services_messages.ServiceusageServicesEnableRequest(
            name='projects/%s/services/%s' % (self.PROJECT_NAME,
                                              self.DEFAULT_SERVICE_NAME),),
        op,
        exception=error)

  def ExpectBatchEnableApiCall(self, operation, error=None):
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=operation, done=False)
    self.mocked_client.services.BatchEnable.Expect(
        self.services_messages.ServiceusageServicesBatchEnableRequest(
            batchEnableServicesRequest=self.services_messages.
            BatchEnableServicesRequest(serviceIds=[
                self.DEFAULT_SERVICE_NAME, self.DEFAULT_SERVICE_NAME_2
            ]),
            parent='projects/%s' % self.PROJECT_NAME),
        op,
        exception=error)

  def ExpectDisableApiCall(self, operation, force=False, error=None):
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=operation, done=False)
    self.mocked_client.services.Disable.Expect(
        self.services_messages.ServiceusageServicesDisableRequest(
            name='projects/%s/services/%s' % (self.PROJECT_NAME,
                                              self.DEFAULT_SERVICE_NAME),
            disableServiceRequest=self.services_messages.DisableServiceRequest(
                disableDependentServices=force,),
        ),
        op,
        exception=error)

  def ExpectListServicesCall(self, error=None):
    if error:
      resp = None
    else:
      resp = self.services_messages.ListServicesResponse(services=[
          self._NewServiceConfig(self.PROJECT_NAME, self.DEFAULT_SERVICE_NAME),
          self._NewServiceConfig(self.PROJECT_NAME, self.DEFAULT_SERVICE_NAME_2)
      ])
    self.mocked_client.services.List.Expect(
        self.services_messages.ServiceusageServicesListRequest(
            parent='projects/%s' % self.PROJECT_NAME),
        resp,
        exception=error)

  def ExpectOperation(self, name, poll_count=2, error=None):
    for _ in range(poll_count):
      op = self.services_messages.Operation(name=name, done=False)
      self.mocked_client.operations.Get.Expect(
          request=self.services_messages.ServiceusageOperationsGetRequest(
              name=name),
          response=op)
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=name, done=True)
    self.mocked_client.operations.Get.Expect(
        self.services_messages.ServiceusageOperationsGetRequest(name=name),
        op,
        exception=error)

  def _NewServiceConfig(self, project, service):
    return self.services_messages.GoogleApiServiceusageV1Service(
        name='projects/%s/services/%s' % (project, service),
        config=self.services_messages.GoogleApiServiceusageV1ServiceConfig(
            name=service,),
    )
