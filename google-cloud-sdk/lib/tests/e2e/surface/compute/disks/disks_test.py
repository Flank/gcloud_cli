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
"""Integration tests for creating/attaching/deleting disks."""

import logging

from googlecloudsdk.calliope import base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class DisksTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.disk_size = '10'
    self.instance_names_used = []
    self.disk_names_used = []

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.instance_names_used:
      self.CleanUpResource(name, 'instances')
    for name in self.disk_names_used:
      self.CleanUpResource(name, 'disks')

  def GetInstanceName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    self.instance_name = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-disks', hash_len=4).next()
    self.instance_names_used.append(self.instance_name)

    self.disk_name = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-disk').next()
    self.disk_names_used.append(self.disk_name)

  def testDisks(self):
    self.GetInstanceName()
    self.CreateInstance(self.instance_name)
    self._TestDiskCreation()
    self._TestDiskAttach()
    self._TestDiskResize()
    self._TestDiskDetach()
    self._TestDiskDeletion()
    self.DeleteInstance(self.instance_name)

  def _TestDiskCreation(self):
    self.Run('compute disks create {0} --zone {1} --size {2}'
             .format(self.disk_name, self.zone, self.disk_size))
    self.AssertNewOutputContains(self.disk_name)
    self.Run('compute disks list')
    self.AssertNewOutputContains(self.disk_name)
    self.Run('compute disks describe {0} --zone {1}'
             .format(self.disk_name, self.zone))
    self.AssertNewOutputContains('name: {0}'.format(self.disk_name),
                                 reset=False)
    self.AssertNewOutputContains('status: READY', reset=False)
    self.AssertNewOutputContains("sizeGb: '{0}'".format(self.disk_size))

  def _TestDiskAttach(self):
    self.Run('compute instances attach-disk {0} --disk {1} --zone {2}'
             .format(self.instance_name, self.disk_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.AssertNewOutputContains('zones/{0}/disks/{1}'
                                 .format(self.zone, self.disk_name))

  def _TestDiskResize(self):
    self.WriteInput('y\n')
    self.Run('compute disks resize {0} --size={1} --zone {2}'
             .format(self.disk_name, '100', self.zone))
    self.AssertNewOutputContains(self.disk_name, reset=False)
    self.AssertNewOutputContains("sizeGb: '100'")
    self.Run('compute disks describe {0} --zone {1}'
             .format(self.disk_name, self.zone))
    self.AssertNewOutputContains(self.disk_name, reset=False)
    self.AssertNewOutputContains("sizeGb: '100'")

  def _TestDiskDetach(self):
    self.Run('compute instances detach-disk {0} --disk {1} --zone {2}'
             .format(self.instance_name, self.disk_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'
             .format(self.instance_name, self.zone))
    self.AssertNewOutputNotContains('zones/{0}/disks/{1}'
                                    .format(self.zone, self.disk_name))

  def _TestDiskDeletion(self):
    self.Run('compute disks list')
    self.AssertNewOutputContains(self.disk_name)
    self.WriteInput('y\n')
    self.Run('compute disks delete {0} --zone {1}'
             .format(self.disk_name, self.zone))
    self.ClearInput()
    self.AssertNewErrContains(
        'The following disks will be deleted', reset=False)
    self.AssertNewErrContains(self.disk_name)
    self.Run('compute disks list')
    self.AssertNewOutputNotContains(self.disk_name)


class DisksLabelsTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.disk_size = 10
    self.disk_names_used = []
    self.track = base.ReleaseTrack.GA

    self.disk_name = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-disk').next()
    self.disk_names_used.append(self.disk_name)

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.disk_names_used:
      self.CleanUpResource(name, 'disks')

  def testDisks(self):
    self._TestDiskCreationWithLabels()
    self._TestAddRemoveLabels()
    self._TestUpdateLabels()

  def _TestDiskCreationWithLabels(self):
    disk_labels = (('x', 'y'), ('abc', 'xyz'))
    self.Run(
        'compute disks create {0} --zone {1} --size {2} --labels {3}'
        .format(self.disk_name, self.zone, self.disk_size,
                ','.join(['{0}={1}'.format(pair[0], pair[1])
                          for pair in disk_labels])
               ))
    self.AssertNewOutputContains(self.disk_name)
    self.Run('compute disks list')
    self.AssertNewOutputContains(self.disk_name)
    self.Run('compute disks describe {0} --zone {1}'
             .format(self.disk_name, self.zone))
    self.AssertNewOutputContains('name: {0}'.format(self.disk_name),
                                 reset=False)
    self.AssertNewOutputContains('status: READY', reset=False)
    self.AssertNewOutputContains(
        "sizeGb: '{0}'".format(self.disk_size), reset=False)
    self.AssertNewOutputContains('abc: xyz', reset=False)
    self.AssertNewOutputContains('x: y')

  def _TestAddRemoveLabels(self):
    # Clear out all labels to start with.
    self.Run('compute disks remove-labels {0} --zone {1} --all'
             .format(self.disk_name,
                     self.zone))
    self.Run(
        'compute disks describe {0} --zone {1}'
        .format(self.disk_name, self.zone))
    self.AssertNewOutputNotContains('labels')

    add_labels = (('x', 'y'), ('abc', 'xyz'))
    self.Run('compute disks add-labels {0} --zone {1} --labels {2}'
             .format(self.disk_name,
                     self.zone,
                     ','.join(['{0}={1}'.format(pair[0], pair[1])
                               for pair in add_labels])))
    self.Run('compute disks describe {0} --zone {1}'
             .format(self.disk_name, self.zone))
    self.AssertNewOutputContains('abc: xyz\n  x: y')

    remove_labels = ('abc',)
    self.Run('compute disks remove-labels {0} --zone {1} --labels {2}'
             .format(self.disk_name,
                     self.zone,
                     ','.join(['{0}'.format(k)
                               for k in remove_labels])))
    self.Run('compute disks describe {0} --zone {1}'
             .format(self.disk_name, self.zone))
    self.AssertNewOutputContains('x: y', reset=False)
    self.AssertNewOutputNotContains('abc: xyz')

    self.Run('compute disks remove-labels {0} --zone {1} --all '
             .format(self.disk_name, self.zone))
    self.Run('compute disks describe {0} --zone {1}'
             .format(self.disk_name, self.zone))
    self.AssertNewOutputNotContains('labels')

  def _TestUpdateLabels(self):
    # Clear out all labels to start with.
    self.Run('compute disks remove-labels {0} --zone {1} --all'
             .format(self.disk_name,
                     self.zone))
    self.Run(
        'compute disks describe {0} --zone {1}'
        .format(self.disk_name, self.zone))
    self.AssertNewOutputNotContains('labels')

    add_labels = (('x', 'y'), ('abc', 'xyz'))
    self.Run('compute disks update {0} --zone {1} --update-labels {2}'
             .format(self.disk_name,
                     self.zone,
                     ','.join(['{0}={1}'.format(pair[0], pair[1])
                               for pair in add_labels])))
    self.Run('compute disks describe {0} --zone {1}'
             .format(self.disk_name, self.zone))
    self.AssertNewOutputContains('abc: xyz\n  x: y')

    update_labels = (('x', 'a'), ('abc', 'xyz'), ('t123', 't7890'))
    remove_labels = ('abc',)
    self.Run(
        """
         compute disks update {0} --zone {1}
             --update-labels {2} --remove-labels {3}
        """
        .format(self.disk_name,
                self.zone,
                ','.join(['{0}={1}'.format(pair[0], pair[1])
                          for pair in update_labels]),
                ','.join(['{0}'.format(k)
                          for k in remove_labels])))

    self.Run('compute disks describe {0} --zone {1}'
             .format(self.disk_name, self.zone))
    self.AssertNewOutputContains('t123: t7890', reset=False)
    self.AssertNewOutputContains('x: a', reset=False)
    self.AssertNewOutputNotContains('abc: xyz')


class DisksTestRegional(e2e_test_base.BaseTest):

  def SetUp(self):
    self.disk_size = 10
    self.instance_names_used = []
    self.disk_names_used = []
    self.track = base.ReleaseTrack.ALPHA

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.instance_names_used:
      self.CleanUpResource(name, 'instances')
    for name in self.disk_names_used:
      self.CleanUpResource(name, 'disks')

  def GetInstanceName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    self.instance_name = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-disks', hash_len=4).next()
    self.instance_names_used.append(self.instance_name)

    self.disk_name = e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-disk').next()
    self.disk_names_used.append(self.disk_name)

  def testDisks(self):
    self.GetInstanceName()
    self.CreateInstance(self.instance_name)
    self._TestDiskCreation()
    self._TestDiskAttach()
    self._TestDiskResize()
    # TODO(b/62473471) Detach regional disk when gcloud support it again
    # self._TestDiskDetach()
    # TODO(b/62473471) Delete instance after disk deletion
    self.DeleteInstance(self.instance_name)
    self._TestDiskDeletion()

  def _TestDiskCreation(self):
    self.Run('compute disks create {0} --region {1} --size {2} --replica-zones '
             '{3},{4}'
             .format(self.disk_name, self.region, self.disk_size, self.zone,
                     self.alternative_zone))
    self.AssertNewOutputContains(self.disk_name)
    self.Run('compute disks list')
    self.AssertNewOutputContains(self.disk_name)
    result = self.Run('compute disks describe {0} --region {1} --format=disable'
                      .format(self.disk_name, self.region))
    self.assertEquals(self.disk_name, result.name)
    self.assertEquals('READY', str(result.status))
    self.assertEquals(self.disk_size, result.sizeGb)

  def _TestDiskAttach(self):
    self.Run('compute instances attach-disk {0} --disk {1} --zone {2} '
             '--disk-scope regional'
             .format(self.instance_name, self.disk_name, self.zone))
    result = self.Run(
        'compute instances describe {0} --zone {1} --format=disable'
        .format(self.instance_name, self.zone))
    self.assertRegexpMatches(
        result.disks[1].source,
        '.*regions/{0}/disks/{1}.*'.format(self.region, self.disk_name))

  def _TestDiskResize(self):
    self.WriteInput('y\n')
    self.Run('compute disks resize {0} --size={1} --region {2}'
             .format(self.disk_name, '100', self.region))
    self.AssertNewOutputContains(self.disk_name, reset=False)
    self.AssertNewOutputContains("sizeGb: '100'")
    result = self.Run('compute disks describe {0} --region {1} --format=disable'
                      .format(self.disk_name, self.region))
    self.assertEquals(self.disk_name, result.name)
    self.assertEquals(100, result.sizeGb)

  def _TestDiskDetach(self):
    self.Run('compute instances detach-disk {0} --disk {1} --zone {2}'
             .format(self.instance_name, self.disk_name, self.zone))
    result = self.Run(
        'compute instances describe {0} --zone {1} --format=disable'
        .format(self.instance_name, self.zone))
    self.assertEquals(len(result.disks), 1)

  def _TestDiskDeletion(self):
    self.Run('compute disks list')
    self.AssertNewOutputContains(self.disk_name)
    self.WriteInput('y\n')
    self.Run('compute disks delete {0} --region {1}'
             .format(self.disk_name, self.region))
    self.ClearInput()
    self.AssertNewErrContains(
        'The following region disks will be deleted', reset=False)
    self.AssertNewErrContains(self.disk_name)
    self.Run('compute disks list')
    self.AssertNewOutputNotContains(self.disk_name)


if __name__ == '__main__':
  e2e_test_base.main()
