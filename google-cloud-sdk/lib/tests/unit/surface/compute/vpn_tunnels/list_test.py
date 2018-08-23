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

"""Tests for the vpn-tunnels list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.compute.vpn_tunnels import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)

  if api_version == 'v1':
    test_obj.vpn_tunnels = test_resources.VPN_TUNNELS_V1
  elif api_version == 'beta':
    test_obj.vpn_tunnels = test_resources.VPN_TUNNELS_BETA
  else:
    raise ValueError('api_version must be \'v1\' or \'beta\','
                     'Got [{0}].'.format(api_version))


class VpnTunnelsListTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    SetUp(self, 'v1')

    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetRegionalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_regional_resources = lister_patcher.start()
    self.mock_get_regional_resources.return_value = (
        resource_projector.MakeSerializable(self.vpn_tunnels))

  def testSimpleInvocationMakesRightRequest(self):
    self.Run("""
        compute vpn-tunnels list --regions region-1
        """)
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute.vpnTunnels,
        project='my-project',
        http=self.mock_http(),
        requested_regions=['region-1'],
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME     REGION   GATEWAY   PEER_ADDRESS
            tunnel-1 region-1 gateway-1 1.1.1.1
            tunnel-3 region-1 gateway-3 3.3.3.3
            """), normalize_space=True)

  def testVpnTunnelsCompleter(self):
    self.RunCompleter(
        flags.VpnTunnelsCompleter,
        expected_command=[
            'compute',
            'vpn-tunnels',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'tunnel-1',
            'tunnel-3',
            'tunnel-2',
        ],
        cli=self.cli,
    )


if __name__ == '__main__':
  test_case.main()
