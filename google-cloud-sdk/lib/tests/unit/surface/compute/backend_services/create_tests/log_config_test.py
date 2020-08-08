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


class WithLogConfigApiTest(test_base.BackendServiceCreateTestBase):

  def SetUp(self):
    self._create_service_cmd_line = (
        """compute backend-services create my-backend-service
           --health-checks my-health-check-1
           --global-health-checks
           --description "My backend service"
           --global""")

  def CheckResults(self, expected_message=None):
    messages = self.messages

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                logConfig=expected_message,
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/healthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30),
            project='my-project'))],)

  def testEnableLogging(self):
    self.Run(self._create_service_cmd_line + ' --load-balancing-scheme external'
             ' --protocol HTTP'
             ' --enable-logging'
             ' --logging-sample-rate 0.7')
    self.CheckResults(
        self.messages.BackendServiceLogConfig(enable=True, sampleRate=0.7))

  def testDisableLogging(self):
    self.Run(self._create_service_cmd_line + ' --load-balancing-scheme external'
             ' --protocol HTTP'
             ' --no-enable-logging'
             ' --logging-sample-rate 0.0')
    self.CheckResults(
        self.messages.BackendServiceLogConfig(enable=False, sampleRate=0.0))

  def testInvalidProtocolWithLogConfig(self):
    self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '^Invalid value for \\[--protocol\\]: can only specify --enable-logging'
        ' or --logging-sample-rate if the protocol is HTTP/HTTPS/HTTP2.',
        self.Run,
        self._create_service_cmd_line + ' --load-balancing-scheme external' +
        ' --protocol TCP' + ' --enable-logging')


if __name__ == '__main__':
  test_case.main()
