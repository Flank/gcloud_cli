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
"""Integration tests for updating networks."""

import logging

from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib.surface.compute import e2e_test_base


class NetworksUpdateTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.network_name = e2e_utils.GetResourceNameGenerator(
        prefix='networks-update-test-network').next()

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    self.CleanUpResource(
        self.network_name, 'networks', scope=e2e_test_base.GLOBAL)

  def testNetworksUpdate(self):
    self.Run('compute networks create {0} '
             '--subnet-mode custom --bgp-routing-mode regional'
             .format(self.network_name))
    self.AssertNewOutputContainsAll([self.network_name, 'CUSTOM', 'REGIONAL'])

    self.Run('compute networks update {0} --bgp-routing-mode global'
             .format(self.network_name))
    self.Run('compute networks describe {0}'.format(self.network_name))
    self.AssertNewOutputContains('routingMode: GLOBAL')

    self._DeleteTestNetwork()

  @sdk_test_base.Retry(
      why=('Retry in case network is not ready to delete.'),
      max_retrials=3,
      sleep_ms=1000)
  def _DeleteTestNetwork(self):
    self.Run('compute networks delete {0}'.format(self.network_name))


if __name__ == '__main__':
  e2e_test_base.main()
