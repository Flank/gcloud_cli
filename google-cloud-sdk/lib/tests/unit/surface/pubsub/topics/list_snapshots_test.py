# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Test of the 'pubsub topics list-snapshots' command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class TopicsListSnapshotsAlphaTest(base.CloudPubsubTestBase,
                                   sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_topics_snapshots.List
    self.topic_ref = util.ParseTopic('topic', self.Project())

  def _CreateSnapshotNames(self, names):
    return [util.ParseSnapshot(name, self.Project()).RelativeName()
            for name in names]

  def testListTopicSnapshots(self):
    snapshots_names = self._CreateSnapshotNames(
        ['snap1', 'snap2', 'snap3'])
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsSnapshotsListRequest(
            topic=self.topic_ref.RelativeName()),
        response=self.msgs.ListTopicSnapshotsResponse(
            snapshots=snapshots_names))

    self.Run('pubsub topics list-snapshots topic')
    self.AssertOutputEquals("""\
---
  projects/{0}/snapshots/snap1
---
  projects/{0}/snapshots/snap2
---
  projects/{0}/snapshots/snap3
""".format(self.Project()))

  def testListTopicSnapshotsUri(self):
    snapshots_names = self._CreateSnapshotNames(
        ['snap1', 'snap2', 'snap3'])
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsSnapshotsListRequest(
            topic=self.topic_ref.RelativeName()),
        response=self.msgs.ListTopicSnapshotsResponse(
            snapshots=snapshots_names))
    print(self.msgs.ListTopicSnapshotsResponse(snapshots=snapshots_names))

    self.Run('pubsub topics list-snapshots topic --uri')

    expected_output = '\n'.join([
        self.GetSnapshotUri(snap) for snap in snapshots_names])
    self.AssertOutputContains(expected_output, normalize_space=True)

  def testListTopicSnapshotsFullUri(self):
    snapshot_names = ['snap1', 'snap2', 'snap3']
    snapshots_names = self._CreateSnapshotNames(snapshot_names)

    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsSnapshotsListRequest(
            topic=self.topic_ref.RelativeName()),
        response=self.msgs.ListTopicSnapshotsResponse(
            snapshots=snapshots_names))

    self.Run('pubsub topics list-snapshots {} --format=list'
             .format(self.topic_ref.SelfLink()))

    output = '\n'.join([' - {}'.format(name) for name in snapshots_names])
    self.AssertOutputContains(output)

  def testListTopicSnapshotsWithFilter(self):
    snapshots_names = self._CreateSnapshotNames(
        ['snap1', 'snap2', 'snap3'])
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsSnapshotsListRequest(
            topic=self.topic_ref.RelativeName()),
        response=self.msgs.ListTopicSnapshotsResponse(
            snapshots=snapshots_names))

    self.Run('pubsub topics list-snapshots topic'
             ' --filter="snap1 OR snap2"')

    self.AssertOutputEquals("""\
---
  projects/{0}/snapshots/snap1
---
  projects/{0}/snapshots/snap2
""".format(self.Project()))

  def testListTopicSnapshotsNoMatch(self):
    snapshots_names = self._CreateSnapshotNames(
        ['snap1', 'snap2', 'snap3'])
    self.svc.Expect(
        request=self.msgs.PubsubProjectsTopicsSnapshotsListRequest(
            topic=self.topic_ref.RelativeName()),
        response=self.msgs.ListTopicSnapshotsResponse(
            snapshots=snapshots_names))

    self.Run('pubsub topics list-snapshots topic'
             ' --filter=no-match')
    self.AssertOutputEquals('')


if __name__ == '__main__':
  test_case.main()
