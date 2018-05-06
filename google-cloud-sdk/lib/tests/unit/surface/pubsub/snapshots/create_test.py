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

"""Test of the 'pubsub snapshots create' command."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.pubsub import base


class SnapshotsCreateTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.svc = self.client.projects_snapshots.Create

  def testSnapshotsCreate(self):
    snap_ref = util.ParseSnapshot('snap1', self.Project())
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())

    create_req = self.msgs.PubsubProjectsSnapshotsCreateRequest(
        createSnapshotRequest=self.msgs.CreateSnapshotRequest(
            subscription=sub_ref.RelativeName()),
        name=snap_ref.RelativeName())

    create_resp = self.msgs.Snapshot(name=snap_ref.RelativeName(),
                                     topic=topic_ref.RelativeName(),
                                     expireTime='sometime')

    self.svc.Expect(request=create_req, response=create_resp)

    result = list(self.Run(
        'pubsub snapshots create snap1 '
        '--subscription subs1'))

    self.assertEqual(result[0]['snapshotId'], snap_ref.RelativeName())
    self.assertEqual(result[0]['topic'], topic_ref.RelativeName())
    self.assertEqual(result[0]['expireTime'], 'sometime')

  def testSnapshotsCreateWithCrossProjectSubscription(self):
    snap_ref = util.ParseSnapshot('snap1', self.Project())
    sub_ref = util.ParseSubscription('subs1', 'other-project')
    topic_ref = util.ParseTopic('topic1', 'other-project')

    create_req = self.msgs.PubsubProjectsSnapshotsCreateRequest(
        createSnapshotRequest=self.msgs.CreateSnapshotRequest(
            subscription=sub_ref.RelativeName()),
        name=snap_ref.RelativeName())

    create_resp = self.msgs.Snapshot(name=snap_ref.RelativeName(),
                                     topic=topic_ref.RelativeName(),
                                     expireTime='sometime')

    self.svc.Expect(request=create_req, response=create_resp)

    result = list(self.Run(
        'pubsub snapshots create snap1 --subscription subs1'
        ' --subscription-project other-project'))

    self.assertEqual(result[0]['snapshotId'], snap_ref.RelativeName())
    self.assertEqual(result[0]['topic'], topic_ref.RelativeName())
    self.assertEqual(result[0]['expireTime'], 'sometime')

  def testSnapshotsCreateWithFullUri(self):
    snap_ref = util.ParseSnapshot('snap1', self.Project())
    sub_ref = util.ParseSubscription('subs1', 'other-project')
    topic_ref = util.ParseTopic('topic1', 'other-project')

    create_req = self.msgs.PubsubProjectsSnapshotsCreateRequest(
        createSnapshotRequest=self.msgs.CreateSnapshotRequest(
            subscription=sub_ref.RelativeName()),
        name=snap_ref.RelativeName())

    create_resp = self.msgs.Snapshot(name=snap_ref.RelativeName(),
                                     topic=topic_ref.RelativeName(),
                                     expireTime='sometime')

    self.svc.Expect(request=create_req, response=create_resp)

    result = list(self.Run(
        'pubsub snapshots create snap1 --subscription {}'.format(
            sub_ref.SelfLink())))

    self.assertEqual(result[0]['snapshotId'], snap_ref.RelativeName())
    self.assertEqual(result[0]['topic'], topic_ref.RelativeName())
    self.assertEqual(result[0]['expireTime'], 'sometime')

  def testSnapshotsCreateWithNonExistentSubscription(self):
    snap_ref = util.ParseSnapshot('snap1', self.Project())
    sub_ref = util.ParseSubscription('subs-DNE', self.Project())

    create_req = self.msgs.PubsubProjectsSnapshotsCreateRequest(
        createSnapshotRequest=self.msgs.CreateSnapshotRequest(
            subscription=sub_ref.RelativeName()),
        name=snap_ref.RelativeName())

    self.svc.Expect(
        request=create_req,
        response=None,
        exception=http_error.MakeHttpError(404, 'Subscription does not exist.'),
    )

    with self.AssertRaisesExceptionMatches(
        util.RequestsFailedError,
        'Failed to create the following: [snap1].'):
      self.Run('pubsub snapshots create snap1 '
               '--subscription subs-DNE')
    self.AssertErrContains(snap_ref.RelativeName())
    self.AssertErrContains('Subscription does not exist.')

  def testSnapshotsCreateLabels(self):
    snap_ref = util.ParseSnapshot('snap1', self.Project())
    sub_ref = util.ParseSubscription('subs1', self.Project())
    topic_ref = util.ParseTopic('topic1', self.Project())

    labels = self.msgs.CreateSnapshotRequest.LabelsValue(additionalProperties=[
        self.msgs.CreateSnapshotRequest.LabelsValue.AdditionalProperty(
            key='key1', value='value1'),
        self.msgs.CreateSnapshotRequest.LabelsValue.AdditionalProperty(
            key='key2', value='value2')])
    create_req = self.msgs.PubsubProjectsSnapshotsCreateRequest(
        createSnapshotRequest=self.msgs.CreateSnapshotRequest(
            subscription=sub_ref.RelativeName(),
            labels=labels),
        name=snap_ref.RelativeName()
    )

    create_resp = self.msgs.Snapshot(
        name=snap_ref.RelativeName(),
        topic=topic_ref.RelativeName(),
        expireTime='sometime')

    self.svc.Expect(request=create_req, response=create_resp)

    result = list(self.Run(
        'pubsub snapshots create snap1 '
        '--labels key1=value1,key2=value2 '
        '--subscription subs1'))

    self.assertEqual(result[0]['snapshotId'], snap_ref.RelativeName())
    self.assertEqual(result[0]['topic'], topic_ref.RelativeName())
    self.assertEqual(result[0]['expireTime'], 'sometime')

if __name__ == '__main__':
  test_case.main()
