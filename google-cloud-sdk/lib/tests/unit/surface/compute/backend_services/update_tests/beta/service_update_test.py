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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute.backend_services.update import test_base


class BetaBackendServiceUpdateTest(test_base.BetaUpdateTestBase):

  def testEnableCdnNotSpecified(self):
    self.make_requests.side_effect = [[self._backend_services[0]], []]

    self.RunUpdate('backend-service-1 --timeout=42')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          self.messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          self.messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=self.messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=(self.messages.BackendService.ProtocolValueValuesEnum
                            .HTTP),
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=42),
              project='my-project'))],
    )

  def testEnableCdn(self):
    self.make_requests.side_effect = [[self._backend_services[0]], []]

    self.RunUpdate('backend-service-1 --enable-cdn')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          self.messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          self.messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=self.messages.BackendService(
                  backends=[],
                  description='my backend service',
                  enableCDN=True,
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=(self.messages.BackendService.ProtocolValueValuesEnum
                            .HTTP),
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testNoEnableCdn(self):
    self.make_requests.side_effect = [[self._backend_services[0]], []]

    self.RunUpdate('backend-service-1 --no-enable-cdn')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          self.messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          self.messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=self.messages.BackendService(
                  backends=[],
                  description='my backend service',
                  enableCDN=False,
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=(self.messages.BackendService.ProtocolValueValuesEnum
                            .HTTP),
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )


if __name__ == '__main__':
  test_case.main()
