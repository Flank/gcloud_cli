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
"""Tests for the sole-tenancy hosts list subcommand."""
import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.sole_tenancy.hosts import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class HostsListTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetZonalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_zonal_resources = lister_patcher.start()
    self.mock_get_zonal_resources.return_value = (
        resource_projector.MakeSerializable(test_resources.HOSTS))

  def testTableOutput(self):
    self.Run('compute sole-tenancy hosts list')
    self.mock_get_zonal_resources.assert_called_once_with(
        service=self.compute_alpha.hosts,
        project='my-project',
        requested_zones=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME ZONE INSTANCES STATUS
            host-1 zone-1 2 READY
            host-2 zone-1 1 READY
            host-3 zone-1 0 REPAIR
            """), normalize_space=True)

  def testHostsCompleter(self):
    self.RunCompleter(
        flags.HostsCompleter,
        expected_command=[
            'alpha',
            'compute',
            'sole-tenancy',
            'hosts',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'host-1',
            'host-2',
            'host-3'
        ],
        cli=self.cli,
    )
    self.mock_get_zonal_resources.assert_called_once_with(
        service=self.compute_alpha.hosts,
        project='my-project',
        requested_zones=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])


if __name__ == '__main__':
  test_case.main()
