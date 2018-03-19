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
"""Tests for the target-https-proxies list subcommand."""
import textwrap

from googlecloudsdk.command_lib.compute.target_https_proxies import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


class TargetHttpsProxiesListTest(test_base.BaseTest,
                                 completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(
            test_resources.TARGET_HTTPS_PROXIES_V1))

  def testSimpleCase(self):
    self.Run("""
        compute target-https-proxies list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.targetHttpsProxies,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
        NAME                 SSL_CERTIFICATES URL_MAP
        target-https-proxy-1 ssl-cert-1       url-map-1
        target-https-proxy-2 ssl-cert-2       url-map-2
        target-https-proxy-3 ssl-cert-3       url-map-3
        """), normalize_space=True)

  def testTargetHttpsProxiesCompleter(self):
    self.RunCompleter(
        flags.TargetHttpsProxiesCompleter,
        expected_command=[
            'compute',
            'target-https-proxies',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'target-https-proxy-1',
            'target-https-proxy-2',
            'target-https-proxy-3',
        ],
        cli=self.cli,
    )
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.targetHttpsProxies,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])


if __name__ == '__main__':
  test_case.main()
