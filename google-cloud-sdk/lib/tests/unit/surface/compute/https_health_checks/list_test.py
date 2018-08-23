# -*- coding: utf-8 -*- #
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
"""Tests for the https-health-checks list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class HttpsHealthChecksListTest(test_base.BaseTest,
                                completer_test_base.CompleterBase):

  def SetUp(self):
    self._https_health_checks = test_resources.HTTPS_HEALTH_CHECKS_V1

    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(self._https_health_checks))

  def testTableOutput(self):
    self.Run("""
        compute https-health-checks list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.httpsHealthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                 HOST            PORT REQUEST_PATH
            https-health-check-1 www.example.com 8888 /testpath
            https-health-check-2                 443  /
            """), normalize_space=True)

  def testHttpsHealthChecksCompleter(self):
    self.RunCompleter(
        completers.HttpsHealthChecksCompleter,
        expected_command=[
            'compute',
            'https-health-checks',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'https-health-check-1',
            'https-health-check-2',
        ],
        cli=self.cli,
    )
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.httpsHealthChecks,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])


if __name__ == '__main__':
  test_case.main()
