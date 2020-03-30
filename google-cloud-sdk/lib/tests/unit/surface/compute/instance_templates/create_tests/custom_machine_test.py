# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute.instance_templates import create_test_base


class InstanceTemplatesCreateTestAlpha(
    create_test_base.InstanceTemplatesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def testWithoutCustomMemorySpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-cpu: --custom-memory must be specified.'):

      self.Run("""
          compute instance-templates create template-1
               --custom-cpu 4
          """)

  def testWithoutCustomCpuSpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-memory: --custom-cpu must be specified.'):

      self.Run("""
          compute instance-templates create template-1
               --custom-memory 4000
          """)

  def testWithMachineTypeAndCustomCpuSpecified(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Cannot set both \[--machine-type\] and \[--custom-cpu\]'):

      self.Run("""
          compute instance-templates create template-1
               --custom-cpu 4
               --custom-memory 4000
               --machine-type n1-standard-1
          """)

  def testWithCustomMachineType(self):
    m = self.messages

    self.Run("""
        compute instance-templates create template-1
          --custom-vm-type n2
          --custom-cpu 4
          --custom-memory 4096MiB
        """)

    template = self._MakeInstanceTemplate(machineType='n2-custom-4-4096')

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithExtendedCustomMachineType(self):
    m = self.messages

    self.Run("""
        compute instance-templates create template-1
          --custom-cpu 4
          --custom-memory 4096MiB
          --custom-extensions
        """)

    template = self._MakeInstanceTemplate(machineType='custom-4-4096-ext')

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )


if __name__ == '__main__':
  test_case.main()
