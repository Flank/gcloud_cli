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


class RegionalTest(test_base.AlphaUpdateTestBase):

  def testWithHealthChecksUpdatedToHealthChecks(self):
    messages = self.messages
    orig_backend_service = messages.BackendService(
        backends=[],
        description='my backend service',
        healthChecks=[(self.compute_uri + '/projects/my-project/global'
                       '/httpHealthChecks/my-health-check')],
        name='backend-service-3',
        portName='http',
        protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
        selfLink=(self.compute_uri + '/projects/my-project'
                  '/region/alaska/backendServices/backend-service-1'),
        timeoutSec=30)
    self.make_requests.side_effect = iter([
        [orig_backend_service],
        [],
    ])

    updated_backend_service = copy.deepcopy(orig_backend_service)
    updated_backend_service.healthChecks = [
        self.compute_uri +
        '/projects/my-project/global/healthChecks/new-health-check'
    ]

    self.RunUpdate('backend-service-3 --region alaska '
                   '--health-checks new-health-check '
                   '--global-health-checks', use_global=False)

    self.CheckRequests(
        [(self.compute.regionBackendServices, 'Get',
          messages.ComputeRegionBackendServicesGetRequest(
              backendService='backend-service-3',
              region='alaska',
              project='my-project'))],
        [(self.compute.regionBackendServices, 'Patch',
          messages.ComputeRegionBackendServicesPatchRequest(
              backendService='backend-service-3',
              backendServiceResource=updated_backend_service,
              region='alaska',
              project='my-project'))],
    )

  def testWithHealthChecksUpdatedToHealthChecksNoGlobalHealthChecksFlag(self):
    messages = self.messages
    orig_backend_service = messages.BackendService(
        backends=[],
        description='my backend service',
        healthChecks=[(self.compute_uri + '/projects/my-project/global'
                       '/httpHealthChecks/my-health-check')],
        name='backend-service-3',
        portName='http',
        protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
        selfLink=(self.compute_uri + '/projects/my-project'
                  '/region/alaska/backendServices/backend-service-1'),
        timeoutSec=30)
    self.make_requests.side_effect = iter([
        [orig_backend_service],
        [],
    ])

    updated_backend_service = copy.deepcopy(orig_backend_service)
    updated_backend_service.healthChecks = [
        self.compute_uri +
        '/projects/my-project/global/healthChecks/new-health-check'
    ]

    self.RunUpdate('backend-service-3 --region alaska '
                   '--health-checks new-health-check', use_global=False)

    self.CheckRequests(
        [(self.compute.regionBackendServices, 'Get',
          messages.ComputeRegionBackendServicesGetRequest(
              backendService='backend-service-3',
              region='alaska',
              project='my-project'))],
        [(self.compute.regionBackendServices, 'Patch',
          messages.ComputeRegionBackendServicesPatchRequest(
              backendService='backend-service-3',
              backendServiceResource=updated_backend_service,
              region='alaska',
              project='my-project'))],
    )

  def testRegionWithHealthChecksUpdatedToRegionHealthChecks(self):
    messages = self.messages
    orig_backend_service = messages.BackendService(
        backends=[],
        description='my backend service',
        healthChecks=[(self.compute_uri + '/projects/my-project/region/global'
                       '/httpHealthChecks/my-health-check')],
        name='backend-service-3',
        portName='http',
        protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
        selfLink=(self.compute_uri + '/projects/my-project'
                  '/region/alaska/backendServices/backend-service-1'),
        timeoutSec=30)
    self.make_requests.side_effect = iter([
        [orig_backend_service],
        [],
    ])

    updated_backend_service = copy.deepcopy(orig_backend_service)
    updated_backend_service.healthChecks = [
        self.compute_uri +
        '/projects/my-project/regions/alaska/healthChecks/new-health-check'
    ]

    self.RunUpdate('backend-service-3 --region alaska '
                   '--health-checks new-health-check '
                   '--health-checks-region alaska', use_global=False)

    self.CheckRequests(
        [(self.compute.regionBackendServices, 'Get',
          messages.ComputeRegionBackendServicesGetRequest(
              backendService='backend-service-3',
              region='alaska',
              project='my-project'))],
        [(self.compute.regionBackendServices, 'Patch',
          messages.ComputeRegionBackendServicesPatchRequest(
              backendService='backend-service-3',
              backendServiceResource=updated_backend_service,
              region='alaska',
              project='my-project'))],
    )


if __name__ == '__main__':
  test_case.main()
