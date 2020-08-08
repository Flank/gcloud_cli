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
"""Unit tests for the intance_utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute import scope as compute_scopes
from googlecloudsdk.core import resources as cloud_resources
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case


class InstanceUtilsTest(cli_test_base.CliTestBase,
                        sdk_test_base.WithFakeAuth,
                        parameterized.TestCase):

  def SetUp(self):
    self.compute_api = base_classes.ComputeApiHolder(
        calliope_base.ReleaseTrack.GA)
    self.messages = self.compute_api.client.messages
    self.resources = self.compute_api.resources

  @parameterized.parameters(
      ('https://compute.googleapis.com/compute/v1/projects/'
       'my-project/zones/us-west1-a/disks/disk-1',
       compute_scopes.ScopeEnum.ZONE,
       'projects/my-project/zones/us-west1-a/disks/disk-1'),
      ('projects/my-project/zones/us-west1-a/disks/disk-1',
       compute_scopes.ScopeEnum.ZONE,
       'projects/my-project/zones/us-west1-a/disks/disk-1'),
      ('projects/my-project/regions/us-west1/disks/disk-1',
       compute_scopes.ScopeEnum.ZONE,
       'projects/project/zones/us-central1-a/disks/'
       'projects/my-project/regions/us-west1/disks/disk-1'),
      ('anything',
       compute_scopes.ScopeEnum.ZONE,
       'projects/project/zones/us-central1-a/disks/anything'),
      ('https://compute.googleapis.com/compute/v1/projects/'
       'my-project/regions/us-west1/disks/disk-1',
       compute_scopes.ScopeEnum.REGION,
       'projects/my-project/regions/us-west1/disks/disk-1'),
      ('projects/my-project/regions/us-west1/disks/disk-1',
       compute_scopes.ScopeEnum.REGION,
       'projects/my-project/regions/us-west1/disks/disk-1'),
      ('projects/my-project/zones/us-west1-a/disks/disk-1',
       compute_scopes.ScopeEnum.REGION,
       'projects/project/regions/us-central1/disks/'
       'projects/my-project/zones/us-west1-a/disks/disk-1'),
      ('anything',
       compute_scopes.ScopeEnum.REGION,
       'projects/project/regions/us-central1/disks/anything'),
  )
  def testParseDiskResource(self, name, disk_type, expected_rel_name):
    parsed = instance_utils.ParseDiskResource(self.resources, name,
                                              'project', 'us-central1-a',
                                              disk_type)
    self.assertEqual(parsed.RelativeName(), expected_rel_name)

  @parameterized.parameters(
      ('https://compute.googleapis.com/compute/v1/projects/'
       'my-project/zones/us-west1-a/disks/disk-1',
       compute_scopes.ScopeEnum.REGION),
      ('https://compute.googleapis.com/compute/v1/projects/'
       'my-project/regions/us-west1/disks/disk-1',
       compute_scopes.ScopeEnum.ZONE),
  )
  def testParseDiskResourceRaisesException(self, name, disk_type):
    with self.assertRaises(cloud_resources.WrongResourceCollectionException):
      instance_utils.ParseDiskResource(self.resources, name,
                                       'project', 'us-central1-a', disk_type)

  @parameterized.parameters(
      ('https://compute.googleapis.com/compute/v1/projects/'
       'my-project/zones/us-central1-a/disks/disk-1',
       'projects/my-project/zones/us-central1-a/disks/disk-1'),
      ('projects/my-project/zones/us-central1-a/disks/disk-1',
       'projects/my-project/zones/us-central1-a/disks/disk-1'),
      ('https://compute.googleapis.com/compute/v1/projects/'
       'my-project/regions/us-central1/disks/disk-1',
       'projects/my-project/regions/us-central1/disks/disk-1'),
      ('projects/my-project/regions/us-central1/disks/disk-1',
       'projects/my-project/regions/us-central1/disks/disk-1'),
  )
  def testParseDiskResourceFromAttachedDisk(self, source, expected_rel_name):
    attached_disk = self.messages.AttachedDisk(
        deviceName='device-1',
        source=source)
    parsed = instance_utils.ParseDiskResourceFromAttachedDisk(self.resources,
                                                              attached_disk)
    self.assertEqual(parsed.RelativeName(), expected_rel_name)

  @parameterized.parameters(
      ('zones/us-central1-a/disks/disk-1',
       cloud_resources.InvalidResourceException),
      ('regions/us-central1/disks/disk-1',
       cloud_resources.InvalidResourceException),
  )
  def testParseDiskResourceFromAttachedDiskRaisesExceptions(self, source,
                                                            expected_exception):
    attached_disk = self.messages.AttachedDisk(
        deviceName='device-1',
        source=source)
    with self.assertRaises(expected_exception):
      instance_utils.ParseDiskResourceFromAttachedDisk(self.resources,
                                                       attached_disk)


if __name__ == '__main__':
  test_case.main()
