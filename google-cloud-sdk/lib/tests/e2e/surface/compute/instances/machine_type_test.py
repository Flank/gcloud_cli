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
"""Integration tests for creating/using/deleting instances."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class InstancesMachineTypeTest(e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _TestInstanceSetCustomMachineType(self, custom_cpu, custom_memory):
    self.Run('compute instances stop --quiet --zone {0} {1}'.format(
        self.zone, self.instance_name))

    self.Run('compute instances set-machine-type '
             '--custom-cpu {0} --custom-memory {1} '
             '--zone {2} {3}'
             .format(custom_cpu, custom_memory, self.zone, self.instance_name))


if __name__ == '__main__':
  e2e_test_base.main()
