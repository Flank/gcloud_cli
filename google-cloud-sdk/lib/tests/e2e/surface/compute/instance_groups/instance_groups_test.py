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
"""Integration tests for instance groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class InstanceGroupsTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.prefix = 'gcloud-instance-groups-test'
    # Note: also change compute.tests.integration.test_base.BaseTest when the
    # track changes
    self.track = calliope_base.ReleaseTrack.GA

    # Containers for created resources.
    self.instance_group_names = []
    self.instance_names = []

  def TearDown(self):
    self.DeleteResources(self.instance_names,
                         self.DeleteInstance,
                         'instance')
    self.DeleteResources(self.instance_group_names,
                         self.DeleteInstanceGroup,
                         'instance group')

  def CreateInstanceGroup(self):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    self.Run('compute instance-groups unmanaged create {0} --zone {1}'
             .format(name, self.zone))
    self.AssertNewOutputContains(name)
    self.instance_group_names.append(name)
    return name

  def CreateInstance(self):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    self.Run('compute instances create {0} --zone {1}'.format(name, self.zone))
    self.AssertNewOutputContains(name)
    self.instance_names.append(name)
    return name

  def testInstanceGroupCreation(self):
    name = self.CreateInstanceGroup()
    self.Run('compute instance-groups list')
    self.AssertNewOutputContains(name)

  def testInstanceAddAndRemove(self):
    instance_group_name = self.CreateInstanceGroup()
    instance_name = self.CreateInstance()

    # Add instance
    self.Run('compute instance-groups unmanaged add-instances {0} '
             '--instances {1} --zone {2}'
             .format(instance_group_name, instance_name, self.zone))
    self.Run(('compute instance-groups unmanaged list-instances {0} '
              '--zone {1}').format(instance_group_name, self.zone))
    self.AssertNewOutputContains(instance_name)

    # Remove instance
    self.Run('compute instance-groups unmanaged remove-instances {0} '
             '--instances {1} --zone {2}'
             .format(instance_group_name, instance_name, self.zone))
    self.Run(('compute instance-groups unmanaged list-instances {0} '
              '--zone {1}').format(instance_group_name, self.zone))
    self.AssertNewOutputNotContains(instance_name)

  def testNamedPorts(self):
    instance_group_name = self.CreateInstanceGroup()

    service_name = 'my-service'
    service_port = '1234'
    self.Run('compute instance-groups unmanaged set-named-ports {0} '
             '--named-ports {1}:{2} --zone {3}'.format(
                 instance_group_name, service_name, service_port, self.zone))
    self.Run(('compute instance-groups unmanaged get-named-ports {0} '
              '--zone {1}').format(instance_group_name, self.zone))
    self.AssertNewOutputContains(service_name, reset=False)
    self.AssertNewOutputContains(service_port)


if __name__ == '__main__':
  e2e_test_base.main()
