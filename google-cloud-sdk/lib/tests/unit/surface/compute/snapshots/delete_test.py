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
"""Tests for the snapshots delete subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class SnapshotsDeleteTest(test_base.BaseTest,
                          completer_test_base.CompleterBase):

  def testWithSingleSnapshot(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute snapshots delete snapshot-1
        """)

    self.CheckRequests(
        [(self.compute_v1.snapshots,
          'Delete',
          messages.ComputeSnapshotsDeleteRequest(
              snapshot='snapshot-1',
              project='my-project'))],
    )

  def testWithManySnapshots(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute snapshots delete snapshot-1 snapshot-2 snapshot-3
        """)

    self.CheckRequests(
        [(self.compute_v1.snapshots,
          'Delete',
          messages.ComputeSnapshotsDeleteRequest(
              snapshot='snapshot-1',
              project='my-project')),

         (self.compute_v1.snapshots,
          'Delete',
          messages.ComputeSnapshotsDeleteRequest(
              snapshot='snapshot-2',
              project='my-project')),

         (self.compute_v1.snapshots,
          'Delete',
          messages.ComputeSnapshotsDeleteRequest(
              snapshot='snapshot-3',
              project='my-project'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute snapshots delete snapshot-1 snapshot-2 snapshot-3
        """)

    self.CheckRequests(
        [(self.compute_v1.snapshots,
          'Delete',
          messages.ComputeSnapshotsDeleteRequest(
              snapshot='snapshot-1',
              project='my-project')),

         (self.compute_v1.snapshots,
          'Delete',
          messages.ComputeSnapshotsDeleteRequest(
              snapshot='snapshot-2',
              project='my-project')),

         (self.compute_v1.snapshots,
          'Delete',
          messages.ComputeSnapshotsDeleteRequest(
              snapshot='snapshot-3',
              project='my-project'))],
    )

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute snapshots delete snapshot-1 snapshot-2 snapshot-3
          """)

    self.CheckRequests()

  def testDeleteCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.SNAPSHOTS)
    self.RunCompletion(
        'compute snapshots delete ',
        [
            'snapshot-1',
            'snapshot-3',
            'snapshot-2',
        ])

if __name__ == '__main__':
  test_case.main()
