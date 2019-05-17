# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Integration tests for instance-configs (MIG subresources)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_managers_stateful_test_base
from tests.lib.surface.compute import e2e_test_base


class ManagedInstanceGroupsInstanceConfigsZonalTest(
    e2e_managers_stateful_test_base.ManagedStatefulTestBase):

  def SetUp(self):
    self.prefix = 'mig-instance-configs-zonal'
    self.scope = e2e_test_base.ZONAL
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _ListInstanceConfigs(self, group_name):
    self.Run("""\
        compute instance-groups managed instance-configs list {group_name} \
          {scope_flag}
    """.format(group_name=group_name, scope_flag=self.GetScopeFlag()))

  def _CreateInstanceConfigs(self, name, instance, stateful_disks):
    command = """\
      compute instance-groups managed instance-configs create {group_name} \
        {scope_flag} \
        --instance {instance}""".format(
            group_name=name, scope_flag=self.GetScopeFlag(), instance=instance)
    for stateful_disk in stateful_disks:
      command += (' --stateful-disk device-name={disk_name}'.format(
          disk_name=stateful_disk))
    self.Run(command)

  @staticmethod
  def _ExtractZoneFromUri(uri):
    return re.search(r'/zones/([^/]+)/', uri).group(1)

  @staticmethod
  def _ExtractInstanceNameFromUri(uri):
    return re.search(r'/instances/([^/]+)', uri).group(1)

  def testCreateEmptyInstanceConfig(self):
    instance_template_name = self.CreateInstanceTemplate()
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template_name, size=1)
    self.WaitUntilStable(igm_name)
    instance_uri = self.GetInstanceUris(igm_name)[0]
    self.Run("""\
        compute instance-groups managed instance-configs create {group_name} \
          {scope_flag} \
          --instance {instance}
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        instance=instance_uri))
    self._ListInstanceConfigs(igm_name)
    self.AssertOutputContains(
        'name: {0}'.format(self._ExtractInstanceNameFromUri(instance_uri)))
    self.AssertOutputNotContains('deviceName:')

  def testCreateInstanceConfigWithStatefulDisksAndForceInstanceUpdate(self):
    instance_template_name = self.CreateInstanceTemplate(
        additional_disks=['disk1', 'disk2'])
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template_name, size=1)
    self.WaitUntilStable(igm_name)
    instance_uri = self.GetInstanceUris(igm_name)[0]
    instance_zone = self._ExtractZoneFromUri(instance_uri)
    new_disk_uri = self.CreateDisk(zone=instance_zone)
    self.Run("""\
        compute instance-groups managed instance-configs create {group_name} \
          {scope_flag} \
          --instance {instance} \
          --stateful-disk device-name=disk1 \
          --stateful-disk device-name=disk3,source={source} \
          --force-instance-update
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        instance=instance_uri,
        source=new_disk_uri))
    self.ClearOutput()
    self._ListInstanceConfigs(igm_name)
    self.AssertNewOutputContainsAll([
        'name: {0}'.format(self._ExtractInstanceNameFromUri(instance_uri)),
        """\
        disk3:
          autoDelete: NEVER
        """,
        """\
        disk1:
          autoDelete: NEVER
        """
    ], normalize_space=True)
    self.AssertOutputNotContains('disk2')
    self.WaitUntilStable(igm_name)
    self.ClearOutput()
    self.DescribeInstance(instance_uri)
    self.AssertNewOutputContainsAll([
        'deviceName: disk3', 'source: {0}'.format(new_disk_uri), 'boot: false'
    ])

  def testUpdateInstanceConfigEditStatefulDisks(self):
    instance_template_name = self.CreateInstanceTemplate(
        additional_disks=['disk1', 'disk2', 'disk3'])
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template_name, size=1)
    self.WaitUntilStable(igm_name)
    instance_uri = self.GetInstanceUris(igm_name)[0]
    self._CreateInstanceConfigs(igm_name, instance_uri, ['disk1', 'disk3'])
    self.Run("""\
        compute instance-groups managed instance-configs update {group_name} \
          {scope_flag} \
          --instance {instance} \
          --update-stateful-disk device-name=disk2 \
          --remove-stateful-disks disk3
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        instance=instance_uri))
    self._ListInstanceConfigs(igm_name)
    self.AssertNewOutputContainsAll([
        """\
        disk1:
          autoDelete: NEVER
        """,
        """\
        disk2:
          autoDelete: NEVER
        """,
        'name: {0}'.format(self._ExtractInstanceNameFromUri(instance_uri))
    ], normalize_space=True)
    self.AssertOutputNotContains('disk3')

  def testUpdateInstanceConfigRemoveAllStatefulDisks(self):
    instance_template_name = self.CreateInstanceTemplate(
        additional_disks=['disk1', 'disk2'])
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template_name, size=1)
    self.WaitUntilStable(igm_name)
    instance_uri = self.GetInstanceUris(igm_name)[0]
    self._CreateInstanceConfigs(igm_name, instance_uri, ['disk1', 'disk2'])
    self.Run("""\
        compute instance-groups managed instance-configs update {group_name} \
          {scope_flag} \
          --instance {instance} \
          --remove-stateful-disks disk1,disk2
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        instance=instance_uri))
    self._ListInstanceConfigs(igm_name)
    self.AssertNewOutputContainsAll(
        ['name: {0}'
         .format(self._ExtractInstanceNameFromUri(instance_uri))])
    self.AssertOutputNotContains('disk1')
    self.AssertOutputNotContains('disk2')

  def testDeleteInstanceConfigs(self):
    instance_template_name = self.CreateInstanceTemplate(
        additional_disks=['disk1', 'disk2'])
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template_name, size=2)
    self.WaitUntilStable(igm_name)
    instance_uris = self.GetInstanceUris(igm_name)
    self._CreateInstanceConfigs(igm_name, instance_uris[0], ['disk1', 'disk2'])
    self._CreateInstanceConfigs(igm_name, instance_uris[1], ['disk1'])
    self.Run("""\
        compute instance-groups managed instance-configs delete {group_name} \
          {scope_flag} \
          --instances {instances}
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        instances=','.join(instance_uris)))
    self._ListInstanceConfigs(igm_name)
    self.AssertErrContains('Listed 0 items')

  def testListInstanceConfigs(self):
    instance_template_name = self.CreateInstanceTemplate()
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template_name, size=1)
    self.WaitUntilStable(igm_name)
    instance_uri = self.GetInstanceUris(igm_name)[0]
    instance_zone = self._ExtractZoneFromUri(instance_uri)
    disk_uri = self.CreateDisk(zone=instance_zone)
    self.Run("""\
        compute instance-groups managed instance-configs create {group_name} \
          {scope_flag} \
          --instance {instance} \
          --stateful-disk device-name=disk1,source={source},mode=ro
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        instance=instance_uri,
        source=disk_uri))
    self._ListInstanceConfigs(igm_name)
    self.AssertNewOutputContainsAll([
        'name: {0}'.format(self._ExtractInstanceNameFromUri(instance_uri)),
        """\
        disk1:
          autoDelete: NEVER
        """,
        'mode: READ_ONLY', 'source: {0}'.format(disk_uri)
    ], normalize_space=True)


class ManagedInstanceGroupsInstanceConfigsRegionalTest(
    ManagedInstanceGroupsInstanceConfigsZonalTest):

  def SetUp(self):
    self.prefix = 'mig-instance-configs-regional'
    self.scope = e2e_test_base.REGIONAL


if __name__ == '__main__':
  e2e_test_base.main()
