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

NETWORK_URL_FORMAT = 'projects/%s/global/networks/%s'


class SNUnitTestBase(sdk_test_base.WithFakeAuth, sdk_test_base.WithLogCapture,
                     cli_test_base.CliTestBase):
  """Base class for service networking unit tests."""

  PROJECT_NAME = 'fake-project'
  PROJECT_NUMBER = 12481632

  def PreSetUp(self):
    self.services_messages = core_apis.GetMessagesModule(
        'servicenetworking', 'v1')

  def SetUp(self):
    properties.VALUES.core.project.Set(self.PROJECT_NAME)

    # Mock out the service networking API
    self.mocked_client = mock.Client(
        core_apis.GetClientClass('servicenetworking', 'v1'),
        real_client=core_apis.GetClientInstance(
            'servicenetworking', 'v1', no_http=True))
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

  def ExpectUpdateConnection(self,
                             network,
                             ranges,
                             operation,
                             force,
                             error=None):
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=operation, done=False)
    self.mocked_client.services_connections.Patch.Expect(
        self.services_messages.ServicenetworkingServicesConnectionsPatchRequest(
            name='services/%s/connections/-' % self.service,
            connection=self.services_messages.Connection(
                network=NETWORK_URL_FORMAT % (self.PROJECT_NUMBER, network),
                reservedPeeringRanges=ranges),
            force=force),
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

  def ExpectEnableVpcServiceControls(self, network, operation, error=None):
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=operation, done=False)
    self.mocked_client.services.EnableVpcServiceControls.Expect(
        self.services_messages
        .ServicenetworkingServicesEnableVpcServiceControlsRequest(
            enableVpcServiceControlsRequest=self.services_messages.
            EnableVpcServiceControlsRequest(consumerNetwork=NETWORK_URL_FORMAT %
                                            (self.PROJECT_NUMBER, network)),
            parent='services/%s' % self.service),
        op,
        exception=error)

  def ExpectDisableVpcServiceControls(self, network, operation, error=None):
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=operation, done=False)
    self.mocked_client.services.DisableVpcServiceControls.Expect(
        self.services_messages
        .ServicenetworkingServicesDisableVpcServiceControlsRequest(
            disableVpcServiceControlsRequest=self.services_messages
            .DisableVpcServiceControlsRequest(
                consumerNetwork=NETWORK_URL_FORMAT %
                (self.PROJECT_NUMBER, network)),
            parent='services/%s' % self.service),
        op,
        exception=error)


class SUUnitTestBase(sdk_test_base.WithFakeAuth, sdk_test_base.WithLogCapture,
                     cli_test_base.CliTestBase):
  """Base class for service usage unit tests."""

  PROJECT_NAME = 'fake-project'
  DEFAULT_SERVICE_NAME = 'service-name.googleapis.com'
  DEFAULT_SERVICE_NAME_2 = 'service-name-1.googleapis.com'

  def PreSetUp(self):
    self.services_messages = core_apis.GetMessagesModule('serviceusage', 'v1')
    self.services_v1beta1_messages = core_apis.GetMessagesModule(
        'serviceusage', 'v1beta1')
    self.services_v1alpha_messages = core_apis.GetMessagesModule(
        'serviceusage', 'v1alpha')

  def SetUp(self):
    properties.VALUES.core.project.Set(self.PROJECT_NAME)

    # Mock out the service usage API
    self.mocked_client = mock.Client(
        core_apis.GetClientClass('serviceusage', 'v1'),
        real_client=core_apis.GetClientInstance(
            'serviceusage', 'v1', no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.mocked_v1beta1_client = mock.Client(
        core_apis.GetClientClass('serviceusage', 'v1beta1'),
        real_client=core_apis.GetClientInstance(
            'serviceusage', 'v1beta1', no_http=True))
    self.mocked_v1beta1_client.Mock()
    self.addCleanup(self.mocked_v1beta1_client.Unmock)
    self.mocked_v1alpha_client = mock.Client(
        core_apis.GetClientClass('serviceusage', 'v1alpha'),
        real_client=core_apis.GetClientInstance(
            'serviceusage', 'v1alpha', no_http=True))
    self.mocked_v1alpha_client.Mock()
    self.addCleanup(self.mocked_v1alpha_client.Unmock)

  def ExpectEnableApiCall(self, operation, error=None, done=False):
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=operation, done=done)
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

  def ExpectGetService(self, service, error=None):
    self.mocked_client.services.Get.Expect(
        self.services_messages.ServiceusageServicesGetRequest(
            name='projects/%s/services/%s' %
            (self.PROJECT_NAME, self.DEFAULT_SERVICE_NAME),),
        response=service,
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

  def _NewServiceConfig(self, project, service, enabled=None):
    state_type = self.services_messages.GoogleApiServiceusageV1Service.StateValueValuesEnum
    return self.services_messages.GoogleApiServiceusageV1Service(
        name='projects/%s/services/%s' % (project, service),
        config=self.services_messages.GoogleApiServiceusageV1ServiceConfig(
            name=service,),
        state=state_type.ENABLED if enabled else state_type.DISABLED,
    )

  def ExpectGenerateServiceIdentityCall(self, email, unique_id, error=None):
    if error:
      op = None
    else:
      resp = encoding.DictToMessage({
          'email': email,
          'unique_id': unique_id
      }, self.services_v1beta1_messages.Operation.ResponseValue)
      op = self.services_v1beta1_messages.Operation(
          name='opname', done=True, response=resp)
    self.mocked_v1beta1_client.services.GenerateServiceIdentity.Expect(
        self.services_v1beta1_messages
        .ServiceusageServicesGenerateServiceIdentityRequest(
            parent='projects/%s/services/%s' %
            (self.PROJECT_NAME, self.DEFAULT_SERVICE_NAME),),
        op,
        exception=error)


class SCMUnitTestBase(sdk_test_base.WithFakeAuth, sdk_test_base.WithLogCapture,
                      cli_test_base.CliTestBase):
  """Base class for service consumer management unit tests."""

  DEFAULT_CONSUMER = 'projects/helloworld'
  DEFAULT_SERVICE = 'example.googleapis.com'
  _LIMIT_OVERRIDE_RESOURCE = '%s/producerOverrides/%s'

  def SetUp(self):
    self.services_messages = core_apis.GetMessagesModule(
        'serviceconsumermanagement', 'v1beta1')
    self.mocked_client = mock.Client(
        core_apis.GetClientClass('serviceconsumermanagement', 'v1beta1'),
        real_client=core_apis.GetClientInstance('serviceconsumermanagement',
                                                'v1beta1'))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    # setup common test resources
    self.mutate_metric = 'example.googleapis.com/mutate_requests'
    self.default_metric = 'example.googleapis.com/default_requests'
    self.mutate_metric_resource_name = 'services/example.googleapis.com/projects/123/quotaMetrics/example.googleapis.com%2Fmutate_requests'
    self.default_metric_resource_name = 'services/example.googleapis.com/projects/123/quotaMetrics/example.googleapis.com%2Fdefault_requests'
    self.mutate_limit_name = 'services/example.googleapis.com/projects/123/quotaMetrics/example.googleapis.com%2Fmutate_requests/limits/%2Fmin%2Fproject'
    self.default_limit_name = 'services/example.googleapis.com/projects/123/quotaMetrics/example.googleapis.com%2Fdefault_requests/limits/%2Fmin%2Fproject'
    self.unit = '1/min/{project}'
    self.mutate_quota_metric = self.services_messages.V1Beta1ConsumerQuotaMetric(
        name=self.mutate_metric_resource_name,
        displayName='Mutate requests',
        metric=self.mutate_metric,
        consumerQuotaLimits=[
            self.services_messages.V1Beta1ConsumerQuotaLimit(
                name=self.mutate_limit_name,
                metric=self.mutate_metric,
                unit=self.unit,
                quotaBuckets=[
                    self.services_messages.V1Beta1QuotaBucket(
                        effectiveLimit=120,
                        defaultLimit=120,
                    ),
                ],
            ),
        ],
    )
    self.default_quota_metric = self.services_messages.V1Beta1ConsumerQuotaMetric(
        name=self.default_metric_resource_name,
        displayName='Default requests',
        metric=self.default_metric,
        consumerQuotaLimits=[
            self.services_messages.V1Beta1ConsumerQuotaLimit(
                name=self.default_limit_name,
                metric=self.default_metric,
                unit=self.unit,
                quotaBuckets=[
                    self.services_messages.V1Beta1QuotaBucket(
                        effectiveLimit=240,
                        defaultLimit=120,
                    ),
                ],
            ),
        ],
    )

  def ExpectListQuotaMetricsCall(self, metrics):
    self.mocked_client.services_consumerQuotaMetrics.List.Expect(
        self.services_messages
        .ServiceconsumermanagementServicesConsumerQuotaMetricsListRequest(
            parent='services/%s/%s' %
            (self.DEFAULT_SERVICE, self.DEFAULT_CONSUMER)),
        self.services_messages.V1Beta1ListConsumerQuotaMetricsResponse(
            metrics=metrics),
    )

  def ExpectCreateQuotaOverrideCall(self,
                                    limit_resource_name,
                                    metric,
                                    unit,
                                    value,
                                    operation,
                                    dimensions=None,
                                    force=False,
                                    error=None):
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=operation, done=False)
    dt = self.services_messages.V1Beta1QuotaOverride.DimensionsValue
    dimensions_message = None
    if dimensions is not None:
      dimensions_message = dt(
          additionalProperties=[
              dt.AdditionalProperty(key=k, value=v) for (k, v) in dimensions
          ],)
    request = self.services_messages.ServiceconsumermanagementServicesConsumerQuotaMetricsLimitsProducerOverridesCreateRequest(
        parent=limit_resource_name,
        v1Beta1QuotaOverride=self.services_messages.V1Beta1QuotaOverride(
            name='%s/producerOverrides/kawaii' % limit_resource_name,
            metric=metric,
            unit=unit,
            dimensions=dimensions_message,
            overrideValue=value,
        ),
        force=force,
    )
    self.mocked_client.services_consumerQuotaMetrics_limits_producerOverrides.Create.Expect(
        request, op, exception=error)

  def ExpectUpdateQuotaOverrideCall(self,
                                    limit_resource_name,
                                    metric,
                                    unit,
                                    override_id,
                                    value,
                                    operation,
                                    dimensions=None,
                                    force=False,
                                    error=None):
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=operation, done=False)
    dt = self.services_messages.V1Beta1QuotaOverride.DimensionsValue
    dimensions_message = None
    if dimensions is not None:
      dimensions_message = dt(
          additionalProperties=[
              dt.AdditionalProperty(key=k, value=v) for (k, v) in dimensions
          ],)
    name = self._LIMIT_OVERRIDE_RESOURCE % (limit_resource_name, override_id)
    request = self.services_messages.ServiceconsumermanagementServicesConsumerQuotaMetricsLimitsProducerOverridesPatchRequest(
        name=name,
        v1Beta1QuotaOverride=self.services_messages.V1Beta1QuotaOverride(
            name=name,
            metric=metric,
            unit=unit,
            dimensions=dimensions_message,
            overrideValue=value,
        ),
        force=force,
    )
    self.mocked_client.services_consumerQuotaMetrics_limits_producerOverrides.Patch.Expect(
        request, op, exception=error)

  def ExpectDeleteQuotaOverrideCall(self,
                                    limit_resource_name,
                                    metric,
                                    unit,
                                    override_id,
                                    operation,
                                    force=False,
                                    error=None):
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=operation, done=False)
    name = self._LIMIT_OVERRIDE_RESOURCE % (limit_resource_name, override_id)
    request = self.services_messages.ServiceconsumermanagementServicesConsumerQuotaMetricsLimitsProducerOverridesDeleteRequest(
        name=name,
        force=force,
    )
    self.mocked_client.services_consumerQuotaMetrics_limits_producerOverrides.Delete.Expect(
        request, op, exception=error)

  def ExpectOperation(self, name, poll_count=2, error=None):
    for _ in range(poll_count):
      op = self.services_messages.Operation(name=name, done=False)
      self.mocked_client.operations.Get.Expect(
          request=self.services_messages
          .ServiceconsumermanagementOperationsGetRequest(name=name),
          response=op)
    if error:
      op = None
    else:
      op = self.services_messages.Operation(name=name, done=True)
    self.mocked_client.operations.Get.Expect(
        self.services_messages.ServiceconsumermanagementOperationsGetRequest(
            name=name),
        op,
        exception=error)


class ApiKeysUnitTestBase(sdk_test_base.WithFakeAuth,
                          sdk_test_base.WithLogCapture,
                          cli_test_base.CliTestBase):
  """Base class for api keys unit tests."""

  DEFAULT_PROJECT = 'helloworld'
  _PROJECT_RESOURCE = 'projects/%s'

  def SetUp(self):
    self.services_messages = core_apis.GetMessagesModule('apikeys', 'v2alpha1')
    self.mocked_client = mock.Client(
        core_apis.GetClientClass('apikeys', 'v2alpha1'),
        real_client=core_apis.GetClientInstance('apikeys', 'v2alpha1'))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

  def ExpectListKeysCall(self, keys):
    self.mocked_client.projects_keys.List.Expect(
        self.services_messages.ApikeysProjectsKeysListRequest(
            parent=self._PROJECT_RESOURCE % self.DEFAULT_PROJECT),
        self.services_messages.V2alpha1ListKeysResponse(keys=keys))
