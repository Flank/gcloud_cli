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

"""Tests for the target-vpn-gateways list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.compute.target_vpn_gateways import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)

  if api_version == 'v1':
    test_obj.target_vpn_gateways = test_resources.TARGET_VPN_GATEWAYS_V1
  elif api_version == 'beta':
    test_obj.target_vpn_gateways = test_resources.TARGET_VPN_GATEWAYS_BETA
  else:
    raise ValueError('api_version must be \'v1\' or \'beta\'. '
                     'Got [{0}].'.format(api_version))


class TargetVpnGatewaysListTest(test_base.BaseTest,
                                completer_test_base.CompleterBase):

  def SetUp(self):
    SetUp(self, 'v1')

    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetRegionalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_regional_resources = lister_patcher.start()
    self.mock_get_regional_resources.return_value = (
        resource_projector.MakeSerializable(self.target_vpn_gateways))

  def testSimpleInvocationMakesRightRequest(self):
    self.Run("""
        compute target-vpn-gateways list --regions region-1
        """)
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute.targetVpnGateways,
        project='my-project',
        http=self.mock_http(),
        requested_regions=['region-1'],
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME      NETWORK      REGION
            gateway-1 my-network   region-1
            gateway-2 my-network   region-1
            """), normalize_space=True)

  def testTargetVpnGatewaysCompleter(self):
    self.RunCompleter(
        flags.TargetVpnGatewaysCompleter,
        expected_command=[
            'compute',
            'target-vpn-gateways',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'gateway-1',
            'gateway-2',
            'gateway-3',
        ],
        cli=self.cli,
    )
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute.targetVpnGateways,
        project='my-project',
        http=self.mock_http(),
        requested_regions=[],
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])

if __name__ == '__main__':
  test_case.main()
