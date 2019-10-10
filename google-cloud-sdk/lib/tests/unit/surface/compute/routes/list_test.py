# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the routes list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class RoutesListTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(test_resources.ROUTES_V1 + [
            core_apis.GetMessagesModule('compute', 'v1').Route(
                destRange='10.10.0.0/16',
                name='route-5',
                network=('v1/projects/my-project/'
                         'network/default'),
                nextHopPeering=('peering-1'),
                selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                          'my-project/global/routes/route-5')),
            core_apis.GetMessagesModule('compute', 'v1').Route(
                destRange='10.10.0.0/16',
                name='route-6',
                network=('v1/projects/my-project/'
                         'network/default'),
                nextHopNetwork=('network-1'),
                selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                          'my-project/global/routes/route-6')),

        ]))

  def testTableOutput(self):
    self.Run("""
        compute routes list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.routes,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME    NETWORK DEST_RANGE   NEXT_HOP                    PRIORITY
            route-1 default 10.0.0.0/8   10.240.0.0
            route-2 default 0.0.0.0/0    zone-1/instances/instance-1
            route-3 default 10.10.0.0/16 default-internet-gateway    1
            route-4 default 10.10.0.0/16 region-1/vpnTunnels/tunnel-1
            route-5 default 10.10.0.0/16 peering-1
            route-6 default 10.10.0.0/16 network-1
            """), normalize_space=True)

  def testUriFlagOutput(self):
    self.Run("""
        compute routes list --uri
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.routes,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals("""\
https://compute.googleapis.com/compute/v1/projects/my-project/global/routes/route-1
https://compute.googleapis.com/compute/v1/projects/my-project/global/routes/route-2
https://compute.googleapis.com/compute/v1/projects/my-project/global/routes/route-3
https://compute.googleapis.com/compute/v1/projects/my-project/global/routes/route-4
https://compute.googleapis.com/compute/v1/projects/my-project/global/routes/route-5
https://compute.googleapis.com/compute/v1/projects/my-project/global/routes/route-6
""", normalize_space=True)

  def testRoutesCompleter(self):
    self.RunCompleter(
        completers.RoutesCompleter,
        expected_command=[
            'compute',
            'routes',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'route-1',
            'route-2',
            'route-3',
            'route-4',
            'route-5',
            'route-6',
        ],
        cli=self.cli,
    )
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.routes,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])

if __name__ == '__main__':
  test_case.main()
