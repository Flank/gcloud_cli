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
"""Tests for the backend services create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from tests.lib import test_case
from tests.lib.surface.compute.backend_services.create import test_base


class TrafficDirectorTest(test_base.BackendServiceCreateTestBase):

  def testLoadBalancingSchemeInternalSelfManaged(self):
    messages = self.messages
    self.Run("""
        compute backend-services create my-backend-service
          --protocol HTTP
          --health-checks my-health-check-1,my-health-check-2
          --description "My backend service"
          --load-balancing-scheme internal_self_managed
          --global
        """)

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/healthChecks/my-health-check-1'),
                    (self.compute_uri + '/projects/'
                     'my-project/global/healthChecks/my-health-check-2')
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                loadBalancingScheme=(
                    messages.BackendService.LoadBalancingSchemeValueValuesEnum
                    .INTERNAL_SELF_MANAGED),
                timeoutSec=30),
            project='my-project'))],)

  def testSimpleHttp2Case(self):
    messages = self.messages
    self.Run("""compute backend-services create backend-service-25
                --global
                --protocol http2
                --health-checks my-health-check-1,my-health-check-2
                --description cheesecake""")

    self.CheckRequests(
        [(self.compute.backendServices, 'Insert',
          messages.ComputeBackendServicesInsertRequest(
              backendService=messages.BackendService(
                  backends=[],
                  description='cheesecake',
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check-1'),
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check-2')
                  ],
                  name='backend-service-25',
                  portName='http2',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP2),
                  timeoutSec=30),
              project='my-project'))],)


if __name__ == '__main__':
  test_case.main()
