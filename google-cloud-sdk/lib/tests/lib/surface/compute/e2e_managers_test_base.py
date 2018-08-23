# -*- coding: utf-8 -*- #
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
"""Module for instance-groups managed integration test base classes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class ManagedTestBase(e2e_test_base.BaseTest):
  """Base class for instance-groups managed tests."""

  DEFAULT_DISK_IMAGE_FAMILY = 'centos-7'
  DEFAULT_DISK_IMAGE_PROJECT = 'centos-cloud'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

    # Containers for created resources.
    self.instance_template_names = []
    self.instance_group_manager_names = []
    self.region_instance_group_manager_names = []
    self.target_pool_names = []
    self.instance_uris = []

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
    self.DeleteResources(self.target_pool_names, self.DeleteTargetPool,
                         'target pool')
    self.DeleteResources(self.instance_uris, self.DeleteInstanceByUri,
                         'instance')

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

  def CreateInstanceTemplate(self,
                             machine_type='n1-standard-1',
                             additional_disks=None):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    command = 'compute instance-templates create {0} --machine-type {1}'.format(
        name, machine_type)
    for additional_disk in additional_disks or []:
      command += (' --create-disk device-name={0},image-family={1},'
                  'image-project={2},auto-delete=yes').format(
                      additional_disk, self.DEFAULT_DISK_IMAGE_FAMILY,
                      self.DEFAULT_DISK_IMAGE_PROJECT)
    self.Run(command)
    self.instance_template_names.append(name)
    self.AssertNewOutputContains(name)
    return name

  def CreateTargetPool(self):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    self.Run('compute target-pools create {0} --region {1}'
             .format(name, e2e_test_base.REGION))
    self.target_pool_names.append(name)
    self.AssertNewOutputContains(name)
    return name

  def CreateInstanceGroupManager(
      self, instance_template_name, size=0, scope_flag=None):
    if scope_flag is None:
      scope_flag = self.GetScopeFlag()
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    if self.scope == e2e_test_base.ZONAL:
      self.instance_group_manager_names.append(name)
    elif self.scope == e2e_test_base.REGIONAL:
      self.region_instance_group_manager_names.append(name)

    self.Run('compute instance-groups managed create {0} '
             '{1} '
             '--base-instance-name {0} '
             '--size {2} '
             '--template {3}'
             .format(name, scope_flag, size, instance_template_name))
    self.AssertNewOutputContains(name)
    return name

  def CreateInstanceTemplateAndInstanceGroupManager(self, size=0):
    instance_template_name = self.CreateInstanceTemplate()
    return self.CreateInstanceGroupManager(instance_template_name, size)

  def DescribeManagedInstanceGroup(self, name):
    self.Run("""
      compute instance-groups managed describe {group_name} \
        {scope_flag}""".format(group_name=name, scope_flag=self.GetScopeFlag()))

  def RunInstanceGroupManagerCreationTest(self, scope_flag=None):
    instance_template_name = self.CreateInstanceTemplate()
    igm_name = self.CreateInstanceGroupManager(
        instance_template_name, scope_flag=scope_flag)
    self.Run('compute instance-groups managed list')
    self.AssertNewOutputContains(igm_name)

  def GetNumInstances(self, igm_name):
    self.ClearOutput()
    self.ClearErr()
    self.Run('compute instance-groups managed list-instances {0} '
             '{1}'.format(igm_name, self.GetScopeFlag()))
    line_count = self.GetNewOutput(reset=True).count('\n')
    if line_count > 1:
      # Non-empty table output - subtract 1 line for the heading.
      return line_count - 1
    else:
      # Confirm that there was no table output.
      self.AssertNewErrContains('Listed 0 items.')
    return line_count

  def GetInstanceUris(self, igm_name):
    self.ClearOutput()
    self.Run('compute instance-groups managed list-instances {0} '
             '--uri '
             '{1}'.format(igm_name, self.GetScopeFlag()))
    output = self.GetNewOutput()
    return re.findall(r'\S+', output)

  def WaitUntilStable(self, igm_name):
    self.Run('compute instance-groups managed wait-until-stable {0} '
             '--timeout 600 '
             '{1}'.format(igm_name, self.GetScopeFlag()))
    self.AssertNewErrNotContains('Timeout')

  def Resize(self, igm_name, size):
    self.Run('compute instance-groups managed resize {0} '
             '--size {1} '
             '{2}'.format(igm_name, size, self.GetScopeFlag()))
    self.WaitUntilStable(igm_name)

  def RunResizeTest(self):
    igm_name = self.CreateInstanceTemplateAndInstanceGroupManager()

    self.Resize(igm_name, 4)
    self.assertEqual(4, self.GetNumInstances(igm_name))

    self.Resize(igm_name, 2)
    self.assertEqual(2, self.GetNumInstances(igm_name))

  def RunSetInstanceTemplateAndRecreateTest(self):
    machine_type1 = 'n1-standard-1'
    machine_type2 = 'f1-micro'
    instance_template_name1 = (
        self.CreateInstanceTemplate(machine_type=machine_type1))
    igm_name = self.CreateInstanceGroupManager(instance_template_name1, size=1)
    self.WaitUntilStable(igm_name)
    instance_uris = self.GetInstanceUris(igm_name)
    self.assertEqual(1, len(instance_uris))
    self.Run('compute instances describe {0}'.format(instance_uris[0]))
    self.AssertNewOutputContains(machine_type1)

    instance_template_name2 = (
        self.CreateInstanceTemplate(machine_type=machine_type2))
    self.Run('compute instance-groups managed set-instance-template {0} '
             '--template {1} '
             '{2}'
             .format(igm_name, instance_template_name2, self.GetScopeFlag()))
    self.Run('compute instances describe {0}'.format(instance_uris[0]))
    self.AssertNewOutputContains(machine_type1)

    self.Run('compute instance-groups managed recreate-instances {0} '
             '--instances {1} '
             '{2}'.format(igm_name, instance_uris[0], self.GetScopeFlag()))
    self.WaitUntilStable(igm_name)

    self.Run('compute instances describe {0}'.format(instance_uris[0]))
    self.AssertNewOutputContains(machine_type2)

  def RunDeleteInstancesTest(self):
    igm_name = self.CreateInstanceTemplateAndInstanceGroupManager(size=1)
    self.WaitUntilStable(igm_name)
    instance_uris = self.GetInstanceUris(igm_name)
    self.assertEqual(1, len(instance_uris))

    self.Run('compute instance-groups managed delete-instances {0} '
             '--instances {1} '
             '{2}'.format(igm_name, instance_uris[0], self.GetScopeFlag()))
    self.WaitUntilStable(igm_name)
    self.assertEqual(0, self.GetNumInstances(igm_name))

  def RunAbandonInstancesTest(self):
    igm_name = self.CreateInstanceTemplateAndInstanceGroupManager(size=1)
    self.WaitUntilStable(igm_name)
    instance_uris = self.GetInstanceUris(igm_name)
    self.assertEqual(1, len(instance_uris))

    # Add instance for later cleanup, as it is not managed by IGM anymore.
    self.instance_uris.append(instance_uris[0])
    self.Run('compute instance-groups managed abandon-instances {0} '
             '--instances {1} '
             '{2}'.format(igm_name, instance_uris[0], self.GetScopeFlag()))
    self.WaitUntilStable(igm_name)
    self.assertEqual(0, self.GetNumInstances(igm_name))

  def RunNamedPortsTest(self):
    igm_name = self.CreateInstanceTemplateAndInstanceGroupManager()

    service_name = 'my-service'
    service_port = '1234'
    self.Run('compute instance-groups managed set-named-ports {0} '
             '--named-ports {1}:{2} '
             '{3}'
             .format(igm_name, service_name, service_port, self.GetScopeFlag()))
    self.Run('compute instance-groups managed get-named-ports {0} '
             '{1}'.format(igm_name, self.GetScopeFlag()))
    self.AssertNewOutputContains(service_name, reset=False)
    self.AssertNewOutputContains(service_port)


if __name__ == '__main__':
  e2e_test_base.main()
