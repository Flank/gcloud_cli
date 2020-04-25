# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

import itertools

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.container import base


class UpdateTestGA(parameterized.TestCase, base.GATestBase,
                   base.NodePoolsTestBase):
  """gcloud GA track using container v1 API."""

  def SetUp(self):
    self.assertIsNone(
        c_util.ClusterConfig.Load(self.CLUSTER_NAME, self.ZONE,
                                  self.PROJECT_ID))
    self.api_adapter = api_adapter.NewAPIAdapter(self.API_VERSION)

  def _TestEnableAutoRepair(self, location):
    pool_kwargs = {
        'version':
            self.VERSION,
        'management':
            self.msgs.NodeManagement(
                autoRepair=None, autoUpgrade=None, upgradeOptions=None),
    }
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool, zone=location)
    self.ExpectSetNodePoolManagement(
        self.NODE_POOL_NAME,
        self.msgs.NodeManagement(
            autoRepair=True, autoUpgrade=None, upgradeOptions=None),
        response=self._MakeNodePoolOperation(),
        zone=location)
    self.ExpectGetOperation(
        self._MakeNodePoolOperation(status=self.op_done, zone=location))
    self.ExpectGetNodePool(pool.name, response=pool, zone=location)
    if location == self.REGION:
      cmdbase = (
          self.regional_node_pools_command_base.format(self.REGION) +
          ' update {0} --cluster={1} --enable-autorepair ' + '--format=disable')
    else:
      cmdbase = (
          self.node_pools_command_base.format(self.ZONE) +
          ' update {0} --cluster={1} --enable-autorepair ' + '--format=disable')
    result = self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.assertEqual(result.name, pool.name)
    self.assertEqual(result.management.autoRepair, True)
    self.assertEqual(result.management.autoUpgrade, None)

    self.AssertErrContains("""This will enable the autorepair feature for \
nodes. Please see \
https://cloud.google.com/kubernetes-engine/docs/node-auto-repair for more \
information on node autorepairs.
{{"ux": "PROGRESS_TRACKER", "message": "Updating node pool my-pool", "status": "SUCCESS"}}
Updated [https://container.googleapis.com/{0}/projects/fake-project-id/zones/{1}/clusters/my-cluster/nodePools/my-pool].
""".format(self.API_VERSION, location))

  def testRegionalEnableAutoRepair(self):
    self._TestEnableAutoRepair(self.REGION)

  def testDisableAutoRepair(self):
    pool_kwargs = {
        'version':
            self.VERSION,
        'management':
            self.msgs.NodeManagement(
                autoRepair=True, autoUpgrade=True, upgradeOptions=None),
    }
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectSetNodePoolManagement(
        self.NODE_POOL_NAME,
        self.msgs.NodeManagement(
            autoRepair=False, autoUpgrade=True, upgradeOptions=None),
        response=self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    cmdbase = (
        self.node_pools_command_base.format(self.ZONE) +
        ' update {0} --cluster={1} --no-enable-autorepair ' +
        '--format=disable')
    result = self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.assertEqual(result.name, pool.name)
    self.assertEqual(result.management.autoRepair, False)
    self.assertEqual(result.management.autoUpgrade, True)
    self.AssertErrContains("""This will disable the autorepair feature for \
nodes. Please see \
https://cloud.google.com/kubernetes-engine/docs/node-auto-repair for more \
information on node autorepairs.
{{"ux": "PROGRESS_TRACKER", "message": "Updating node pool my-pool", "status": "SUCCESS"}}
Updated [https://container.googleapis.com/{0}/projects/fake-project-id/zones/us-central1-f/clusters/my-cluster/nodePools/my-pool].
""".format(self.API_VERSION))

  def testEnableAutoUpgrade(self):
    pool_kwargs = {
        'version':
            self.VERSION,
        'management':
            self.msgs.NodeManagement(
                autoRepair=None, autoUpgrade=None, upgradeOptions=None),
    }
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectSetNodePoolManagement(
        self.NODE_POOL_NAME,
        self.msgs.NodeManagement(
            autoRepair=None, autoUpgrade=True, upgradeOptions=None),
        response=self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    cmdbase = (
        self.node_pools_command_base.format(self.ZONE) +
        ' update {0} --cluster={1} --enable-autoupgrade ' + '--format=disable')
    result = self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.assertEqual(result.management.autoRepair, None)
    self.assertEqual(result.management.autoUpgrade, True)
    self.AssertErrContains("""{{"ux": "PROGRESS_TRACKER", "message": "Updating \
node pool my-pool", "status": "SUCCESS"}}
Updated [https://container.googleapis.com/{0}/projects/fake-project-id/zones\
/us-central1-f/clusters/my-cluster/nodePools/my-pool].
""".format(self.API_VERSION))

  def testDisableAutoUpgrade(self):
    pool_kwargs = {
        'version':
            self.VERSION,
        'management':
            self.msgs.NodeManagement(
                autoRepair=True, autoUpgrade=True, upgradeOptions=None),
    }
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectSetNodePoolManagement(
        self.NODE_POOL_NAME,
        self.msgs.NodeManagement(
            autoRepair=True, autoUpgrade=False, upgradeOptions=None),
        response=self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    cmdbase = (
        self.node_pools_command_base.format(self.ZONE) +
        ' update {0} --cluster={1} --no-enable-autoupgrade ' +
        '--format=disable')
    result = self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.assertEqual(result.management.autoRepair, True)
    self.assertEqual(result.management.autoUpgrade, False)
    self.AssertErrContains("""{{"ux": "PROGRESS_TRACKER", "message": "Updating \
node pool my-pool", "status": "SUCCESS"}}
Updated [https://container.googleapis.com/{0}/projects/fake-project-id/zones\
/us-central1-f/clusters/my-cluster/nodePools/my-pool].
""".format(self.API_VERSION))

  def testEnableAutoUpgradeWithUrlCluster(self):
    pool_kwargs = {
        'version':
            self.VERSION,
        'management':
            self.msgs.NodeManagement(
                autoRepair=None, autoUpgrade=None, upgradeOptions=None),
    }
    pool = self._MakeNodePool(**pool_kwargs)
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectSetNodePoolManagement(
        self.NODE_POOL_NAME,
        self.msgs.NodeManagement(
            autoRepair=None, autoUpgrade=True, upgradeOptions=None),
        response=self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    cmdbase = (
        self.node_pools_command_base.format(self.ZONE) +
        ' update {0} --cluster={1} --enable-autoupgrade ' + '--format=disable')
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
    result = self.Run(
        cmdbase.format(node_pool_ref.SelfLink(), cluster_ref.SelfLink()))
    self.assertEqual(result.management.autoRepair, None)
    self.assertEqual(result.management.autoUpgrade, True)
    self.AssertErrContains("""{{"ux": "PROGRESS_TRACKER", "message": "Updating \
node pool my-pool", "status": "SUCCESS"}}
Updated [https://container.googleapis.com/{0}/projects/fake-project-id/zones\
/us-central1-f/clusters/my-cluster/nodePools/my-pool].
""".format(self.API_VERSION))

  def testUpdateHttpError(self):
    pool = self._MakeNodePool(
        version=self.VERSION, management=self.msgs.NodeManagement())
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectSetNodePoolManagement(
        self.NODE_POOL_NAME,
        self.msgs.NodeManagement(
            autoRepair=None, autoUpgrade=True, upgradeOptions=None),
        exception=self.HttpError())
    with self.assertRaises(exceptions.HttpException):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' update {0} --cluster={1} --enable-autoupgrade'.format(
              self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains(
        'ResponseError: code=400, message=your request is bad '
        'and you should feel bad.')

  def testNoFlagsError(self):
    with self.AssertRaisesArgumentErrorRegexp('[Mm]ust be specified'):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' update {0} --cluster={1}'.format(self.NODE_POOL_NAME,
                                             self.CLUSTER_NAME))

  def testEnableAutoscaling(self):
    pool_kwargs = {}
    pool = self._MakeNodePool(**pool_kwargs)
    update = self.msgs.ClusterUpdate(
        desiredNodePoolId=self.NODE_POOL_NAME,
        desiredNodePoolAutoscaling=self.msgs.NodePoolAutoscaling(
            enabled=True, autoprovisioned=True, minNodeCount=3, maxNodeCount=5))
    cmdbase = (
        self.node_pools_command_base.format(self.ZONE) +
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
        'autoscaling':
            self.msgs.NodePoolAutoscaling(
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
    cmdbase = (
        self.node_pools_command_base.format(self.ZONE) +
        ' update {0} --cluster={1} --no-enable-autoscaling ')
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectUpdateCluster(
        cluster_name=self.CLUSTER_NAME,
        update=update,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))

  def testWorkloadMetadata(self):
    enum = self.messages.WorkloadMetadataConfig.ModeValueValuesEnum
    state_string_names = {
        enum.GCE_METADATA: 'GCE_METADATA',
        enum.GKE_METADATA: 'GKE_METADATA',
    }

    for from_state, to_state in itertools.product(state_string_names,
                                                  state_string_names):

      pool = self._MakeNodePool(
          version=self.VERSION,
          workloadMetadataConfig=self.messages.WorkloadMetadataConfig(
              mode=from_state),
      )

      self.ExpectUpdateNodePool(
          self.NODE_POOL_NAME,
          workload_metadata_config=self.messages.WorkloadMetadataConfig(
              mode=to_state,),
          response=self._MakeOperation(operationType=self.op_upgrade_nodes))
      self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
      self.ExpectGetNodePool(pool.name, response=pool)

      command = ('{command_base} update {node_pool} --cluster={cluster} '
                 '--workload-metadata={to_state}').format(
                     command_base=self.node_pools_command_base.format(
                         self.ZONE),
                     node_pool=pool.name,
                     cluster=self.CLUSTER_NAME,
                     to_state=state_string_names[to_state])

      self.Run(command)

  def testEnableAutoprovisioning(self):
    pool_kwargs = {
        'autoscaling':
            self.msgs.NodePoolAutoscaling(
                enabled=True,
                autoprovisioned=False,
                minNodeCount=3,
                maxNodeCount=5),
    }
    pool = self._MakeNodePool(**pool_kwargs)
    update = self.msgs.ClusterUpdate(
        desiredNodePoolId=self.NODE_POOL_NAME,
        desiredNodePoolAutoscaling=self.msgs.NodePoolAutoscaling(
            enabled=True, autoprovisioned=True, minNodeCount=0, maxNodeCount=5))
    cmdbase = (
        self.node_pools_command_base.format(self.ZONE) +
        ' update {0} --cluster={1} --enable-autoprovisioning')
    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectUpdateCluster(
        cluster_name=self.CLUSTER_NAME,
        update=update,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))

  def testNodeLocations(self):
    pool = self._MakeNodePool(
        version=self.VERSION, locations=['us-central1-a', 'us-central1-b'])
    cmdbase = (
        self.node_pools_command_base.format(self.ZONE) +
        ' update {0} --cluster={1} ' +
        '--node-locations=us-central1-a,us-central1-b')
    self.ExpectUpdateNodePool(
        self.NODE_POOL_NAME,
        locations=['us-central1-a', 'us-central1-b'],
        response=self._MakeOperation(operationType=self.op_upgrade_nodes))
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))

  @parameterized.parameters(
      ((3, 2), (4, 1), (4, 1)), ((3, None), (4, 1), (4, 1)),
      ((None, 2), (4, 1), (4, 1)), ((None, None), (4, 1), (4, 1)),
      (None, (4, 1), (4, 1)))
  def testSurgeUpgradeSettings(self, old_upgrade_settings,
                               patch_upgrade_settings,
                               expected_upgrade_settings):
    if old_upgrade_settings is None:
      pool = self._MakeNodePool(upgradeSettings=None)
    else:
      old_ms, old_mu = old_upgrade_settings
      pool = self._MakeNodePool(
          upgradeSettings=self._MakeUpgradeSettings(
              maxSurge=old_ms, maxUnavailable=old_mu))
    patch_ms, patch_mu = patch_upgrade_settings
    expected_ms, expected_mu = expected_upgrade_settings
    max_surge_arg = ('--max-surge-upgrade={}'.format(patch_ms)
                     if patch_ms is not None else '')
    max_unavailable_arg = ('--max-unavailable-upgrade={}'.format(patch_mu)
                           if patch_mu is not None else '')

    cmd = (
        self.node_pools_command_base.format(self.ZONE) +
        ' update {0} --cluster={1} {2} {3}'.format(
            self.NODE_POOL_NAME, self.CLUSTER_NAME, max_surge_arg,
            max_unavailable_arg))

    updated_upgrade_settings = self._MakeUpgradeSettings(
        maxSurge=expected_ms, maxUnavailable=expected_mu)

    self.ExpectGetNodePool(pool.name, response=pool)
    self.ExpectUpdateNodePool(
        self.NODE_POOL_NAME,
        zone=self.ZONE,
        upgrade_settings=updated_upgrade_settings,
        response=self._MakeNodePoolOperation())
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    self.Run(cmd)

  @parameterized.parameters((3, None), (None, 1))
  def testInvalidSurgeUpgradeSettings(self, max_surge, max_unavai):
    max_surge_arg = ('--max-surge-upgrade={}'.format(max_surge)
                     if max_surge is not None else '')
    max_unavailable_arg = ('--max-unavailable-upgrade={}'.format(max_unavai)
                           if max_unavai is not None else '')

    cmd = (
        self.node_pools_command_base.format(self.ZONE) +
        ' update {0} --cluster={1} {2} {3}'.format(
            self.NODE_POOL_NAME, self.CLUSTER_NAME, max_surge_arg,
            max_unavailable_arg))

    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run(cmd)
    self.AssertErrContains(c_util.INVALIID_SURGE_UPGRADE_SETTINGS)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpdateTestBeta(base.BetaTestBase, UpdateTestGA):
  """gcloud Beta track using container v1beta1 API."""

  def testWorkloadMetadataFromNode(self):
    enum = self.messages.WorkloadMetadataConfig.NodeMetadataValueValuesEnum
    state_string_names = {
        enum.EXPOSE: 'EXPOSED',
        enum.SECURE: 'SECURE',
        enum.GKE_METADATA_SERVER: 'GKE_METADATA_SERVER',
    }

    for from_state, to_state in itertools.product(state_string_names,
                                                  state_string_names):

      pool = self._MakeNodePool(
          version=self.VERSION,
          workloadMetadataConfig=self.messages.WorkloadMetadataConfig(
              nodeMetadata=from_state),
      )

      self.ExpectUpdateNodePool(
          self.NODE_POOL_NAME,
          workload_metadata_config=self.messages.WorkloadMetadataConfig(
              nodeMetadata=to_state,),
          response=self._MakeOperation(operationType=self.op_upgrade_nodes))
      self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
      self.ExpectGetNodePool(pool.name, response=pool)

      command = ('{command_base} update {node_pool} --cluster={cluster} '
                 '--workload-metadata-from-node={to_state}').format(
                     command_base=self.node_pools_command_base.format(
                         self.ZONE),
                     node_pool=pool.name,
                     cluster=self.CLUSTER_NAME,
                     to_state=state_string_names[to_state])

      self.Run(command)

  def testConflictingFlagsError(self):
    with self.AssertRaisesArgumentErrorRegexp('Exactly one of '):
      self.Run(
          self.node_pools_command_base.format(self.ZONE) +
          ' update {0} --cluster={1}'
          ' --enable-autoprovisioning --enable-autoupgrade'.format(
              self.NODE_POOL_NAME, self.CLUSTER_NAME))
    self.AssertErrContains('--enable-autoupgrade')
    self.AssertErrContains('--enable-autoprovisioning')

  def testNodeLocations(self):
    pool = self._MakeNodePool(
        version=self.VERSION, locations=['us-central1-a', 'us-central1-b'])
    cmdbase = (
        self.node_pools_command_base.format(self.ZONE) +
        ' update {0} --cluster={1} ' +
        '--node-locations=us-central1-a,us-central1-b')
    self.ExpectUpdateNodePool(
        self.NODE_POOL_NAME,
        locations=['us-central1-a', 'us-central1-b'],
        response=self._MakeOperation(operationType=self.op_upgrade_nodes))
    self.ExpectGetOperation(self._MakeNodePoolOperation(status=self.op_done))
    self.ExpectGetNodePool(pool.name, response=pool)
    self.Run(cmdbase.format(self.NODE_POOL_NAME, self.CLUSTER_NAME))


# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpdateTestAlpha(base.AlphaTestBase, UpdateTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""


if __name__ == '__main__':
  test_case.main()
