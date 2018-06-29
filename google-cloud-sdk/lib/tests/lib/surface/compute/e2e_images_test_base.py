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
"""Base class for images integration testing."""
from __future__ import absolute_import
from __future__ import unicode_literals
import logging

from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class ImagesTestBase(e2e_test_base.BaseTest):
  """Base class for images integration testing."""

  def _SetUp(self, track):
    self.disk_size = 10
    self.image_names_used = []
    self.disk_names_used = []
    self.instance_names_used = []
    self.track = track

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.image_names_used:
      self.CleanUpResource(name, 'images', scope=e2e_test_base.GLOBAL)
    for name in self.disk_names_used:
      self.CleanUpResource(name, 'disks')
    for name in self.instance_names_used:
      self.CleanUpResource(name, 'instances')

  def _GetDiskName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up.
    disk_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-disks', hash_len=4))
    self.disk_names_used.append(disk_name)
    return disk_name

  def _GetImageName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up.
    image_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-images', hash_len=4))
    self.image_names_used.append(image_name)
    return image_name

  def _GetInstanceName(self):
    # Make sure a new name is used if the test is retried, and make sure all
    # used names get cleaned up
    name = next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test'))
    self.instance_name = name
    self.instance_names_used.append(name)
    return name

  def _CreateDisk(self):
    disk_name = self._GetDiskName()
    self.Run('compute disks create {0} --zone {1} --size {2}'
             .format(disk_name, self.zone, self.disk_size))
    self.AssertNewOutputContains(disk_name)
    self.Run('compute disks list')
    self.AssertNewOutputContains(disk_name)
    return disk_name

  def _CreateImage(self):
    disk_name = self._CreateDisk()
    image_name = self._GetImageName()
    self.Run(
        'compute images create {0} --source-disk {1} --source-disk-zone {2}'
        .format(image_name, disk_name, self.zone))
    self.AssertNewOutputContains(image_name)
    self.Run('compute images list')
    self.AssertNewOutputContains(image_name)
    return image_name

  def _CreateDiskWithInstance(self):
    """Creates a new disk attached to an instance.

    Returns:
      str, The name of the newly created disk.
    """
    disk_name = self._CreateDisk()
    instance_name = self._GetInstanceName()
    self.Run('compute instances create {0} '
             '--disk name={1},mode=rw,device-name=data --zone {2}'.format(
                 instance_name, disk_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'.format(
        instance_name, self.zone))
    self.AssertNewOutputContainsAll(['deviceName: data', 'mode: READ_WRITE'])
    return disk_name
