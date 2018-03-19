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
"""Integration tests for creating/updating/deleting images."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from tests.lib.surface.compute import e2e_images_test_base


class ImagesTest(e2e_images_test_base.ImagesTestBase):

  def SetUp(self):
    self._SetUp(base.ReleaseTrack.GA)

  def testImageCreationWithLabels(self):
    disk_name = self._CreateDisk()

    image_labels = (('x', 'y'), ('abc', 'xyz'))
    image_name = self._GetImageName()
    self.Run(
        """
        compute images create {0} --source-disk {1} --source-disk-zone {2}
            --labels {3}
        """
        .format(image_name, disk_name, self.zone,
                ','.join(['{0}={1}'.format(pair[0], pair[1])
                          for pair in image_labels])))
    self.AssertNewOutputContains(image_name)
    self.Run('compute images describe {0}'.format(image_name))
    self.AssertNewOutputContainsAll(['abc: xyz', 'x: y'])

  def testAddRemoveLabels(self):
    image_name = self._CreateImage()

    add_labels = (('x', 'y'), ('abc', 'xyz'))
    self.Run('compute images add-labels {0} --labels {1}'
             .format(image_name,
                     ','.join(['{0}={1}'.format(pair[0], pair[1])
                               for pair in add_labels])))
    self.Run('compute images describe {0}'.format(image_name))
    self.AssertNewOutputContainsAll(['abc: xyz', 'x: y'])

    remove_labels = ('abc',)
    self.Run('compute images remove-labels {0} --labels {1}'
             .format(image_name,
                     ','.join(['{0}'.format(k)
                               for k in remove_labels])))
    self.Run('compute images describe {0}'.format(image_name))
    self.AssertNewOutputContains('x: y', reset=False)
    self.AssertNewOutputNotContains('abc: xyz')

    self.Run('compute images remove-labels {0} --all '
             .format(image_name))
    self.Run('compute images describe {0}'.format(image_name))
    self.AssertNewOutputNotContains('labels')

  def testUpdateLabels(self):
    image_name = self._CreateImage()

    add_labels = (('x', 'y'), ('abc', 'xyz'))
    self.Run('compute images update {0} --update-labels {1}'
             .format(image_name,
                     ','.join(['{0}={1}'.format(pair[0], pair[1])
                               for pair in add_labels])))
    self.Run('compute images describe {0}'.format(image_name))
    self.AssertNewOutputContainsAll(['abc: xyz', 'x: y'])

    update_labels = (('x', 'a'), ('abc', 'xyz'), ('t123', 't7890'))
    remove_labels = ('abc',)
    self.Run(
        'compute images update {0} --update-labels {1} --remove-labels {2}'
        .format(image_name,
                ','.join(['{0}={1}'.format(pair[0], pair[1])
                          for pair in update_labels]),
                ','.join(['{0}'.format(k)
                          for k in remove_labels])))
    self.Run('compute images describe {0}'.format(image_name))
    self.AssertNewOutputContains('t123: t7890', reset=False)
    self.AssertNewOutputContains('x: a', reset=False)
    self.AssertNewOutputNotContains('abc: xyz')

  def testForceFlag(self):
    disk_name = self._CreateDiskWithInstance()
    image_name = self._GetImageName()

    self.Run(
        'compute images create {0} --source-disk {1} --source-disk-zone {2} '
        '--force'
        .format(image_name, disk_name, self.zone))
    self.Run('compute images list')
    self.AssertNewOutputContains(image_name)

  def testFailWithoutForceFlag(self):
    disk_name = self._CreateDiskWithInstance()
    image_name = self._GetImageName()

    with self.assertRaisesRegexp(
        exceptions.ToolException,
        'The disk resource.*is already being used by.*'):
      self.Run(
          'compute images create {0} --source-disk {1} --source-disk-zone {2} '
          .format(image_name, disk_name, self.zone))


class ImagesBetaTest(e2e_images_test_base.ImagesTestBase):

  def SetUp(self):
    self._SetUp(base.ReleaseTrack.BETA)

  def testTrustedImageProjects(self):
    # This test checks Trusted Image Projects feature currently in beta
    # by calling beta compute images list command
    image_name = self._CreateImage()

    self.Run('compute images list')
    self.AssertNewOutputContains(image_name)

  def testForceCreateFlag(self):
    disk_name = self._CreateDiskWithInstance()
    image_name = self._GetImageName()

    self.Run(
        'compute images create {0} --source-disk {1} --source-disk-zone {2} '
        '--force-create'
        .format(image_name, disk_name, self.zone))
    self.Run('compute images list')
    self.AssertNewOutputContains(image_name)

  def testFailWithoutForceCreateFlag(self):
    disk_name = self._CreateDiskWithInstance()
    image_name = self._GetImageName()

    with self.assertRaisesRegexp(
        exceptions.ToolException,
        'The disk resource.*is already being used by.*'):
      self.Run(
          'compute images create {0} --source-disk {1} --source-disk-zone {2} '
          .format(image_name, disk_name, self.zone))


if __name__ == '__main__':
  e2e_images_test_base.main()
