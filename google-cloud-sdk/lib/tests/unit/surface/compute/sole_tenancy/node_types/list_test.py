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
"""Tests for the sole-tenancy node-types list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.compute.sole_tenancy.node_types import flags
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class NodeTypesListTest(test_base.BaseTest,
                        completer_test_base.CompleterBase):

  def SetUp(self):
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def testTableOutput(self):
    self.list_json.side_effect = iter([test_resources.NODE_TYPES])
    result = list(self.Run('compute sole-tenancy node-types list'))
    self.list_json.assert_called_once_with(
        requests=[(self.compute.nodeTypes, 'AggregatedList',
                   self.messages.ComputeNodeTypesAggregatedListRequest(
                       project='my-project', includeAllScopes=True))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.assertEqual(test_resources.NODE_TYPES, result)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME           ZONE   CPUs MEMORY_MB DEPRECATED
            iAPX-286       zone-1 1    256       OBSOLETE
            n1-node-96-624 zone-1 96   416000
            """),
        normalize_space=True)

  def testNodeTypesCompleter(self):
    self.list_json.side_effect = iter([test_resources.NODE_TYPES])
    self.RunCompleter(
        flags.NodeTypesCompleter,
        expected_command=[
            'compute',
            'sole-tenancy',
            'node-types',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'iAPX-286',
            'n1-node-96-624',
        ],
        cli=self.cli,
    )

    self.list_json.assert_called_once_with(
        requests=[(self.compute.nodeTypes, 'AggregatedList',
                   self.messages.ComputeNodeTypesAggregatedListRequest(
                       project='my-project', includeAllScopes=True))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])


if __name__ == '__main__':
  test_case.main()
