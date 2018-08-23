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
"""Integration tests for creating/using/deleting snapshots."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.compute import e2e_test_base
from tests.lib.surface.compute import utils


class _SnapshotsTestBase(e2e_test_base.BaseTest):

  def GetResourceName(self):
    return next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-snapshot', sequence_start=1))

  @contextlib.contextmanager
  def _CreateDisk(self):
    disk_name = self.GetResourceName()
    try:
      self.Run('compute disks create {0} --image-family {1} '
               '--image-project debian-cloud --zone {2}'
               .format(disk_name, utils.DEBIAN_IMAGE_FAMILY, self.zone))
      yield disk_name
    finally:
      self.Run('compute disks delete {0} --zone {1} --quiet'
               .format(disk_name, self.zone))

  @contextlib.contextmanager
  def _CreateSnapshot(self, disk_name, use_storage_location=False,
                      guest_flush=False):
    snapshot_name = self.GetResourceName()
    extra_flags = ''
    if guest_flush:
      extra_flags = '--guest-flush'
    try:
      if use_storage_location:
        self.Run('compute disks snapshot {0} --snapshot-names {1} --zone {2} '
                 '--storage-location {3} {4}'.format(
                     disk_name, snapshot_name, self.zone,
                     self.storage_location, extra_flags))
      else:
        self.Run('compute disks snapshot {0} --snapshot-names {1} --zone {2} '
                 '{3}'.format(
                     disk_name, snapshot_name, self.zone, extra_flags))
      yield snapshot_name
    finally:
      self.Run('compute snapshots delete {0} --quiet'.format(snapshot_name))

  @contextlib.contextmanager
  def _CreateDiskFromSnapshot(self, snapshot_name):
    disk_name = self.GetResourceName()
    try:
      self.Run('compute disks create {0} --source-snapshot {1} --zone {2}'
               .format(disk_name, snapshot_name, self.zone))
      yield disk_name
    finally:
      self.Run('compute disks delete {0} --zone {1} --quiet'
               .format(disk_name, self.zone))

  @contextlib.contextmanager
  def _CreateInstance(self, extra_flags=''):
    instance_name = self.GetResourceName()
    try:
      self.Run('compute instances create {0} --zone {1} {2}'
               .format(instance_name, self.zone, extra_flags))
      yield instance_name
    finally:
      self.Run('compute instances delete {0} --zone {1} --quiet'.format(
          instance_name, self.zone))


class SnapshotsTestGA(_SnapshotsTestBase):

  def testSnapshots(self):
    with self._CreateDisk() as disk_name, \
         self._CreateSnapshot(disk_name) as snapshot_name, \
         self._CreateDiskFromSnapshot(snapshot_name) as disk_name2, \
         self._CreateInstance('--disk name={},boot=yes'
                              .format(disk_name2)) as instance_name:
      # Check snapshot properties
      self.Run('compute snapshots describe {0}'.format(snapshot_name))
      self.AssertNewOutputContains('name: {0}'.format(snapshot_name),
                                   reset=False)
      self.AssertNewOutputContains('status: READY')

      # Check disk from snapshot properties
      self.Run('compute disks describe {0} --zone {1}'
               .format(disk_name2, self.zone))
      self.AssertNewOutputContains('global/snapshots/{0}'
                                   .format(snapshot_name),
                                   reset=False)
      self.AssertNewOutputContains('name: {0}'.format(disk_name2))

      # Check instance properties
      self.Run('compute instances describe {0} --zone {1}'
               .format(instance_name, self.zone))
      self.AssertNewOutputContains('zones/{0}/disks/{1}'
                                   .format(self.zone, disk_name2),
                                   reset=False)
      self.AssertNewOutputContains('status: RUNNING')
    # Check resources were cleaned up.
    self.Run('compute snapshots list')
    self.AssertNewOutputNotContains(snapshot_name)
    self.Run('compute disks list')
    self.AssertNewOutputNotContains(disk_name, reset=False)
    self.AssertNewOutputNotContains(disk_name2)

  def testWindowsVssSnapshot(self):
    extra_flags = '--image-project windows-cloud --image-family windows-2012-r2'
    with self._CreateInstance(extra_flags) as instance_name:
      # Create Windows Instance and wait for it to boot
      message = 'Instance setup finished.'
      booted = self.WaitForBoot(instance_name, message, retries=10,
                                polling_interval=60)
      self.assertTrue(booted, msg='Timed out waiting for Windows to boot.')
      # Snapshot Instance with VSS
      with self._CreateSnapshot(
          instance_name, guest_flush=True) as snapshot_name:
        # Check that snapshot exists
        self.Run('compute snapshots describe {0}'.format(snapshot_name))
        self.AssertNewOutputContains('name: {0}'.format(snapshot_name),
                                     reset=False)
        self.AssertNewOutputContains('status: READY')


class SnapshotsTestAlpha(_SnapshotsTestBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.storage_location = 'us-west1'

  def testStorageLocation(self):
    with self._CreateDisk() as disk_name, \
         self._CreateSnapshot(
             disk_name, use_storage_location=True) as snapshot_name:
      self.Run('compute snapshots describe {0}'.format(snapshot_name))
      self.AssertNewOutputContains('name: {0}'.format(snapshot_name),
                                   reset=False)
      self.AssertNewOutputContains("""storageLocations:
                                     - {0}""".format(self.storage_location),
                                   reset=False, normalize_space=True)
      self.AssertNewOutputContains('status: READY')


class SnapshotsLabelsTest(_SnapshotsTestBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.GA

  def GetResourceName(self):
    return next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-snapshot-labels'))

  def testAddRemoveLabels(self):
    with self._CreateDisk() as disk_name, \
         self._CreateSnapshot(disk_name) as snapshot_name:
      add_labels = (('x', 'y'), ('abc', 'xyz'))
      self.Run('compute snapshots add-labels {0} --labels {1}'
               .format(snapshot_name,
                       ','.join(['{0}={1}'.format(pair[0], pair[1])
                                 for pair in add_labels])))
      self.Run('compute snapshots describe {0}'.format(snapshot_name))
      self.AssertNewOutputContainsAll(['abc: xyz', 'x: y'])

      remove_labels = ('abc',)
      self.Run('compute snapshots remove-labels {0} --labels {1}'
               .format(snapshot_name,
                       ','.join(['{0}'.format(k)
                                 for k in remove_labels])))
      self.Run('compute snapshots describe {0}'
               .format(snapshot_name))
      self.AssertNewOutputContains('x: y', reset=False)
      self.AssertNewOutputNotContains('abc: xyz')

      self.Run('compute snapshots remove-labels {0} --all '
               .format(snapshot_name))
      self.Run('compute snapshots describe {0}'.format(snapshot_name))
      self.AssertNewOutputNotContains('labels:')

  def testUpdateLabels(self):
    with self._CreateDisk() as disk_name, \
         self._CreateSnapshot(disk_name) as snapshot_name:
      add_labels = (('x', 'y'), ('abc', 'xyz'))
      self.Run('compute snapshots update {0} --update-labels {1}'
               .format(snapshot_name,
                       ','.join(['{0}={1}'.format(pair[0], pair[1])
                                 for pair in add_labels])))
      self.Run('compute snapshots describe {0}'.format(snapshot_name))
      self.AssertNewOutputContainsAll(['abc: xyz', 'x: y'])

      update_labels = (('x', 'a'), ('abc', 'xyz'), ('t123', 't7890'))
      remove_labels = ('abc',)
      self.Run(
          'compute snapshots update {0} --update-labels {1} --remove-labels {2}'
          .format(snapshot_name,
                  ','.join(['{0}={1}'.format(pair[0], pair[1])
                            for pair in update_labels]),
                  ','.join(['{0}'.format(k)
                            for k in remove_labels])))

      self.Run('compute snapshots describe {0}'.format(snapshot_name))
      self.AssertNewOutputContains('t123: t7890', reset=False)
      self.AssertNewOutputContains('x: a', reset=False)
      self.AssertNewOutputNotContains('abc: xyz')


if __name__ == '__main__':
  test_case.main()
