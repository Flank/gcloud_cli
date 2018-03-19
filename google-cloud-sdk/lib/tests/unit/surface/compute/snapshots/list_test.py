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
"""Tests for the snapshots list subcommand."""
import textwrap

from googlecloudsdk.command_lib.compute.disks import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class SnapshotsListTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(test_resources.SNAPSHOTS))

  def testTableOutput(self):
    self.Run(
        'compute snapshots list')
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute_v1.snapshots,
        project='my-project',
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       DISK_SIZE_GB SRC_DISK            STATUS
            snapshot-1 10           zone-1/disks/disk-1 READY
            snapshot-2 10           zone-1/disks/disk-2 READY
            snapshot-3 10           zone-1/disks/disk-3 READY
            """), normalize_space=True)

  def testPositionalArgsWithSimpleNames(self):
    self.Run("""
        compute snapshots list
          snapshot-1 snapshot-2
          --uri
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute_v1.snapshots,
        project='my-project',
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/global/snapshots/snapshot-1
            https://www.googleapis.com/compute/v1/projects/my-project/global/snapshots/snapshot-2
            """))

  def testPositionalArgsWithUri(self):
    self.Run("""
        compute snapshots list
          https://www.googleapis.com/compute/v1/projects/my-project/global/snapshots/snapshot-1
          --uri
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute_v1.snapshots,
        project='my-project',
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/global/snapshots/snapshot-1
            """))

  def testPositionalArgsWithUriAndSimpleName(self):
    self.Run("""
        compute snapshots list
          https://www.googleapis.com/compute/v1/projects/my-project/global/snapshots/snapshot-1
          snapshot-2
          --uri
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute_v1.snapshots,
        project='my-project',
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/global/snapshots/snapshot-1
            https://www.googleapis.com/compute/v1/projects/my-project/global/snapshots/snapshot-2
            """))

  def testSnapshotsCompleter(self):
    self.RunCompleter(
        flags.SnapshotsCompleter,
        expected_command=[
            'compute',
            'snapshots',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'snapshot-1',
            'snapshot-2',
            'snapshot-3',
        ],
        cli=self.cli,
    )


if __name__ == '__main__':
  test_case.main()
