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
"""Tests for 'clusters list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.command_lib.container import constants
from googlecloudsdk.core import properties
from surface.container.clusters.upgrade import UpgradeHelpText
from tests.lib import test_case
from tests.lib.surface.container import base
from six.moves import zip  # pylint: disable=redefined-builtin


def _MockUri(project='test', zone='us-central1-a', name=None):
  return ('https://container.googleapis.com/v1/projects/{project}/zones/{zone}/'
          'clusters/{name}').format(
              project=project, zone=zone, name=name)


class ListTestGA(base.GATestBase, base.ClustersTestBase):
  """gcloud GA track using container v1 API."""

  def testListAggregate(self):
    clusters = [
        self._MakeCluster(
            name='cluster1',
            currentNodeCount=4,
            status=self.running,
            statusMessage='Running',
            endpoint='1.1.1.1',
            zone='zone1'),
        self._MakeCluster(
            name='cluster2',
            initialNodeCount=5,
            status=self.provisioning,
            statusMessage='Provisioning',
            endpoint='2.2.2.2',
            zone='zone2'),
        self._MakeCluster(
            name='cluster3',
            currentNodeCount=6,
            initialNodeCount=7,
            status=self.stopping,
            statusMessage='Stopping',
            endpoint='3.3.3.3',
            zone=self.ZONE),
        self._MakeCluster(
            name='update-cluster',
            status=self.reconciling,
            statusMessage='Reconciling',
            endpoint='7.7.7.7',
            zone='random-zone'),
    ]
    # Test a cluster with no node config
    no_node_config_cluster = self._MakeCluster(
        name='no_node_config',
        status=self.running,
        statusMessage='Running',
        endpoint='1.1.1.1',
        zone='zone1')
    no_node_config_cluster.nodeConfig = None
    clusters.append(no_node_config_cluster)
    self.ExpectListClusters(clusters)
    self.Run(self.COMMAND_BASE + ' clusters list')
    self.AssertOutputEquals("""\
NAME LOCATION MASTER_VERSION MASTER_IP MACHINE_TYPE NODE_VERSION NUM_NODES STATUS
update-cluster random-zone 7.7.7.7 RECONCILING
cluster3 us-central1-f 3.3.3.3 6 STOPPING
cluster1 zone1 1.1.1.1 4 RUNNING
no_node_config zone1 1.1.1.1 RUNNING
cluster2 zone2 2.2.2.2 5 PROVISIONING
""", normalize_space=True)

  def testListMissing(self):
    clusters = [
        self._MakeCluster(
            name='cluster1',
            status=self.running,
            statusMessage='Running',
            endpoint='1.1.1.1',
            zone='zone1'),
        self._MakeCluster(
            name='cluster2',
            status=self.provisioning,
            statusMessage='Provisioning',
            endpoint='2.2.2.2',
            zone='zone2'),
    ]
    self.ExpectListClusters(clusters, missing=['zonefoo', 'zonebar'])
    self.Run(self.COMMAND_BASE + ' clusters list')
    for cluster in clusters:
      self.AssertOutputContains(str(cluster.endpoint))
      self.AssertOutputContains(str(cluster.status))
    self.AssertErrContains(
        'The following zones did not respond: zonefoo, zonebar. '
        'List results may be incomplete.')

  def testListJsonOutput(self):

    def _SortKey(cluster):
      return (cluster.zone, cluster.name)

    # Reverse sorted clusters on zone then name
    clusters = [
        self._MakeCluster(
            name='cluster4',
            status=self.provisioning,
            statusMessage='Provisioning',
            endpoint='2.2.2.2',
            zone='zone2',
            selfLink=_MockUri('cluster4')),
        self._MakeCluster(
            name='cluster3',
            status=self.provisioning,
            statusMessage='Provisioning',
            endpoint='2.2.2.2',
            zone='zone2',
            selfLink=_MockUri('cluster3')),
        self._MakeCluster(
            name='cluster2',
            status=self.running,
            statusMessage='Running',
            endpoint='1.1.1.1',
            zone='zone1',
            selfLink=_MockUri('cluster2')),
        self._MakeCluster(
            name='cluster1',
            status=self.running,
            statusMessage='Running',
            endpoint='1.1.1.1',
            zone='zone1',
            selfLink=_MockUri('cluster1')),
    ]
    self.ExpectListClusters(clusters)
    self.Run(self.COMMAND_BASE + ' clusters list --format=json')
    json_clusters = json.loads(self.GetOutput())
    n = len(clusters)
    self.assertEqual(n, len(json_clusters))
    sorted_clusters = sorted(clusters, key=_SortKey)
    for json_cluster, cluster in zip(json_clusters, sorted_clusters):
      self.assertEqual(json_cluster['name'], cluster.name)
      self.AssertOutputContains(json_cluster['endpoint'], cluster.endpoint)
      self.AssertOutputContains(json_cluster['status'], cluster.status)
      self.AssertOutputContains(json_cluster['selfLink'], cluster.selfLink)

  def testListUriFlagOutput(self):
    # Reverse sorted clusters on zone then name
    clusters = [
        self._MakeCluster(
            name='cluster4',
            status=self.provisioning,
            statusMessage='Provisioning',
            endpoint='2.2.2.2',
            zone='zone2',
            selfLink=_MockUri('cluster4')),
        self._MakeCluster(
            name='cluster3',
            status=self.provisioning,
            statusMessage='Provisioning',
            endpoint='2.2.2.2',
            zone='zone2',
            selfLink=_MockUri('cluster3')),
        self._MakeCluster(
            name='cluster2',
            status=self.running,
            statusMessage='Running',
            endpoint='1.1.1.1',
            zone='zone1',
            selfLink=_MockUri('cluster2')),
        self._MakeCluster(
            name='cluster1',
            status=self.running,
            statusMessage='Running',
            endpoint='1.1.1.1',
            zone='zone1',
            selfLink=_MockUri('cluster1')),
    ]
    self.ExpectListClusters(clusters)
    self.Run(self.COMMAND_BASE + ' clusters list --uri')
    for cluster in clusters:
      self.AssertOutputContains(cluster.selfLink)

  def testListOldVersion(self):
    self.ExpectListClusters(
        [
            self._MakeCluster(
                currentNodeVersion='1.1.1', currentMasterVersion='1.2.2')
        ],
        zone=self.ZONE)
    self.Run(self.clusters_command_base.format(self.ZONE) + ' list')
    self.AssertErrContains(UpgradeHelpText.UPGRADE_AVAILABLE)
    self.AssertErrContains(UpgradeHelpText.UPGRADE_COMMAND.format(name='NAME'))
    self.AssertErrNotContains(UpgradeHelpText.UNSUPPORTED)
    self.AssertErrNotContains(UpgradeHelpText.SUPPORT_ENDING)
    self.AssertOutputContains('1.1.1 *')

  def testListSupportEndingVersion(self):
    self.ExpectListClusters(
        [
            self._MakeCluster(
                currentNodeVersion='1.1.1', currentMasterVersion='1.3.2')
        ],
        zone=self.ZONE)
    self.Run(self.clusters_command_base.format(self.ZONE) + ' list')
    self.AssertErrContains(UpgradeHelpText.SUPPORT_ENDING)
    self.AssertErrContains(UpgradeHelpText.UPGRADE_COMMAND.format(name='NAME'))
    self.AssertErrNotContains(UpgradeHelpText.UNSUPPORTED)
    self.AssertErrNotContains(UpgradeHelpText.UPGRADE_AVAILABLE)
    self.AssertOutputContains('1.1.1 **')

  def testListUnsupportedVersion(self):
    self.ExpectListClusters(
        [
            self._MakeCluster(
                currentNodeVersion='1.1.1', currentMasterVersion='1.4.2')
        ],
        zone=self.ZONE)
    self.Run(self.clusters_command_base.format(self.ZONE) + ' list')
    self.AssertErrContains(UpgradeHelpText.UNSUPPORTED)
    self.AssertErrContains(UpgradeHelpText.UPGRADE_COMMAND.format(name='NAME'))
    self.AssertErrNotContains(UpgradeHelpText.UPGRADE_AVAILABLE)
    self.AssertErrNotContains(UpgradeHelpText.SUPPORT_ENDING)
    self.AssertOutputContains('1.1.1 ***')

  def testListOneZone(self):
    self.ExpectListClusters([self._RunningCluster()], zone=self.ZONE)
    self.Run(self.clusters_command_base.format(self.ZONE) + ' list')
    self.AssertOutputContains(self.ENDPOINT)
    self.AssertOutputContains(str(self.running))

  def testListOneRegion(self):
    kwargs = {'zone': self.REGION}
    self.ExpectListClusters([self._RunningCluster(**kwargs)], zone=self.REGION)
    self.Run(self.regional_clusters_command_base.format(self.REGION) + ' list')
    self.AssertOutputContains(self.ENDPOINT)
    self.AssertOutputContains(str(self.running))

  def testListMissingProject(self):
    properties.VALUES.core.project.Set(None)
    with self.assertRaises(properties.RequiredPropertyError):
      self.Run(self.COMMAND_BASE + ' clusters list')

  def testListNoNodePools(self):
    self.ExpectListClusters([self._MakeCluster(nodePools=[])], zone=self.ZONE)
    self.Run(self.clusters_command_base.format(self.ZONE) + ' list')
    self.AssertOutputContains('-')

  def testListAlphaClusters(self):
    cluster_kwargs = {
        'enableKubernetesAlpha': True,
        'expireTime': base.format_date_time('P30D'),
    }
    self.ExpectListClusters(
        [self._RunningClusterForVersion('1.3.5', **cluster_kwargs)])
    self.Run(self.COMMAND_BASE + ' clusters list')
    self.AssertOutputContains('1.3.5 ALPHA (29 days left)  ')

  def testListExpiringClusters(self):
    new_alpha = {
        'enableKubernetesAlpha': True,
        'expireTime': base.format_date_time('P30D'),
    }
    expiring = {
        'expireTime': base.format_date_time('P10D'),
    }
    # In practice version skewed alpha clusters will not exist, but if they did,
    # we should not print upgrade hints for them.
    skew_alpha = {
        'enableKubernetesAlpha': True,
        'currentNodeVersion': '1.3.3',
    }
    self.ExpectListClusters([
        self._RunningClusterForVersion('1.3.5', **new_alpha),
        self._RunningClusterForVersion('1.3.6', **expiring),
        self._RunningClusterForVersion('1.3.4', **skew_alpha),
    ])
    self.Run(self.COMMAND_BASE + ' clusters list')
    self.AssertOutputContains('1.3.5 ALPHA (29 days left)  ')
    self.AssertOutputContains('1.3.6 (! 9 days left !)  ')
    self.AssertOutputContains('1.3.4 ALPHA  ')
    self.AssertOutputContains('1.3.3  ')
    self.AssertErrNotContains(UpgradeHelpText.UPGRADE_COMMAND)
    self.AssertErrContains(constants.EXPIRE_WARNING)

  def testDegradedClusters(self):
    self.ExpectListClusters([self._MakeCluster(status=self.degraded)])
    self.Run(self.COMMAND_BASE + ' clusters list')
    self.AssertOutputContains(str(self.degraded))
    self.AssertOutputContains(str('DEGRADED'))
    self.AssertErrContains('Missing edit permissions on project')


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class ListTestBeta(base.BetaTestBase, ListTestGA):
  """gcloud Beta track using container v1beta1 API."""

  def testDegradedClusters(self):
    code = self.messages.StatusCondition.CodeValueValuesEnum.GCE_STOCKOUT
    message = 'test error message'
    self.ExpectListClusters([
        self._MakeCluster(
            status=self.degraded,
            conditions=[
                self.messages.StatusCondition(
                    code=code,
                    message=message,
                ),
            ]),
    ])
    self.Run(self.COMMAND_BASE + ' clusters list')
    self.AssertOutputContains(str(self.degraded))
    self.AssertOutputContains(str('DEGRADED'))
    self.AssertErrContains(str(code))
    self.AssertErrContains(message)


# Mixin class must come in first to have the correct multi-inheritance behavior.
class ListTestAlphaV1Alpha1API(base.AlphaTestBase, ListTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""


if __name__ == '__main__':
  test_case.main()
