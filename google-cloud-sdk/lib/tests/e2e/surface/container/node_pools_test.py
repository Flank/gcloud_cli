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

from __future__ import absolute_import
from __future__ import unicode_literals
import logging

from googlecloudsdk.calliope import base
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container import base as testbase


class NodePoolsTestGA(testbase.IntegrationTestBase):

  def SetUp(self):
    self.releasetrack = base.ReleaseTrack.GA

  # We need to write a kubeconfig entry that has the executable path to gcloud,
  # so we run this test only in bundle.
  def NodePoolsUpdate(self, location_flag, prefix, track):
    self.cluster_name = next(
        e2e_utils.GetResourceNameGenerator(prefix=prefix))

    # Cluster deleted in "TeadDown" method of base class.
    logging.info('Creating %s', self.cluster_name)
    self.Run('container clusters create {0} {1} --num-nodes=1 '
             '--timeout={2}'
             .format(self.cluster_name, location_flag, self.TIMEOUT),
             track=track)
    self.AssertErrContains('Created')
    self.AssertOutputContains(self.cluster_name)
    self.AssertOutputContains('RUNNING')
    logging.info('Enabling auto-upgrade')
    self.Run('container node-pools update default-pool --cluster={0} {1} '
             '--enable-autoupgrade --timeout={2}'
             .format(self.cluster_name, location_flag, self.TIMEOUT),
             track=track)
    self.AssertErrContains('Updated')
    node_pool = self.Run('container node-pools describe default-pool '
                         '--cluster={0} {1}'
                         .format(self.cluster_name, location_flag))
    self.assertTrue(node_pool.management.autoUpgrade)

  def testNodePoolsUpdateZone(self):
    self.NodePoolsUpdate('--zone=' + self.ZONE, 'test-pool',
                         self.releasetrack)

  def testNodePoolsUpdateRegion(self):
    self.NodePoolsUpdate('--region=' + self.REGION,
                         'test-pool-region', self.releasetrack)

  # This test will cleanup the leaked clusters.
  # Delete clusters that are older than 1h.
  @sdk_test_base.Filters.RunOnlyInBundle
  def testCleanup(self):
    self.CleanupLeakedClusters(self.ZONE, self.releasetrack)
    self.CleanupLeakedClusters(self.REGION, self.releasetrack)


class NodePoolsTestBeta(NodePoolsTestGA):

  def SetUp(self):
    self.releasetrack = base.ReleaseTrack.BETA
    # Required to call v1beta1 API.
    self.Run('config set container/use_v1_api false')
    self.ZONE = 'us-east1-d'  # pylint: disable=invalid-name
    self.REGION = 'us-east1'  # pylint: disable=invalid-name


if __name__ == '__main__':
  test_case.main()
