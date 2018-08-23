# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Integration tests for manipulating networks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging

from tests.lib import e2e_utils
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.surface.compute import e2e_test_base


class NetworksTest(parameterized.TestCase, e2e_test_base.BaseTest):

  def SetUp(self):
    self.network_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='networks-test-network'))

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    self.CleanUpResource(
        self.network_name, 'networks', scope=e2e_test_base.GLOBAL)

  # Skip auto mode because it consumes an expensive amount of subnet quota.
  @parameterized.parameters('LEGACY', 'CUSTOM')
  def testNetworks(self, subnet_mode_arg):
    self.Run('compute networks create {0} --subnet-mode {1}'
             .format(self.network_name, subnet_mode_arg))
    self.AssertNewOutputContainsAll([self.network_name, subnet_mode_arg])

    self.Run('compute networks describe {0}'.format(self.network_name))
    self.AssertNewOutputContains('name: {0}'.format(self.network_name))

    self._DeleteTestNetwork()

  @parameterized.parameters('REGIONAL', 'GLOBAL')
  def testNetworksBgpRoutingMode(self, bgp_routing_mode_arg):
    self.Run('compute networks create {0} --bgp-routing-mode {1}'
             .format(self.network_name, bgp_routing_mode_arg))
    self.AssertNewOutputContainsAll([self.network_name, bgp_routing_mode_arg])

    self._DeleteTestNetwork()

  @sdk_test_base.Retry(
      why=('Retry in case network is not ready to delete.'),
      max_retrials=3,
      sleep_ms=1000)
  def _DeleteTestNetwork(self):
    self.Run('compute networks delete {0}'.format(self.network_name))


if __name__ == '__main__':
  e2e_test_base.main()
