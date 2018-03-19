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

"""Unit tests for bigtable arguments module."""

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import properties
from tests.lib import completer_test_base
from tests.lib.surface.bigtable import base


class CompleterCommandTest(completer_test_base.CompleterBase):

  def testClusterCompleterCommand(self):
    self.RunCompleter(
        arguments.ClusterCompleter,
        command_only=True,
        expected_command=[
            'beta', 'bigtable', 'clusters', 'list', '--uri', '--quiet',
            '--format=disable', '--instances=my-instance',
        ],
        args={
            '--id': 'my-id',
            '--instances': 'my-instance',
        },
    )

  def testClusterCompleterCommandWithProject(self):
    self.RunCompleter(
        arguments.ClusterCompleter,
        command_only=True,
        expected_command=[
            'beta', 'bigtable', 'clusters', 'list', '--uri', '--quiet',
            '--format=disable', '--project=my-project',
            '--instances=my-instance',
        ],
        args={
            '--id': 'my-id',
            '--instances': 'my-instance',
            '--project': 'my-project',
        },
    )

  def testInstanceCompleterCommand(self):
    self.RunCompleter(
        arguments.InstanceCompleter,
        command_only=True,
        expected_command=[
            'beta', 'bigtable', 'instances', 'list', '--uri', '--quiet',
            '--format=disable',
        ],
        args={
            '--id': 'my-id',
        },
    )

  def testInstanceCompleterCommandWithProject(self):
    self.RunCompleter(
        arguments.InstanceCompleter,
        command_only=True,
        expected_command=[
            'beta', 'bigtable', 'instances', 'list', '--uri', '--quiet',
            '--format=disable', '--project=my-project',
        ],
        args={
            '--id': 'my-id',
            '--project': 'my-project',
        },
    )


class InstancesClustersCompletionTest(base.BigtableV2TestBase,
                                      completer_test_base.CompleterBase):

  def SetUp(self):
    self.clusters_list_mock = self.client.projects_instances_clusters.List
    self.instance_ref = util.GetInstanceRef('theinstance')

  def testClusterCompletion(self):
    self.clusters_list_mock.Expect(
        request=self.msgs.BigtableadminProjectsInstancesClustersListRequest(
            parent=self.instance_ref.RelativeName()),
        response=self.msgs.ListClustersResponse(clusters=[self.msgs.Cluster(
            name=('projects/theprojects/instances/'
                  'theinstance/clusters/thecluster'),
            location='projects/theprojects/locations/thezone',
            defaultStorageType=(
                self.msgs.Cluster.DefaultStorageTypeValueValuesEnum.SSD),
            state=self.msgs.Cluster.StateValueValuesEnum.READY,
            serveNodes=5)]))
    self.RunCompleter(
        arguments.ClusterCompleter,
        expected_command=[
            'beta', 'bigtable', 'clusters', 'list', '--uri', '--quiet',
            '--format=disable', '--instances=theinstance',
        ],
        expected_completions=['thecluster'],
        cli=self.cli,
        args={
            '--id': 'my-id',
            '--instances': 'theinstance',
        },
    )


class InstanceCompletionTest(base.BigtableV2TestBase,
                             completer_test_base.CompleterBase):

  def SetUp(self):
    self.svc = self.client.projects_instances.List
    self.msg = self.msgs.BigtableadminProjectsInstancesListRequest(
        parent='projects/' + self.Project())

  def testInstanceCompletion(self):
    properties.VALUES.core.print_completion_tracebacks.Set(True)
    self.svc.Expect(
        request=self.msg,
        response=self.msgs.ListInstancesResponse(instances=[self.msgs.Instance(
            name='projects/theprojects/instances/theinstance',
            displayName='thedisplayname',
            state=self.msgs.Instance.StateValueValuesEnum.READY)]))
    self.RunCompleter(
        arguments.InstanceCompleter,
        expected_command=[
            'beta', 'bigtable', 'instances', 'list', '--uri', '--quiet',
            '--format=disable',
        ],
        expected_completions=['theinstance'],
        cli=self.cli,
        args={
            '--id': 'my-id',
        },
    )


if __name__ == '__main__':
  completer_test_base.main()
