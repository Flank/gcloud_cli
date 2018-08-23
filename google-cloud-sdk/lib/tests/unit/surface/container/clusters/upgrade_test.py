# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.command_lib.container import container_command_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.container import base


class UpgradeTestGA(parameterized.TestCase,
                    base.GATestBase,
                    base.ClustersTestBase):
  """gcloud GA track using container v1 API."""

  def SetUp(self):
    self.locations = [self.ZONE, self.REGION]

  def _TestUpgrade(self, update, flags, cluster_kwargs=None):
    for location in self.locations:
      self._TestUpgradeNoAsync(update, flags, location, cluster_kwargs)
      self._TestUpgradeAsync(update, flags, location, cluster_kwargs)

  def _TestUpgradeNoAsync(self, update, flags, location, cluster_kwargs=None):
    properties.VALUES.core.disable_prompts.Set(False)
    cluster_kwargs = cluster_kwargs or {}
    self.WriteInput('y\ny')
    name = 'tobeupgraded'
    cluster = self._RunningCluster(name=name, **cluster_kwargs)
    cluster.currentNodeVersion = '1.1.2'
    cluster.currentMasterVersion = '1.1.3'
    self.ExpectGetCluster(cluster, zone=location)
    self.ExpectGetServerConfig(location)
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
    self.AssertErrContains('Upgrading {cluster}'.format(cluster=name))

  def _TestUpgradeAsync(self, update, flags, location, cluster_kwargs=None):
    properties.VALUES.core.disable_prompts.Set(False)
    cluster_kwargs = cluster_kwargs or {}
    self.WriteInput('y')
    name = 'tobeupgraded'
    cluster = self._RunningCluster(name=name, **cluster_kwargs)
    cluster.currentNodeVersion = '1.1.2'
    cluster.currentMasterVersion = '1.1.3'
    self.ExpectGetCluster(cluster, zone=location)
    self.ExpectGetServerConfig(location)
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

  def testUpgradeAborted(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('n')
    self.ExpectGetCluster(self._RunningCluster())
    self.ExpectGetServerConfig(self.locations[0])
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' upgrade {0}'.format(self.CLUSTER_NAME))
    self.AssertErrContains('Aborted by user.')

  def testBadUpgrade(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    name = 'tobeupgraded'
    message = 'Bad upgrade, no cookie'
    update = self.msgs.ClusterUpdate(desiredNodeVersion='-')
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectGetServerConfig(self.locations[0])
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

  def testUpgradeNodesGetClusterFailure(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y\ny')
    name = 'tobeupgraded'
    location = self.locations[0]
    cluster = self._RunningCluster(name=name)
    cluster.currentNodeVersion = '1.1.2'
    cluster.currentMasterVersion = '1.1.3'
    update = self.msgs.ClusterUpdate(desiredNodeVersion='-')
    flags = ''

    self.ExpectGetCluster(cluster, base.UNAUTHORIZED_ERROR)
    self.ExpectGetServerConfig(location)
    self.ExpectUpgradeCluster(
        cluster_name=name,
        update=update,
        response=self._MakeOperation(operationType=self.op_upgrade_nodes))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done,
                                                zone=location))

    if location == self.REGION:
      self.Run(self.regional_clusters_command_base.format(self.REGION) +
               ' upgrade {0} {1}'.format(name, flags))
    else:
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' upgrade {0} {1}'.format(name, flags))

    self.AssertErrContains('All nodes of cluster [tobeupgraded] will be '
                           'upgraded from its current version '
                           'to the master version')

  def testUpgradeMasterGetClusterFailure(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y\ny')
    name = 'tobeupgraded'
    location = self.locations[0]
    cluster = self._RunningCluster(name=name)
    cluster.currentNodeVersion = '1.1.2'
    cluster.currentMasterVersion = '1.1.3'
    update = self.msgs.ClusterUpdate(desiredMasterVersion='-')
    flags = '--master'

    self.ExpectGetCluster(cluster,
                          exception=base.UNAUTHORIZED_ERROR)
    self.ExpectGetServerConfig(location)
    self.ExpectUpgradeCluster(
        cluster_name=name,
        update=update,
        response=self._MakeOperation(operationType=self.op_upgrade_nodes))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done,
                                                zone=location))

    if location == self.REGION:
      self.Run(self.regional_clusters_command_base.format(self.REGION) +
               ' upgrade {0} {1}'.format(name, flags))
    else:
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' upgrade {0} {1}'.format(name, flags))

    self.AssertErrContains('Master of cluster [tobeupgraded] will be upgraded '
                           'from its current version to version [1.2.3]')

  def testUpgradeNodesGetServerConfigFailure(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y\ny')
    name = 'tobeupgraded'
    location = self.locations[0]
    cluster = self._RunningCluster(name=name)
    cluster.currentNodeVersion = '1.1.2'
    cluster.currentMasterVersion = '1.1.3'
    update = self.msgs.ClusterUpdate(desiredNodeVersion='-')
    flags = ''

    self.ExpectGetCluster(cluster)
    self.ExpectGetServerConfig(location,
                               exception=base.UNAUTHORIZED_ERROR)
    self.ExpectUpgradeCluster(
        cluster_name=name,
        update=update,
        response=self._MakeOperation(operationType=self.op_upgrade_nodes))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done,
                                                zone=location))

    if location == self.REGION:
      self.Run(self.regional_clusters_command_base.format(self.REGION) +
               ' upgrade {0} {1}'.format(name, flags))
    else:
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' upgrade {0} {1}'.format(name, flags))

    self.AssertErrContains('All nodes (3 nodes) of cluster [tobeupgraded] '
                           'will be upgraded from version [1.1.2] '
                           'to version [1.1.3]')

  def testUpgradeMasterGetServerConfigFailure(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y\ny')
    name = 'tobeupgraded'
    location = self.locations[0]
    cluster = self._RunningCluster(name=name)
    cluster.currentNodeVersion = '1.1.2'
    cluster.currentMasterVersion = '1.1.3'
    update = self.msgs.ClusterUpdate(desiredMasterVersion='-')
    flags = '--master'

    self.ExpectGetCluster(cluster)
    self.ExpectGetServerConfig(location, base.UNAUTHORIZED_ERROR)
    self.ExpectUpgradeCluster(
        cluster_name=name,
        update=update,
        response=self._MakeOperation(operationType=self.op_upgrade_nodes))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done,
                                                zone=location))

    if location == self.REGION:
      self.Run(self.regional_clusters_command_base.format(self.REGION) +
               ' upgrade {0} {1}'.format(name, flags))
    else:
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' upgrade {0} {1}'.format(name, flags))

    self.AssertErrContains('Master of cluster [tobeupgraded] '
                           'will be upgraded from version [1.1.3] '
                           'to the default cluster version')

  def testUpgradeNodesNoVersion(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredNodeVersion='-'),
        flags='')
    self.AssertErrContains('All nodes (3 nodes) of cluster [tobeupgraded] '
                           'will be upgraded from version [1.1.2] '
                           'to version [1.1.3]')

  def testUpgradeNodesWithVersion(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredNodeVersion='1.2.3'),
        flags='--cluster-version=1.2.3')
    self.AssertErrContains('All nodes (3 nodes) of cluster [tobeupgraded] '
                           'will be upgraded from version [1.1.2] '
                           'to version [1.2.3]')

  def testUpgradeNodesSameVersion(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredNodeVersion='1.1.2'),
        flags='--cluster-version=1.1.2')
    self.AssertErrContains('All nodes (3 nodes) of cluster [tobeupgraded] '
                           'will be upgraded from version [1.1.2] '
                           'to version [1.1.2]')

  def testUpgradeMasterNoVersion(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredMasterVersion='-'),
        flags='--master')
    self.AssertErrContains('Master of cluster [tobeupgraded] will be upgraded '
                           'from version [1.1.3] to version [1.2.3]')

  def testUpgradeMasterWithVersion(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredMasterVersion='1.3.2'),
        flags='--cluster-version=1.3.2 --master')
    self.AssertErrContains('Master of cluster [tobeupgraded] will be upgraded '
                           'from version [1.1.3] to version [1.3.2]')

  def testUpgradeMasterSameVersion(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredMasterVersion='1.1.3'),
        flags='--cluster-version=1.1.3 --master')
    self.AssertErrContains('Master of cluster [tobeupgraded] will be upgraded '
                           'from version [1.1.3] to version [1.1.3]')

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
    self.AssertErrContains('All nodes in node pool [NodePoolName] '
                           'of cluster [tobeupgraded] '
                           'will be upgraded from version [1.1.4] '
                           'to version [1.2.3]')

  def testUpgradeNodesWithNonExistentNodePool(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    name = 'tobeupgraded'
    cluster_kwargs = {
        'nodePools': [{'name': 'default-pool', 'version': '1.1.2'},
                      {'name': 'NodePoolName', 'version': '1.1.4'}]}
    cluster = self._RunningCluster(name=name, **cluster_kwargs)
    self.ExpectGetCluster(cluster)
    self.ExpectGetServerConfig(self.locations[0])
    with self.assertRaises(container_command_util.NodePoolError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' upgrade tobeupgraded --cluster-version=1.2.3 '
               '--node-pool=NotAPoolName')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpgradeTestBeta(base.BetaTestBase, UpgradeTestGA):
  """gcloud Beta track using container v1beta1 API."""


# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpgradeTestAlpha(base.AlphaTestBase, UpgradeTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""

  @parameterized.parameters(
      0, -1, 21
  )
  def testUpgradeNodesWithConcurrentNodeCountError(self, concurrent_node_count):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' upgrade {0} --concurrent-node-count={1}'.format(
                   self.CLUSTER_NAME,
                   concurrent_node_count))
    self.AssertErrContains('argument --concurrent-node-count:')

  def testUpgradeNodesWithConcurrentNodeCountTwoNodes(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredNodeVersion='-',
                                       concurrentNodeCount=2),
        flags='--concurrent-node-count=2')
    self.AssertErrContains(' nodes will be upgraded at a time.')

  def testUpgradeNodesWithNodePoolWithConcurrentNodeCountFourNodes(self):
    self._TestUpgrade(
        update=self.msgs.ClusterUpdate(desiredNodeVersion='1.2.3',
                                       desiredNodePoolId='NodePoolName',
                                       concurrentNodeCount=4),
        flags=('--node-pool=NodePoolName --cluster-version=1.2.3 '
               '--concurrent-node-count=4'),
        cluster_kwargs={
            'nodePools': [{'name': 'default-pool', 'version': '1.1.2'},
                          {'name': 'NodePoolName', 'version': '1.1.4'}]
        })
    self.AssertErrContains(' nodes will be upgraded at a time.')


if __name__ == '__main__':
  test_case.main()
