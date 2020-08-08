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


class WithConnectionDrainingTimeoutApiTest(
    test_base.BackendServiceCreateTestBase):

  def testConnectionDrainingTimeout(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --connection-draining-timeout 120
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
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30,
                connectionDraining=messages.ConnectionDraining(
                    drainingTimeoutSec=120)),
            project='my-project'))],)

  def testConnectionDrainingTimeoutInMinutes(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --connection-draining-timeout 2m
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
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30,
                connectionDraining=messages.ConnectionDraining(
                    drainingTimeoutSec=120)),
            project='my-project'))],)

  def testConnectionDrainingDisabled(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --connection-draining-timeout 0
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
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30,
                connectionDraining=messages.ConnectionDraining(
                    drainingTimeoutSec=0)),
            project='my-project'))],)


if __name__ == '__main__':
  test_case.main()
