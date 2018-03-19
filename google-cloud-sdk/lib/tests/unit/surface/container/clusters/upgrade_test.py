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

"""Tests for 'clusters upgrade' command."""

from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.command_lib.container import container_command_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.container import base


class UpgradeTestGA(base.TestBaseV1,
                    base.GATestBase,
                    base.ClustersTestBase):
  """gcloud GA track using container v1 API."""

  def SetUp(self):
    self.api_mismatch = False
    self.locations = [self.ZONE]

  def _TestUpgrade(self, update, flags, cluster_kwargs=None):
    for location in self.locations:
      self._TestUpgradeNoAsync(update, flags, location, cluster_kwargs)
      self._TestUpgradeAsync(update, flags, location, cluster_kwargs)

  def _TestUpgradeNoAsync(self, update, flags, location, cluster_kwargs=None):
    properties.VALUES.core.disable_prompts.Set(False)
    cluster_kwargs = cluster_kwargs or {}
    self.WriteInput('y\ny')
    name = u'tobeupgraded'
    cluster = self._RunningCluster(name=name, **cluster_kwargs)
    cluster.currentNodeVersion = '1.1.2'
    cluster.currentMasterVersion = '1.1.3'
    self.ExpectGetCluster(cluster, zone=location)
    if update.desiredNodeVersion:
      op_type = self.op_upgrade_nodes
    else:
      op_type = self.op_upgrade_master

    self.ExpectUpgradeCluster(
        cluster_name=name,
        update=update,
        response=self._MakeOperation(operationType=op_type),
        location=location)
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done,
                                                zone=location))
    if location == self.REGION:
      self.Run(self.regional_clusters_command_base.format(self.REGION) +
               ' upgrade {0} {1}'.format(name, flags))
    else:
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' upgrade {0} {1}'.format(name, flags))
    if self.api_mismatch and location == self.REGION:
      self.AssertErrContains('You invoked')
    self.AssertErrContains('Upgrading {cluster}'.format(cluster=name))

  def _TestUpgradeAsync(self, update, flags, location, cluster_kwargs=None):
    properties.VALUES.core.disable_prompts.Set(False)
    cluster_kwargs = cluster_kwargs or {}
    self.WriteInput('y')
    name = u'tobeupgraded'
    cluster = self._RunningCluster(name=name, **cluster_kwargs)
    cluster.currentNodeVersion = '1.1.2'
    cluster.currentMasterVersion = '1.1.3'
    self.ExpectGetCluster(cluster, zone=location)
    if update.desiredNodeVersion:
      op_type = self.op_upgrade_nodes
    else:
      op_type = self.op_upgrade_master
    self.ExpectUpgradeCluster(
        cluster_name=name,
        update=update,
        response=self._MakeOperation(operationType=op_type),
        location=location)
    if location == self.REGION:
      self.Run(self.regional_clusters_command_base.format(self.REGION) +
               ' upgrade {0} {1} --async'.format(name, flags))
    else:
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' upgrade {0} {1} --async'.format(name, flags))
    if self.api_mismatch and location == self.REGION:
      self.AssertErrContains('You invoked')

  def testUpgradeAborted(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('n')
    self.ExpectGetCluster(self._RunningCluster())
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' upgrade {0}'.format(self.CLUSTER_NAME))
    self.AssertErrContains('Aborted by user.')

  def testBadUpgrade(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    name = u'tobeupgraded'
    message = u'Bad upgrade, no cookie'
    update = self.msgs.ClusterUpdate(desiredNodeVersion='-')
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectUpgradeCluster(
        cluster_name=name,
        update=update,
        response=self._MakeOperation(operationType=self.op_upgrade_nodes))
    self.ExpectGetOperation(self._MakeOperation(
        status=self.op_done,
        errorMessage=message))
    with self.assertRaises(c_util.Error):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' upgrade {0}'.format(name))
    self.AssertErrContains('Upgrading {cluster}'.format(cluster=name))
    self.AssertErrContains('finished with error: {error}'.format(error=message))

  def testUpgradeNodesNoVersion(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredNodeVersion='-'),
        flags='')
    self.AssertErrContains('All nodes (3 nodes) of cluster [tobeupgraded]')
    self.AssertErrContains(
        'will be upgraded from version [1.1.2] to master version')

  def testUpgradeNodesWithVersion(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredNodeVersion='1.2.3'),
        flags='--cluster-version=1.2.3')
    self.AssertErrContains(
        'will be upgraded from version [1.1.2] to version [1.2.3]')

  def testUpgradeMasterNoVersion(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredMasterVersion='-'),
        flags='--master')

  def testUpgradeMasterWithVersion(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredMasterVersion='1.2.3'),
        flags='--cluster-version=1.2.3 --master')

  def testUpgradeNodesWithImageType(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredNodeVersion='-',
                                       desiredImageType='gci'),
        flags='--image-type=gci')

  def testUpgradeNodesWithImageTypeCustom(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(
            desiredNodeVersion='-',
            desiredImageType='custom',
            desiredImage='cos-63',
            desiredImageProject='gke-node-images'),
        flags=
        '--image-type=custom --image=cos-63 --image-project=gke-node-images')

  def testUpgradeNodesWithImageTypeAndVersion(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredNodeVersion='1.2.3',
                                       desiredImageType='gci'),
        flags='--cluster-version=1.2.3 --image-type=gci')

  def testUpgradeNodesWithNodePool(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredNodeVersion='1.2.3',
                                       desiredNodePoolId='NodePoolName'),
        flags='--node-pool=NodePoolName --cluster-version=1.2.3',
        cluster_kwargs={
            'nodePools': [{'name': 'default-pool', 'version': '1.1.2'},
                          {'name': 'NodePoolName', 'version': '1.1.4'}]
        })
    self.AssertErrContains(
        'will be upgraded from version [1.1.4] to version [1.2.3]')
    self.AssertErrContains(
        'All nodes in node pool [NodePoolName]')

  def testUpgradeNodesWithNonExistentNodePool(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    name = u'tobeupgraded'
    cluster_kwargs = {
        'nodePools': [{'name': 'default-pool', 'version': '1.1.2'},
                      {'name': 'NodePoolName', 'version': '1.1.4'}]}
    cluster = self._RunningCluster(name=name, **cluster_kwargs)
    self.ExpectGetCluster(cluster)
    with self.assertRaises(container_command_util.NodePoolError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' upgrade tobeupgraded --cluster-version=1.2.3 '
               '--node-pool=NotAPoolName')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpgradeTestBetaV1API(base.BetaTestBase, UpgradeTestGA):
  """gcloud Beta track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)
    self.api_mismatch = True
    self.locations = [self.ZONE, self.REGION]


# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpgradeTestBetaV1Beta1API(base.TestBaseV1Beta1, UpgradeTestBetaV1API):
  """gcloud Beta track using container v1beta1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)
    self.api_mismatch = False


# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpgradeTestAlphaV1API(base.AlphaTestBase, UpgradeTestBetaV1API):
  """gcloud Alpha track using container v1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(True)
    self.api_mismatch = True


# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpgradeTestAlphaV1Alpha1API(base.TestBaseV1Alpha1, UpgradeTestAlphaV1API,
                                  UpgradeTestBetaV1Beta1API):
  """gcloud Alpha track using container v1alpha1 API."""

  def SetUp(self):
    properties.VALUES.container.use_v1_api.Set(False)
    self.api_mismatch = False


if __name__ == '__main__':
  test_case.main()
