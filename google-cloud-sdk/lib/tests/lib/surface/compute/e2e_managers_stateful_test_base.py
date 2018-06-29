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
"""Module for instance-groups managed stateful integration test base classes."""

from __future__ import absolute_import
from __future__ import unicode_literals
import re

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_managers_test_base
from tests.lib.surface.compute import e2e_test_base


class ManagedStatefulTestBase(e2e_managers_test_base.ManagedTestBase):
  """Base class for instance-groups managed tests around Stateful API."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def TearDown(self):
    # Remove all disks left for MIGs (they may not be deleted by design)
    for instance_group_manager_name in (
        self.instance_group_manager_names +
        self.region_instance_group_manager_names):
      for disk in self._GetDiskUris(instance_group_manager_name):
        try:
          self.DeleteDisk(disk)
        except (AssertionError, exceptions.ToolException):
          # Delete may not be successful for some cases (it may still be linked
          # to MIG being deleted), cleanup will take care for these
          pass

  def _GetDiskUris(self, filter_name):
    self.ClearOutput()
    self.Run('compute disks list --uri --filter name~{0}'.format(filter_name))
    output = self.GetNewOutput()
    return re.findall(r'\S+', output)

  def CreateInstanceGroupManagerStateful(self,
                                         instance_template_name,
                                         size=0,
                                         stateful_names=False,
                                         stateful_disks=None):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    if self.scope == e2e_test_base.ZONAL:
      self.instance_group_manager_names.append(name)
    elif self.scope == e2e_test_base.REGIONAL:
      self.region_instance_group_manager_names.append(name)
    command = """\
      compute instance-groups managed create {group_name} \
        {scope_flag} \
        --base-instance-name {group_name} \
        --size {size} \
        --template {template}""".format(
            group_name=name,
            scope_flag=self.GetScopeFlag(),
            size=size,
            template=instance_template_name)
    if stateful_names:
      command += """\
        --stateful-names"""
    if stateful_disks:
      command += """\
        --stateful-disks {0}""".format(','.join(stateful_disks))
    self.Run(command)
    self.AssertNewOutputContains(name)
    return name

  def UpdateInstanceGroupManagerStateful(self,
                                         name,
                                         add_stateful_names=False,
                                         remove_stateful_names=False,
                                         add_stateful_disks=None,
                                         remove_stateful_disks=None):
    command = """\
      compute instance-groups managed update {group_name} \
        {scope_flag}""".format(
            group_name=name, scope_flag=self.GetScopeFlag())
    if add_stateful_names:
      command += """\
        --stateful-names"""
    if remove_stateful_names:
      command += """\
        --no-stateful-names"""
    if add_stateful_disks:
      command += """\
        --add-stateful-disks {0}""".format(','.join(add_stateful_disks))
    if remove_stateful_disks:
      command += """\
        --remove-stateful-disks {0}""".format(','.join(remove_stateful_disks))
    self.Run(command)
    return name

  def DescribeInstance(self, name):
    self.Run('compute instances describe {name}'.format(name=name))

  def CreateDisk(self, zone=None):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    # Update seek position
    self.GetNewErr()
    self.Run("""
      compute disks create {disk_name} \
        --zone {zone} \
        --size 10GB""".format(disk_name=name, zone=zone or self.zone))
    stderr = self.GetNewErr()
    # Return URI to the disk
    return re.search(r'Created \[(.*)\]', stderr).group(1)


if __name__ == '__main__':
  e2e_test_base.main()
