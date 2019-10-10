# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Integration tests for stateful policy feature of instance group managers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_managers_stateful_test_base
from tests.lib.surface.compute import e2e_test_base


class ManagedInstanceGroupsStatefulPolicyZonalTest(
    e2e_managers_stateful_test_base.ManagedStatefulTestBase):

  def SetUp(self):
    self.prefix = 'mig-stateful-policy-zonal'
    self.scope = e2e_test_base.ZONAL
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreateManageInstanceGroupWithStatefulDisks(self):
    instance_template_name = self.CreateInstanceTemplate(
        additional_disks=['disk1', 'disk2', 'disk3'])
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template_name,
        stateful_disks=['disk1', 'disk3'])
    self.DescribeManagedInstanceGroup(igm_name)
    self.AssertNewOutputContainsAll([
        igm_name,
        'statefulPolicy',
        """\
          preservedState:
            disks:
              disk1:
                autoDelete: NEVER
              disk3:
                autoDelete: NEVER
        """,
    ], normalize_space=True)
    self.AssertOutputNotContains('disk2')

  def testUpdateManageInstanceGroupAddingStatefulDisks(self):
    instance_template_name = self.CreateInstanceTemplate(
        additional_disks=['disk1', 'disk2', 'disk3'])
    igm_name = self.CreateInstanceGroupManagerStateful(instance_template_name)
    self.UpdateInstanceGroupManagerStateful(
        name=igm_name, add_stateful_disks=['disk1', 'disk3'])
    self.DescribeManagedInstanceGroup(igm_name)
    self.AssertNewOutputContainsAll([
        igm_name,
        'statefulPolicy',
        """\
          preservedState:
            disks:
              disk1:
                autoDelete: NEVER
              disk3:
                autoDelete: NEVER
        """,
    ], normalize_space=True)
    self.AssertOutputNotContains('disk2')

  def testUpdateManageInstanceGroupRemovingStatefulDisks(self):
    instance_template_name = self.CreateInstanceTemplate(
        additional_disks=['disk1'])
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template_name)
    self.UpdateInstanceGroupManagerStateful(
        name=igm_name, add_stateful_disks=['disk1'])
    self.UpdateInstanceGroupManagerStateful(
        name=igm_name, remove_stateful_disks=['disk1'])
    self.DescribeManagedInstanceGroup(igm_name)
    self.AssertNewOutputContains(igm_name)

  def testUpdateManageInstanceGroupRemovingOneStatefulDisk(self):
    instance_template_name = self.CreateInstanceTemplate(
        additional_disks=['disk1', 'disk2', 'disk3'])
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template_name,
        stateful_disks=['disk1', 'disk3'])
    self.UpdateInstanceGroupManagerStateful(
        name=igm_name, remove_stateful_disks=['disk1'])
    self.DescribeManagedInstanceGroup(igm_name)
    self.AssertNewOutputContainsAll([
        igm_name,
        'statefulPolicy',
        """\
          preservedState:
            disks:
              disk3:
                autoDelete: NEVER
        """,
    ], normalize_space=True)
    self.AssertOutputNotContains('disk1')

  def testUpdateManageInstanceGroupRemovingAllStatefulDisks(self):
    instance_template_name = self.CreateInstanceTemplate(
        additional_disks=['disk1', 'disk2', 'disk3'])
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template_name,
        stateful_disks=['disk1', 'disk3'])
    self.UpdateInstanceGroupManagerStateful(
        name=igm_name,
        remove_stateful_disks=['disk1', 'disk3'])
    self.DescribeManagedInstanceGroup(igm_name)
    self.AssertNewOutputContainsAll([igm_name, 'statefulPolicy'])
    self.AssertOutputNotContains('disk1')
    self.AssertOutputNotContains('disk3')


class ManagedInstanceGroupsStatefulPolicyRegionalTest(
    ManagedInstanceGroupsStatefulPolicyZonalTest):

  def SetUp(self):
    self.prefix = 'mig-stateful-policy-regional'
    self.scope = e2e_test_base.REGIONAL


if __name__ == '__main__':
  e2e_test_base.main()
