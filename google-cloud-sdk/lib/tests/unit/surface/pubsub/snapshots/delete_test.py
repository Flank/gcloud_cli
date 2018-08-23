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

"""Test of the 'pubsub snapshots delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.pubsub import base


class SnapshotsDeleteTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.svc = self.client.projects_snapshots.Delete

  def testSnapshotsDelete(self):
    snapshot_to_delete = util.ParseSnapshot('snap1', self.Project())

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsDeleteRequest(
            snapshot=snapshot_to_delete.RelativeName()),
        response='')

    result = list(self.Run('pubsub snapshots delete snap1'))

    self.assertEqual(1, len(result))
    self.assertEqual(result[0]['snapshotId'], snapshot_to_delete.RelativeName())

  def testSnapshotsDeleteNonExistent(self):
    snapshot_to_delete = util.ParseSnapshot('not_there', self.Project())

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsDeleteRequest(
            snapshot=snapshot_to_delete.RelativeName()),
        response='',
        exception=http_error.MakeHttpError(message='Snapshot does not exist.'))

    with self.AssertRaisesExceptionMatches(
        util.RequestsFailedError,
        'Failed to delete the following: [not_there].'):
      self.Run('pubsub snapshots delete not_there')
    self.AssertErrContains(snapshot_to_delete.RelativeName())
    self.AssertErrContains('Snapshot does not exist.')

  def testSnapshotsDeleteFullUri(self):
    snapshot_to_delete = util.ParseSnapshot('snap1', self.Project())

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsDeleteRequest(
            snapshot=snapshot_to_delete.RelativeName()),
        response='')

    result = list(self.Run('pubsub snapshots delete {}'.format(
        snapshot_to_delete.SelfLink())))

    self.assertEqual(1, len(result))
    self.assertEqual(result[0]['snapshotId'], snapshot_to_delete.RelativeName())


if __name__ == '__main__':
  test_case.main()
