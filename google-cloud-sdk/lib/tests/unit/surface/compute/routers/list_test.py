# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests for the routers list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
import mock


class RoutersListTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetRegionalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_regional_resources = lister_patcher.start()
    self.mock_get_regional_resources.return_value = (
        resource_projector.MakeSerializable(self._GetTestRouters()))

  def testSimple(self):
    self.Run("""compute routers list""")
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute.routers,
        project='my-project',
        requested_regions=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME REGION NETWORK
            my-router us-central1 default
            my-router-2 us-central2 default
            """),
        normalize_space=True)

  def _GetTestRouters(self):
    return [
        self.messages.Router(
            name='my-router',
            region='us-central1',
            network=(
                'https://compute.googleapis.com/compute/v1/projects/my-project/'
                'global/networks/default'),
            selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                      'my-project/regions/us-central2/routers/my-router'),
        ),
        self.messages.Router(
            name='my-router-2',
            region='us-central2',
            network=(
                'https://compute.googleapis.com/compute/v1/projects/my-project/'
                'global/networks/default'),
            selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                      'my-project/regions/us-central2/routers/my-router-2'),
        )
    ]

  def testRoutersCompleter(self):
    self.RunCompleter(
        flags.RoutersCompleter,
        expected_command=[
            'compute',
            'routers',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'my-router',
            'my-router-2',
        ],
        cli=self.cli,
    )
    self.mock_get_regional_resources.assert_called_once_with(
        service=self.compute.routers,
        project='my-project',
        requested_regions=[],
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])


if __name__ == '__main__':
  test_case.main()
