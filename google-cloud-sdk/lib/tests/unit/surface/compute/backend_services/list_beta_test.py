# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the backend-services list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import encoding
from googlecloudsdk.core.resource import resource_projector
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


class BackendServicesListTest(test_base.BaseTest):

  def _MakeBackendServicesWithInternalLoadBalancing(self):
    msgs = self.messages
    prefix = self.compute_uri
    return [
        msgs.BackendService(
            backends=[],
            description='my backend service',
            healthChecks=[
                ('https://www.googleapis.com/compute/{0}/projects/'
                 'my-project/global/healthChecks/my-health-check'.format(
                     self.resource_api))
            ],
            name='backend-service-lb-1',
            protocol=msgs.BackendService.ProtocolValueValuesEnum.TCP,
            loadBalancingScheme=(
                msgs.BackendService.
                LoadBalancingSchemeValueValuesEnum.INTERNAL),
            selfLink=(prefix + '/projects/my-project'
                      '/regions/region-1/backendServices/backend-service-lb-1'),
            timeoutSec=30),
        msgs.BackendService(
            backends=[],
            description='my backend service',
            healthChecks=[
                ('https://www.googleapis.com/compute/{0}/projects/'
                 'my-project/global/healthChecks/my-health-check'.format(
                     self.resource_api))
            ],
            name='backend-service-lb-2',
            protocol=msgs.BackendService.ProtocolValueValuesEnum.TCP,
            loadBalancingScheme=(
                msgs.BackendService.
                LoadBalancingSchemeValueValuesEnum.INTERNAL),
            selfLink=(prefix + '/projects/my-project'
                      '/regions/region-2/backendServices/backend-service-lb-2'),
            timeoutSec=30),
    ]

  def SetUp(self):
    self.SelectApi('beta')
    self.internal_load_balancing_backend_services = (
        self._MakeBackendServicesWithInternalLoadBalancing())

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def testTableOutput(self):
    messages = self.messages
    self.list_json.side_effect = [
        [encoding.MessageToDict(messages.BackendService(
            backends=[
                messages.Backend(
                    balancingMode=(
                        messages.Backend.BalancingModeValueValuesEnum.RATE),
                    description='group one',
                    group=(
                        self.compute_uri + '/projects/my-project/zones/zone-1/'
                        'instanceGroups/group-1'),
                    maxRate=100),
            ],
            description='my backend service',
            healthChecks=[
                (self.compute_uri + '/projects/my-project/global'
                 '/httpHealthChecks/my-health-check')
            ],
            name='backend-service-1',
            loadBalancingScheme=(
                messages.BackendService.LoadBalancingSchemeValueValuesEnum
                .EXTERNAL),
            port=80,
            protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
            region=self.compute_uri + '/projects/my-project/regions/alaska',
            selfLink=(self.compute_uri + '/projects/my-project'
                      '/region/alaska/backendServices/backend-service-1'),
            timeoutSec=30))],
    ]
    self.Run('beta compute backend-services list --regions alaska,kansas')
    self.list_json.assert_called_once_with(
        requests=[(self.compute.regionBackendServices,
                   'List',
                   messages.ComputeRegionBackendServicesListRequest(
                       region='alaska',
                       project='my-project')),
                  (self.compute.regionBackendServices,
                   'List',
                   messages.ComputeRegionBackendServicesListRequest(
                       region='kansas',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME              BACKENDS                      PROTOCOL LOAD_BALANCING_SCHEME HEALTH_CHECKS
            backend-service-1 zone-1/instanceGroups/group-1 HTTP EXTERNAL my-health-check
            """), normalize_space=True)

  def testAggregatedList(self):
    self.list_json.side_effect = [resource_projector.MakeSerializable(
        test_resources.BACKEND_SERVICES_V1
        + self.internal_load_balancing_backend_services)]
    self.Run('beta compute backend-services list')
    self.list_json.assert_called_once_with(
        requests=[(self.compute.backendServices,
                   'AggregatedList',
                   self.messages.ComputeBackendServicesAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME BACKENDS PROTOCOL LOAD_BALANCING_SCHEME HEALTH_CHECKS
            backend-service-1 HTTP my-health-check
            backend-service-2 zone-1/instanceGroups/group-1,zone-2/instanceGroups/group-2 HTTP my-health-check
            instance-group-service zone-1/instanceGroups/group-1 HTTP my-health-check
            regional-instance-group-service region-1/instanceGroups/group-1 HTTP my-health-check
            backend-service-tcp zone-1/instanceGroups/group-1,zone-2/instanceGroups/group-2 TCP my-health-check
            backend-service-lb-1 TCP INTERNAL my-health-check
            backend-service-lb-2 TCP INTERNAL my-health-check
            """), normalize_space=True)


if __name__ == '__main__':
  test_case.main()
