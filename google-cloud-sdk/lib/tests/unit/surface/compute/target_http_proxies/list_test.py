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
"""Tests for the target-http-proxies list subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.command_lib.compute.target_http_proxies import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


class TargetHttpProxiesListTest(test_base.BaseTest,
                                completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(test_resources.TARGET_HTTP_PROXIES))

  def testSimpleCase(self):
    self.Run("""
        compute target-http-proxies list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute_v1.targetHttpProxies,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                URL_MAP
            target-http-proxy-1 url-map-1
            target-http-proxy-2 url-map-2
            target-http-proxy-3 url-map-3
            """), normalize_space=True)

  def testTargetHttpProxiesCompleter(self):
    self.RunCompleter(
        flags.TargetHttpProxiesCompleter,
        expected_command=[
            'compute',
            'target-http-proxies',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'target-http-proxy-1',
            'target-http-proxy-2',
            'target-http-proxy-3',
        ],
        cli=self.cli,
    )
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute_v1.targetHttpProxies,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])


if __name__ == '__main__':
  test_case.main()
