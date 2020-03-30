# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the instances set-scheduling subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.sole_tenancy import util as sole_tenancy_util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)
  test_obj.track = calliope_base.ReleaseTrack.GA

  if api_version == 'alpha':
    test_obj.client = test_obj.compute_alpha
    test_obj.track = calliope_base.ReleaseTrack.ALPHA
  elif api_version == 'beta':
    test_obj.client = test_obj.compute_beta
    test_obj.track = calliope_base.ReleaseTrack.BETA
  else:
    test_obj.client = test_obj.compute_v1
    test_obj.track = calliope_base.ReleaseTrack.GA

  maintenance = test_obj.messages.Scheduling.OnHostMaintenanceValueValuesEnum

  test_obj.migrate = maintenance.MIGRATE
  test_obj.terminate = maintenance.TERMINATE

  test_obj.node_affinity = test_obj.messages.SchedulingNodeAffinity
  test_obj.operator_enum = test_obj.node_affinity.OperatorValueValuesEnum


class InstancesSetSchedulingTest(test_base.BaseTest, parameterized.TestCase):

  def SetUp(self):
    SetUp(self, 'v1')

  def testWithDefaults(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testRestartMigrate(self):
    self.Run("""
        compute instances set-scheduling instance-1
        --restart-on-failure
        --maintenance-policy MIGRATE
        --zone central2-a
        """)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(
                  automaticRestart=True,
                  onHostMaintenance=self.migrate),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testNoRestartMigrate(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --no-restart-on-failure
          --maintenance-policy MIGRATE
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(
                  automaticRestart=False,
                  onHostMaintenance=self.migrate),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testRestartTerminate(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --restart-on-failure
          --maintenance-policy TERMINATE
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(
                  automaticRestart=True,
                  onHostMaintenance=self.terminate),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testNoRestartTerminate(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --no-restart-on-failure
          --maintenance-policy TERMINATE
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(
                  automaticRestart=False,
                  onHostMaintenance=self.terminate),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testRestart(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --restart-on-failure
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(automaticRestart=True),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testNoRestart(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --no-restart-on-failure
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(automaticRestart=False),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testMigrate(self):
    self.templateTestMigrate("""
        compute instances set-scheduling instance-1
          --maintenance-policy MIGRATE
          --zone central2-a
        """)

  def testMigrateLowerCase(self):
    self.templateTestMigrate("""
        compute instances set-scheduling instance-1
          --maintenance-policy migrate
          --zone central2-a
        """)

  def templateTestMigrate(self, cmd):
    self.Run(cmd)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(
                  onHostMaintenance=self.migrate),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testTerminate(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --maintenance-policy TERMINATE
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(
                  onHostMaintenance=self.terminate),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testUriSupport(self):
    self.Run("""
        compute instances set-scheduling
          https://compute.googleapis.com/compute/v1/projects/my-project/zones/central2-a/instances/instance-1
        """)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(name='instance-1', zone='central1-a'),
            self.messages.Instance(name='instance-1', zone='central1-b'),
            self.messages.Instance(name='instance-1', zone='central2-a'),
        ],

        [],
    ])
    self.WriteInput('3\n')

    self.Run("""
        compute instances set-scheduling
          instance-1
        """)

    self.AssertErrContains('instance-1')
    self.AssertErrContains('central1-a')
    self.AssertErrContains('central1-b')
    self.AssertErrContains('central2-a')
    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance-1'),

        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def _CheckNodeAffinityRequests(self, node_affinities):
    m = self.messages
    self.CheckRequests([(
        self.client.instances, 'SetScheduling',
        m.ComputeInstancesSetSchedulingRequest(
            instance='instance-1',
            project='my-project',
            scheduling=m.Scheduling(nodeAffinities=node_affinities),
            zone='central2-a')
    )])

  def testSetSimpleNodeAffinityJson(self):
    node_affinities = [
        self.node_affinity(
            key='key1',
            operator=self.operator_enum.IN,
            values=['value1', 'value2'])]
    contents = """\
[{"operator": "IN", "values": ["value1", "value2"], "key": "key1"}]
    """
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    self.Run("""
        compute instances set-scheduling instance-1 --zone central2-a
          --node-affinity-file {}
        """.format(node_affinity_file))

    self._CheckNodeAffinityRequests(node_affinities)

  def testSetSimpleNodeAffinityYaml(self):
    node_affinities = [
        self.node_affinity(
            key='key1',
            operator=self.operator_enum.IN,
            values=['value1', 'value2'])]
    contents = """\
- key: key1
  operator: IN
  values: [value1, value2]
    """
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    self.Run("""
        compute instances set-scheduling instance-1 --zone central2-a
          --node-affinity-file {}
        """.format(node_affinity_file))

    self._CheckNodeAffinityRequests(node_affinities)

  def testSetMultipleNodeAffinityMessages(self):
    node_affinities = [
        self.node_affinity(
            key='key1',
            operator=self.operator_enum.IN,
            values=['value1']),
        self.node_affinity(
            key='key2',
            operator=self.operator_enum.NOT_IN,
            values=['value2', 'value3']),
        self.node_affinity(
            key='key3',
            operator=self.operator_enum.IN,
            values=[])]
    contents = """\
- key: key1
  operator: IN
  values: [value1]
- key: key2
  operator: NOT_IN
  values: [value2, value3]
- key: key3
  operator: IN
    """
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    self.Run("""
        compute instances set-scheduling instance-1 --zone central2-a
          --node-affinity-file {}
        """.format(node_affinity_file))

    self._CheckNodeAffinityRequests(node_affinities)

  def testSetInvalidOperator(self):
    contents = """\
- key: key1
  operator: HelloWorld
  values: [value1, value2]
    """
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    with self.AssertRaisesExceptionMatches(
        sole_tenancy_util.NodeAffinityFileParseError,
        "Key [key1] has invalid field formats for: ['operator']"):
      self.Run("""
          compute instances set-scheduling instance-1 --zone central2-a
            --node-affinity-file {}
          """.format(node_affinity_file))

  def testSetNoKey(self):
    contents = """\
- operator: IN
  values: [value1, value2]
    """
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    with self.AssertRaisesExceptionMatches(
        sole_tenancy_util.NodeAffinityFileParseError,
        'A key must be specified for every node affinity label.'):
      self.Run("""
          compute instances set-scheduling instance-1 --zone central2-a
            --node-affinity-file {}
          """.format(node_affinity_file))

  def testSetInvalidYaml(self):
    contents = """\
- key: key1
  operator: IN
  values: 3
    """
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    with self.assertRaisesRegexp(
        sole_tenancy_util.NodeAffinityFileParseError,
        r'Expected type .* for field values, found .*'):
      self.Run("""
          compute instances set-scheduling instance-1 --zone central2-a
            --node-affinity-file {}
          """.format(node_affinity_file))

  @parameterized.parameters('-', '[{}]')
  def testSetEmptyListItem(self, contents):
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    with self.AssertRaisesExceptionMatches(
        sole_tenancy_util.NodeAffinityFileParseError,
        'Empty list item in JSON/YAML file.'):
      self.Run("""
          compute instances set-scheduling instance-1 --zone central2-a
            --node-affinity-file {}
          """.format(node_affinity_file))

  @parameterized.parameters('', '[]')
  def testSetAffinityFileWithLabels(self, contents):
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)
    with self.AssertRaisesExceptionMatches(
        sole_tenancy_util.NodeAffinityFileParseError,
        'No node affinity labels specified. You must specify at least one '
        'label to create a sole tenancy instance.'):
      self.Run("""
          compute instances set-scheduling instance-1 --zone central2-a
            --node-affinity-file {}
          """.format(node_affinity_file))

  def testSetNodeGroup(self):
    node_affinities = [
        self.node_affinity(
            key='compute.googleapis.com/node-group-name',
            operator=self.operator_enum.IN,
            values=['my-node-group'])]
    self.Run("""
        compute instances set-scheduling instance-1 --zone central2-a
          --node-group my-node-group
        """)

    self._CheckNodeAffinityRequests(node_affinities)

  def testSetNode(self):
    node_affinities = [
        self.node_affinity(
            key='compute.googleapis.com/node-name',
            operator=self.operator_enum.IN,
            values=['my-node'])
    ]
    self.Run("""
        compute instances set-scheduling instance-1 --zone central2-a
          --node my-node
        """)

    self._CheckNodeAffinityRequests(node_affinities)

  def testClearNode(self):
    node_affinities = []

    self.Run("""
        compute instances set-scheduling instance-1 --zone central2-a
          --clear-node-affinities
        """)

    self._CheckNodeAffinityRequests(node_affinities)


class InstancesSetSchedulingTestBeta(test_base.BaseTest):

  def SetUp(self):
    SetUp(self, 'beta')

  def testMinNodeCpuFlag(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --min-node-cpu 10
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(
                  minNodeCpus=10),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testClearMinNodeCpu(self):
    self.Run("""
      compute instances set-scheduling instance-1
        --clear-min-node-cpu
        --zone central2-a
      """)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )


class InstancesSetSchedulingTestAlpha(InstancesSetSchedulingTestBeta):

  def SetUp(self):
    SetUp(self, 'alpha')

  def testMaintenancePolicyDeprecation(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --maintenance-policy TERMINATE
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(
                  onHostMaintenance=self.terminate),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )
    self.AssertErrContains(
        'WARNING: The --maintenance-policy flag is now deprecated. '
        'Please use `--on-host-maintenance` instead')

  def testOnHostMaintenanceFlag(self):
    self.Run("""
        compute instances set-scheduling instance-1
          --on-host-maintenance TERMINATE
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.client.instances,
          'SetScheduling',
          self.messages.ComputeInstancesSetSchedulingRequest(
              scheduling=self.messages.Scheduling(
                  onHostMaintenance=self.terminate),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )


if __name__ == '__main__':
  test_case.main()
