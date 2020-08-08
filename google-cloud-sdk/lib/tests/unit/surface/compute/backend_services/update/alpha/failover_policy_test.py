# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""Tests for the backend services update alpha command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from tests.lib import test_case
from tests.lib.surface.compute.backend_services.update import test_base


class WithFailoverPolicyApiTest(test_base.AlphaUpdateTestBase):

  def SetUp(self):
    messages = self.messages

    self.orig_backend_service = messages.BackendService(
        backends=[],
        description='my backend service',
        healthChecks=[
            self.resources.Create(
                'compute.healthChecks',
                healthCheck='orig-health-check',
                project='my-project').SelfLink(),
        ],
        loadBalancingScheme=(messages.BackendService
                             .LoadBalancingSchemeValueValuesEnum.INTERNAL),
        name='backend-service-3',
        portName='http',
        protocol=messages.BackendService.ProtocolValueValuesEnum.TCP,
        selfLink=self.resources.Create(
            'compute.backendServices',
            backendService='backend-service-3',
            project='my-project').SelfLink(),
        timeoutSec=30)

  def CheckResults(self, expected_message=None):
    messages = self.messages

    self.CheckRequests(
        [(self.compute.regionBackendServices, 'Get',
          messages.ComputeRegionBackendServicesGetRequest(
              backendService='backend-service-3',
              project='my-project',
              region='us-central1'))],
        [(self.compute.regionBackendServices, 'Patch',
          messages.ComputeRegionBackendServicesPatchRequest(
              backendService='backend-service-3',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[
                      self.resources.Create(
                          'compute.healthChecks',
                          healthCheck='orig-health-check',
                          project='my-project').SelfLink(),
                  ],
                  loadBalancingScheme=(
                      messages.BackendService.LoadBalancingSchemeValueValuesEnum
                      .INTERNAL),
                  failoverPolicy=expected_message,
                  name='backend-service-3',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.TCP),
                  selfLink=self.resources.Create(
                      'compute.backendServices',
                      backendService='backend-service-3',
                      project='my-project').SelfLink(),
                  timeoutSec=30),
              project='my-project',
              region='us-central1'))],
    )

  def testEnableFailoverOptions(self):
    self.make_requests.side_effect = iter([
        [self.orig_backend_service],
        [],
    ])

    self.RunUpdate(
        'backend-service-3 --region us-central1'
        ' --no-connection-drain-on-failover'
        ' --drop-traffic-if-unhealthy'
        ' --failover-ratio 0.5',
        use_global=False)
    self.CheckResults(
        self.messages.BackendServiceFailoverPolicy(
            disableConnectionDrainOnFailover=True,
            dropTrafficIfUnhealthy=True,
            failoverRatio=0.5))

  def testDisableFailoverOptions(self):
    self.make_requests.side_effect = iter([
        [self.orig_backend_service],
        [],
    ])

    self.RunUpdate(
        'backend-service-3 --region us-central1'
        ' --connection-drain-on-failover'
        ' --no-drop-traffic-if-unhealthy'
        ' --failover-ratio 0.5',
        use_global=False)
    self.CheckResults(
        self.messages.BackendServiceFailoverPolicy(
            disableConnectionDrainOnFailover=False,
            dropTrafficIfUnhealthy=False,
            failoverRatio=0.5))

  def testEnableFailoverOptionsWithExistingFailoverOptions(self):
    backend_service_with_failover_options = copy.deepcopy(
        self.orig_backend_service)
    backend_service_with_failover_options.failoverPolicy = (
        self.messages.BackendServiceFailoverPolicy(failoverRatio=0.5))
    self.make_requests.side_effect = iter([
        [backend_service_with_failover_options],
        [],
    ])

    self.RunUpdate(
        'backend-service-3 --region us-central1'
        ' --no-connection-drain-on-failover',
        use_global=False)
    self.CheckResults(
        self.messages.BackendServiceFailoverPolicy(
            disableConnectionDrainOnFailover=True, failoverRatio=0.5))

  def testCannotSpecifyFailoverPolicyForGlobalBackendService(self):
    self.make_requests.side_effect = iter([
        [self._http_backend_services_with_health_check[0]],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        '^Invalid value for \\[--global\\]: cannot specify failover policies'
        ' for global backend services.'):
      self.RunUpdate('backend-service-3'
                     ' --protocol TCP'
                     ' --connection-drain-on-failover')

  def testInvalidLoadBalancingSchemeWithInternalFailoverOptions(self):
    external_tcp_backend_service = copy.deepcopy(
        self._tcp_backend_services_with_health_check[0])
    external_tcp_backend_service.loadBalancingScheme = (
        self.messages.BackendService.LoadBalancingSchemeValueValuesEnum.EXTERNAL
    )
    self.make_requests.side_effect = iter([
        [external_tcp_backend_service],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        '^Invalid value for \\[--load-balancing-scheme\\]: can only specify '
        '--connection-drain-on-failover or --drop-traffic-if-unhealthy'
        ' if the load balancing scheme is INTERNAL.'):
      self.RunUpdate(
          'backend-service-3'
          ' --region us-central1'
          ' --drop-traffic-if-unhealthy',
          use_global=False)

  def testInvalidProtocolWithConnectionDrainOnFailover(self):
    self.make_requests.side_effect = iter([
        [self._ssl_backend_services_with_health_check[0]],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        '^Invalid value for \\[--protocol\\]: can only specify '
        '--connection-drain-on-failover if the protocol is TCP.'):
      self.RunUpdate(
          'backend-service-3'
          ' --region us-central1'
          ' --connection-drain-on-failover',
          use_global=False)


if __name__ == '__main__':
  test_case.main()
