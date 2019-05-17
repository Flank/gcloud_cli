# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Integration tests for describing instance's OS inventory data."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.instances.os_inventory import exceptions
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


# Setup instructions for the required static resource is at
# go/os-inventory-cloud-sdk-test-resource-setup.
class DescribeTestAlpha(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.instance_names_used = []

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.instance_names_used:
      self.CleanUpResource(name, 'instances')

  def GetInstanceName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up.
    name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='compute-instances-os-inventory'))
    self.instance_names_used.append(name)
    return name

  def testDescribeWithInventoryData(self):
    name = 'do-not-delete-compute-instances-os-inventory-test'
    zone = 'us-east1-b'
    self.Run('compute instances os-inventory describe {0} --zone {1}'.format(
        name, zone))
    self.AssertNewOutputContainsAll([
        'x86_64', 'do-not-delete-compute-instances-os-inventory-test', 'debian'
    ])

  def testDescribeWithoutInventoryData(self):
    name = self.GetInstanceName()
    self.CreateInstance(name)
    with self.assertRaises(exceptions.OsInventoryNotFoundException):
      self.Run('compute instances os-inventory describe {0} --zone {1}'.format(
          name, self.zone))
    self.AssertNewErrContains(
        'OS inventory data was not found. Make sure the OS Config agent is '
        'running on this instance.'
    )

    # Cleanup.
    self.DeleteInstance(name)


if __name__ == '__main__':
  e2e_test_base.main()
