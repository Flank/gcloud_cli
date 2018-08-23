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
"""Tests for zone completers for miscellaneous instance commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class ZonesMiscTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.ZONES)

  def runTest(self, command, release_track=''):
    self.RunCompletion(release_track + 'compute instances ' + command +
                       ' --zone ',
                       ['us-central1-a', 'us-central1-b', 'europe-west1-a'])
    self.RunCompletion(release_track + 'compute instances ' + command +
                       ' --zone u',
                       ['us-central1-a', 'us-central1-b'])
    self.RunCompletion(release_track + 'compute instances ' + command +
                       ' --zone e',
                       ['europe-west1-a'])

  def testAddAccessConfigZonesCompletion(self):
    self.runTest('add-access-config')

  def testAddTagsZonesCompletion(self):
    self.runTest('add-tags')

  def testAddMetadataZonesCompletion(self):
    self.runTest('add-metadata')

  def testDeleAccessConfigZonesCompletion(self):
    self.runTest('delete-access-config')

  def testRemoveTabsZonesCompletion(self):
    self.runTest('remove-tags')

  def testRemoveMetadataZonesCompletion(self):
    self.runTest('remove-metadata')

  def testAttachDiskZonesCompletion(self):
    self.runTest('attach-disk')

  def testDetachDiskZonesCompletion(self):
    self.runTest('detach-disk')

  def testGetSerialPortOutputZonesCompletion(self):
    self.runTest('get-serial-port-output')

  def testMoveZonesCompletion(self):
    self.runTest('move')

  def testResetZonesCompletion(self):
    self.runTest('reset')

  def testStartZonesCompletion(self):
    self.runTest('start')

  def testStopZonesCompletion(self):
    self.runTest('stop')

  def testListZonesCompletion(self):
    self.runTest('list')

  def testSetDiskAutoDeleteZonesCompletion(self):
    self.runTest('set-disk-auto-delete')

  def testSetSchedulingZonesCompletion(self):
    self.runTest('set-scheduling')

  def testSetMachineTypeZonesCompletion(self):
    self.runTest('set-machine-type', release_track='beta ')

if __name__ == '__main__':
  test_case.main()
