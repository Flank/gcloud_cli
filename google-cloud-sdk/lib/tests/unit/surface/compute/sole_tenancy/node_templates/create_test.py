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
"""Tests for the sole-tenancy node-templates create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class NodeTemplatesCreateTest(test_base.BaseTest, parameterized.TestCase):

  def SetUp(self):
    self.region = 'us-central1'
    self.api_version = 'v1'

  def _ExpectCreate(self, template):
    request = self.messages.ComputeNodeTemplatesInsertRequest(
        project=self.Project(),
        region=self.region,
        nodeTemplate=template)
    self.make_requests.side_effect = [[template]]
    return request

  def _CreateAffinityLabelsMessage(self, affinity_labels):
    return encoding.DictToAdditionalPropertyMessage(
        affinity_labels, self.messages.NodeTemplate.NodeAffinityLabelsValue,
        sort_items=True)

  def _CreateBaseNodeTemplateMessage(self):
    affinity_labels = {'environment': 'prod', 'grouping': 'frontend'}
    server_binding = (self.messages.ServerBinding.TypeValueValuesEnum
                      .RESTART_NODE_ON_ANY_SERVER)
    return self.messages.NodeTemplate(
        name='my-template',
        nodeAffinityLabels=self._CreateAffinityLabelsMessage(affinity_labels),
        serverBinding=self.messages.ServerBinding(type=server_binding))

  def testCreate_AllOptionsWithNodeType(self):
    template = self._CreateBaseNodeTemplateMessage()
    template.description = 'Awesome Template'
    template.nodeType = 'n1-node-96-624'
    request = self._ExpectCreate(template)

    result = self.Run(
        'compute sole-tenancy node-templates create my-template '
        '--node-affinity-labels environment=prod,grouping=frontend '
        '--node-type n1-node-96-624 --description "Awesome Template" '
        '--region {}'.format(self.region))

    self.CheckRequests([(self.compute.nodeTemplates, 'Insert', request)])
    self.assertEqual(result, template)

  def testCreate_AllOptionsWithNodeRequirements(self):
    template = self._CreateBaseNodeTemplateMessage()
    template.description = 'Awesome Template'
    template.nodeTypeFlexibility = (
        self.messages.NodeTemplateNodeTypeFlexibility(
            cpus='64', localSsd='512', memory='any'))
    request = self._ExpectCreate(template)

    result = self.Run(
        'compute sole-tenancy node-templates create my-template '
        '--node-affinity-labels environment=prod,grouping=frontend '
        '--node-requirements vCPU=64,localSSD=512GB,memory=any '
        '--description "Awesome Template" --region {}'.format(self.region))

    self.CheckRequests([(self.compute.nodeTemplates, 'Insert', request)])
    self.assertEqual(result, template)

  @parameterized.named_parameters(
      ('OmittingMemoryRequirement', 'vCPU=64,localSSD=512GB', '64', '512',
       'any'),
      ('UnitConversion', 'localSSD=1TB,memory=16GB', 'any', '1024', '16384'),
      ('SettingCPUToAny', 'vCPU=any,localSSD=1TB,memory=16GB', 'any', '1024',
       '16384'), ('SettingAllToAny', 'vCPU=any,localSSD=any,memory=any', 'any',
                  'any', 'any'),
      ('SettingAnyCaseInsensitive', 'vCPU=ANY,localSSD=Any,memory=anY', 'any',
       'any', 'any'),
      ('SettingAllToAnyMinimalKeys', 'localSSD=any', 'any', 'any', 'any'),
      ('OmittingLocalSSD', 'vCPU=64,memory=128MB', '64', None, '128'))
  def testCreate_NodeRequirements(self, node_requirements, cpus, local_ssd,
                                  memory):
    template = self._CreateBaseNodeTemplateMessage()
    template.nodeTypeFlexibility = (
        self.messages.NodeTemplateNodeTypeFlexibility(
            cpus=cpus, localSsd=local_ssd, memory=memory))
    request = self._ExpectCreate(template)

    result = self.Run(
        'compute sole-tenancy node-templates create my-template '
        '--node-affinity-labels environment=prod,grouping=frontend '
        '--node-requirements {0} '
        '--region {1}'.format(node_requirements, self.region))

    self.CheckRequests([(self.compute.nodeTemplates, 'Insert', request)])
    self.assertEqual(result, template)

  @parameterized.parameters(
      ('vCPU=whatever', "invalid .* value: 'vCPU=whatever'"),
      ('vCPU=whatever,memory=asdf',
       "invalid .* value: 'vCPU=whatever,memory=asdf'"),
      ('memory=51mg', 'unit must be one of .* received: mg'))
  def testCreate_InvalidNodeRequirements(self, node_requirements, error_msg):
    with self.AssertRaisesArgumentErrorRegexp(
        'argument --node-requirements: ' + error_msg):
      self.Run(
          'compute sole-tenancy node-templates create my-template '
          '--node-affinity-labels environment=prod,grouping=frontend '
          '--node-requirements {0} '
          '--region {1}'.format(node_requirements, self.region))

  def testCreate_NodeRequirementsMutuallyExlusiveWithNodeType(self):
    with self.AssertRaisesArgumentError():
      self.Run(
          'compute sole-tenancy node-templates create my-template '
          '--node-affinity-labels environment=prod,grouping=frontend '
          '--node-requirements localSSD=1TB,memory=16GB --node-type iAPX-286 '
          '--region {}'.format(self.region))
    self.AssertErrContains('--node-requirements')
    self.AssertErrContains('--node-type')

  @parameterized.named_parameters(
      ('DefaultSpecified', '--server-binding restart-node-on-any-server',
       'RESTART_NODE_ON_ANY_SERVER'),
      ('Default', '', 'RESTART_NODE_ON_ANY_SERVER'),
      ('MinimalServersSpecified',
       '--server-binding restart-node-on-minimal-servers',
       'RESTART_NODE_ON_MINIMAL_SERVERS'))
  def testCreate_ServerBinding(self, cmd_line_flag, expected_server_binding):
    server_binding = self.messages.ServerBinding.TypeValueValuesEnum(
        expected_server_binding)
    template = self._CreateBaseNodeTemplateMessage()
    template.nodeType = 'n1-node-96-624'
    template.serverBinding = self.messages.ServerBinding(type=server_binding)
    request = self._ExpectCreate(template)

    result = self.Run(
        'compute sole-tenancy node-templates create my-template '
        '--node-affinity-labels environment=prod,grouping=frontend '
        '--node-type n1-node-96-624 '
        '{0} --region {1}'.format(cmd_line_flag, self.region))

    self.CheckRequests([(self.compute.nodeTemplates, 'Insert', request)])
    self.assertEqual(result, template)

  def testCreateWithOvercommitType(self):
    template = self._CreateBaseNodeTemplateMessage()
    template.nodeType = 'n1-node-96-624'
    template.cpuOvercommitType = self.messages.NodeTemplate.CpuOvercommitTypeValueValuesEnum.ENABLED
    request = self._ExpectCreate(template)

    result = self.Run(
        'compute sole-tenancy node-templates create my-template '
        '--node-affinity-labels environment=prod,grouping=frontend '
        '--cpu-overcommit-type=enabled '
        '--node-type n1-node-96-624 '
        '--region {}'.format(self.region))

    self.CheckRequests([(self.compute.nodeTemplates, 'Insert', request)])
    self.assertEqual(result, template)


class NodeTemplatesCreateBetaTest(NodeTemplatesCreateTest):

  def SetUp(self):
    self.region = 'us-central1'
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.api_version = 'beta'

  @parameterized.named_parameters(
      ('SimpleDisk', 'type=local-ssd,count=1', 'local-ssd', 1, None),
      ('SizeSpecified', 'type=local-ssd,count=1,size=375GB', 'local-ssd', 1,
       375),
      )
  def testCreate_Disk(self, disk, disk_type, count, size):
    template = self._CreateBaseNodeTemplateMessage()
    template.disks = [(
        self.messages.LocalDisk(
            diskType=disk_type, diskCount=count, diskSizeGb=size))]
    template.nodeTypeFlexibility = (
        self.messages.NodeTemplateNodeTypeFlexibility(
            cpus='64', localSsd=None, memory='128'))
    request = self._ExpectCreate(template)

    result = self.Run(
        'compute sole-tenancy node-templates create my-template '
        '--node-affinity-labels environment=prod,grouping=frontend '
        '--node-requirements vCPU=64,memory=128MB '
        '--disk {0} '
        '--region {1}'.format(disk, self.region))

    self.CheckRequests([(self.compute.nodeTemplates, 'Insert', request)])
    self.assertEqual(result, template)

  @parameterized.parameters(
      ('type=invalid,count=1', r'\[type\] must be one of \[local-ssd\]'),
      ('count=1', r'Key \[type\] required in dict arg but not provided'),
      ('type=local-ssd',
       r'Key \[count\] required in dict arg but not provided'),
      ('type=local-ssd,count=1,size=200GB',
       'value must be greater than or equal to 375GB'),
      ('type=local-ssd,count=1,size=500GB',
       'value must be less than or equal to 375GB'))
  def testCreate_InvalidDisk(self, disk, error_msg):
    with self.AssertRaisesArgumentErrorRegexp(
        'argument --disk: ' + error_msg):
      self.Run(
          'compute sole-tenancy node-templates create my-template '
          '--node-affinity-labels environment=prod,grouping=frontend '
          '--node-requirements vCPU=64,memory=128MB '
          '--disk {0} '
          '--region {1}'.format(disk, self.region))

  def testCreateWithAccelerator(self):
    template = self._CreateBaseNodeTemplateMessage()
    template.nodeType = 'n1-node-96-624'
    accelerator_type = ('https://compute.googleapis.com/compute/{api}/'
                        'projects/my-project/regions/us-central1/'
                        'acceleratorTypes/p100'.format(api=self.api_version))
    template.accelerators = [
        self.messages.AcceleratorConfig(
            acceleratorType=accelerator_type, acceleratorCount=2)
    ]
    request = self._ExpectCreate(template)

    result = self.Run(
        'compute sole-tenancy node-templates create my-template '
        '--node-affinity-labels environment=prod,grouping=frontend '
        '--accelerator=type=p100,count=2 '
        '--node-type n1-node-96-624 '
        '--region {}'.format(self.region))

    self.CheckRequests([(self.compute.nodeTemplates, 'Insert', request)])
    self.assertEqual(result, template)


class NodeTemplatesCreateAlphaTest(NodeTemplatesCreateBetaTest):

  def SetUp(self):
    self.region = 'us-central1'
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
