# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for in-place snapshot add-labels subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import in_place_snapshots_labels_test_base


class AddLabelsTest(
    in_place_snapshots_labels_test_base.InPlaceSnapshotsLabelsTestBase):
  """In-place snapshot add-labels test."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self._SetUp(self.track)

  def testZonalUpdateValidInPlaceSnapshotsWithLabelsAndRemoveLabels(self):
    ips_ref = self._GetInPlaceSnapshotRef('ips-1', zone='zone-1')

    ips_labels = (('key1', 'value1'), ('key2', 'value2'))
    add_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (('key1', 'value1'), ('key2', 'update2'), ('key4',
                                                               'value4'))

    ips = self._MakeInPlaceSnapshotProto(
        labels=ips_labels, fingerprint=b'fingerprint-42')
    updated_ips = self._MakeInPlaceSnapshotProto(labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1', zone='zone-1')
    operation = self._MakeOperationMessage(operation_ref, ips_ref)

    self._ExpectGetRequest(ips_ref, ips)
    self._ExpectLabelsSetRequest(ips_ref, edited_labels, b'fingerprint-42',
                                 operation)
    self._ExpectOperationPollingRequest(operation_ref, operation)
    self._ExpectGetRequest(ips_ref, updated_ips)

    response = self.Run(
        'compute in-place-snapshots add-labels {} --labels {}'.format(
            ips_ref.SelfLink(), ','.join(
                ['{0}={1}'.format(pair[0], pair[1]) for pair in add_labels])))
    self.assertEqual(response, updated_ips)

  def testRegionalUpdateValidInPlaceSnapshotsWithLabelsAndRemoveLabels(self):
    ips_ref = self._GetInPlaceSnapshotRef('ips-1', region='region-1')

    ips_labels = (('key1', 'value1'), ('key2', 'value2'))
    add_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (('key1', 'value1'), ('key2', 'update2'), ('key4',
                                                               'value4'))

    ips = self._MakeInPlaceSnapshotProto(
        labels=ips_labels, fingerprint=b'fingerprint-42')
    updated_ips = self._MakeInPlaceSnapshotProto(labels=edited_labels)
    operation_ref = self._GetOperationRef('operation-1', region='region-1')
    operation = self._MakeOperationMessage(operation_ref, ips_ref)

    self._ExpectGetRequest(ips_ref, ips)
    self._ExpectLabelsSetRequest(ips_ref, edited_labels, b'fingerprint-42',
                                 operation)
    self._ExpectOperationPollingRequest(operation_ref, operation)
    self._ExpectGetRequest(ips_ref, updated_ips)

    response = self.Run(
        'compute in-place-snapshots add-labels {} --labels {}'.format(
            ips_ref.SelfLink(), ','.join(
                ['{0}={1}'.format(pair[0], pair[1]) for pair in add_labels])))
    self.assertEqual(response, updated_ips)

  def testNoUpdate(self):
    ips_ref = self._GetInPlaceSnapshotRef('ips-1', zone='zone-1')

    ips_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    add_labels = (('key1', 'value1'), ('key3', 'value3'))

    ips = self._MakeInPlaceSnapshotProto(
        labels=ips_labels, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(ips_ref, ips)

    response = self.Run(
        'compute in-place-snapshots add-labels {} --labels {} '.format(
            ips_ref.SelfLink(), ','.join(
                ['{0}={1}'.format(pair[0], pair[1]) for pair in add_labels])))
    self.assertEqual(response, ips)

  def testNoLabelsSpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --labels: Must be specified.'):
      self.Run('compute in-place-snapshots add-labels label-1')

  def testInvalidLabel(self):
    ips_ref = self._GetInPlaceSnapshotRef('ips-1', zone='atlanta')

    ips = self._MakeInPlaceSnapshotProto(
        labels={}, fingerprint=b'fingerprint-42')
    add_labels = (('+notvalid', 'a'),)

    error = http_error.MakeHttpError(
        code=400,
        message='+notvalid',
        reason='Invalid label',
        content={},
        url='')

    self._ExpectGetRequest(ips_ref, ips)
    self._ExpectLabelsSetRequest(
        ips_ref=ips_ref,
        labels=add_labels,
        fingerprint=b'fingerprint-42',
        exception=error)

    with self.AssertRaisesHttpExceptionMatches('Invalid label: +notvalid'):
      self.Run('compute in-place-snapshots add-labels {} --labels {} '.format(
          ips_ref.SelfLink(),
          ','.join(['{0}={1}'.format(pair[0], pair[1]) for pair in add_labels
                   ])))


if __name__ == '__main__':
  test_case.main()
