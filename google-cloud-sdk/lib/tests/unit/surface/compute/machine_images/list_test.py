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
"""Tests for the machine-images list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.machine_images import test_resources
import mock


class MachineImagesListTestBeta(test_base.BaseTest,
                                completer_test_base.CompleterBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)
    self.api_version = 'beta'
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(
            test_resources.MakeMachineImages(self.messages, self.api_version)))

  def testTableOutput(self):
    self.Run('compute machine-images list')
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.machineImages,
        project='my-project',
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME STATUS
            machine-image-1 READY
            machine-image-2 CREATING
            """),
        normalize_space=True)

  def testMachineImagesCompleter(self):
    self.RunCompleter(
        completers.MachineImagesCompleter,
        expected_command=[
            'beta',
            'compute',
            'machine-images',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=['machine-image-1', 'machine-image-2'],
        cli=self.cli)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.machineImages,
        project='my-project',
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])


class MachineImagesListTestAlpha(test_base.BaseTest,
                                 completer_test_base.CompleterBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)
    self.api_version = 'alpha'
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(
            test_resources.MakeMachineImages(self.messages, self.api_version)))


if __name__ == '__main__':
  test_case.main()
