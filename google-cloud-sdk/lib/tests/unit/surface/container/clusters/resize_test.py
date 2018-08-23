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

"""Test of the 'clusters resize' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.container import base


class ResizeTestGA(base.GATestBase, base.ClustersTestBase):
  """gcloud GA track using container v1 API."""

  def SetUp(self):
    self.api_mismatch = False

  def testResizeAborted(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('n')
    self.ExpectGetCluster(self._RunningClusterWithNodePool())
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' resize {0} --size 4'.format(self.CLUSTER_NAME))
    self.AssertErrContains('Aborted by user.')

  def testResizeWithSameNumberOfNodes(self):
    # TODO(b/27950609): enable this when we have current node count for
    # node pools.
    return
    # properties.VALUES.core.disable_prompts.Set(False)
    # self.ExpectGetCluster(self._RunningClusterWithNodePool())
    # self.ClearOutput()
    # self.ClearErr()
    # self.Run(self.clusters_command_base.format(self.ZONE) +
    #         ' resize {0} --size 3'.format(self.CLUSTER_NAME))
    # self.AssertErrContains('Cluster [my-cluster] already has a size of 3. '
    #                       'Please specify a different size.')

  def _ExpectResizeOperations(self, cluster, size, nodepool, zone=None):
    op = self._MakeOperation()
    if zone is not None:
      op.zone = zone
    self.ExpectResizeNodePool(nodepool.name, size, op, zone=zone)
    return [op]

  def _ExpectGetOperations(self, ops):
    for op in ops:
      doneop = self._MakeOperation(
          status=self.op_done,
          name=op.name,
          zone=op.zone,
          statusMessage=op.statusMessage)
      self.ExpectGetOperation(doneop)

  def _TestResizeMoreNodes(self, location):
    properties.VALUES.core.disable_prompts.Set(False)
    kwargs = {'zone': location}
    cluster = self._RunningClusterWithNodePool(**kwargs)
    pool = cluster.nodePools[0]
    self.ExpectGetCluster(cluster, zone=location)
    ops = self._ExpectResizeOperations(cluster, 4, pool, zone=location)
    self._ExpectGetOperations(ops)
    self.ClearOutput()
    self.ClearErr()
    if location == self.REGION:
      self.Run(self.regional_clusters_command_base.format(location) +
               ' resize {0} --size 4'.format(self.CLUSTER_NAME))
    else:
      self.Run(self.clusters_command_base.format(location) +
               ' resize {0} --size 4'.format(self.CLUSTER_NAME))
    if self.api_mismatch and location == self.REGION:
      self.AssertErrContains('You invoked')

  def testResizeMoreNodes(self):
    self.WriteInput('y')
    self._TestResizeMoreNodes(self.ZONE)

  def testResizeMoreNodesAsync(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    cluster = self._RunningClusterWithNodePool()
    pool = cluster.nodePools[0]
    self.ExpectGetCluster(cluster)
    self._ExpectResizeOperations(cluster, 4, pool)
    self.ClearOutput()
    self.ClearErr()
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' resize {0} --size 4 --async'.format(self.CLUSTER_NAME))

  def testResizeLessNodes(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    cluster = self._RunningClusterWithNodePool()
    pool = cluster.nodePools[0]
    self.ExpectGetCluster(cluster)
    ops = self._ExpectResizeOperations(cluster, 2, pool)
    self._ExpectGetOperations(ops)
    self.ClearOutput()
    self.ClearErr()
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' resize {0} --size 2'.format(self.CLUSTER_NAME))

  def testResizeError(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    cluster = self._RunningClusterWithNodePool()
    pool = cluster.nodePools[0]
    pool.instanceGroupUrls.append(self._MakeInstanceGroupUrl(
        self.PROJECT_ID, self.ZONE, cluster.name, 'other-group'))
    self.ExpectGetCluster(cluster)
    ops = self._ExpectResizeOperations(cluster, 2, pool)
    ops[0].statusMessage = 'some error'
    self._ExpectGetOperations(ops)
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(c_util.Error):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' resize {0} --size 2'.format(self.CLUSTER_NAME))

  def testResizeMultipleGroups(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    cluster = self._RunningClusterWithNodePool()
    pool = cluster.nodePools[0]
    pool.instanceGroupUrls.append(self._MakeInstanceGroupUrl(
        self.PROJECT_ID, self.ZONE, cluster.name, 'other-group'))
    self.ExpectGetCluster(cluster)
    ops = self._ExpectResizeOperations(cluster, 2, pool)
    self._ExpectGetOperations(ops)
    self.ClearOutput()
    self.ClearErr()
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' resize {0} --size 2'.format(self.CLUSTER_NAME))

  def testResizeMultiplePools(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    cluster = self._RunningClusterWithNodePool()
    pool2 = self._MakeNodePool(
        name='pool-to-resize',
        instanceGroupUrls=[
            self._MakeInstanceGroupUrl(
                self.PROJECT_ID,
                self.ZONE,
                cluster.name, 'pool-to-resize')])
    cluster.nodePools.append(pool2)
    self.ExpectGetCluster(cluster)
    ops = self._ExpectResizeOperations(cluster, 2, pool2)
    self._ExpectGetOperations(ops)
    self.ClearOutput()
    self.ClearErr()
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' resize {0} --node-pool {1} --size 2'.format(
                 cluster.name, pool2.name))

  def testResizeUnknownPool(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    cluster = self._RunningClusterWithNodePool()
    self.ExpectGetCluster(cluster)
    self.ClearOutput()
    self.ClearErr()

    with self.assertRaises(c_util.Error):
      self.Run(self.clusters_command_base.format(self.ZONE) +
               ' resize {0} --node-pool bar --size 2'.format(
                   cluster.name))
    self.AssertErrContains('No node pool named \'bar\' in {0}'.format(
        cluster.name))

  def testResizeMoreNodesRegional(self):
    self.WriteInput('y\ny')
    self._TestResizeMoreNodes(self.REGION)

  def testCanResizeAfterFailedGet(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput('y')
    location = self.ZONE
    kwargs = {'zone': location, 'nodePoolName': 'default-pool'}
    cluster = self._RunningClusterWithNodePool(**kwargs)
    self.ExpectGetCluster(
        cluster, exception=
        apitools_exceptions.HttpForbiddenError(
            {'status': 403, 'reason': 'missing permission'},
            'forbidden', 'foo.com/bar'))
    ops = self._ExpectResizeOperations(
        cluster, 4, cluster.nodePools[0], zone=location)
    self._ExpectGetOperations(ops)
    self.ClearOutput()
    self.ClearErr()
    self.Run(self.clusters_command_base.format(location) +
             ' resize {0} --size 4'.format(self.CLUSTER_NAME))
    self.AssertErrContains('Problem loading details of cluster')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class ResizeTestBeta(base.BetaTestBase, ResizeTestGA):
  """gcloud Beta track using container v1beta1 API."""


# Mixin class must come in first to have the correct multi-inheritance behavior.
class ResizeTestAlpha(base.AlphaTestBase, ResizeTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""


if __name__ == '__main__':
  test_case.main()
