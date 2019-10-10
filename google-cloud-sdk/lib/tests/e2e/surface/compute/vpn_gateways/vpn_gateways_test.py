# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Integration tests for VPN gateways labels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class VpnGatewaysGaTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.vpn_gateway_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-vpn-gateway'))

  def RunCompute(self, *cmd):
    return self.Run(('compute',) + cmd)

  def CleanUpResource(self, subcommand, name, *args):
    try:
      cmd = (subcommand, 'delete', name, '--quiet') + args
      self.RunCompute(*cmd)
    except exceptions.ToolException:
      pass

  @contextlib.contextmanager
  def _VpnGateway(self, name, region):
    try:
      yield self.RunCompute('vpn-gateways', 'create',
                            name, '--region', region, '--network', 'default')
    finally:
      self.CleanUpResource('vpn-gateways', name, '--region', region)

  def testVpnGateway(self):
    with self._VpnGateway(self.vpn_gateway_name, self.region):
      self.AssertNewOutputContains(self.vpn_gateway_name)
      self.Run('compute vpn-gateways describe {0} --region {1}'.format(
          self.vpn_gateway_name, self.region))
      self.AssertNewOutputContains('name: {0}'.format(
          self.vpn_gateway_name), reset=False)
      self.AssertNewOutputContains(
          'vpnInterfaces:\n- id: 0', reset=False)
      self.AssertNewOutputContains(
          'network:', reset=False)


if __name__ == '__main__':
  e2e_test_base.main()
