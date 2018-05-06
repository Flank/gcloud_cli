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

"""Tests for the Cloud Pub/Sub Snapshots library."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import snapshots
from googlecloudsdk.command_lib.pubsub import util
from tests.lib import test_case
from tests.lib.api_lib.util import list_slicer
from tests.lib.surface.pubsub import base

from six.moves import range  # pylint: disable=redefined-builtin
from six.moves import zip  # pylint: disable=redefined-builtin


class SnapshotsTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.snapshots_client = snapshots.SnapshotsClient(self.client,
                                                      self.msgs)
    self.snapshots_service = self.client.projects_snapshots

  def testCreate(self):
    snapshot_ref = util.ParseSnapshot('snap1', self.Project())
    subscription_ref = util.ParseSubscription('sub1', self.Project())
    create_req = self.msgs.PubsubProjectsSnapshotsCreateRequest(
        createSnapshotRequest=self.msgs.CreateSnapshotRequest(
            subscription=subscription_ref.RelativeName()),
        name=snapshot_ref.RelativeName())
    snapshot = self.msgs.Snapshot(name=snapshot_ref.RelativeName())
    self.snapshots_service.Create.Expect(create_req, snapshot)
    result = self.snapshots_client.Create(snapshot_ref, subscription_ref)
    self.assertEqual(result, snapshot)

  def testCreate_Labels(self):
    labels = self.msgs.CreateSnapshotRequest.LabelsValue(additionalProperties=[
        self.msgs.CreateSnapshotRequest.LabelsValue.AdditionalProperty(
            key='label1', value='value1')
    ])
    snapshot_ref = util.ParseSnapshot('snap1', self.Project())
    subscription_ref = util.ParseSubscription('sub1', self.Project())
    create_req = self.msgs.PubsubProjectsSnapshotsCreateRequest(
        createSnapshotRequest=self.msgs.CreateSnapshotRequest(
            subscription=subscription_ref.RelativeName(),
            labels=labels
        ),
        name=snapshot_ref.RelativeName())
    snapshot = self.msgs.Snapshot(name=snapshot_ref.RelativeName())
    self.snapshots_service.Create.Expect(create_req, snapshot)
    result = self.snapshots_client.Create(snapshot_ref, subscription_ref,
                                          labels=labels)
    self.assertEqual(result, snapshot)

  def testDelete(self):
    snapshot_ref = util.ParseSnapshot('snap1', self.Project())
    self.snapshots_service.Delete.Expect(
        self.msgs.PubsubProjectsSnapshotsDeleteRequest(
            snapshot=snapshot_ref.RelativeName()),
        self.msgs.Empty())
    self.snapshots_client.Delete(snapshot_ref)

  def testList(self):
    project_ref = util.ParseProject(self.Project())
    snapshots_list = [self.msgs.Snapshot(name=str(i)) for i in range(200)]
    slices, token_pairs = list_slicer.SliceList(snapshots_list, 100)
    for slice_, (current_token, next_token) in zip(slices, token_pairs):
      self.snapshots_service.List.Expect(
          self.msgs.PubsubProjectsSnapshotsListRequest(
              project=project_ref.RelativeName(),
              pageSize=100,
              pageToken=current_token),
          self.msgs.ListSnapshotsResponse(
              snapshots=snapshots_list[slice_],
              nextPageToken=next_token))

    result = self.snapshots_client.List(project_ref)
    self.assertEqual(list(result), snapshots_list)

  def testPatch(self):
    snapshot_ref = util.ParseSnapshot('snapshot1', self.Project())
    labels = self.msgs.Snapshot.LabelsValue(additionalProperties=[
        self.msgs.Snapshot.LabelsValue.AdditionalProperty(
            key='label', value='value')])
    snapshot = self.msgs.Snapshot(
        name=snapshot_ref.RelativeName(),
        labels=labels)
    self.snapshots_service.Patch.Expect(
        self.msgs.PubsubProjectsSnapshotsPatchRequest(
            name=snapshot_ref.RelativeName(),
            updateSnapshotRequest=self.msgs.UpdateSnapshotRequest(
                snapshot=snapshot,
                updateMask='labels')),
        snapshot)
    self.assertEqual(self.snapshots_client.Patch(snapshot_ref, labels),
                     snapshot)

  def testPatchNoFieldsSpecified(self):
    snapshot_ref = util.ParseSnapshot('snapshot1', self.Project())
    with self.assertRaises(snapshots.NoFieldsSpecifiedError):
      self.snapshots_client.Patch(snapshot_ref)

if __name__ == '__main__':
  test_case.main()

