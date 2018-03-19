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
"""Tests for snapshots update."""

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.compute import snapshots_labels_test_base


class UpdateLabelsTestBeta(snapshots_labels_test_base.SnapshotsLabelsTestBase):

  def testUpdateMissingNameOrLabels(self):
    snapshot_ref = self._GetSnapshotRef('snapshot-1')
    with self.assertRaisesRegexp(
        calliope_exceptions.RequiredArgumentException,
        'At least one of --update-labels, '
        '--remove-labels, or --clear-labels must be specified.'):
      self.Run('compute snapshots update {}'.format(snapshot_ref.Name()))

  def testUpdateAndRemoveLabels(self):
    snapshot_ref = self._GetSnapshotRef('snapshot-1')

    snapshot_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (
        ('key2', 'update2'), ('key3', 'value3'), ('key4', 'value4'))

    snapshot = self._MakeSnapshotProto(
        snapshot_ref, labels=snapshot_labels, fingerprint='fingerprint-42')
    updated_snapshot = self._MakeSnapshotProto(
        snapshot_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, snapshot_ref)

    self._ExpectGetRequest(snapshot_ref, snapshot)
    self._ExpectLabelsSetRequest(
        snapshot_ref, edited_labels, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(snapshot_ref, updated_snapshot)

    response = self.Run(
        'compute snapshots update {} --update-labels {} '
        '--remove-labels key1,key0'
        .format(
            snapshot_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])))
    self.assertEqual(response, updated_snapshot)

  def testUpdateClearLabels(self):
    snapshot_ref = self._GetSnapshotRef('snapshot-1')

    snapshot_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    edited_labels = ()

    snapshot = self._MakeSnapshotProto(
        snapshot_ref, labels=snapshot_labels, fingerprint='fingerprint-42')
    updated_snapshot = self._MakeSnapshotProto(
        snapshot_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, snapshot_ref)

    self._ExpectGetRequest(snapshot_ref, snapshot)
    self._ExpectLabelsSetRequest(
        snapshot_ref, edited_labels, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(snapshot_ref, updated_snapshot)

    response = self.Run('compute snapshots update {} --clear-labels'
                        .format(snapshot_ref.SelfLink()))
    self.assertEqual(response, updated_snapshot)

  def testUpdateWithNoLabels(self):
    snapshot_ref = self._GetSnapshotRef('snapshot-1')

    update_labels = (('key2', 'update2'), ('key4', 'value4'))

    snapshot = self._MakeSnapshotProto(
        snapshot_ref, labels=(), fingerprint='fingerprint-42')
    updated_snapshot = self._MakeSnapshotProto(
        snapshot_ref, labels=update_labels)
    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, snapshot_ref)

    self._ExpectGetRequest(snapshot_ref, snapshot)
    self._ExpectLabelsSetRequest(
        snapshot_ref, update_labels, 'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(snapshot_ref, updated_snapshot)

    response = self.Run(
        'compute snapshots update {} --update-labels {} '
        .format(
            snapshot_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])
        ))
    self.assertEqual(response, updated_snapshot)

  def testRemoveWithNoLabelsOnSnapshot(self):
    snapshot_ref = self._GetSnapshotRef('snapshot-1')
    snapshot = self._MakeSnapshotProto(
        snapshot_ref, labels={}, fingerprint='fingerprint-42')

    self._ExpectGetRequest(snapshot_ref, snapshot)

    response = self.Run(
        'compute snapshots update {} --remove-labels DoesNotExist'
        .format(snapshot_ref.SelfLink()))
    self.assertEqual(response, snapshot)

  def testNoNetUpdate(self):
    snapshot_ref = self._GetSnapshotRef('snapshot-1')

    snapshot_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    update_labels = (
        ('key1', 'value1'), ('key3', 'value3'), ('key4', 'value4'))

    snapshot = self._MakeSnapshotProto(
        snapshot_ref, labels=snapshot_labels, fingerprint='fingerprint-42')

    self._ExpectGetRequest(snapshot_ref, snapshot)

    response = self.Run(
        'compute snapshots update {} --update-labels {} --remove-labels key4'
        .format(
            snapshot_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])
        ))
    self.assertEqual(response, snapshot)


if __name__ == '__main__':
  test_case.main()
