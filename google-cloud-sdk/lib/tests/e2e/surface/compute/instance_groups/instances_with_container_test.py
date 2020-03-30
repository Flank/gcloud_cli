# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Integration tests for Kontainers-on-GCE."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


CONTAINER_IMAGE = 'gcr.io/google-containers/nginx:latest'

TEST_SCRIPT = """\
until sudo docker ps | grep -q nginx; do sleep 1; done; sudo docker ps"""


class InstancesWithContainerTest(e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.prefix = b'create-with-container'
    self.track = calliope_base.ReleaseTrack.ALPHA

    # Containers for created resources.
    self.instance_group_manager_names = []
    self.instance_template_names = []
    self.instance_names = []

  def TearDown(self):
    self.DeleteResources(self.instance_names,
                         self.DeleteInstance,
                         'instance')
    self.DeleteResources(self.instance_group_manager_names,
                         self.DeleteInstanceGroupManager,
                         'instance group manager')
    try:
      self.DeleteResources(self.instance_template_names,
                           self.DeleteInstanceTemplate, 'instance template')
    except AssertionError:
      # Cleanup script should handle teardown issues
      pass

  def testInstanceFromContainer(self):
    self.GetInstanceName()
    name = self.instance_name
    self.Run('compute instances create-with-container {0} '
             '--zone {1} '
             '--container-image "{2}"'.format(name, self.zone, CONTAINER_IMAGE))

  def testInstanceGroupFromContainer(self):
    self.GetInstanceName()
    name = self.instance_name
    self.Run('compute instance-templates create-with-container {0} '
             '--machine-type n1-standard-1 '
             '--container-image "{1}"'.format(name, CONTAINER_IMAGE))
    self.AssertNewOutputContains(name)
    self.instance_template_names.append(name)

    self.Run('compute instance-groups managed create {0} '
             '--zone {1} '
             '--size {2} '
             '--template {3}'
             .format(name, self.zone, 1, name))
    self.AssertNewOutputContains(name)
    self.instance_group_manager_names.append(name)

    self.Run('compute instance-groups managed wait-until --stable {0} '
             '--timeout 600 '
             '--zone {1}'.format(name, self.zone))
    self.AssertNewErrNotContains('Timeout')

    self.ClearOutput()
    self.Run('compute instance-groups managed list-instances {0} '
             '--uri '
             '--zone {1}'
             .format(name, self.zone))


if __name__ == '__main__':
  e2e_test_base.main()
