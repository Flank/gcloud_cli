# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Module for instance group managers updater feature test base classes."""

import datetime
import re

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class InstanceGroupsUpdaterTestBase(e2e_test_base.BaseTest):
  """Base class for Managed Instance Group Updater e2e tests."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

    # Containers for created resources.
    self.instance_template_names = []
    self.instance_group_manager_names = []
    self.region_instance_group_manager_names = []

  def TearDown(self):
    self.DeleteResources(self.instance_group_manager_names,
                         self.DeleteInstanceGroupManager,
                         'instance group manager')
    self.DeleteResources(self.region_instance_group_manager_names,
                         self.DeleteRegionalInstanceGroupManager,
                         'regional instance group manager')
    try:
      self.DeleteResources(self.instance_template_names,
                           self.DeleteInstanceTemplate, 'instance template')
    except AssertionError:
      # Cleanup script should handle teardown issues
      pass

  def GetScopeFlag(self, plural=False):
    if self.scope == e2e_test_base.ZONAL:
      flag_name = 'zone'
      flag_value = self.zone
    elif self.scope == e2e_test_base.REGIONAL:
      flag_name = 'region'
      flag_value = self.region
    elif self.scope == e2e_test_base.EXPLICIT_GLOBAL:
      flag_name = 'global'
      flag_value = ''
    else:
      return ''
    if plural:
      flag_name += 's'
    return '--' + flag_name + ' ' + flag_value

  def CreateInstanceTemplate(self, machine_type='n1-standard-1'):
    name = e2e_utils.GetResourceNameGenerator(prefix=self.prefix).next()
    self.Run('compute instance-templates create {0} --machine-type {1}'
             .format(name, machine_type))
    self.instance_template_names.append(name)
    self.AssertNewOutputContains(name)
    return name

  def CreateInstanceGroupManager(self, instance_template_name, size=0):
    name = e2e_utils.GetResourceNameGenerator(prefix=self.prefix).next()
    if self.scope == e2e_test_base.ZONAL:
      self.instance_group_manager_names.append(name)
    elif self.scope == e2e_test_base.REGIONAL:
      self.region_instance_group_manager_names.append(name)

    self.Run('compute instance-groups managed create {0} '
             '{1} '
             '--base-instance-name {2} '
             '--size {3} '
             '--template {4}'
             .format(name,
                     self.GetScopeFlag(), name, size, instance_template_name))
    self.AssertNewOutputContains(name)
    return name

  def VerifyNumInstancesWithMachineType(self, igm_name, machine_type,
                                        expected_number):
    self.ClearOutput()
    self.Run('compute instances list --uri --filter=\'machineType:{0}\''
             ''.format(machine_type))
    output = self.GetNewOutput()
    instance_names = [instance_name
                      for instance_name in re.findall(r'\S+', output)
                      if igm_name in instance_name]
    self.assertEqual(expected_number, len(instance_names))

  def VerifyNumInstancesWithVersionName(self, igm_name, expected_number):
    self.ClearOutput()
    self.Run('compute instance-groups managed list-instances {0} {1} '
             .format(igm_name, self.GetScopeFlag()))
    output = self.GetNewOutput()
    lines = output.split('\n')
    # Verify that there is at least 1 instance in the output table.
    self.assertGreater(len(lines), 1)
    # Find the position of 'VERSION_NAME' column.
    column_names = lines[0].split()
    version_name_column_index = column_names.index('VERSION_NAME')
    # Count the instances which have non-empty value in 'VERSION_NAME' column.
    # This non-empty value must also parse as a date.
    num_instances_with_version_name = 0
    for line in lines[1:]:
      values = line.split()
      if version_name_column_index < len(values):
        datetime.datetime.strptime(
            values[version_name_column_index].split('/')[-1],
            '%Y-%m-%d')
        num_instances_with_version_name += 1
    self.assertEqual(expected_number, num_instances_with_version_name)

  def WaitUntilStable(self, igm_name):
    self.Run('compute instance-groups managed wait-until-stable {0} '
             '--timeout 600 '
             '{1}'.format(igm_name, self.GetScopeFlag()))
    self.AssertNewErrNotContains('Timeout')

  # The Updater Restart test:
  # - first, we set updatePolicy to new template and type to OPPORTUNISTIC
  #   (it does not trigger any instance creation/deletion on IGM),
  # - then, we trigger restart of all the machines at once and change type to
  #   PROACTIVE (default).
  def _RunUpdateInstancesRestartTest(self, size):
    machine_type_original = 'n1-standard-1'
    machine_type_new = 'f1-micro'
    instance_template_original = (
        self.CreateInstanceTemplate(machine_type=machine_type_original))
    instance_template_new = (
        self.CreateInstanceTemplate(machine_type=machine_type_new))

    igm_name = self.CreateInstanceGroupManager(instance_template_original,
                                               size=size)
    self.WaitUntilStable(igm_name)
    self.VerifyNumInstancesWithMachineType(igm_name, machine_type_original,
                                           size)
    self.VerifyNumInstancesWithVersionName(igm_name, 0)

    result = self.Run(
        'compute instance-groups managed rolling-action start-update {0} '
        '--type opportunistic --version template={1} --format=disable '
        '{2}'.format(igm_name, instance_template_new, self.GetScopeFlag()))[0]
    self.assertRegexpMatches(result.instanceTemplate,
                             '.*' + instance_template_new)
    self.assertEqual(result.targetSize, size)
    self.assertEqual(str(result.updatePolicy.type), 'OPPORTUNISTIC')
    self.assertNotRegexpMatches(result.versions[0].instanceTemplate,
                                '.*' + instance_template_original)
    self.VerifyNumInstancesWithMachineType(igm_name, machine_type_original,
                                           size)
    self.VerifyNumInstancesWithVersionName(igm_name, 0)

    result = self.Run(
        'compute instance-groups managed rolling-action restart {0} '
        '--max-unavailable=100% --format=disable '
        '{1}'.format(igm_name, self.GetScopeFlag()))[0]
    self.assertRegexpMatches(result.instanceTemplate,
                             '.*' + instance_template_new)
    self.assertEqual(result.targetSize, size)
    self.assertEqual(result.updatePolicy.maxUnavailable.calculated, size)
    self.assertEqual(result.updatePolicy.maxUnavailable.percent, 100)
    self.assertEqual(str(result.updatePolicy.minimalAction), 'RESTART')
    self.assertEqual(str(result.updatePolicy.type), 'PROACTIVE')
    self.assertNotRegexpMatches(result.versions[0].instanceTemplate,
                                '.*' + instance_template_original)
    self.WaitUntilStable(igm_name)
    self.VerifyNumInstancesWithMachineType(igm_name, machine_type_new, size)
    self.VerifyNumInstancesWithVersionName(igm_name, size)

  def _RunUpdateInstancesRestartTest_SwitchFromFixedToPercent(self, size):
    igm_name = self.CreateInstanceGroupManager(
        self.CreateInstanceTemplate(machine_type='n1-standard-1'),
        size=size)

    result = self.Run(
        'compute instance-groups managed rolling-action restart {0} '
        '--max-unavailable 3 --format=disable '
        '{1}'.format(igm_name, self.GetScopeFlag()))[0]
    self.assertEqual(result.updatePolicy.maxUnavailable.calculated, 3)
    self.assertEqual(result.updatePolicy.maxUnavailable.fixed, 3)
    self.assertEqual(str(result.updatePolicy.minimalAction), 'RESTART')
    self.assertEqual(str(result.updatePolicy.type), 'PROACTIVE')

    result = self.Run(
        'compute instance-groups managed rolling-action restart {0} '
        '--max-unavailable 25% --format=disable '
        '{1}'.format(igm_name, self.GetScopeFlag()))[0]
    self.assertEqual(result.updatePolicy.maxUnavailable.calculated, 2)
    self.assertEqual(result.updatePolicy.maxUnavailable.percent, 25)
    self.assertEqual(str(result.updatePolicy.minimalAction), 'RESTART')
    self.assertEqual(str(result.updatePolicy.type), 'PROACTIVE')

    result = self.Run(
        'compute instance-groups managed rolling-action restart {0} '
        '--max-unavailable 4 --format=disable '
        '{1}'.format(igm_name, self.GetScopeFlag()))[0]
    self.assertEqual(result.updatePolicy.maxUnavailable.calculated, 4)
    self.assertEqual(result.updatePolicy.maxUnavailable.fixed, 4)
    self.assertEqual(str(result.updatePolicy.minimalAction), 'RESTART')
    self.assertEqual(str(result.updatePolicy.type), 'PROACTIVE')

  # The Updater Replace test: we perform an update from original template to
  # (20% instances in original template, all other in new template) "mix"
  # with each new machine waiting 1 min before serving.
  def _RunUpdateInstancesReplaceTest(self, expected_machine_type_count_map):
    machine_type_original = 'n1-standard-1'
    machine_type_new = 'f1-micro'
    instance_template_original = (
        self.CreateInstanceTemplate(machine_type=machine_type_original))
    instance_template_new = (
        self.CreateInstanceTemplate(machine_type=machine_type_new))

    total_machine_count = sum(expected_machine_type_count_map.values())
    igm_name = self.CreateInstanceGroupManager(instance_template_original,
                                               size=total_machine_count)
    self.WaitUntilStable(igm_name)
    self.VerifyNumInstancesWithMachineType(igm_name, machine_type_original,
                                           total_machine_count)

    result = self.Run(
        'compute instance-groups managed rolling-action start-update {0} '
        '--type proactive '
        '--max-surge 100% --max-unavailable 100% --min-ready 1m '
        '--canary-version template={1},target-size=20% '
        '--version template={2} {3} --format=disable'.format(
            igm_name, instance_template_original, instance_template_new,
            self.GetScopeFlag()))[0]
    self.assertRegexpMatches(result.versions[0].instanceTemplate,
                             '.*' + instance_template_new)
    self.assertEqual(result.targetSize, total_machine_count)
    self.assertEqual(result.updatePolicy.maxSurge.calculated,
                     total_machine_count)
    self.assertEqual(result.updatePolicy.maxSurge.percent, 100)
    self.assertEqual(result.updatePolicy.maxUnavailable.calculated,
                     total_machine_count)
    self.assertEqual(result.updatePolicy.maxUnavailable.percent, 100)
    self.assertEqual(str(result.updatePolicy.minimalAction), 'REPLACE')
    self.assertEqual(str(result.updatePolicy.type), 'PROACTIVE')
    self.assertRegexpMatches(result.versions[1].instanceTemplate,
                             '.*' + instance_template_original)
    self.assertEqual(result.versions[1].targetSize.calculated,
                     expected_machine_type_count_map[machine_type_original])
    self.assertEqual(result.versions[1].targetSize.percent, 20)

    self.WaitUntilStable(igm_name)
    for machine_type, num_instances in (expected_machine_type_count_map
                                        .iteritems()):
      self.VerifyNumInstancesWithMachineType(
          igm_name, machine_type, num_instances)

  # The Stop Proactive Update test:
  # - we start an update with updatePolicy type PROACTIVE from original template
  #   to (1 instance in new template, all other in original template) mix,
  # - we stop proactive update and check if updatePolicy type is OPPORTUNISTIC.
  def _RunStopProactiveUpdateInstancesTest(self, max_surge, max_unavailable):
    machine_type_original = 'n1-standard-1'
    machine_type_new = 'f1-micro'
    instance_template_original = (
        self.CreateInstanceTemplate(machine_type=machine_type_original))
    instance_template_new = (
        self.CreateInstanceTemplate(machine_type=machine_type_new))

    igm_name = self.CreateInstanceGroupManager(instance_template_original,
                                               size=5)
    self.WaitUntilStable(igm_name)

    result = self.Run(
        'compute instance-groups managed rolling-action start-update {0} '
        '--type proactive '
        '--version template={1} '
        '--canary-version template={2},target-size=3 '
        '--format=disable '
        '{3}'.format(igm_name, instance_template_original,
                     instance_template_new, self.GetScopeFlag()))[0]
    self.assertEqual(result.targetSize, 5)
    self.assertEqual(result.updatePolicy.maxSurge.calculated, max_surge)
    self.assertEqual(result.updatePolicy.maxUnavailable.calculated,
                     max_unavailable)
    self.assertEqual(str(result.updatePolicy.minimalAction), 'REPLACE')
    self.assertEqual(str(result.updatePolicy.type), 'PROACTIVE')

    self.assertRegexpMatches(result.versions[0].instanceTemplate,
                             '.*' + instance_template_original)
    self.assertEqual(result.versions[0].targetSize.calculated, 2)
    self.assertRegexpMatches(result.versions[1].instanceTemplate,
                             '.*' + instance_template_new)
    self.assertEqual(result.versions[1].targetSize.calculated, 3)
    self.assertEqual(result.versions[1].targetSize.fixed, 3)

    result = self.Run('compute instance-groups managed rolling-action '
                      'stop-proactive-update {0} '
                      '--format=disable '
                      '{1}'.format(igm_name, self.GetScopeFlag()))[0]
    self.assertEqual(result.targetSize, 5)
    self.assertEqual(str(result.updatePolicy.type), 'OPPORTUNISTIC')
    self.assertRegexpMatches(result.versions[0].instanceTemplate,
                             '.*' + instance_template_original)
    self.assertEqual(result.versions[0].targetSize.calculated, 2)
    self.assertRegexpMatches(result.versions[1].instanceTemplate,
                             '.*' + instance_template_new)
    self.assertEqual(result.versions[1].targetSize.calculated, 3)
    self.assertEqual(result.versions[1].targetSize.fixed, 3)
