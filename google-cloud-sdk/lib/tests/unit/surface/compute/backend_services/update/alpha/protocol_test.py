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

from tests.lib import test_case
from tests.lib.surface.compute.backend_services.update import test_base


class WithProtocolTest(test_base.AlphaUpdateTestBase):

  def testScopeWarning(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])
    self.RunUpdate(
        'backend-service-1 --region alaska '
        '--description cool-description',
        use_global=False)
    self.AssertErrNotContains('WARNING:')

  def testWithProtocolHttp(self):
    self.templateTestWithProtocol(
        'backend-service-3 --protocol HTTP',
        self.messages.BackendService.ProtocolValueValuesEnum.HTTP,
        self._https_backend_services_with_health_check[0])

  def testWithProtocolHttpLowerCase(self):
    self.templateTestWithProtocol(
        'backend-service-3 --protocol http',
        self.messages.BackendService.ProtocolValueValuesEnum.HTTP,
        self._https_backend_services_with_health_check[0])

  def testWithProtocolHttps(self):
    self.templateTestWithProtocol(
        'backend-service-3 --protocol HTTPS',
        self.messages.BackendService.ProtocolValueValuesEnum.HTTPS,
        self._http_backend_services_with_health_check[0])

  def testWithProtocolHttp2(self):
    self.templateTestWithProtocol(
        'backend-service-3 --protocol HTTP2',
        self.messages.BackendService.ProtocolValueValuesEnum.HTTP2,
        self._http_backend_services_with_health_check[0])

  def testWithProtocolTcp(self):
    self.templateTestWithProtocol(
        'backend-service-3 --protocol TCP',
        self.messages.BackendService.ProtocolValueValuesEnum.TCP,
        self._ssl_backend_services_with_health_check[0])

  def testWithProtocolSsl(self):
    self.templateTestWithProtocol(
        'backend-service-3 --protocol SSL',
        self.messages.BackendService.ProtocolValueValuesEnum.SSL,
        self._tcp_backend_services_with_health_check[0])

  def templateTestWithProtocol(self, cmd, protocol_enum,
                               original_backend_service):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [original_backend_service],
        [],
    ])

    self.RunUpdate(cmd)

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-3', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-3',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/orig-health-check'),
                  ],
                  name='backend-service-3',
                  portName='http',
                  protocol=protocol_enum,
                  selfLink=(self.compute_uri +
                            '/projects/my-project/global/backendServices/'
                            'backend-service-3'),
                  timeoutSec=30),
              project='my-project'))],
    )


if __name__ == '__main__':
  test_case.main()
