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

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import exceptions as core_exceptions
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

    with self.assertRaisesRegex(
        exceptions.ToolException,
        'The disk resource.*is already being used by.*'):
      self.Run(
          'compute images create {0} --source-disk {1} --source-disk-zone {2} '
          .format(image_name, disk_name, self.zone))

  def testExport(self):
    image_name = self._CreateImage()
    destination_uri = 'gs://bucketthatdoesnotexistasdf1234567890/image.tar.gz'
    # This should fail quickly, since the destination-uri doesn't exist, but
    # a timeout is added just in case. This test checks to make sure that
    # Daisy is called with the correct workflow.
    with self.assertRaisesRegex(
        core_exceptions.Error,
        'completed with status'):
      self.Run(
          """
          compute images export --image {0} --destination-uri {1}
          --timeout 30s --quiet
          """.format(image_name, destination_uri))

    self.AssertNewOutputContains('[Daisy] Running workflow "image-export"')

  def testImport(self):
    image_name = self._GetImageName()
    source_image = self._CreateImage()
    # Pass in a dummy translate workflow, so that Daisy will throw an error.
    # This allows us to confirm that Daisy was called as expected without
    # having Daisy attempt to actually import files and create resources.
    dummy_workflow = 'dummy.wf.json'
    with self.assertRaisesRegex(
        core_exceptions.Error,
        'completed with status'):
      self.Run(
          """
          compute images import {0} --source-image {1}
          --custom-workflow {2} --timeout 10s --quiet
          """.format(image_name, source_image, dummy_workflow))

    self.AssertNewOutputContainsAll(
        ['[Daisy] Running workflow "import-from-image"',
         ('error populating step "translate-disk": open '
          '/workflows/image_import/{0}: no such file or directory'
          .format(dummy_workflow))])


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

    with self.assertRaisesRegex(
        exceptions.ToolException,
        'The disk resource.*is already being used by.*'):
      self.Run(
          'compute images create {0} --source-disk {1} --source-disk-zone {2} '
          .format(image_name, disk_name, self.zone))


if __name__ == '__main__':
  e2e_images_test_base.main()
