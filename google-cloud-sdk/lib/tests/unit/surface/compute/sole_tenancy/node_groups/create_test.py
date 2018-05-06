# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for the sole-tenancy node-groups delete subcommand."""
from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class NodeGroupsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)
    self.region = 'us-central1'
    self.zone = 'us-central1-a'

  def _ExpectCreate(self, node_group, target_size):
    request = self.messages.ComputeNodeGroupsInsertRequest(
        project=self.Project(),
        zone=self.zone,
        nodeGroup=node_group,
        initialNodeCount=target_size)
    self.make_requests.side_effect = [[node_group]]
    return request

  def _CreateNodeGroup(self, name, description, node_template):
    node_template_self_link = (
        'https://www.googleapis.com/compute/alpha/projects/{project}/regions/'
        '{region}/nodeTemplates/{name}'.format(
            project=self.Project(), region=self.region, name=node_template))
    node_group = self.messages.NodeGroup(
        name=name,
        description=description,
        nodeTemplate=node_template_self_link)
    return node_group

  def testCreate_AllOptions(self):
    node_group = self._CreateNodeGroup(
        name='my-node-group',
        description='Frontend Group',
        node_template='my-template')
    request = self._ExpectCreate(node_group, 3)

    result = self.Run(
        'compute sole-tenancy node-groups create my-node-group '
        '--node-template my-template --target-size 3 '
        '--description "Frontend Group" --zone ' + self.zone)

    self.CheckRequests([(self.compute.nodeGroups, 'Insert', request)])
    self.assertEqual(result, node_group)

  def testCreate_NodeTemplateRelativeName(self):
    node_group = self._CreateNodeGroup(
        name='my-node-group',
        description='Frontend Group',
        node_template='my-template')
    request = self._ExpectCreate(node_group, 3)

    result = self.Run(
        'compute sole-tenancy node-groups create my-node-group '
        '--node-template '
        '  projects/{project}/regions/{region}/nodeTemplates/my-template '
        '--target-size 3 --description "Frontend Group" --zone {zone}'
        .format(project=self.Project(), region=self.region, zone=self.zone))

    self.CheckRequests([(self.compute.nodeGroups, 'Insert', request)])
    self.assertEqual(result, node_group)


if __name__ == '__main__':
  test_case.main()
