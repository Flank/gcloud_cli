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
"""Tests for the target-pools list subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.command_lib.compute.target_pools import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class TargetPoolsListTest(test_base.BaseTest,
                          completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetRegionalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_regional_resources = lister_patcher.start()
    self.mock_get_regional_resources.return_value = (
        resource_projector.MakeSerializable(test_resources.TARGET_POOLS))

  def testTableOutput(self):
    self.Run(
        'compute target-pools list')
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute_v1.targetPools,
        project='my-project',
        requested_regions=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   REGION   SESSION_AFFINITY BACKUP HEALTH_CHECKS
            pool-1 region-1 CLIENT_IP        pool-2
            pool-2 region-1 CLIENT_IP_PROTO         check-1,check-2
            pool-3 region-1 NONE
            """), normalize_space=True)

  def testPositionalArgsWithSimpleNames(self):
    self.Run("""
        compute target-pools list
          pool-1 pool-2
          --uri
        """)
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute_v1.targetPools,
        project='my-project',
        requested_regions=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-1
            https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-2
            """))

  def testPositionalArgsWithUri(self):
    self.Run("""
        compute target-pools list
            https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-1
          --uri
        """)
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute_v1.targetPools,
        project='my-project',
        requested_regions=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-1
            """))

  def testPositionalArgsWithUriAndSimpleName(self):
    self.Run("""
        compute target-pools list
            https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-1
          pool-3
          --uri
        """)
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute_v1.targetPools,
        project='my-project',
        requested_regions=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-1
            https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-3
            """))

  def testPositionalArgsWithSimpleNamesAndRegionFlag(self):
    self.Run("""
        compute target-pools list
          pool-1 pool-2
          --regions region-1
          --uri
        """)
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute_v1.targetPools,
        project='my-project',
        requested_regions=['region-1'],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-1
            https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-2
            """))

  def testPositionalArgsWithSimpleNameAndUriAndRegionFlag(self):
    self.Run("""
        compute target-pools list
          pool-1
          https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-3
          --regions region-1
          --uri
        """)
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute_v1.targetPools,
        project='my-project',
        requested_regions=['region-1'],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-1
            https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/targetPools/pool-3
            """))

  def testTargetPoolsCompleter(self):
    self.RunCompleter(
        flags.TargetPoolsCompleter,
        expected_command=[
            'compute',
            'target-pools',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'pool-1',
            'pool-2',
            'pool-3',
        ],
        cli=self.cli,
    )
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute_v1.targetPools,
        project='my-project',
        requested_regions=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

if __name__ == '__main__':
  test_case.main()
