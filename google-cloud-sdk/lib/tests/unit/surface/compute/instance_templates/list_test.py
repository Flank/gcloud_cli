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
"""Tests for the instance-templates list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.instance_templates import test_resources

import mock


class InstancesListTest(test_base.BaseTest,
                        completer_test_base.CompleterBase):

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(
            test_resources.INSTANCE_TEMPLATES_V1))

  def testTableOutput(self):
    self.Run("""
        compute instance-templates list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute_v1.instanceTemplates,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                MACHINE_TYPE     PREEMPTIBLE    CREATION_TIMESTAMP
            instance-template-1 n1-standard-1                   2013-09-06T17:54:10.636-07:00
            instance-template-2 n1-highmem-1                    2013-10-06T17:54:10.636-07:00
            instance-template-3 custom (n2, 6 vCPU, 16.75 GiB)  2013-11-06T17:54:10.636-07:00
            """), normalize_space=True)

  def testInstanceTemplatesCompleter(self):
    self.RunCompleter(
        completers.InstanceTemplatesCompleter,
        expected_command=[
            'compute',
            'instance-templates',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'instance-template-1',
            'instance-template-2',
            'instance-template-3'
        ],
        cli=self.cli,
    )


if __name__ == '__main__':
  test_case.main()
