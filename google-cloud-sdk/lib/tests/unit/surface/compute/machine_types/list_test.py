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
"""Tests for the machine-types list subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
from tests.lib.surface.compute import utils

import mock


class MachineTypesListTest(test_base.BaseTest,
                           completer_test_base.CompleterBase):

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetZonalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_zonal_resources = lister_patcher.start()
    self.mock_get_zonal_resources.return_value = (
        resource_projector.MakeSerializable(test_resources.MACHINE_TYPES))

  def testTableDefaultFilter(self):
    self.Run("""
        compute machine-types list
        """)
    self.mock_get_zonal_resources.assert_called_once_with(
        service=self.compute_v1.machineTypes,
        project='my-project',
        requested_zones=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME            ZONE   CPUS MEMORY_GB DEPRECATED
            n1-standard-1   zone-1 1     3.75
            n1-highmem-2    zone-1 2    30.00
            """), normalize_space=True)

  def testTableEmptyFilter(self):
    self.Run("""
        compute machine-types list --filter=""
        """)
    self.mock_get_zonal_resources.assert_called_once_with(
        service=self.compute_v1.machineTypes,
        project='my-project',
        requested_zones=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME            ZONE   CPUS MEMORY_GB DEPRECATED
            n1-standard-1   zone-1 1     3.75
            n1-standard-1-d zone-1 1     3.75     OBSOLETE
            n1-highmem-2    zone-1 2    30.00
            """), normalize_space=True)

  def testTableExplicitFilter(self):
    self.Run("""
        compute machine-types list --filter=deprecated.state=OBSOLETE
        """)
    self.mock_get_zonal_resources.assert_called_once_with(
        service=self.compute_v1.machineTypes,
        project='my-project',
        requested_zones=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME            ZONE   CPUS MEMORY_GB DEPRECATED
            n1-standard-1-d zone-1 1     3.75     OBSOLETE
            """), normalize_space=True)

  def testMachineTypesCompleter(self):
    self.RunCompleter(
        completers.MachineTypesCompleter,
        expected_command=[
            'compute',
            'machine-types',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'n1-standard-1',
            'n1-standard-2',
        ],
        cli=self.cli,
    )

  def testSimple(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=test_resources.MACHINE_TYPES)
    result = list(self.Run(
        'compute machine-types list --format=disable --filter=""'))
    self.assertEqual(result, test_resources.MACHINE_TYPES)

  def testComplex(self):
    self.api_mock = utils.ComputeApiMock('v1').Start()
    self.addCleanup(self.api_mock.Stop)
    self.ExpectListerInvoke(
        scope_set=self.MakeZoneSet(['my-zone']),
        filter_expr='name eq ".*(asdf).*"',
        max_results=123,
        result=[],
        with_implementation=lister.ZonalLister(
            self.api_mock.adapter,
            self.api_mock.adapter.apitools_client.machineTypes))

    result = list(
        self.Run('compute machine-types list '
                 '--page-size=123 '
                 '--filter="name ~ asdf" '
                 '--zones=my-zone '
                 '--format=disable'))
    self.assertEqual(result, [])


if __name__ == '__main__':
  test_case.main()
