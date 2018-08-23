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
"""e2e tests for Cloud Filestore instances command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.filestore import e2e_test_base


class InstancesTests(e2e_test_base.InstancesTestBase):
  """E2E tests for Cloud Filestore instances command group."""

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA

  def testStandardTierInstance(self):
    tier = 'STANDARD'
    instance_name = self.GetInstanceName(prefix='filestore-test-instance')
    # The new instance should not be in the list yet.
    self.Run('filestore instances list --location {}'.format(self.location))
    self.AssertNewOutputNotContains(instance_name)
    args = (
        '--tier {} --file-share=name="my_vol",capacity=1TB '
        '--network=name=filestore-net,reserved-ip-range="{}"'.format(
            tier,
            self.NonDefaultRandCIDR()))
    with self.CreateInstance(instance_name, self.location, args):
      # Check that the instance is in the output list.
      self.Run('filestore instances list --location {}'.format(self.location))
      self.AssertNewOutputContains(instance_name)
      # Check that the instance details can be described.
      self.Run('filestore instances describe {0} --location {1}'.format(
          instance_name, self.location))
      new_output = self.GetNewOutput()
      self.assertIn(instance_name, new_output)
      self.assertIn(tier, new_output)
      # Update the instance.
      self.Run('filestore instances update {0} --location {1} --description '
               '"New description" --update-labels key1=value1 --file-share '
               'name="my_vol",capacity=2TB'
               .format(instance_name, self.location))
      # Check that the instance details can be described.
      self.Run('filestore instances describe {0} --location {1}'.format(
          instance_name, self.location))
      new_output = self.GetNewOutput()
      self.assertIn('New description', new_output)
      self.assertIn('key1', new_output)
      self.assertIn('2048', new_output)
    # Check that the instance is no longer in the output list.
    self.Run('filestore instances list --location {}'.format(self.location))
    self.AssertNewOutputNotContains(instance_name)


class InstancesAlphaTests(InstancesTests):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA

  def testStandardTierInstance(self):
    tier = 'STANDARD'
    instance_name = self.GetInstanceName(prefix='filestore-test-instance')
    # The new instance should not be in the list yet.
    self.Run('filestore instances list --location {}'.format(self.location))
    self.AssertNewOutputNotContains(instance_name)
    args = (
        '--tier {} --file-share=name="my_vol",capacity=1TB '
        '--network=name=filestore-net,reserved-ip-range="{}"'.format(
            tier,
            self.NonDefaultRandCIDR()))
    with self.CreateInstance(instance_name, self.location, args):
      # Check that the instance is in the output list.
      self.Run('filestore instances list --location {}'.format(self.location))
      self.AssertNewOutputContains(instance_name)
      # Check that the instance details can be described.
      self.Run('filestore instances describe {0} --location {1}'.format(
          instance_name, self.location))
      new_output = self.GetNewOutput()
      self.assertIn(instance_name, new_output)
      self.assertIn(tier, new_output)
    # Check that the instance is no longer in the output list.
    self.Run('filestore instances list --location {}'.format(self.location))
    self.AssertNewOutputNotContains(instance_name)


if __name__ == '__main__':
  test_case.main()
