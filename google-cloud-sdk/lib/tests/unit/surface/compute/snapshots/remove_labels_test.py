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
"""Tests for the snapshots remove-labels subcommand."""


from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import snapshots_labels_test_base


class RemoveLabelsTest(snapshots_labels_test_base.SnapshotsLabelsTestBase):
  """Snapshots remove-labels test."""

  def testUpdateWithLabelsAndRemoveLabels(self):
    snapshot_ref = self._GetSnapshotRef('snapshot-1')

    snapshot_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')
    )
    edited_labels = (('key2', 'value2'), ('key3', 'value3'))

    snapshot = self._MakeSnapshotProto(
        snapshot_ref, labels=snapshot_labels, fingerprint=b'fingerprint-42')
    updated_snapshot = self._MakeSnapshotProto(
        snapshot_ref, labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, snapshot_ref)

    self._ExpectGetRequest(snapshot_ref, snapshot)
    self._ExpectLabelsSetRequest(
        snapshot_ref, edited_labels, b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(snapshot_ref, updated_snapshot)

    response = self.Run(
        'compute snapshots remove-labels {} --labels key1,key0'
        .format(snapshot_ref.SelfLink()))
    self.assertEqual(response, updated_snapshot)

  def testRemoveAll(self):
    snapshot_ref = self._GetSnapshotRef('snapshot-1')

    snapshot_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3')
    )

    snapshot = self._MakeSnapshotProto(
        snapshot_ref, labels=snapshot_labels, fingerprint=b'fingerprint-42')
    updated_snapshot = self._MakeSnapshotProto(snapshot_ref, labels={})
    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, snapshot_ref)

    self._ExpectGetRequest(snapshot_ref, snapshot)
    self._ExpectLabelsSetRequest(
        snapshot_ref, {}, b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(snapshot_ref, updated_snapshot)

    response = self.Run(
        'compute snapshots remove-labels {} --all'
        .format(snapshot_ref.SelfLink()))
    self.assertEqual(response, updated_snapshot)

  def testRemoveNonExisting(self):
    snapshot_ref = self._GetSnapshotRef('snapshot-1')

    snapshot_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))

    snapshot = self._MakeSnapshotProto(
        snapshot_ref, labels=snapshot_labels, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(snapshot_ref, snapshot)

    response = self.Run(
        'compute snapshots remove-labels {} --labels DoesNotExist'
        .format(snapshot_ref.SelfLink()))
    self.assertEqual(response, snapshot)

  def testRemoveWithNoLabelsOnSnapshot(self):
    snapshot_ref = self._GetSnapshotRef('snapshot-1')
    snapshot = self._MakeSnapshotProto(
        snapshot_ref, labels={}, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(snapshot_ref, snapshot)

    response = self.Run(
        'compute snapshots remove-labels {} --labels DoesNotExist'
        .format(snapshot_ref.SelfLink()))
    self.assertEqual(response, snapshot)

  def testNoLabelsOrAllSpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--all | --labels) must be specified.'):
      self.Run('compute snapshots remove-labels snapshot-1')

  def testResourceNotFound(self):
    snapshot_ref = self._GetSnapshotRef('some-snapshot')
    error = http_error.MakeHttpError(
        code=404,
        message='some-snapshot was not found',
        reason='NOT FOUND',
        content={},
        url='')

    self._ExpectGetRequest(
        snapshot_ref=snapshot_ref, snapshot=None, exception=error)

    with self.AssertRaisesHttpExceptionMatches(
        'NOT FOUND: some-snapshot was not found'):
      self.Run(
          'compute snapshots remove-labels {} --all'
          .format(snapshot_ref.SelfLink()))


if __name__ == '__main__':
  test_case.main()
