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
"""Tests for the snapshots describe subcommand."""
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class SnapshotsDescribeTest(test_base.BaseTest,
                            completer_test_base.CompleterBase,
                            test_case.WithOutputCapture):

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.SNAPSHOTS[0]],
    ])

    self.Run("""
        compute snapshots describe snapshot-1
        """)

    self.CheckRequests(
        [(self.compute_v1.snapshots,
          'Get',
          messages.ComputeSnapshotsGetRequest(
              project='my-project',
              snapshot='snapshot-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            diskSizeGb: '10'
            name: snapshot-1
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/global/snapshots/snapshot-1
            sourceDisk: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/disks/disk-1
            status: READY
            """))

  def testDescribeCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.SNAPSHOTS)
    self.RunCompletion(
        'compute snapshots describe ',
        [
            'snapshot-1',
            'snapshot-3',
            'snapshot-2',
        ])

if __name__ == '__main__':
  test_case.main()
