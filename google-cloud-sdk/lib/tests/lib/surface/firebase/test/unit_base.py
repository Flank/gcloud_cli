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

"""Base classes for all 'gcloud firebase test' unit tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.firebase.test import history_picker
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

TEST_DATA_PATH = sdk_test_base.SdkBase.Resource('tests', 'unit', 'surface',
                                                'firebase', 'test', 'testdata')

TESTING_V1_MSGS = core_apis.GetMessagesModule('testing', 'v1')


class TestUnitTestBase(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth,
                       sdk_test_base.WithOutputCapture):
  """Base class for all 'gcloud firebase test' unit tests.

  Attributes:
    PROJECT_ID: a default cloud project ID for unit tests.
  """
  PROJECT_ID = 'superbowl'


class TestMockClientTest(TestUnitTestBase):
  """Base class for all 'gcloud test' tests using mocked ApiTools clients.

  Attributes:
    testing_client: mocked ApiTools client for the Testing API.
    tr_client: mocked ApiTools client for the ToolResults API.
    context: the gcloud command context (a str:value dict) which holds common
      initialization values, such as the client and messages objects generated
      from the Testing API definition by ApiTools.
    args: an argparse.Namespace initialized with a minimal set of args required
      by the Testing service backend.
    picker: a ToolResultsHistoryPicker created with the mocked tr_client.
  """

  def CreateMockedClients(self):
    """Set up mocked clients for each API used."""
    properties.VALUES.core.project.Set(self.PROJECT_ID)

    self.testing_client = api_mock.Client(
        core_apis.GetClientClass('testing', 'v1'))
    self.testing_client.Mock()
    self.addCleanup(self.testing_client.Unmock)
    self.testing_msgs = TESTING_V1_MSGS

    self.tr_client = api_mock.Client(
        core_apis.GetClientClass('toolresults', 'v1beta3'))
    self.tr_client.Mock()
    self.addCleanup(self.tr_client.Unmock)
    self.toolresults_msgs = core_apis.GetMessagesModule('toolresults',
                                                        'v1beta3')

    self.storage_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.storage_client.Mock()
    self.addCleanup(self.storage_client.Unmock)
    self.storage_msgs = core_apis.GetMessagesModule('storage', 'v1')

    self.context = {
        'testing_client': self.testing_client,
        'testing_messages': self.testing_msgs,
    }

    self.picker = history_picker.ToolResultsHistoryPicker(
        self.PROJECT_ID, self.tr_client, self.toolresults_msgs)

  def CheckArgNamesForHyphens(self, arg_rules):
    args = (
        arg_rules['required'] + arg_rules['optional'] + list(
            arg_rules['defaults'].keys()))
    for arg in args:
      self.assertNotIn('-', arg, 'arg names in rules should use underscores')
