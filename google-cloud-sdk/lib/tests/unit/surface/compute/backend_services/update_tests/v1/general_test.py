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
"""Test for the backend services update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.backend_services.update import test_base


class BackendServiceUpdateTest(test_base.UpdateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testScopeWarning(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])
    self.RunUpdate('backend-service-1 --description "my new description"')
    self.AssertErrNotContains('WARNING:')

  def testWithNoFlags(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one property must be modified.'):
      self.RunUpdate('backend-service-1')

    self.CheckRequests()

  def testNoChange(self):
    messages = self.messages
    self.make_requests.side_effect = [[self._backend_services[0]]]

    self.RunUpdate('backend-service-1 --port-name http')

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1',
              project='my-project'))],
    )

    self.AssertErrEquals(
        'No change requested; skipping update for [backend-service-1].\n',
        normalize_space=True)

  def testWithNewDescription(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],

        [],
    ])

    self.RunUpdate('backend-service-1 --description "my new description"')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my new description',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithDescriptionRemoval(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],

        [],
    ])

    self.RunUpdate('backend-service-1 --description ""')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  description='',
                  backends=[],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithHttpHealthChecks(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],

        [],
    ])

    self.RunUpdate('backend-service-1 --http-health-checks '
                   'http-health-check-1,http-health-check-2')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[(self.compute_uri + '/projects/'
                                 'my-project/global/httpHealthChecks/'
                                 'http-health-check-1'),
                                (self.compute_uri + '/projects/'
                                 'my-project/global/httpHealthChecks/'
                                 'http-health-check-2')],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithDeprectatedFlag(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 '
                   '--http-health-checks my-other-health-check')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[(self.compute_uri + '/projects/'
                                 'my-project/global/httpHealthChecks/'
                                 'my-other-health-check')],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithTimeout(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 --timeout 10s')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=10),
              project='my-project'))],
    )

  def testWithPortName(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 --port-name my-port-name')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-1',
                  portName='my-port-name',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithBothHealthChecks(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._https_backend_services_with_legacy_health_check[0]],
        [],
    ])

    self.RunUpdate(
        'backend-service-1 '
        '--http-health-checks http-health-check-1,http-health-check-2 '
        '--https-health-checks https-health-check-1,https-health-check-2')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[(self.compute_uri + '/projects/'
                                 'my-project/global/httpHealthChecks/'
                                 'http-health-check-1'),
                                (self.compute_uri + '/projects/'
                                 'my-project/global/httpHealthChecks/'
                                 'http-health-check-2'),
                                (self.compute_uri + '/projects/'
                                 'my-project/global/httpsHealthChecks/'
                                 'https-health-check-1'),
                                (self.compute_uri + '/projects/'
                                 'my-project/global/httpsHealthChecks/'
                                 'https-health-check-2')],
                  name='backend-service-1',
                  portName='https',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTPS),
                  selfLink=(self.compute_uri + ''
                            '/projects/my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithProtocolHttp(self):
    self.templateTestWithProtocol(
        'backend-service-1 --protocol HTTP',
        self.messages.BackendService.ProtocolValueValuesEnum.HTTP,
        self._https_backend_services_with_legacy_health_check[0])

  def testWithProtocolHttpLowerCase(self):
    self.templateTestWithProtocol(
        'backend-service-1 --protocol http',
        self.messages.BackendService.ProtocolValueValuesEnum.HTTP,
        self._https_backend_services_with_legacy_health_check[0])

  def testWithProtocolHttps(self):
    self.templateTestWithProtocol(
        'backend-service-1 --protocol HTTPS',
        self.messages.BackendService.ProtocolValueValuesEnum.HTTPS,
        self._http_backend_services_with_legacy_health_check[0])

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
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
              backendService='backend-service-1',
              backendServiceResource=messages.BackendService(
                  backends=[],
                  description='my backend service',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/'
                       'http-health-check'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpsHealthChecks/'
                       'https-health-check'),
                  ],
                  name='backend-service-1',
                  portName='https',
                  protocol=protocol_enum,
                  selfLink=(self.compute_uri +
                            '/projects/my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
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
                  protocol=(self.messages.BackendService.
                            ProtocolValueValuesEnum.HTTP),
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
                  protocol=(self.messages.BackendService.
                            ProtocolValueValuesEnum.HTTP),
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-1'),
                  timeoutSec=30),
              project='my-project'))],
    )


if __name__ == '__main__':
  test_case.main()
