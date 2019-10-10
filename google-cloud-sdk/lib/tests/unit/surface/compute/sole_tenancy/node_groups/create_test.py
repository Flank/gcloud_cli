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
"""Tests for the sole-tenancy node-groups delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class NodeGroupsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.api_version = 'v1'
    self.SelectApi(self.api_version)
    self.track = calliope_base.ReleaseTrack.GA
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

  def _CreateNodeGroup(self, name, description, node_template,
                       maintenance_policy=None, autoscaling_policy=None):
    node_template_self_link = (
        'https://compute.googleapis.com/compute/{version}/projects/{project}/'
        'regions/{region}/nodeTemplates/{name}'.format(
            version=self.api_version, project=self.Project(),
            region=self.region, name=node_template))
    node_group = self.messages.NodeGroup(
        name=name,
        description=description,
        nodeTemplate=node_template_self_link)
    if maintenance_policy:
      node_group.maintenancePolicy = (
          self.messages.NodeGroup.MaintenancePolicyValueValuesEnum(
              maintenance_policy))
    if autoscaling_policy:
      node_group.autoscalingPolicy = self.messages.NodeGroupAutoscalingPolicy(
          mode=self.messages.NodeGroupAutoscalingPolicy.ModeValueValuesEnum(
              autoscaling_policy['mode']),
          minSize=autoscaling_policy.get('minSize'),
          maxSize=autoscaling_policy.get('maxSize'))
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


class NodeGroupsCreateTestBeta(NodeGroupsCreateTest):

  def SetUp(self):
    self.api_version = 'beta'
    self.SelectApi(self.api_version)
    self.track = calliope_base.ReleaseTrack.BETA


class NodeGroupsCreateTestAlpha(NodeGroupsCreateTestBeta):

  def SetUp(self):
    self.api_version = 'alpha'
    self.SelectApi(self.api_version)
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreate_MaintenancePolicy(self):
    node_group = self._CreateNodeGroup(
        name='my-node-group',
        description='Frontend Group',
        node_template='my-template',
        maintenance_policy='RESTART_IN_PLACE')
    request = self._ExpectCreate(node_group, 3)

    result = self.Run(
        'compute sole-tenancy node-groups create my-node-group '
        '--node-template my-template --target-size 3 '
        '--maintenance-policy restart-in-place '
        '--description "Frontend Group" --zone ' + self.zone)

    self.CheckRequests([(self.compute.nodeGroups, 'Insert', request)])
    self.assertEqual(result, node_group)

  def testCreate_AutoscalingPolicy(self):
    node_group = self._CreateNodeGroup(
        name='my-node-group',
        description='Frontend Group',
        node_template='my-template',
        autoscaling_policy={'mode': 'ON',
                            'minSize': 10,
                            'maxSize': 60})
    request = self._ExpectCreate(node_group, 3)

    result = self.Run(
        'compute sole-tenancy node-groups create my-node-group '
        '--node-template my-template --target-size 3 '
        '--autoscaling-policy mode=on,min-size=10,max-size=60 '
        '--description "Frontend Group" --zone ' + self.zone)

    self.CheckRequests([(self.compute.nodeGroups, 'Insert', request)])
    self.assertEqual(result, node_group)

  def testCreate_AutoscalingPolicyNoMode(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --autoscaling-policy: Key [mode] required in dict arg but '
        'not provided'):
      self.Run(
          'compute sole-tenancy node-groups create my-node-group '
          '--node-template my-template --target-size 3 '
          '--autoscaling-policy min-size=10,max-size=60 '
          '--description "Frontend Group" --zone ' + self.zone)

  def testCreate_AutoscalingPolicyWrongMode(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --autoscaling-policy: [mode] must be one of [off,on]'):
      self.Run(
          'compute sole-tenancy node-groups create my-node-group '
          '--node-template my-template --target-size 3 '
          '--autoscaling-policy mode=foo '
          '--description "Frontend Group" --zone ' + self.zone)

  def testCreate_AutoscalingPolicyModeMin(self):
    node_group = self._CreateNodeGroup(
        name='my-node-group',
        description='Frontend Group',
        node_template='my-template',
        autoscaling_policy={'mode': 'ON',
                            'minSize': 10})
    request = self._ExpectCreate(node_group, 3)

    result = self.Run(
        'compute sole-tenancy node-groups create my-node-group '
        '--node-template my-template --target-size 3 '
        '--autoscaling-policy mode=on,min-size=10 '
        '--description "Frontend Group" --zone ' + self.zone)

    self.CheckRequests([(self.compute.nodeGroups, 'Insert', request)])
    self.assertEqual(result, node_group)

  def testCreate_AutoscalingPolicyModeMax(self):
    node_group = self._CreateNodeGroup(
        name='my-node-group',
        description='Frontend Group',
        node_template='my-template',
        autoscaling_policy={'mode': 'ON',
                            'maxSize': 60})
    request = self._ExpectCreate(node_group, 3)

    result = self.Run(
        'compute sole-tenancy node-groups create my-node-group '
        '--node-template my-template --target-size 3 '
        '--autoscaling-policy mode=on,max-size=60 '
        '--description "Frontend Group" --zone ' + self.zone)

    self.CheckRequests([(self.compute.nodeGroups, 'Insert', request)])
    self.assertEqual(result, node_group)

if __name__ == '__main__':
  test_case.main()
