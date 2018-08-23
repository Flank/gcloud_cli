# -*- coding: utf-8 -*- #
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
"""Tests for the node-groups list-nodes subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class NodeGroupsListNodesTest(test_base.BaseTest):

  def SetUp(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.NodeGroupsListNodes(
                items=test_resources.MakeNodesInNodeGroup(
                    self.messages, self.resource_api))
        ],
    ])

  def testListNodes(self):
    self.Run("""
        compute sole-tenancy node-groups list-nodes group-1
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.nodeGroups,
          'ListNodes',
          self.messages.ComputeNodeGroupsListNodesRequest(
              nodeGroup='group-1',
              zone='zone-1',
              project='my-project'))],
    )

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                      STATUS  NODE_TYPE       INSTANCES
            node-1                    READY   iAPX-286        instance-1,instance-2
            node-2                    READY   iAPX-286        instance-3
            """),
        normalize_space=True)

  def testListNodesWithLimit(self):
    self.Run("""
        compute sole-tenancy node-groups list-nodes group-1
          --zone zone-1
          --limit 1
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                      STATUS  NODE_TYPE       INSTANCES
            node-1                    READY   iAPX-286        instance-1,instance-2
            """),
        normalize_space=True)

  def testListNodesByUri(self):
    self.Run("""
        compute sole-tenancy node-groups list-nodes
          {0}/projects/my-project/zones/zone-1/nodeGroups/group-1
          --zone zone-1
        """.format(self.compute_uri))
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                      STATUS  NODE_TYPE       INSTANCES
            node-1                    READY   iAPX-286        instance-1,instance-2
            node-2                    READY   iAPX-286        instance-3
            """),
        normalize_space=True)

  def testListNodesBySorted(self):
    self.Run("""
        compute sole-tenancy node-groups list-nodes group-1
          --zone zone-1
          --sort-by ~NAME
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                      STATUS  NODE_TYPE       INSTANCES
            node-2                    READY   iAPX-286        instance-3
            node-1                    READY   iAPX-286        instance-1,instance-2
            """),
        normalize_space=True)

  def testListNodesPromptScope(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [self.messages.Zone(name='zone-1'),
         self.messages.Zone(name='zone-2')],
        [self.messages.NodeGroupsListNodes(
            items=test_resources.MakeNodesInNodeGroup(
                self.messages, 'v1'))],
    ])
    self.WriteInput('1\n')
    self.Run('compute sole-tenancy node-groups list-nodes group-1')
    self.CheckRequests(
        self.zones_list_request,
        [(self.compute.nodeGroups,
          'ListNodes',
          self.messages.ComputeNodeGroupsListNodesRequest(
              nodeGroup='group-1',
              zone='zone-1',
              project='my-project'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                      STATUS  NODE_TYPE       INSTANCES
            node-1                    READY   iAPX-286        instance-1,instance-2
            node-2                    READY   iAPX-286        instance-3
            """), normalize_space=True)

if __name__ == '__main__':
  test_case.main()
