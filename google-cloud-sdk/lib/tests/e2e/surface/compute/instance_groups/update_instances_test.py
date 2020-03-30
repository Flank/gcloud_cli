# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Integration tests for gcloud update-instances (ApplyUpdatesToInstances API call)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib.surface.compute import e2e_managers_stateful_test_base
from tests.lib.surface.compute import e2e_test_base


class ManagedInstanceGroupsUpdateInstancesBetaZonalTest(
    e2e_managers_stateful_test_base.ManagedStatefulTestBase):

  def SetUp(self):
    self.prefix = 'mig-update-instances-zonal'
    self.scope = e2e_test_base.ZONAL
    self.track = calliope_base.ReleaseTrack.GA

  def _SetInstanceTemplate(self, igm_name, template_name):
    """Update instance template for group to template_name."""
    self.Run("""\
        compute instance-groups managed set-instance-template \
          {group_name} \
          {scope_flag} \
          --template {template}
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        template=template_name))

  def _DescribeInstance(self, instance_uri):
    instance_name = self._ExtractInstanceNameFromUri(instance_uri)
    zone_flag = '--zone {zone_name}'.format(
        zone_name=self.ExtractZoneFromUri(instance_uri))
    self.Run('compute instances describe {instance} {zone_flag}'
             .format(instance=instance_name, zone_flag=zone_flag))

  def _GetInstanceId(self, instance_uri):
    self.ClearOutput()
    self._DescribeInstance(instance_uri)
    new_output = self.GetNewOutput(reset=True)
    return re.search(r"id: '([0-9]+)'", new_output).group(1)

  def _ListInstanceConfigs(self, group_name):
    self.Run("""\
        compute instance-groups managed instance-configs list \
          {group_name} \
          {scope_flag}
    """.format(group_name=group_name, scope_flag=self.GetScopeFlag()))

  @staticmethod
  def ExtractZoneFromUri(uri):
    return re.search(r'/zones/([^/]+)/', uri).group(1)

  @staticmethod
  def _ExtractInstanceNameFromUri(uri):
    return re.search(r'/instances/([^/]+)', uri).group(1)

  def testUpdateInstancesNormalUsage(self):
    template1_name = self.CreateInstanceTemplate()
    template2_name = self.CreateInstanceTemplate(machine_type='n1-standard-4')
    igm_name = self.CreateInstanceGroupManagerStateful(template1_name, size=1)
    self.WaitUntilStable(igm_name)
    instance_uri = self.GetInstanceUris(igm_name)[0]
    self._SetInstanceTemplate(igm_name, template2_name)
    self._DescribeInstance(instance_uri)
    self.AssertNewOutputContains('n1-standard-1')
    self.AssertNewOutputNotContains('n1-standard-4')
    self.Run("""\
        compute instance-groups managed update-instances {group_name} \
          {scope_flag} \
          --instances {instance}
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        instance=self._ExtractInstanceNameFromUri(instance_uri)))
    self.WaitUntilStable(igm_name)
    self._DescribeInstance(instance_uri)
    self.AssertNewOutputContains('n1-standard-4')
    self.AssertNewOutputNotContains('n1-standard-1')

  def testUpdateInstancesMostDisruptiveAllowedAction(self):
    template1_name = self.CreateInstanceTemplate()
    template2_name = self.CreateInstanceTemplate(machine_type='n1-standard-4')
    igm_name = self.CreateInstanceGroupManagerStateful(template1_name, size=1)
    self.WaitUntilStable(igm_name)
    instance_uri = self.GetInstanceUris(igm_name)[0]
    old_instance_id = self._GetInstanceId(instance_uri)
    self._SetInstanceTemplate(igm_name, template2_name)
    with self.AssertRaisesExceptionRegexp(
        exceptions.ToolException,
        r"""Effective update action .* is REPLACE, which is """
        r"""greater than the most disruptive allowed action REFRESH .*"""):
      self.Run("""\
          compute instance-groups managed update-instances {group_name} \
            {scope_flag} \
            --instances {instance} --most-disruptive-allowed-action refresh
      """.format(
          group_name=igm_name,
          scope_flag=self.GetScopeFlag(),
          instance=self._ExtractInstanceNameFromUri(instance_uri)))
    self.WaitUntilStable(igm_name)
    instance_uri = self.GetInstanceUris(igm_name)[0]
    new_instance_id = self._GetInstanceId(instance_uri)
    # Check that the instance was not replaced
    self.assertEqual(old_instance_id, new_instance_id)
    self.ClearOutput()
    self._DescribeInstance(instance_uri)
    self.AssertNewOutputContains('n1-standard-1')
    self.AssertNewOutputNotContains('n1-standard-4')

  def testUpdateInstancesMinimalAction(self):
    template1_name = self.CreateInstanceTemplate()
    igm_name = self.CreateInstanceGroupManagerStateful(template1_name, size=1)
    self.WaitUntilStable(igm_name)
    instance_uri = self.GetInstanceUris(igm_name)[0]
    old_instance_id = self._GetInstanceId(instance_uri)
    self.Run("""\
        compute instance-groups managed update-instances {group_name} \
          {scope_flag} \
          --instances {instance} --minimal-action replace
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        instance=self._ExtractInstanceNameFromUri(instance_uri)))
    self.WaitUntilStable(igm_name)
    instance_uri = self.GetInstanceUris(igm_name)[0]
    new_instance_id = self._GetInstanceId(instance_uri)
    # Check that the instance was replaced
    self.assertNotEqual(old_instance_id, new_instance_id)


class ManagedInstanceGroupsUpdateInstancesBetaRegionalTest(
    ManagedInstanceGroupsUpdateInstancesBetaZonalTest):

  def SetUp(self):
    self.prefix = 'mig-update-instances-regional'
    self.scope = e2e_test_base.REGIONAL


if __name__ == '__main__':
  e2e_test_base.main()
