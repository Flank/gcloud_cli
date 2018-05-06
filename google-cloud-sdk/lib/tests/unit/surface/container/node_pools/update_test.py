# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Tests for 'node-pools delete' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.container import base


class UpdateTestV1API(base.TestBaseV1,
                      base.GATestBase,
                      base.NodePoolsTestBase):
  """gcloud GA track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)
    self.assertIsNone(c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                                self.PROJECT_ID))
    self.api_adapter = api_adapter.NewAPIAdapter(self.API_VERSION)

  def _TestEnableAutoRepair(self, location):
    pool_kwargs = {
        'version': self.VERSION,
        'management': self.msgs.NodeManagement(
            autoRepair=None,
            autoUpgrade=None,
            upgradeOptions=None
        ),
    }
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool, zone=location)
    self.ExpectUpdateNodePool(
        self.NODE_POOL_NAME,
        self.msgs.NodeManagement(
            autoRepair=True,
            autoUpgrade=None,
            upgradeOptions=None),
        response=self._MakeNodePoolOperation(),
        zone=location)
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done,
                                                        zone=location))
    self.ExpectGetNodePool(pool.name, response=pool, zone=location)
    if location == self.REGION:
      cmdbase = (self.regional_node_pools_command_base.format(self.REGION) +
                 ' update {0} --cluster={1} --enable-autorepair ' +
                 '--format=disable')
    else:
      cmdbase = (self.node_pools_command_base.format(self.ZONE) +
                 ' update {0} --cluster={1} --enable-autorepair ' +
                 '--format=disable')
    result = self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.assertEqual(result.name, pool.name)
    self.assertEqual(result.management.autoRepair, True)
    self.assertEqual(result.management.autoUpgrade, None)

    self.AssertErrContains("""This will enable the autorepair feature for \
nodes. Please see
https://cloud.google.com/kubernetes-engine/docs/node-auto-repair for more
information on node autorepairs.

<START PROGRESS TRACKER>Updating node pool my-pool
<END PROGRESS TRACKER>SUCCESS
Updated [https://container.googleapis.com/{0}/projects/fake-project-id/zones/{1}/clusters/my-cluster/nodePools/my-pool].
""".format(self.API_VERSION, location))

  def testRegionalEnableAutoRepair(self):
    self._TestEnableAutoRepair(self.REGION)

  def testDisableAutoRepair(self):
    pool_kwargs = {
        'version': self.VERSION,
        'management': self.msgs.NodeManagement(
            autoRepair=True,
            autoUpgrade=True,
            upgradeOptions=None
        ),
    }
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectUpdateNodePool(
        self.NODE_POOL_NAME,
        self.msgs.NodeManagement(
            autoRepair=False,
            autoUpgrade=True,
            upgradeOptions=None),
        response=self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    cmdbase = (self.node_pools_command_base.format(self.ZONE) +
               ' update {0} --cluster={1} --no-enable-autorepair ' +
               '--format=disable')
    result = self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.assertEqual(result.name, pool.name)
    self.assertEqual(result.management.autoRepair, False)
    self.assertEqual(result.management.autoUpgrade, True)
    self.AssertErrContains("""This will disable the autorepair feature for \
nodes. Please see
https://cloud.google.com/kubernetes-engine/docs/node-auto-repair for more
information on node autorepairs.

<START PROGRESS TRACKER>Updating node pool my-pool
<END PROGRESS TRACKER>SUCCESS
Updated [https://container.googleapis.com/{0}/projects/fake-project-id/zones/us-central1-f/clusters/my-cluster/nodePools/my-pool].
""".format(self.API_VERSION))

  def testEnableAutoUpgrade(self):
    pool_kwargs = {
        'version': self.VERSION,
        'management': self.msgs.NodeManagement(
            autoRepair=None,
            autoUpgrade=None,
            upgradeOptions=None
        ),
    }
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectUpdateNodePool(
        self.NODE_POOL_NAME,
        self.msgs.NodeManagement(
            autoRepair=None,
            autoUpgrade=True,
            upgradeOptions=None),
        response=self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    cmdbase = (self.node_pools_command_base.format(self.ZONE) +
               ' update {0} --cluster={1} --enable-autoupgrade ' +
               '--format=disable')
    result = self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.assertEqual(result.management.autoRepair, None)
    self.assertEqual(result.management.autoUpgrade, True)
    self.AssertErrContains("""This will enable the autoupgrade feature for \
nodes. Please see
https://cloud.google.com/kubernetes-engine/docs/node-management for more
information on node autoupgrades.

<START PROGRESS TRACKER>Updating node pool my-pool
<END PROGRESS TRACKER>SUCCESS
Updated [https://container.googleapis.com/{0}/projects/fake-project-id/zones/us-central1-f/clusters/my-cluster/nodePools/my-pool].
""".format(self.API_VERSION))

  def testDisableAutoUpgrade(self):
    pool_kwargs = {
        'version': self.VERSION,
        'management': self.msgs.NodeManagement(
            autoRepair=True,
            autoUpgrade=True,
            upgradeOptions=None
        ),
    }
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectUpdateNodePool(
        self.NODE_POOL_NAME,
        self.msgs.NodeManagement(
            autoRepair=True,
            autoUpgrade=False,
            upgradeOptions=None),
        response=self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    cmdbase = (self.node_pools_command_base.format(self.ZONE) +
               ' update {0} --cluster={1} --no-enable-autoupgrade ' +
               '--format=disable')
    result = self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.assertEqual(result.management.autoRepair, True)
    self.assertEqual(result.management.autoUpgrade, False)
    self.AssertErrContains("""This will disable the autoupgrade feature for \
nodes. Please see
https://cloud.google.com/kubernetes-engine/docs/node-management for more
information on node autoupgrades.

<START PROGRESS TRACKER>Updating node pool my-pool
<END PROGRESS TRACKER>SUCCESS
Updated [https://container.googleapis.com/{0}/projects/fake-project-id/zones/us-central1-f/clusters/my-cluster/nodePools/my-pool].
""".format(self.API_VERSION))

  def testEnableAutoUpgradeWithUrlCluster(self):
    pool_kwargs = {
        'version': self.VERSION,
        'management': self.msgs.NodeManagement(
            autoRepair=None,
            autoUpgrade=None,
            upgradeOptions=None
        ),
    }
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectUpdateNodePool(
        self.NODE_POOL_NAME,
        self.msgs.NodeManagement(
            autoRepair=None,
            autoUpgrade=True,
            upgradeOptions=None),
        response=self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    cmdbase = (self.node_pools_command_base.format(self.ZONE) +
               ' update {0} --cluster={1} --enable-autoupgrade ' +
               '--format=disable')
    cluster_ref = self.api_adapter.registry.Create(
        'container.projects.zones.clusters',
        clusterId=self.CLUSTER_NAME,
        zone=self.ZONE,
        projectId=self.PROJECT_ID)
    node_pool_ref = self.api_adapter.registry.Create(
        'container.projects.zones.clusters.nodePools',
        nodePoolId=self.NODE_POOL_NAME,
        clusterId=self.CLUSTER_NAME,
        zone=self.ZONE,
        projectId=self.PROJECT_ID)
    result = self.Run(cmdbase.format(
        node_pool_ref.SelfLink(),
        cluster_ref.SelfLink()))
    self.assertEqual(result.management.autoRepair, None)
    self.assertEqual(result.management.autoUpgrade, True)
    self.AssertErrContains("""This will enable the autoupgrade feature for \
nodes. Please see
https://cloud.google.com/kubernetes-engine/docs/node-management for more
information on node autoupgrades.

<START PROGRESS TRACKER>Updating node pool my-pool
<END PROGRESS TRACKER>SUCCESS
Updated [https://container.googleapis.com/{0}/projects/fake-project-id/zones/us-central1-f/clusters/my-cluster/nodePools/my-pool].
""".format(self.API_VERSION))

  def testUpdateHttpError(self):
    pool = self._MakeNodePool(version=self.VERSION)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectUpdateNodePool(
        self.NODE_POOL_NAME,
        self.msgs.NodeManagement(
            autoRepair=None,
            autoUpgrade=True,
            upgradeOptions=None),
        exception=self.HttpError())
    with self.assertRaises(exceptions.HttpException):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' update {0} --cluster={1} --enable-autoupgrade'
               .format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains(
        'ResponseError: code=400, message=your request is bad '
        'and you should feel bad.')

  def testNoFlagsError(self):
    with self.AssertRaisesArgumentErrorRegexp('^argument'):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' update {0} --cluster={1}'
               .format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('Must be specified')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpdateTestBetaV1API(base.BetaTestBase, UpdateTestV1API):
  """gcloud Beta track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpdateTestBetaV1Beta1API(base.TestBaseV1Beta1, UpdateTestBetaV1API):
  """gcloud Beta track using container v1beta1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpdateTestAlphaV1API(base.AlphaTestBase, UpdateTestBetaV1API):
  """gcloud Alpha track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)

  def testNoFlagsError(self):
    with self.AssertRaisesArgumentErrorRegexp('^Exactly one of '):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' update {0} --cluster={1}'
               .format(self.NODE_POOL_NAME, self.CLUSTER_NAME))


# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpdateTestAlphaV1Alpha1API(base.TestBaseV1Alpha1, UpdateTestAlphaV1API,
                                 UpdateTestBetaV1Beta1API):
  """gcloud Alpha track using container v1alpha1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)

  def testEnableAutoscaling(self):
    pool_kwargs = {}
    pool = self._MakeNodePool(**pool_kwargs)
    update = self.msgs.ClusterUpdate(
        desiredNodePoolId=self.NODE_POOL_NAME,
        desiredNodePoolAutoscaling=self.msgs.NodePoolAutoscaling(
            enabled=True,
            autoprovisioned=True,
            minNodeCount=3,
            maxNodeCount=5))
    cmdbase = (self.node_pools_command_base.format(self.ZONE) +
               ' update {0} --cluster={1} --enable-autoscaling ' +
               '--max-nodes 5 --min-nodes 3 --enable-autoprovisioning')
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectUpdateCluster(
        cluster_name=self.CLUSTER_NAME,
        update=update,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))

  def testDisableAutoscaling(self):
    pool_kwargs = {
        'autoscaling': self.msgs.NodePoolAutoscaling(
            enabled=True,
            autoprovisioned=True,
            minNodeCount=3,
            maxNodeCount=5),
    }
    pool = self._MakeNodePool(**pool_kwargs)
    update = self.msgs.ClusterUpdate(
        desiredNodePoolId=self.NODE_POOL_NAME,
        desiredNodePoolAutoscaling=self.msgs.NodePoolAutoscaling(
            enabled=False,
            autoprovisioned=False,
            minNodeCount=0,
            maxNodeCount=0))
    cmdbase = (self.node_pools_command_base.format(self.ZONE) +
               ' update {0} --cluster={1} --no-enable-autoscaling ')
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectUpdateCluster(
        cluster_name=self.CLUSTER_NAME,
        update=update,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))

  def testEnableAutoprovisioning(self):
    pool_kwargs = {
        'autoscaling': self.msgs.NodePoolAutoscaling(
            enabled=True,
            autoprovisioned=False,
            minNodeCount=3,
            maxNodeCount=5),
    }
    pool = self._MakeNodePool(**pool_kwargs)
    update = self.msgs.ClusterUpdate(
        desiredNodePoolId=self.NODE_POOL_NAME,
        desiredNodePoolAutoscaling=self.msgs.NodePoolAutoscaling(
            enabled=True,
            autoprovisioned=True,
            minNodeCount=0,
            maxNodeCount=5))
    cmdbase = (self.node_pools_command_base.format(self.ZONE) +
               ' update {0} --cluster={1} --enable-autoprovisioning')
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectUpdateCluster(
        cluster_name=self.CLUSTER_NAME,
        update=update,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))

  def testConflictingFlagsError(self):
    with self.AssertRaisesArgumentErrorRegexp('Exactly one of '):
      self.Run(self.node_pools_command_base.format(self.ZONE) +
               ' update {0} --cluster={1}'
               ' --enable-autoprovisioning --enable-autoupgrade'
               .format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('--enable-autoupgrade')
    self.AssertErrContains('--enable-autoprovisioning')


if __name__ == '__main__':
  test_case.main()
