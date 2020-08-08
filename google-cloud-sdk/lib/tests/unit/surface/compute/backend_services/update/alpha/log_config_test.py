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


class WithLogConfigApiTest(test_base.AlphaUpdateTestBase):

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
                             .LoadBalancingSchemeValueValuesEnum.EXTERNAL),
        name='backend-service-3',
        portName='http',
        protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
        selfLink=self.resources.Create(
            'compute.backendServices',
            backendService='backend-service-3',
            project='my-project').SelfLink(),
        timeoutSec=30)

  def CheckResults(self, expected_message=None):
    messages = self.messages

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-3', project='my-project'))],
        [(self.compute.backendServices, 'Patch',
          messages.ComputeBackendServicesPatchRequest(
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
                      .EXTERNAL),
                  logConfig=expected_message,
                  name='backend-service-3',
                  portName='http',
                  protocol=(
                      messages.BackendService.ProtocolValueValuesEnum.HTTP),
                  selfLink=self.resources.Create(
                      'compute.backendServices',
                      backendService='backend-service-3',
                      project='my-project').SelfLink(),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testEnableLogging(self):
    self.make_requests.side_effect = iter([
        [self.orig_backend_service],
        [],
    ])

    self.RunUpdate('backend-service-3 --global'
                   ' --enable-logging'
                   ' --logging-sample-rate 0.7')
    self.CheckResults(
        self.messages.BackendServiceLogConfig(enable=True, sampleRate=0.7))

  def testDisableLogging(self):
    self.make_requests.side_effect = iter([
        [self.orig_backend_service],
        [],
    ])

    self.RunUpdate('backend-service-3 --global'
                   ' --no-enable-logging'
                   ' --logging-sample-rate 0.0')
    self.CheckResults(
        self.messages.BackendServiceLogConfig(enable=False, sampleRate=0.0))

  def testToggleSampleRateWithExistingLogConfig(self):
    backend_service_with_log_config = copy.deepcopy(self.orig_backend_service)
    backend_service_with_log_config.logConfig = (
        self.messages.BackendServiceLogConfig(enable=True))
    self.make_requests.side_effect = iter([
        [backend_service_with_log_config],
        [],
    ])

    self.RunUpdate('backend-service-3 --global --logging-sample-rate 0.9')
    self.CheckResults(
        self.messages.BackendServiceLogConfig(enable=True, sampleRate=0.9))


if __name__ == '__main__':
  test_case.main()
