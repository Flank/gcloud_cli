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
"""Tests for the target-instances list subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.command_lib.compute.target_instances import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


class DisksListTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetZonalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_zonal_resources = lister_patcher.start()
    self.mock_get_zonal_resources.return_value = (
        resource_projector.MakeSerializable(test_resources.TARGET_INSTANCES))

  def testTableOutput(self):
    self.Run(
        'compute target-instances list')
    self.mock_get_zonal_resources.assert_called_once_with(
        service=self.compute_v1.targetInstances,
        project='my-project',
        requested_zones=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME              ZONE   INSTANCE   NAT_POLICY
            target-instance-1 zone-1 instance-1 NO_NAT
            target-instance-2 zone-1 instance-2 NO_NAT
            target-instance-3 zone-2 instance-3 NO_NAT
            """), normalize_space=True)

  def testTargetInstancesCompleter(self):
    self.RunCompleter(
        flags.TargetInstancesCompleter,
        expected_command=[
            'compute',
            'target-instances',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'target-instance-1',
            'target-instance-2',
            'target-instance-3',
        ],
        cli=self.cli,
    )
    self.mock_get_zonal_resources.assert_called_once_with(
        service=self.compute_v1.targetInstances,
        project='my-project',
        requested_zones=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])


if __name__ == '__main__':
  test_case.main()
