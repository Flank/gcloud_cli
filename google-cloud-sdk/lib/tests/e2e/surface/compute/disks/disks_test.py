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
"""Integration tests for creating/attaching/deleting disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib import parameterized
from tests.lib.surface.compute import e2e_test_base


def GetResourceName():
  return next(e2e_utils.GetResourceNameGenerator(
      prefix='gcloud-compute-test-disks', hash_len=4))


class DisksTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.disk_size = '10'

  def testDisks(self):
    with self._CreateInstance() as instance_name, \
         self._CreateDisk() as disk_name:
      self._TestDiskAttach(disk_name, instance_name)
      self._TestDiskResize(disk_name)
      self._TestDiskDetach(disk_name, instance_name)
    self.Run('compute disks list')
    self.AssertNewOutputNotContains(disk_name)

  @contextlib.contextmanager
  def _CreateInstance(self):
    instance_name = GetResourceName()
    try:
      self.Run('compute instances create {0} --zone {1}'
               .format(instance_name, self.zone))
      yield instance_name
    finally:
      self.Run('compute instances delete {0} --zone {1} --quiet'.format(
          instance_name, self.zone))

  @contextlib.contextmanager
  def _CreateDisk(self):
    disk_name = GetResourceName()
    try:
      self.Run('compute disks create {0} --zone {1} --size {2}'
               .format(disk_name, self.zone, self.disk_size))
      self.AssertNewOutputContains(disk_name)
      self.Run('compute disks list')
      self.AssertNewOutputContains(disk_name)
      self.Run('compute disks describe {0} --zone {1}'
               .format(disk_name, self.zone))
      self.AssertNewOutputContains('name: {0}'.format(disk_name),
                                   reset=False)
      self.AssertNewOutputContains('status: READY', reset=False)
      self.AssertNewOutputContains("sizeGb: '{0}'".format(self.disk_size))
      yield disk_name
    finally:
      self.Run('compute disks delete {0} --zone {1} --quiet'.format(
          disk_name, self.zone))

  def _TestDiskAttach(self, disk_name, instance_name):
    self.Run('compute instances attach-disk {0} --disk {1} --zone {2}'
             .format(instance_name, disk_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'
             .format(instance_name, self.zone))
    self.AssertNewOutputContains('zones/{0}/disks/{1}'
                                 .format(self.zone, disk_name))

  def _TestDiskResize(self, disk_name):
    self.WriteInput('y\n')
    self.Run('compute disks resize {0} --size={1} --zone {2}'
             .format(disk_name, '100', self.zone))
    self.AssertNewOutputContains(disk_name, reset=False)
    self.AssertNewOutputContains("sizeGb: '100'")
    self.Run('compute disks describe {0} --zone {1}'
             .format(disk_name, self.zone))
    self.AssertNewOutputContains(disk_name, reset=False)
    self.AssertNewOutputContains("sizeGb: '100'")

  def _TestDiskDetach(self, disk_name, instance_name):
    self.Run('compute instances detach-disk {0} --disk {1} --zone {2}'
             .format(instance_name, disk_name, self.zone))
    self.Run('compute instances describe {0} --zone {1}'
             .format(instance_name, self.zone))
    self.AssertNewOutputNotContains('zones/{0}/disks/{1}'
                                    .format(self.zone, disk_name))


class DisksLabelsTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.disk_size = 10
    self.track = calliope_base.ReleaseTrack.GA

  def testDisks(self):
    with self._CreateDiskWithLabels() as disk_name:
      self._TestAddRemoveLabels(disk_name)
      self._TestUpdateLabels(disk_name)

  @contextlib.contextmanager
  def _CreateDiskWithLabels(self):
    disk_name = GetResourceName()
    try:
      self.Run('compute disks create {0} --zone {1} --size {2} '
               '--labels x=y,abc=xyz '.format(
                   disk_name, self.zone, self.disk_size))
      self.AssertNewOutputContains(disk_name)
      self.Run('compute disks list')
      self.AssertNewOutputContains(disk_name)
      self.Run('compute disks describe {0} --zone {1}'
               .format(disk_name, self.zone))
      self.AssertNewOutputContains('name: {0}'.format(disk_name),
                                   reset=False)
      self.AssertNewOutputContains('status: READY', reset=False)
      self.AssertNewOutputContains("sizeGb: '{0}'".format(self.disk_size),
                                   reset=False)
      self.AssertNewOutputContains('abc: xyz', reset=False)
      self.AssertNewOutputContains('x: y')
      yield disk_name
    finally:
      self.Run('compute disks delete {0} --zone {1} --quiet'.format(
          disk_name, self.zone))

  def _TestAddRemoveLabels(self, disk_name):
    # Clear out all labels to start with.
    self.Run('compute disks remove-labels {0} --zone {1} --all'
             .format(disk_name,
                     self.zone))
    self.Run(
        'compute disks describe {0} --zone {1}'
        .format(disk_name, self.zone))
    self.AssertNewOutputNotContains('labels')

    add_labels = (('x', 'y'), ('abc', 'xyz'))
    self.Run('compute disks add-labels {0} --zone {1} --labels {2}'
             .format(disk_name,
                     self.zone,
                     ','.join(['{0}={1}'.format(pair[0], pair[1])
                               for pair in add_labels])))
    self.Run('compute disks describe {0} --zone {1}'
             .format(disk_name, self.zone))
    self.AssertNewOutputContains('abc: xyz\n  x: y')

    remove_labels = ('abc',)
    self.Run('compute disks remove-labels {0} --zone {1} --labels {2}'
             .format(disk_name,
                     self.zone,
                     ','.join(['{0}'.format(k)
                               for k in remove_labels])))
    self.Run('compute disks describe {0} --zone {1}'
             .format(disk_name, self.zone))
    self.AssertNewOutputContains('x: y', reset=False)
    self.AssertNewOutputNotContains('abc: xyz')

    self.Run('compute disks remove-labels {0} --zone {1} --all '
             .format(disk_name, self.zone))
    self.Run('compute disks describe {0} --zone {1}'
             .format(disk_name, self.zone))
    self.AssertNewOutputNotContains('labels')

  def _TestUpdateLabels(self, disk_name):
    # Clear out all labels to start with.
    self.Run('compute disks remove-labels {0} --zone {1} --all'
             .format(disk_name,
                     self.zone))
    self.Run(
        'compute disks describe {0} --zone {1}'
        .format(disk_name, self.zone))
    self.AssertNewOutputNotContains('labels')

    add_labels = (('x', 'y'), ('abc', 'xyz'))
    self.Run('compute disks update {0} --zone {1} --update-labels {2}'
             .format(disk_name,
                     self.zone,
                     ','.join(['{0}={1}'.format(pair[0], pair[1])
                               for pair in add_labels])))
    self.Run('compute disks describe {0} --zone {1}'
             .format(disk_name, self.zone))
    self.AssertNewOutputContains('abc: xyz\n  x: y')

    update_labels = (('x', 'a'), ('abc', 'xyz'), ('t123', 't7890'))
    remove_labels = ('abc',)
    self.Run(
        """
         compute disks update {0} --zone {1}
             --update-labels {2} --remove-labels {3}
        """
        .format(disk_name,
                self.zone,
                ','.join(['{0}={1}'.format(pair[0], pair[1])
                          for pair in update_labels]),
                ','.join(['{0}'.format(k)
                          for k in remove_labels])))

    self.Run('compute disks describe {0} --zone {1}'
             .format(disk_name, self.zone))
    self.AssertNewOutputContains('t123: t7890', reset=False)
    self.AssertNewOutputContains('x: a', reset=False)
    self.AssertNewOutputNotContains('abc: xyz')


class DisksTestRegional(e2e_test_base.BaseTest, parameterized.TestCase):

  def SetUp(self):
    self.disk_size = 10

  # TODO(b/117336602) Stop using parameterized for track parameterization.
  @parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                            calliope_base.ReleaseTrack.BETA)
  def testDisks(self, track):
    self.track = track
    with self._CreateInstance() as instance_name, \
         self._CreateRegionalDisk() as disk_name:
      self._TestDiskAttach(disk_name, instance_name)
      self._TestDiskResize(disk_name)
      self._TestDiskDetach(disk_name, instance_name)
    self.Run('compute disks list')
    self.AssertNewOutputNotContains(disk_name)

  @contextlib.contextmanager
  def _CreateInstance(self):
    instance_name = GetResourceName()
    try:
      self.Run('compute instances create {0} --zone {1}'
               .format(instance_name, self.zone))
      yield instance_name
    finally:
      self.Run('compute instances delete {0} --zone {1} --quiet'.format(
          instance_name, self.zone))

  @contextlib.contextmanager
  def _CreateRegionalDisk(self):
    disk_name = GetResourceName()
    try:
      self.Run('compute disks create {0} --region {1} --size {2} '
               '--replica-zones {3},{4}'
               .format(disk_name, self.region, self.disk_size, self.zone,
                       self.alternative_zone))
      self.AssertNewOutputContains(disk_name)
      self.Run('compute disks list')
      self.AssertNewOutputContains(disk_name)
      result = self.Run(
          'compute disks describe {0} --region {1} --format=disable'
          .format(disk_name, self.region))
      self.assertEqual(disk_name, result.name)
      self.assertEqual('READY', str(result.status))
      self.assertEqual(self.disk_size, result.sizeGb)
      yield disk_name
    finally:
      self.Run('compute disks delete {0} --region {1} --quiet'
               .format(disk_name, self.region))

  def _TestDiskAttach(self, disk_name, instance_name):
    self.Run('compute instances attach-disk {0} --disk {1} --zone {2} '
             '--disk-scope regional'
             .format(instance_name, disk_name, self.zone))
    result = self.Run(
        'compute instances describe {0} --zone {1} --format=disable'
        .format(instance_name, self.zone))
    self.assertRegexpMatches(
        result.disks[1].source,
        '.*regions/{0}/disks/{1}.*'.format(self.region, disk_name))

  def _TestDiskResize(self, disk_name):
    self.WriteInput('y\n')
    self.Run('compute disks resize {0} --size={1} --region {2}'
             .format(disk_name, '100', self.region))
    self.AssertNewOutputContains(disk_name, reset=False)
    self.AssertNewOutputContains("sizeGb: '100'")
    result = self.Run('compute disks describe {0} --region {1} --format=disable'
                      .format(disk_name, self.region))
    self.assertEqual(disk_name, result.name)
    self.assertEqual(100, result.sizeGb)

  def _TestDiskDetach(self, disk_name, instance_name):
    self.Run('compute instances detach-disk {0} --disk {1} --zone {2} '
             '--disk-scope regional'
             .format(instance_name, disk_name, self.zone))
    result = self.Run(
        'compute instances describe {0} --zone {1} --format=disable'
        .format(instance_name, self.zone))
    self.assertEqual(len(result.disks), 1)


if __name__ == '__main__':
  e2e_test_base.main()
