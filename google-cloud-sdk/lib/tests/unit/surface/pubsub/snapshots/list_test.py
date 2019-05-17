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

"""Test of the 'pubsub snapshots list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib.surface.pubsub import base

from six.moves import range  # pylint: disable=redefined-builtin


class SnapshotsListTest(base.CloudPubsubTestBase,
                        sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_snapshots.List
    self.project_ref = util.ParseProject(self.Project())
    self.snapshot_refs = [
        util.ParseSnapshot('snap{}'.format(i+1), self.Project())
        for i in range(3)]
    self.topic_refs = [
        util.ParseTopic('topic1', self.Project()),
        util.ParseTopic('topic2', self.Project())]
    self.snapshots = [
        self.msgs.Snapshot(
            name=self.snapshot_refs[0].RelativeName(),
            topic=self.topic_refs[0].RelativeName(),
            expireTime='2016-10-31T12:34:56.000000Z',
        ),
        self.msgs.Snapshot(
            name=self.snapshot_refs[1].RelativeName(),
            topic=self.topic_refs[1].RelativeName(),
            expireTime='2015-02-12T09:08:07.000000Z'
        ),
        self.msgs.Snapshot(
            name=self.snapshot_refs[2].RelativeName(),
            topic=self.topic_refs[1].RelativeName(),
            expireTime='2015-02-13T09:08:07.000000Z'
        )]

  def testSnapshotsListFields(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSnapshotsResponse(snapshots=self.snapshots))

    self.Run('pubsub snapshots list --format=flattened[nopad]')

    self.AssertOutputEquals("""\
---
expireTime: 2016-10-31T12:34:56.000000Z
name: projects/{project}/snapshots/snap1
projectId: {project}
snapshotId: snap1
topic: projects/{project}/topics/topic1
topicId: topic1
---
expireTime: 2015-02-12T09:08:07.000000Z
name: projects/{project}/snapshots/snap2
projectId: {project}
snapshotId: snap2
topic: projects/{project}/topics/topic2
topicId: topic2
---
expireTime: 2015-02-13T09:08:07.000000Z
name: projects/{project}/snapshots/snap3
projectId: {project}
snapshotId: snap3
topic: projects/{project}/topics/topic2
topicId: topic2
""".format(project=self.Project()), normalize_space=True)

  def testSnapshotsList(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSnapshotsResponse(
            snapshots=self.snapshots))

    self.Run('pubsub snapshots list --format=[no-box]')

    self.AssertOutputContains("""\
{project} snap1 topic1 2016-10-31T12:34:56.000000Z
{project} snap2 topic2 2015-02-12T09:08:07.000000Z
{project} snap3 topic2 2015-02-13T09:08:07.000000Z
""".format(project=self.Project()), normalize_space=True)

  def testSnapshotsListUri(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSnapshotsResponse(
            snapshots=self.snapshots))

    self.Run('pubsub snapshots list --uri')

    expected_output = '\n'.join([
        self.GetSnapshotUri(snap.name) for snap in self.snapshots])
    self.AssertOutputContains(expected_output, normalize_space=True)

  def testSnapshotsListWithFilter(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSnapshotsResponse(
            snapshots=self.snapshots))

    self.Run('pubsub snapshots list --format=csv[no-heading](projectId,'
             'snapshotId,topicId,expireTime)'
             ' --filter=snapshotId:snap2')

    self.AssertOutputEquals("""\
{project},snap2,topic2,2015-02-12T09:08:07.000000Z
""".format(project=self.Project()))

  def testSnapshotsListWithFilterAndLimit(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSnapshotsResponse(
            snapshots=self.snapshots))

    self.Run('pubsub snapshots list --format=csv[no-heading](projectId,'
             'snapshotId,topicId,expireTime)'
             ' --filter=snapshotId:snap3 --limit=2')

    self.AssertOutputEquals("""\
{project},snap3,topic2,2015-02-13T09:08:07.000000Z
""".format(project=self.Project()))

  def testSnapshotsPaginatedList(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSnapshotsResponse(
            snapshots=[self.snapshots[0]],
            nextPageToken='thereisanotherpage'))

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsListRequest(
            project=self.project_ref.RelativeName(),
            pageToken='thereisanotherpage'),
        response=self.msgs.ListSnapshotsResponse(
            snapshots=[self.snapshots[1]]))

    self.Run('pubsub snapshots list --format=csv[no-heading]'
             '(projectId,snapshotId,topicId,expireTime)')

    self.AssertOutputEquals("""\
{project},snap1,topic1,2016-10-31T12:34:56.000000Z
{project},snap2,topic2,2015-02-12T09:08:07.000000Z
""".format(project=self.Project()))

  def testSnapshotsListLimit(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsListRequest(
            project=self.project_ref.RelativeName()),
        response=self.msgs.ListSnapshotsResponse(
            snapshots=self.snapshots,
            nextPageToken='thereisanotherpage'))

    self.Run('pubsub snapshots list --format=csv[no-heading]'
             '(projectId,snapshotId,topicId,expireTime) --limit=2')

    self.AssertOutputEquals("""\
{project},snap1,topic1,2016-10-31T12:34:56.000000Z
{project},snap2,topic2,2015-02-12T09:08:07.000000Z
""".format(project=self.Project()))

  def testSnapshotsListPage(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsListRequest(
            project=self.project_ref.RelativeName(),
            pageSize=2),
        response=self.msgs.ListSnapshotsResponse(
            snapshots=self.snapshots[0:2],
            nextPageToken='thereisanotherpage'))

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsListRequest(
            project=self.project_ref.RelativeName(),
            pageSize=2,
            pageToken='thereisanotherpage'),
        response=self.msgs.ListSnapshotsResponse(
            snapshots=self.snapshots[2:3]))

    self.Run('pubsub snapshots list --format=csv[no-heading]'
             '(projectId,snapshotId,topicId,expireTime) --page-size=2')

    self.AssertOutputEquals("""\
{project},snap1,topic1,2016-10-31T12:34:56.000000Z
{project},snap2,topic2,2015-02-12T09:08:07.000000Z
{project},snap3,topic2,2015-02-13T09:08:07.000000Z
""".format(project=self.Project()))

  def testSnapshotsListPageLimit(self):
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsListRequest(
            project=self.project_ref.RelativeName(),
            pageSize=2),
        response=self.msgs.ListSnapshotsResponse(
            snapshots=self.snapshots[0:2],
            nextPageToken='thereisanotherpage'))

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSnapshotsListRequest(
            project=self.project_ref.RelativeName(),
            pageSize=2,
            pageToken='thereisanotherpage'),
        response=self.msgs.ListSnapshotsResponse(
            snapshots=self.snapshots[2:3]))

    self.Run('pubsub snapshots list --format=csv[no-heading]'
             '(projectId,snapshotId,topicId,expireTime)'
             ' --page-size=2 --limit=2')

    self.AssertOutputEquals("""\
{project},snap1,topic1,2016-10-31T12:34:56.000000Z
{project},snap2,topic2,2015-02-12T09:08:07.000000Z
""".format(project=self.Project()))


if __name__ == '__main__':
  sdk_test_base.main()
