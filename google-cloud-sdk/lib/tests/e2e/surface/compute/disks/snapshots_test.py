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

import logging

from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import e2e_resource_managers
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base
from tests.lib.surface.compute import resource_managers


class SnapshotsTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.disk_names_used = []
    self.snapshot_names_used = []

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.disk_names_used:
      self.CleanUpResource(name, 'disks')
    for name in self.snapshot_names_used:
      self.CleanUpResource(self.snapshot_name, 'snapshots',
                           scope=e2e_test_base.GLOBAL)

  def _GetInstanceRef(self, prefix=None, zone=None, project=None):
    prefix = prefix or 'gcloud-compute-test-instance'
    zone = zone or self.zone
    project = project or self.Project()
    return resources.REGISTRY.Create(
        'compute.instances', instance=prefix, zone=zone, project=project)

  def GetResourceName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    g = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-disk', sequence_start=1)
    self.disk1_name = g.next()
    self.disk2_name = g.next()
    self.disk_names_used.extend(
        [self.disk1_name, self.disk2_name])
    self.snapshot_name = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-snapshot').next()
    self.snapshot_names_used.append(self.snapshot_name)

  def testSnapshots(self):
    instance_parameters = e2e_resource_managers.ResourceParameters(
        prefix_ref=self._GetInstanceRef())
    with resource_managers.Instance(self.Run, instance_parameters):
      self.GetResourceName()
      self._TestCreateSnapshot()
      self._TestCreateDiskFromSnapshot()
      self._TestCreateInstanceFromDisk()
      self._TestDeleteSnapshot()
    self._TestDeleteDisks()

  def testWindowsVssSnapshot(self):
    instance_ref = self._GetInstanceRef()
    extra_creation_flags = [
        ('--image-project', 'windows-cloud'),
        ('--image-family', 'windows-2012-r2'),
    ]
    instance_parameters = e2e_resource_managers.ResourceParameters(
        prefix_ref=instance_ref, extra_creation_flags=extra_creation_flags)
    with resource_managers.Instance(self.Run, instance_parameters) as instance:
      instance_name = instance.ref.Name()
      self.GetResourceName()
      # Create Windows Instance and wait for it to boot
      message = 'Instance setup finished.'
      booted = self.WaitForBoot(instance_name, message, retries=10,
                                polling_interval=60)
      self.assertTrue(booted, msg='Timed out waiting for Windows to boot.')
      # Snapshot Instance with VSS
      self.Run('compute disks snapshot {0} --snapshot-names {1}'
               ' --zone {2} --guest-flush'
               .format(instance_name, self.snapshot_name, self.zone))
      # Check that snapshot exists
      self.Run('compute snapshots describe {0}'.format(self.snapshot_name))
      self.AssertNewOutputContains('name: {0}'.format(self.snapshot_name),
                                   reset=False)
      self.AssertNewOutputContains('status: READY')

  def _TestCreateSnapshot(self):
    # Create disk first
    self.Run('compute disks create {0} --image debian-8 --zone {1}'
             .format(self.disk1_name, self.zone))
    self.Run('compute disks snapshot {0} --snapshot-names {1} --zone {2}'
             .format(self.disk1_name, self.snapshot_name, self.zone))
    self.Run('compute snapshots describe {0}'.format(self.snapshot_name))
    self.AssertNewOutputContains('name: {0}'.format(self.snapshot_name),
                                 reset=False)
    self.AssertNewOutputContains('status: READY')

  def _TestCreateDiskFromSnapshot(self):
    self.Run('compute disks create {0} --source-snapshot {1} --zone {2}'
             .format(self.disk2_name, self.snapshot_name, self.zone))
    self.Run('compute disks describe {0} --zone {1}'
             .format(self.disk2_name, self.zone))
    self.AssertNewOutputContains('global/snapshots/{0}'
                                 .format(self.snapshot_name),
                                 reset=False)
    self.AssertNewOutputContains('name: {0}'.format(self.disk2_name))

  def _TestCreateInstanceFromDisk(self):
    instance_ref = self._GetInstanceRef()
    extra_creation_flags = [
        ('--disk', 'name={},boot=yes'.format(self.disk2_name)),
    ]
    instance_parameters = e2e_resource_managers.ResourceParameters(
        prefix_ref=instance_ref, extra_creation_flags=extra_creation_flags)
    with resource_managers.Instance(self.Run, instance_parameters) as instance:
      self.Run('compute instances describe {0} --zone {1}'
               .format(instance.ref.Name(), self.zone))
      self.AssertNewOutputContains('zones/{0}/disks/{1}'
                                   .format(self.zone, self.disk2_name),
                                   reset=False)
      self.AssertNewOutputContains('status: RUNNING')

  def _TestDeleteSnapshot(self):
    self.Run('compute snapshots list')
    self.AssertNewOutputContains(self.snapshot_name)
    self.WriteInput('y\n')
    self.Run('compute snapshots delete {0}'.format(self.snapshot_name))
    self.ClearInput()
    self.AssertNewErrContains(
        'The following snapshots will be deleted', reset=False)
    self.AssertNewErrContains(self.snapshot_name)
    self.Run('compute snapshots list')
    self.AssertNewOutputNotContains(self.snapshot_name)

  def _TestDeleteDisks(self):
    self.Run('compute disks list')
    self.AssertNewOutputContains(self.disk1_name, reset=False)
    self.AssertNewOutputContains(self.disk2_name)
    self.WriteInput('y\n')
    self.Run('compute disks delete {0} {1} --zone {2}'
             .format(self.disk1_name, self.disk2_name, self.zone))
    self.ClearInput()
    self.AssertNewErrContains(
        'The following disks will be deleted', reset=False)
    self.AssertNewErrContains(self.disk1_name, reset=False)
    self.AssertNewErrContains(self.disk2_name)
    self.Run('compute disks list')
    self.AssertNewOutputNotContains(self.disk1_name, reset=False)
    self.AssertNewOutputNotContains(self.disk2_name)


class SnapshotsLabelsTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.disk_names_used = []
    self.snapshot_names_used = []
    self.track = base.ReleaseTrack.GA

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.disk_names_used:
      self.CleanUpResource(name, 'disks')
    for name in self.snapshot_names_used:
      self.CleanUpResource(name, 'snapshots', scope=e2e_test_base.GLOBAL)

  def _GetSnapshotName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    snapshot_name = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-snapshot').next()
    self.snapshot_names_used.append(snapshot_name)
    return snapshot_name

  def _GetDiskName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    disk_name = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-disk').next()
    self.disk_names_used.append(disk_name)
    return disk_name

  def testAddRemoveLabels(self):
    snapshot_name = self._CreateSnapshot()
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
    self.AssertNewOutputNotContains('labels')

  def testUpdateLabels(self):
    snapshot_name = self._CreateSnapshot()

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

  def _CreateSnapshot(self):
    """Creates a disk first, then create a snapshot out of it."""
    snapshot_name = self._GetSnapshotName()
    disk_name = self._GetDiskName()
    self.Run('compute disks create {0} --image debian-8 --zone {1}'
             .format(disk_name, self.zone))
    self.Run('compute disks snapshot {0} --snapshot-names {1} --zone {2}'
             .format(disk_name, snapshot_name, self.zone))
    self.Run('compute snapshots describe {0}'.format(snapshot_name))
    self.AssertNewOutputContains('name: {0}'.format(snapshot_name))
    return snapshot_name


if __name__ == '__main__':
  e2e_test_base.main()
