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
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.instance_templates import create_test_base


class InstanceTemplatesCreateTest(
    create_test_base.InstanceTemplatesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testAcceleratorWithDefaultCount(self):
    self.Run("""
          compute instance-templates create template-1
            --accelerator type=nvidia-tesla-k80
          """)
    m = self.messages
    template = self._MakeInstanceTemplate(guestAccelerators=[
        m.AcceleratorConfig(
            acceleratorType='nvidia-tesla-k80', acceleratorCount=1)
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testAcceleratorWithSpecifiedCount(self):
    self.Run("""
          compute instance-templates create template-1
            --accelerator type=nvidia-tesla-k80,count=4
          """)
    m = self.messages
    template = self._MakeInstanceTemplate(guestAccelerators=[
        m.AcceleratorConfig(
            acceleratorType='nvidia-tesla-k80', acceleratorCount=4)
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testAcceleratorWithInvalidDictArg(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'Bad syntax for dict arg: \[invalid_value]'):
      self.Run("""
            compute instance-templates create template-1
              --accelerator invalid_value
            """)

  def testAcceleratorWithNoAcceleratorType(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--accelerator]: '
        r'accelerator type must be specified\.'):
      self.Run("""
            compute instance-templates create template-1
              --accelerator count=4
            """)


class InstanceTemplatesCreateTestBeta(InstanceTemplatesCreateTest,
                                      parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstanceTemplatesCreateTestAlpha(InstanceTemplatesCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
