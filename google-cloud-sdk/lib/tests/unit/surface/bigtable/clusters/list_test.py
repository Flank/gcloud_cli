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
"""Test of the 'list' command."""

from googlecloudsdk.api_lib.bigtable import util
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.bigtable import base


class ListCommandTest(base.BigtableV2TestBase, cli_test_base.CliTestBase):

  def SetUp(self):
    self.clusters_list_mock = self.client.projects_instances_clusters.List
    self.instance_ref = util.GetInstanceRef('theinstance')
    self.other_instance_ref = util.GetInstanceRef('theotherinstance')

  def expectClusterList(self, instance_ref, cluster_name):
    self.clusters_list_mock.Expect(
        request=self.msgs.BigtableadminProjectsInstancesClustersListRequest(
            parent=instance_ref.RelativeName()),
        response=self.msgs.ListClustersResponse(clusters=[
            self.msgs.Cluster(
                name=('projects/theprojects/instances/'
                      '{}/clusters/{}'.format(instance_ref.Name(),
                                              cluster_name)),
                location='projects/theprojects/locations/thezone',
                defaultStorageType=(
                    self.msgs.Cluster.DefaultStorageTypeValueValuesEnum.SSD),
                state=self.msgs.Cluster.StateValueValuesEnum.READY,
                serveNodes=5)
        ]))

  def testList(self):
    self.expectClusterList(self.instance_ref, 'thecluster')
    self.RunBT('clusters list --instances theinstance')

    self.AssertOutputEquals(
        'INSTANCE     NAME        ZONE     NODES  STORAGE  STATE\n'
        'theinstance  thecluster  thezone  5      SSD      READY\n')

  def testUri(self):
    self.expectClusterList(self.instance_ref, 'thecluster')
    # Check that URI project is used for instance and list of clusters.
    self.RunBT('clusters list --instances {} --uri --project bogus'
               .format(self.instance_ref.RelativeName()))

    self.AssertOutputEquals(
        'https://bigtableadmin.googleapis.com/v2/'
        'projects/theprojects/instances/theinstance/clusters/thecluster\n')

  def testListMultiple(self):
    self.expectClusterList(self.instance_ref, 'thecluster')
    self.expectClusterList(self.other_instance_ref, 'theothercluster')
    self.RunBT('clusters list --instances theinstance,theotherinstance')

    self.AssertOutputEquals(
        'INSTANCE          NAME             ZONE     NODES  STORAGE  STATE\n'
        'theinstance       thecluster       thezone  5      SSD      READY\n'
        'theotherinstance  theothercluster  thezone  5      SSD      READY\n')

  def testListNoInstanceProvided(self):
    self.clusters_list_mock.Expect(
        request=self.msgs.BigtableadminProjectsInstancesClustersListRequest(
            parent=util.GetInstanceRef('-').RelativeName()),
        response=self.msgs.ListClustersResponse(clusters=[
            self.msgs.Cluster(
                name=('projects/theprojects/instances/'
                      '{}/clusters/{}'.format('theinstance',
                                              'thecluster')),
                location='projects/theprojects/locations/thezone',
                defaultStorageType=(
                    self.msgs.Cluster.DefaultStorageTypeValueValuesEnum.SSD),
                state=self.msgs.Cluster.StateValueValuesEnum.READY,
                serveNodes=5),
            self.msgs.Cluster(
                name=('projects/theprojects/instances/'
                      '{}/clusters/{}'.format('theotherinstance',
                                              'theothercluster')),
                location='projects/theprojects/locations/thezone',
                defaultStorageType=(
                    self.msgs.Cluster.DefaultStorageTypeValueValuesEnum.SSD),
                state=self.msgs.Cluster.StateValueValuesEnum.READY,
                serveNodes=5)
        ]))
    self.RunBT('clusters list')

    self.AssertOutputEquals(
        'INSTANCE          NAME             ZONE     NODES  STORAGE  STATE\n'
        'theinstance       thecluster       thezone  5      SSD      READY\n'
        'theotherinstance  theothercluster  thezone  5      SSD      READY\n')

  def testCompletion(self):
    self.expectClusterList(self.instance_ref, 'thecluster')
    self.RunCompletion('beta bigtable clusters update --instance theinstance t',
                       ['thecluster --project=theprojects'])


if __name__ == '__main__':
  test_case.main()
