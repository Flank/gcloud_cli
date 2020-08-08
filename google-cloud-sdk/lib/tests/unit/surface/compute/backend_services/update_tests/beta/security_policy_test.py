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

from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute.backend_services.update import test_base


class SetSecurityPolicyTest(test_base.BetaUpdateTestBase):

  def SetUp(self):
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')
    self.my_policy = self.resources.Create(
        'compute.securityPolicies',
        securityPolicy='my-policy',
        project='my-project')

  def testSetSecurityPolicy(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 --security-policy {}'.format(
        self.my_policy.Name()))

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'SetSecurityPolicy',
          messages.ComputeBackendServicesSetSecurityPolicyRequest(
              backendService='backend-service-1',
              project='my-project',
              securityPolicyReference=messages.SecurityPolicyReference(
                  securityPolicy=self.my_policy.SelfLink())))],
    )

  def testSetSecurityPolicyAndUpdateDescription(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
        [],
    ])

    self.RunUpdate('backend-service-1 --description "my new description" '
                   '--security-policy {}'.format(self.my_policy.Name()))

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
        [(self.compute.backendServices, 'SetSecurityPolicy',
          messages.ComputeBackendServicesSetSecurityPolicyRequest(
              backendService='backend-service-1',
              project='my-project',
              securityPolicyReference=messages.SecurityPolicyReference(
                  securityPolicy=self.my_policy.SelfLink())))],
    )

  def testClearSecurityPolicy(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 --security-policy ""')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'SetSecurityPolicy',
          messages.ComputeBackendServicesSetSecurityPolicyRequest(
              backendService='backend-service-1',
              project='my-project',
              securityPolicyReference=messages.SecurityPolicyReference(
                  securityPolicy=None)))],
    )

  def testUriSupport(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[0]],
        [],
    ])

    self.RunUpdate('backend-service-1 --security-policy {}'.format(
        self.my_policy.SelfLink()))

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-1', project='my-project'))],
        [(self.compute.backendServices, 'SetSecurityPolicy',
          messages.ComputeBackendServicesSetSecurityPolicyRequest(
              backendService='backend-service-1',
              project='my-project',
              securityPolicyReference=messages.SecurityPolicyReference(
                  securityPolicy=self.my_policy.SelfLink())))],
    )


if __name__ == '__main__':
  test_case.main()
