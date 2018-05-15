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
"""Tests for the sole-tenancy node-groups update subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base


class NodeGroupsCreateTest(sdk_test_base.WithFakeAuth,
                           cli_test_base.CliTestBase, waiter_test_base.Base):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.client = mock.Client(core_apis.GetClientClass('compute', 'alpha'))
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.client.Mock()
    self.messages = self.client.MESSAGES_MODULE
    self.addCleanup(self.client.Unmock)

    self.operation_status_enum = self.messages.Operation.StatusValueValuesEnum
    self.region = 'us-central1'
    self.zone = 'us-central1-a'

  def _GetOperationMessage(self, operation_name, status, resource_uri=None):
    return self.messages.Operation(
        name=operation_name,
        status=status,
        selfLink='https://www.googleapis.com/compute/alpha/projects/{0}/zones/'
                 '{1}/operations/{2}'.format(
                     self.Project(), self.zone, operation_name),
        targetLink=resource_uri)

  def _ExpectSetNodeTemplate(self, node_template, operation_suffix='X'):
    set_request = self.messages.NodeGroupsSetNodeTemplateRequest(
        nodeTemplate='projects/{0}/regions/{1}/nodeTemplates/{2}'.format(
            self.Project(), self.region, node_template))
    self.client.nodeGroups.SetNodeTemplate.Expect(
        self.messages.ComputeNodeGroupsSetNodeTemplateRequest(
            nodeGroupsSetNodeTemplateRequest=set_request,
            nodeGroup='my-node-group',
            project=self.Project(),
            zone=self.zone),
        self._GetOperationMessage(
            'operation-' + operation_suffix,
            self.operation_status_enum.PENDING))

  def _ExpectAddNodes(self, additional_node_count, operation_suffix='X'):
    self.client.nodeGroups.AddNodes.Expect(
        self.messages.ComputeNodeGroupsAddNodesRequest(
            nodeGroupsAddNodesRequest=self.messages.NodeGroupsAddNodesRequest(
                additionalNodeCount=additional_node_count),
            nodeGroup='my-node-group',
            project=self.Project(),
            zone=self.zone),
        self._GetOperationMessage(
            'operation-' + operation_suffix,
            self.operation_status_enum.PENDING))

  def _ExpectDeleteNodes(self, node_indexes, operation_suffix='X'):
    delete_request_class = self.messages.NodeGroupsDeleteNodesRequest
    self.client.nodeGroups.DeleteNodes.Expect(
        self.messages.ComputeNodeGroupsDeleteNodesRequest(
            nodeGroupsDeleteNodesRequest=delete_request_class(
                nodeIndexes=node_indexes),
            nodeGroup='my-node-group',
            project=self.Project(),
            zone=self.zone),
        self._GetOperationMessage(
            'operation-' + operation_suffix,
            self.operation_status_enum.PENDING))

  def _ExpectPollAndGet(self, operation_suffix='X'):
    self.client.zoneOperations.Get.Expect(
        self.messages.ComputeZoneOperationsGetRequest(
            operation='operation-' + operation_suffix,
            zone=self.zone,
            project=self.Project()),
        self._GetOperationMessage(
            'operation-' + operation_suffix,
            self.messages.Operation.StatusValueValuesEnum.DONE,
            'https://www.googleapis.com/compute/alpha/projects/{0}/zones/'
            '{1}/nodeGroups/{2}'.format(
                self.Project(), self.zone, 'my-node-group')))
    self.client.nodeGroups.Get.Expect(
        self.messages.ComputeNodeGroupsGetRequest(
            nodeGroup='my-node-group', project=self.Project(), zone=self.zone),
        self.messages.NodeGroup(name='my-node-group'))

  def testUpdate_SetNodeTemplate(self):
    self._ExpectSetNodeTemplate('new-template')
    self._ExpectPollAndGet()
    result = self.Run('compute sole-tenancy node-groups update my-node-group '
                      '--node-template new-template '
                      '--zone ' + self.zone)
    expected_node_group = self.messages.NodeGroup(name='my-node-group')
    self.assertEqual(expected_node_group, result)
    self.AssertErrContains(
        'Setting node template on [my-node-group] to [new-template].')

  def testUpdate_AddNodes(self):
    self._ExpectAddNodes(2)
    self._ExpectPollAndGet()
    self.Run('compute sole-tenancy node-groups update my-node-group '
             '--add-nodes 2 --zone ' + self.zone)
    self.AssertErrContains(
        'Adding [2] nodes to [my-node-group].')

  def testUpdate_DeleteNodes(self):
    self._ExpectDeleteNodes([2, 5])
    self._ExpectPollAndGet()
    self.Run('compute sole-tenancy node-groups update my-node-group '
             '--delete-nodes 2,5 --zone ' + self.zone)
    self.AssertErrContains(
        'Deleting nodes [2,5] in [my-node-group].')

  def testUpdate_SetTemplateAndDeleteNodes(self):
    self._ExpectSetNodeTemplate('new-template', 'X')
    self._ExpectDeleteNodes([2, 5], 'Y')
    self._ExpectPollAndGet('X')
    self._ExpectPollAndGet('Y')

    self.Run('compute sole-tenancy node-groups update my-node-group '
             '--node-template new-template '
             '--delete-nodes 2,5 --zone ' + self.zone)
    self.AssertErrContains(
        'Deleting nodes [2,5] in [my-node-group].')
    self.AssertErrContains(
        'Setting node template on [my-node-group] to [new-template].')

  def testUpdate_SetTemplateAndAddNodes(self):
    self._ExpectSetNodeTemplate('new-template', 'X')
    self._ExpectAddNodes(2, 'Y')
    self._ExpectPollAndGet('X')
    self._ExpectPollAndGet('Y')

    self.Run('compute sole-tenancy node-groups update my-node-group '
             '--node-template new-template '
             '--add-nodes 2 --zone ' + self.zone)
    self.AssertErrContains(
        'Adding [2] nodes to [my-node-group].')
    self.AssertErrContains(
        'Setting node template on [my-node-group] to [new-template].')

  def testUpdate_CannotAddAndDeleteNodes(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --add-nodes: At most one of --add-nodes | --delete-nodes '
        'may be specified.'):
      self.Run('compute sole-tenancy node-groups update my-node-group '
               '--add-nodes 2 --delete-nodes 2,5 --zone ' + self.zone)


if __name__ == '__main__':
  test_case.main()
