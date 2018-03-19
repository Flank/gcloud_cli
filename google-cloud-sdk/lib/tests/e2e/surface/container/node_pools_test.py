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

"""Integration tests for container node pools."""

import logging

from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container import base


class NodePoolsTest(base.IntegrationTestBase):

  # We need to write a kubeconfig entry that has the executable path to gcloud,
  # so we run this test only in bundle.
  # TODO(b/67013344): Remove DoNotRunOnWindows after fix the tests on windows.
  @sdk_test_base.Filters.RunOnlyInBundle
  def testNodePoolsUpdate(self):
    self.cluster_name = e2e_utils.GetResourceNameGenerator(
        prefix='container-test-pool').next()

    # Cluster deleted in "TeadDown" method of base class.
    logging.info('Creating %s', self.cluster_name)
    self.Run('container clusters create {0} --zone={1} --num-nodes=1 '
             '--timeout={2}'
             .format(self.cluster_name, self.ZONE, self.TIMEOUT))
    self.AssertErrContains('Created')
    self.AssertOutputContains(self.cluster_name)
    self.AssertOutputContains('RUNNING')
    logging.info('Enabling auto-upgrade')
    self.Run('container node-pools update default-pool --cluster={0} '
             '--zone={1} --enable-autoupgrade --timeout={2}'
             .format(self.cluster_name, self.ZONE, self.TIMEOUT))
    self.AssertErrContains('Updated')
    node_pool = self.Run('container node-pools describe default-pool '
                         '--cluster={0} --zone={1}'
                         .format(self.cluster_name, self.ZONE))
    self.assertTrue(node_pool.management.autoUpgrade)


if __name__ == '__main__':
  test_case.main()
