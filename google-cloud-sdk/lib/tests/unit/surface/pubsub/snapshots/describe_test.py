# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Test of the 'pubsub snapshots describe' command."""
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.pubsub import base


class SnapshotsDescribeTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.svc = self.client.projects_snapshots.Get
    self.snapshot_ref = util.ParseSnapshot('snap1', self.Project())
    self.topic_ref = util.ParseTopic('topic1', self.Project())
    self.snapshot = self.msgs.Snapshot(
        name=self.snapshot_ref.RelativeName(),
        topic=self.topic_ref.RelativeName(),
        expireTime='2018-01-12T12:34:56.000000Z')

  def testSnapshotsDescribe_Name(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsGetRequest(
            snapshot=self.snapshot_ref.RelativeName()),
        response=self.snapshot)
    result = self.Run('pubsub snapshots describe {}'.format(
        self.snapshot_ref.Name()))
    self.assertEqual(result, self.snapshot)

  def testSnapshotsDescribe_FullUri(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsGetRequest(
            snapshot=self.snapshot_ref.RelativeName()),
        response=self.snapshot)

    result = self.Run('pubsub snapshots describe {}'.format(
        self.snapshot_ref.SelfLink()))

    self.assertEqual(result, self.snapshot)

  def testSnapshotsDescribeNonExistent(self):
    snapshot_dne = util.ParseSnapshot('dne', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsGetRequest(
            snapshot=snapshot_dne.RelativeName()),
        response='',
        exception=http_error.MakeHttpError(message='Snapshot does not exist.'))

    with self.AssertRaisesHttpExceptionMatches('Snapshot does not exist.'):
      self.Run('pubsub snapshots describe dne')


if __name__ == '__main__':
  test_case.main()
