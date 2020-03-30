# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from apitools.base.py import encoding
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base

import mock


class BackendServicesListGATest(test_base.BaseTest,
                                completer_test_base.CompleterBase):
  _API_VERSION = 'v1'
  _RELEASE_TRACK = ''
  _DEFAULT_LIST_METHOD = 'AggregatedList'

  def _MakeBackendServicesWithInternalLoadBalancing(self):
    msgs = self.messages
    prefix = self.compute_uri
    return [
        msgs.BackendService(
            backends=[],
            description='my backend service',
            healthChecks=[
                ('https://compute.googleapis.com/compute/{0}/projects/'
                 'my-project/global/healthChecks/my-health-check'.format(
                     self.resource_api))
            ],
            name='backend-service-lb-1',
            protocol=msgs.BackendService.ProtocolValueValuesEnum.TCP,
            loadBalancingScheme=(
                msgs.BackendService.
                LoadBalancingSchemeValueValuesEnum.INTERNAL),
            region='region-1',
            selfLink=(prefix + '/projects/my-project'
                      '/regions/region-1/backendServices/backend-service-lb-1'),
            timeoutSec=30),
        msgs.BackendService(
            backends=[],
            description='my backend service',
            healthChecks=[
                ('https://compute.googleapis.com/compute/{0}/projects/'
                 'my-project/global/healthChecks/my-health-check'.format(
                     self.resource_api))
            ],
            name='backend-service-lb-2',
            protocol=msgs.BackendService.ProtocolValueValuesEnum.TCP,
            loadBalancingScheme=(
                msgs.BackendService.
                LoadBalancingSchemeValueValuesEnum.INTERNAL),
            region='region-1',
            selfLink=(prefix + '/projects/my-project'
                      '/regions/region-2/backendServices/backend-service-lb-2'),
            timeoutSec=30),
    ]

  def SetUp(self):
    self.SelectApi(self._API_VERSION)
    self.default_list_request = (
        self.compute.backendServices.GetRequestType(self._DEFAULT_LIST_METHOD))
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
            port=80,
            protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
            region='region-1',
            selfLink=(self.compute_uri + '/projects/my-project'
                      '/regions/alaska/backendServices/backend-service-1'),
            timeoutSec=30))],
    ]
    self.Run(self._RELEASE_TRACK + ' compute backend-services list')
    self.list_json.assert_called_once_with(
        requests=[(self.compute.backendServices, self._DEFAULT_LIST_METHOD,
                   self._getListRequestMessage('my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputContains('NAME BACKENDS PROTOCOL', normalize_space=True)
    self.AssertOutputContains(
        'backend-service-1 zone-1/instanceGroups/group-1 HTTP',
        normalize_space=True)

  def testBackendServicesCompleter(self):
    messages = self.messages
    side_effect = [
        messages.BackendService(
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
            port=80,
            protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
            region='region-1',
            selfLink=(self.compute_uri + '/projects/my-project'
                      '/regions/alaska/backendServices/backend-service-1'),
            timeoutSec=30
        )
    ]
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(side_effect), []
    ]

    self.RunCompleter(
        flags.BackendServicesCompleter,
        expected_command=[
            [
                'compute',
                'backend-services',
                'list',
                '--filter=region:*',
                '--uri',
                '--quiet',
                '--format=disable',
                '--project=my-project',
            ],
            [
                'compute',
                'backend-services',
                'list',
                '--global',
                '--uri',
                '--quiet',
                '--format=disable',
                '--project=my-project',
            ],
        ],
        expected_completions=[
            'backend-service-1',
        ],
        args={
            '--project': 'my-project',
        },
        cli=self.cli,
    )

  def _getListRequestMessage(self, project):
    return self.default_list_request(project=project, includeAllScopes=True)


class BackendServicesListAlphaTest(BackendServicesListGATest):
  _API_VERSION = 'alpha'
  _RELEASE_TRACK = 'alpha'
  _DEFAULT_LIST_METHOD = 'AggregatedList'

  def SetUp(self):
    self.SelectApi(self._API_VERSION)

  def _getListRequestMessage(self, project):
    return self.default_list_request(project=project, includeAllScopes=True)


if __name__ == '__main__':
  test_case.main()
