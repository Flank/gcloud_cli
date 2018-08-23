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
"""Integration tests for creating/using/deleting instances."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.calliope import base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_instances_test_base


class InstancesTest(e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.template_name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='instance-from-instance-template', sequence_start=1)
    self.template_name = next(self.template_name_generator)
    self.Run(
        'compute instance-templates create {}'.format(self.template_name),
        track=base.ReleaseTrack.GA)

  def TearDown(self):
    # Raise exception only if there is no active exception to preserve original
    # error in test report.
    can_raise = not sys.exc_info()
    try:
      self.Run('compute instance-templates delete {} --quiet'.format(
          self.template_name), track=base.ReleaseTrack.GA)
    except:  # pylint:disable=bare-except
      if can_raise:
        raise

  def testCreate(self):
    instance_name = self.GetInstanceName()
    result = next(iter(self.Run(
        'compute instances create {} '
        '--source-instance-template {} '
        '--format=disable '
        '--zone={}'.format(instance_name, self.template_name, self.zone))))
    self.assertEqual(result.name, instance_name, result)

  def testCreateWithContainer(self):
    instance_name = self.GetInstanceName()
    result = next(iter(self.Run(
        'compute instances create-with-container {} '
        '--source-instance-template {} '
        '--format=disable '
        '--container-image=gcr.io/google-containers/busybox '
        '--zone={}'.format(instance_name, self.template_name, self.zone))))
    self.assertEqual(result.name, instance_name, result)
