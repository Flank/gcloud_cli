# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for disks update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.compute import disks_labels_test_base


class UpdateLabelsTestGA(disks_labels_test_base.DisksLabelsTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self._SetUp(self.track)

  def testUpdateMissingNameOrLabels(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')
    with self.assertRaisesRegex(
        calliope_exceptions.RequiredArgumentException,
        'At least one of --update-labels, '
        '--remove-labels, or --clear-labels must be specified.'):
      self.Run('compute disks update {} --zone {}'
               .format(disk_ref.Name(), disk_ref.zone))

  def testZonalUpdateWithLabelsAndRemoveLabels(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    disk_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (
        ('key2', 'update2'), ('key3', 'value3'), ('key4', 'value4'))

    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint=b'fingerprint-42')
    updated_disk = self._MakeDiskProto(disk_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1', zone='atlanta')
    operation = self._MakeOperationMessage(operation_ref, disk_ref)

    self._ExpectGetRequest(disk_ref, disk)
    self._ExpectLabelsSetRequest(
        disk_ref, edited_labels, b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(disk_ref, updated_disk)

    response = self.Run(
        'compute disks update {} --update-labels {} '
        '--remove-labels key1,key0'
        .format(
            disk_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])))
    self.assertEqual(response, updated_disk)

  def testZonalUpdateClearLabels(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    disk_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    edited_labels = ()

    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint=b'fingerprint-42')
    updated_disk = self._MakeDiskProto(disk_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1', zone='atlanta')
    operation = self._MakeOperationMessage(operation_ref, disk_ref)

    self._ExpectGetRequest(disk_ref, disk)
    self._ExpectLabelsSetRequest(
        disk_ref, edited_labels, b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(disk_ref, updated_disk)

    response = self.Run(
        'compute disks update {} --clear-labels'.format(disk_ref.SelfLink()))
    self.assertEqual(response, updated_disk)

  def testZonalUpdateDiskWithNoLabels(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    update_labels = (('key2', 'update2'), ('key4', 'value4'))

    disk = self._MakeDiskProto(
        disk_ref, labels=(), fingerprint=b'fingerprint-42')
    updated_disk = self._MakeDiskProto(disk_ref, labels=update_labels)
    operation_ref = self._GetOperationRef('operation-1', zone='atlanta')
    operation = self._MakeOperationMessage(operation_ref, disk_ref)

    self._ExpectGetRequest(disk_ref, disk)
    self._ExpectLabelsSetRequest(
        disk_ref, update_labels, b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(disk_ref, updated_disk)

    response = self.Run(
        'compute disks update {} --update-labels {} '
        .format(
            disk_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])
        ))
    self.assertEqual(response, updated_disk)

  def testRemoveWithNoLabelsOnDisk(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')
    disk = self._MakeDiskProto(
        disk_ref, labels={}, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(disk_ref, disk)

    response = self.Run(
        'compute disks update {} --remove-labels DoesNotExist'
        .format(disk_ref.SelfLink()))
    self.assertEqual(response, disk)

  def testNoNetUpdate(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    disk_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    update_labels = (
        ('key1', 'value1'), ('key3', 'value3'), ('key4', 'value4'))

    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(disk_ref, disk)

    response = self.Run(
        'compute disks update {} --update-labels {} --remove-labels key4'
        .format(
            disk_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])
        ))
    self.assertEqual(response, disk)

  def testZonalUpdateValidDisksWithLabelsAndRemoveLabels(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    disk_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (
        ('key2', 'update2'), ('key3', 'value3'), ('key4', 'value4'))

    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint=b'fingerprint-42')
    updated_disk = self._MakeDiskProto(disk_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1', zone='atlanta')
    operation = self._MakeOperationMessage(operation_ref, disk_ref)

    self._ExpectGetRequest(disk_ref, disk)
    self._ExpectLabelsSetRequest(
        disk_ref, edited_labels, b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(disk_ref, updated_disk)

    response = self.Run(
        'compute disks update {} --update-labels {} '
        '--remove-labels key1,key0'
        .format(
            disk_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])))
    self.assertEqual(response, updated_disk)

  def testZonalUpdateValidDisksWithNoUpdate(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    disk_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))

    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(disk_ref, disk)

    response = self.Run(
        'compute disks update {} --update-labels {}'
        .format(
            disk_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in disk_labels])))
    self.assertEqual(response, disk)

  def testRegionalUpdateValidDisksWithLabelsAndRemoveLabels(self):
    disk_ref = self._GetDiskRef('disk-1', region='us-central')

    disk_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (
        ('key2', 'update2'), ('key3', 'value3'), ('key4', 'value4'))

    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint=b'fingerprint-42')
    updated_disk = self._MakeDiskProto(disk_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1', region='us-central')
    operation = self._MakeOperationMessage(operation_ref, disk_ref)

    self._ExpectGetRequest(disk_ref, disk)
    self._ExpectLabelsSetRequest(
        disk_ref, edited_labels, b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(disk_ref, updated_disk)

    response = self.Run(
        'compute disks update {} --update-labels {} '
        '--remove-labels key1,key0'
        .format(
            disk_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])))
    self.assertEqual(response, updated_disk)

  def testScopePromptWithRegionAndZone(self):
    disk_ref = self._GetDiskRef('disk-1', region='us-central')
    disk = self._MakeDiskProto(disk_ref, labels=[])
    self._ExpectGetRequest(disk_ref, disk)

    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.StartPatch('googlecloudsdk.api_lib.compute.zones.service.List',
                    return_value=[
                        self.messages.Zone(name='us-central1'),
                        self.messages.Zone(name='us-central2')],
                   )
    self.StartPatch('googlecloudsdk.api_lib.compute.regions.service.List',
                    return_value=[
                        self.messages.Region(name='us-central')],
                   )
    self.WriteInput('1\n')
    self.Run('compute disks update disk-1 --remove-labels key0')
    self.AssertErrContains('us-central1')
    self.AssertErrContains('us-central2')
    self.AssertErrContains('us-central')


class UpdateLabelsTestBeta(UpdateLabelsTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class UpdateLabelsTestAlpha(UpdateLabelsTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
