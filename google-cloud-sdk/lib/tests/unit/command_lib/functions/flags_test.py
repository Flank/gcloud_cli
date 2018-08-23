# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unit tests for cpanner flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.functions import flags
from tests.lib import completer_test_base
from tests.lib.surface.functions import base


class CompletionTest(base.FunctionsTestBase, completer_test_base.CompleterBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('cloudfunctions', 'v1')

  def testLocationsCompleter(self):
    locations = [
        self.messages.Location(name='us-central1'),
        self.messages.Location(name='us-central2'),
    ]
    response = self.messages.ListLocationsResponse(locations=locations)
    self.mock_client.projects_locations.List.Expect(
        self.messages.CloudfunctionsProjectsLocationsListRequest(
            name='projects/{0}'.format(self.Project()),
            pageSize=100,
        ),
        response)

    self.RunCompleter(
        flags.LocationsCompleter,
        expected_command=[
            'alpha',
            'functions',
            'regions',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=['us-central1', 'us-central2'],
        cli=self.cli,
    )


if __name__ == '__main__':
  completer_test_base.main()
