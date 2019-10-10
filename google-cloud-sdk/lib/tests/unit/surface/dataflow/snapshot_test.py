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
"""Tests for 'dataflow snapshots' command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dataflow import base


class SnapshotTest(base.DataflowMockingTestBase,
                   sdk_test_base.WithOutputCapture):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreateSnapshot(self):
    self.MockCreateSnapshot(
        job_id='job1',
        location='us-central1',
        ttl='259200s',
        snapshot_sources=True)

    snapshot = self.Run(
        'dataflow snapshots create --job-id=job1 --region=us-central1 ' +
        '--snapshot-ttl=3d --snapshot-sources=true')
    self.assertEqual(snapshot.sourceJobId, 'job1')
    self.assertEqual(snapshot.ttl, '259200s')
    self.assertEqual(snapshot.pubsubMetadata[0].topicName, 'topic')

  def testListSnapshots(self):
    self.MockListSnapshot(job_id='job1', location='us-central1')
    response = self.Run('dataflow snapshots list --job-id=job1'
                        ' --region=us-central1')
    self.assertEqual(response.snapshots[0].sourceJobId, 'job1')


if __name__ == '__main__':
  test_case.main()
