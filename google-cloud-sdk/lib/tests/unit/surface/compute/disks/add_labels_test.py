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
"""Tests for disks add-labels."""

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import disks_labels_test_base


class AddLabelsTestAlpha(disks_labels_test_base.DisksLabelsTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)

  def testRegionalUpdateValidDisksWithLabelsAndRemoveLabels(self):
    disk_ref = self._GetDiskRef('disk-1', region='us-central')

    disk_labels = (('key1', 'value1'), ('key2', 'value2'))
    add_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (
        ('key1', 'value1'), ('key2', 'update2'), ('key4', 'value4')
    )

    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint='fingerprint-42')
    updated_disk = self._MakeDiskProto(disk_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1', region='us-central')
    operation = self._MakeOperationMessage(operation_ref, disk_ref)

    self._ExpectGetRequest(disk_ref, disk)
    self._ExpectLabelsSetRequest(
        disk_ref, edited_labels, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(disk_ref, updated_disk)

    response = self.Run(
        'compute disks add-labels {} --labels {}'
        .format(
            disk_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in add_labels])))
    self.assertEqual(response, updated_disk)

  def testScopePromptWithRegionAndZone(self):
    disk_ref = self._GetDiskRef('disk-1', region='us-central')

    # Make a disk that already has labels and add-labels later
    # adds existing labels. So, we only test the prompting portion.
    disk_labels = (('key1', 'value1'), ('key2', 'value2'))
    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint='fingerprint-42')
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
    self.Run('compute disks add-labels disk-1 --labels key1=value1')
    self.AssertErrContains('us-central1')
    self.AssertErrContains('us-central2')
    self.AssertErrContains('us-central')


class AddLabelsTest(disks_labels_test_base.DisksLabelsTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.GA)

  def testZonalUpdateDiskWithNoLabels(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    add_labels = (('key2', 'update2'), ('key4', 'value4'))

    disk = self._MakeDiskProto(
        disk_ref, labels=(), fingerprint='fingerprint-42')
    updated_disk = self._MakeDiskProto(disk_ref, labels=add_labels)
    operation_ref = self._GetOperationRef('operation-1', zone='atlanta')
    operation = self._MakeOperationMessage(operation_ref, disk_ref)

    self._ExpectGetRequest(disk_ref, disk)
    self._ExpectLabelsSetRequest(
        disk_ref, add_labels, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(disk_ref, updated_disk)

    response = self.Run(
        'compute disks add-labels {} --labels {} '
        .format(
            disk_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in add_labels])
        ))
    self.assertEqual(response, updated_disk)

  def testZonalUpdateValidDisksWithLabelsAndRemoveLabels(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    disk_labels = (('key1', 'value1'), ('key2', 'value2'))
    add_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = ((
        ('key1', 'value1'), ('key2', 'update2'), ('key4', 'value4')
    ))

    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint='fingerprint-42')
    updated_disk = self._MakeDiskProto(disk_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1', zone='atlanta')
    operation = self._MakeOperationMessage(operation_ref, disk_ref)

    self._ExpectGetRequest(disk_ref, disk)
    self._ExpectLabelsSetRequest(
        disk_ref, edited_labels, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(disk_ref, updated_disk)

    response = self.Run(
        'compute disks add-labels {} --labels {} '
        .format(
            disk_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in add_labels])
        ))
    self.assertEqual(response, updated_disk)

  def testNoUpdate(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    disk_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    add_labels = (('key1', 'value1'), ('key3', 'value3'))

    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint='fingerprint-42')

    self._ExpectGetRequest(disk_ref, disk)

    response = self.Run(
        'compute disks add-labels {} --labels {} '
        .format(
            disk_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in add_labels])
        ))
    self.assertEqual(response, disk)

  def testNoLabelsSpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --labels: Must be specified.'
        ):
      self.Run('compute disks add-labels disk-1')

  def testScopePromptWithZone(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    # Make a disk that already has labels and add-labels later
    # adds existing labels. So, we only test the prompting portion.
    disk_labels = (('key1', 'value1'), ('key2', 'value2'))
    disk = self._MakeDiskProto(
        disk_ref, labels=disk_labels, fingerprint='fingerprint-42')
    self._ExpectGetRequest(disk_ref, disk)

    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.StartPatch('googlecloudsdk.api_lib.compute.zones.service.List',
                    return_value=[
                        self.messages.Zone(name='atlanta'),
                        self.messages.Zone(name='charlotte')],
                   )
    self.StartPatch('googlecloudsdk.api_lib.compute.regions.service.List',
                    return_value=[
                        self.messages.Region(name='georgia')],
                   )
    self.WriteInput('1\n')
    self.Run('compute disks add-labels disk-1 --labels key1=value1')
    self.AssertErrContains('atlanta')
    self.AssertErrContains('charlotte')
    self.AssertErrNotContains('georgia')

  def testInvalidLabel(self):
    disk_ref = self._GetDiskRef('disk-1', zone='atlanta')

    disk = self._MakeDiskProto(
        disk_ref, labels={}, fingerprint='fingerprint-42')
    add_labels = (('+notvalid', 'a'),)

    error = http_error.MakeHttpError(
        code=400,
        message='+notvalid',
        reason='Invalid label',
        content={},
        url='')

    self._ExpectGetRequest(disk_ref, disk)
    self._ExpectLabelsSetRequest(
        disk_ref=disk_ref,
        labels=add_labels,
        fingerprint='fingerprint-42',
        exception=error)

    with self.AssertRaisesHttpExceptionMatches(
        'Invalid label: +notvalid'):
      self.Run(
          'compute disks add-labels {} --labels {} '
          .format(
              disk_ref.SelfLink(),
              ','.join(['{0}={1}'.format(pair[0], pair[1])
                        for pair in add_labels])
          ))


if __name__ == '__main__':
  test_case.main()
