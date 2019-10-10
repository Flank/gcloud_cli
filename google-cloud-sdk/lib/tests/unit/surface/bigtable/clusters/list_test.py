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
"""Test of the 'list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.bigtable import arguments
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.command_lib.util.concepts import resource_completer_test_base
from tests.lib.surface.bigtable import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class ListCommandTest(base.BigtableV2TestBase, cli_test_base.CliTestBase,
                      resource_completer_test_base.ResourceCompleterBase):

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
                name=('projects/{}/instances/{}/clusters/{}'.format(
                    self.Project(), instance_ref.Name(), cluster_name)),
                location='projects/{}/locations/thezone'.format(self.Project()),
                defaultStorageType=(
                    self.msgs.Cluster.DefaultStorageTypeValueValuesEnum.SSD),
                state=self.msgs.Cluster.StateValueValuesEnum.READY,
                serveNodes=5)
        ]))

  def testList(self, track):
    self.track = track
    self.expectClusterList(self.instance_ref, 'thecluster')
    self.Run('bigtable clusters list --instances theinstance')

    self.AssertOutputEquals(
        'INSTANCE     NAME        ZONE     NODES  STORAGE  STATE\n'
        'theinstance  thecluster  thezone  5      SSD      READY\n')

  def testUri(self, track):
    self.track = track
    self.expectClusterList(self.instance_ref, 'thecluster')
    # Check that URI project is used for instance and list of clusters.
    self.Run('bigtable clusters list --instances {} --uri --project bogus'
             .format(self.instance_ref.RelativeName()))

    self.AssertOutputEquals(
        'https://bigtableadmin.googleapis.com/v2/'
        'projects/{}/instances/theinstance/clusters/thecluster\n'.format(
            self.Project()))

  def testListMultiple(self, track):
    self.track = track
    self.expectClusterList(self.instance_ref, 'thecluster')
    self.expectClusterList(self.other_instance_ref, 'theothercluster')
    self.Run('bigtable clusters list --instances theinstance,theotherinstance')

    self.AssertOutputEquals(
        'INSTANCE          NAME             ZONE     NODES  STORAGE  STATE\n'
        'theinstance       thecluster       thezone  5      SSD      READY\n'
        'theotherinstance  theothercluster  thezone  5      SSD      READY\n')

  def testListNoInstanceProvided(self, track):
    self.track = track
    self.clusters_list_mock.Expect(
        request=self.msgs.BigtableadminProjectsInstancesClustersListRequest(
            parent=util.GetInstanceRef('-').RelativeName()),
        response=self.msgs.ListClustersResponse(clusters=[
            self.msgs.Cluster(
                name=('projects/{}/instances/{}/clusters/{}'.format(
                    self.Project, 'theinstance', 'thecluster')),
                location='projects/{}/locations/thezone'.format(self.Project()),
                defaultStorageType=(
                    self.msgs.Cluster.DefaultStorageTypeValueValuesEnum.SSD),
                state=self.msgs.Cluster.StateValueValuesEnum.READY,
                serveNodes=5),
            self.msgs.Cluster(
                name=('projects/{}/instances/{}/clusters/{}'.format(
                    self.Project(), 'theotherinstance', 'theothercluster')),
                location='projects/{}/locations/thezone'.format(self.Project()),
                defaultStorageType=(
                    self.msgs.Cluster.DefaultStorageTypeValueValuesEnum.SSD),
                state=self.msgs.Cluster.StateValueValuesEnum.READY,
                serveNodes=5)
        ]))
    self.Run('bigtable clusters list')

    self.AssertOutputEquals(
        'INSTANCE          NAME             ZONE     NODES  STORAGE  STATE\n'
        'theinstance       thecluster       thezone  5      SSD      READY\n'
        'theotherinstance  theothercluster  thezone  5      SSD      READY\n')

  def testCompletion(self, track):
    self.track = track
    self.expectClusterList(self.instance_ref, 'thecluster')
    self.RunResourceCompleter(
        arguments.GetClusterResourceSpec(),
        'cluster',
        args={'--instance': 'theinstance'},
        expected_completions=['thecluster'])


if __name__ == '__main__':
  test_case.main()
