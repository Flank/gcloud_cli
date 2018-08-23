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
"""Integration tests for creating/using/deleting instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.resource import resource_projector
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class InstancesMinCpuPlatformTest(
    e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.zone = 'us-central1-a'  # Only this zone supports minimum CPU platform

  def GetCpuPlatforms(self):
    result = self.Run(
        'compute zones describe {} --format=disable'.format(self.zone))
    return result.availableCpuPlatforms

  def testInstanceWithMinCpuPlatform(self):
    self.GetInstanceName()
    cpu_platforms = self.GetCpuPlatforms()
    self.assertGreater(len(cpu_platforms), 1,
                       msg='Zone has less than 2 CPU platforms available')
    instance = list(self.Run(
        'compute instances create {} --zone {} --min-cpu-platform "{}" '
        '--format=disable'.format(self.instance_name, self.zone,
                                  cpu_platforms[0])))[0]
    instance = resource_projector.MakeSerializable(instance)
    result = self.Run(
        'compute instances describe {} --format=disable'.format(
            instance['selfLink']))
    self.assertEqual(cpu_platforms[0], result.cpuPlatform)

    # Stop instance and change CPU Platform
    self.Run(
        'compute instances stop {}'.format(instance['selfLink']))

    self.Run(
        'compute instances update {} --min-cpu-platform "{}"'.
        format(instance['selfLink'], cpu_platforms[1]))

    # Start again and check CPU platform
    # TODO(b/33488865) - Don't start when this bug get fix.
    result = self.Run(
        'compute instances start {} --format=disable'.format(
            instance['selfLink']))[0]

    self.assertEqual(cpu_platforms[1], result.cpuPlatform)


if __name__ == '__main__':
  e2e_test_base.main()
