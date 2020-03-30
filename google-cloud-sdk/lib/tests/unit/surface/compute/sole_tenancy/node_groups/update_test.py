# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base


class NodeGroupsUpdateTest(sdk_test_base.WithFakeAuth,
                           cli_test_base.CliTestBase, waiter_test_base.Base):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.client = mock.Client(core_apis.GetClientClass('compute',
                                                       self.api_version))
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
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
        selfLink='https://compute.googleapis.com/compute/{0}/projects/{1}/zones/'
        '{2}/operations/{3}'.format(self.api_version, self.Project(), self.zone,
                                    operation_name),
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

  def _ExpectDeleteNodes(self, node_names, operation_suffix='X'):
    delete_request_class = self.messages.NodeGroupsDeleteNodesRequest
    self.client.nodeGroups.DeleteNodes.Expect(
        self.messages.ComputeNodeGroupsDeleteNodesRequest(
            nodeGroupsDeleteNodesRequest=delete_request_class(nodes=node_names),
            nodeGroup='my-node-group',
            project=self.Project(),
            zone=self.zone),
        self._GetOperationMessage('operation-' + operation_suffix,
                                  self.operation_status_enum.PENDING))

  def _ExpectSetAutoscalingPolicy(self, autoscaling_policy,
                                  operation_suffix='X'):
    autoscaling_request_class = self.messages.NodeGroup
    self.client.nodeGroups.Patch.Expect(
        self.messages.ComputeNodeGroupsPatchRequest(
            nodeGroupResource=autoscaling_request_class(
                autoscalingPolicy=autoscaling_policy),
            nodeGroup='my-node-group',
            project=self.Project(),
            zone=self.zone),
        self._GetOperationMessage('operation-' + operation_suffix,
                                  self.operation_status_enum.PENDING))

  def _ExpectPollAndGet(self, operation_suffix='X'):
    self.client.zoneOperations.Wait.Expect(
        self.messages.ComputeZoneOperationsWaitRequest(
            operation='operation-' + operation_suffix,
            zone=self.zone,
            project=self.Project()),
        self._GetOperationMessage(
            'operation-' + operation_suffix,
            self.messages.Operation.StatusValueValuesEnum.DONE,
            'https://compute.googleapis.com/compute/v1/projects/{0}/zones/'
            '{1}/nodeGroups/{2}'.format(self.Project(), self.zone,
                                        'my-node-group')))

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
    self._ExpectDeleteNodes(['node-2', 'node-5'])
    self._ExpectPollAndGet()
    self.Run('compute sole-tenancy node-groups update my-node-group '
             '--delete-nodes node-2,node-5 --zone ' + self.zone)
    self.AssertErrContains('Deleting nodes [node-2,node-5] in [my-node-group].')

  def testUpdate_SetTemplateAndDeleteNodes(self):
    self._ExpectSetNodeTemplate('new-template', 'X')
    self._ExpectDeleteNodes(['node-2', 'node-5'], 'Y')
    self._ExpectPollAndGet('X')
    self._ExpectPollAndGet('Y')

    self.Run('compute sole-tenancy node-groups update my-node-group '
             '--node-template new-template '
             '--delete-nodes node-2,node-5 --zone ' + self.zone)
    self.AssertErrContains('Deleting nodes [node-2,node-5] in [my-node-group].')
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
               '--add-nodes 2 --delete-nodes node-2,node-5 --zone ' + self.zone)


class NodeGroupsUpdateTestBeta(NodeGroupsUpdateTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testUpdate_SetAutoscalingPolicy(self):
    mode = self.messages.NodeGroupAutoscalingPolicy.ModeValueValuesEnum('ON')
    self._ExpectSetAutoscalingPolicy({'mode': mode,
                                      'minNodes': 10,
                                      'maxNodes': 60})
    self._ExpectPollAndGet()
    self.Run('compute sole-tenancy node-groups update my-node-group '
             '--autoscaler-mode=on --min-nodes=10 --max-nodes=60 '
             '--zone ' + self.zone)
    self.AssertErrContains(
        'Updating autoscaling policy on [my-node-group] to '
        '[autoscaler-mode=on,min-nodes=10,max-nodes=60].')

  def testUpdate_SetAutoscalingPolicyMode(self):
    mode = self.messages.NodeGroupAutoscalingPolicy.ModeValueValuesEnum('ON')
    self._ExpectSetAutoscalingPolicy({'mode': mode})
    self._ExpectPollAndGet()
    self.Run('compute sole-tenancy node-groups update my-node-group '
             '--autoscaler-mode=on '
             '--zone ' + self.zone)
    self.AssertErrContains(
        'Updating autoscaling policy on [my-node-group] to '
        '[autoscaler-mode=on].')

  def testUpdate_SetAutoscalingPolicyWrongMode(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r"argument --autoscaler-mode: Invalid choice: 'foo'\." '\n\n'
        r'Valid choices are \[off, on, only-scale-out\]'):
      self.Run('compute sole-tenancy node-groups update my-node-group '
               '--autoscaler-mode=foo '
               '--zone ' + self.zone)

  def testUpdate_SetAutoscalingPolicyModeMin(self):
    mode = self.messages.NodeGroupAutoscalingPolicy.ModeValueValuesEnum('ON')
    self._ExpectSetAutoscalingPolicy({'mode': mode,
                                      'minNodes': 10})
    self._ExpectPollAndGet()
    self.Run('compute sole-tenancy node-groups update my-node-group '
             '--autoscaler-mode=on --min-nodes=10 '
             '--zone ' + self.zone)
    self.AssertErrContains(
        'Updating autoscaling policy on [my-node-group] to '
        '[autoscaler-mode=on,min-nodes=10].')

  def testUpdate_SetAutoscalingPolicyModeMax(self):
    mode = self.messages.NodeGroupAutoscalingPolicy.ModeValueValuesEnum('ON')
    self._ExpectSetAutoscalingPolicy({'mode': mode,
                                      'maxNodes': 60})
    self._ExpectPollAndGet()
    self.Run('compute sole-tenancy node-groups update my-node-group '
             '--autoscaler-mode=on --max-nodes=60 '
             '--zone ' + self.zone)
    self.AssertErrContains(
        'Updating autoscaling policy on [my-node-group] to '
        '[autoscaler-mode=on,max-nodes=60].')

  def testUpdate_PatchAutoscalingNoMode(self):
    self._ExpectSetAutoscalingPolicy({'maxNodes': 60})
    self._ExpectPollAndGet()
    self.Run('compute sole-tenancy node-groups update my-node-group '
             '--max-nodes=60 '
             '--zone ' + self.zone)
    self.AssertErrContains(
        'Updating autoscaling policy on [my-node-group] to '
        '[max-nodes=60].')

  def testUpdate_MinNodesZero(self):
    self._ExpectSetAutoscalingPolicy({'minNodes': 0})
    self._ExpectPollAndGet()
    self.Run('compute sole-tenancy node-groups update my-node-group '
             '--min-nodes=0 '
             '--zone ' + self.zone)
    self.AssertErrContains(
        'Updating autoscaling policy on [my-node-group] to [min-nodes=0].')


class NodeGroupsUpdateTestAlpha(NodeGroupsUpdateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

if __name__ == '__main__':
  test_case.main()
