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

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute.backend_services.create import test_base


class WithFailoverPolicyApiTest(test_base.BackendServiceCreateTestBase):

  def SetUp(self):
    self._create_service_cmd_line = (
        """compute backend-services create my-backend-service
           --health-checks my-health-check-1
           --global-health-checks
           --description "My backend service"
           --region us-central1""")

  def CheckResults(self, expected_message=None):
    messages = self.messages

    self.CheckRequests([
        (self.compute.regionBackendServices, 'Insert',
         messages.ComputeRegionBackendServicesInsertRequest(
             backendService=messages.BackendService(
                 backends=[],
                 description='My backend service',
                 failoverPolicy=expected_message,
                 healthChecks=[
                     (self.compute_uri + '/projects/'
                      'my-project/global/healthChecks/my-health-check-1'),
                 ],
                 loadBalancingScheme=(
                     messages.BackendService.LoadBalancingSchemeValueValuesEnum
                     .INTERNAL),
                 name='my-backend-service',
                 protocol=(messages.BackendService.ProtocolValueValuesEnum.TCP),
                 timeoutSec=30),
             project='my-project',
             region='us-central1'))
    ],)

  def testEnableFailoverOptions(self):
    self.Run(self._create_service_cmd_line + ' --load-balancing-scheme internal'
             ' --no-connection-drain-on-failover'
             ' --drop-traffic-if-unhealthy'
             ' --failover-ratio 0.5')
    self.CheckResults(
        self.messages.BackendServiceFailoverPolicy(
            disableConnectionDrainOnFailover=True,
            dropTrafficIfUnhealthy=True,
            failoverRatio=0.5))

  def testDisableFailoverOptions(self):
    self.Run(self._create_service_cmd_line + ' --load-balancing-scheme internal'
             ' --connection-drain-on-failover'
             ' --no-drop-traffic-if-unhealthy'
             ' --failover-ratio 0.5')
    self.CheckResults(
        self.messages.BackendServiceFailoverPolicy(
            disableConnectionDrainOnFailover=False,
            dropTrafficIfUnhealthy=False,
            failoverRatio=0.5))

  def testCannotSpecifyFailoverPolicyForGlobalBackendService(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--global\\]: cannot specify failover policies'
        ' for global backend services.', self.Run,
        'compute backend-services create backend-service-1'
        ' --http-health-checks my-health-check-1'
        ' --description "My backend service"'
        ' --global'
        ' --connection-drain-on-failover')

  def testInvalidLoadBalancingSchemeWithInternalFailoverOptions(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--load-balancing-scheme\\]: can only specify '
        '--connection-drain-on-failover or --drop-traffic-if-unhealthy'
        ' if the load balancing scheme is INTERNAL.', self.Run,
        self._create_service_cmd_line + ' --protocol TCP' +
        ' --drop-traffic-if-unhealthy')

  def testInvalidProtocolWithConnectionDrainOnFailover(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--protocol\\]: can only specify '
        '--connection-drain-on-failover if the protocol is TCP.', self.Run,
        self._create_service_cmd_line + ' --load-balancing-scheme INTERNAL' +
        ' --protocol SSL' + ' --connection-drain-on-failover')


if __name__ == '__main__':
  test_case.main()
