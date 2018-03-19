# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Base class for all Updater tests."""

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base

messages = core_apis.GetMessagesModule('replicapoolupdater', 'v1beta1')

ZONE = 'some-zone'
OPERATION_DONE_WITH_ERRORS = messages.Operation(
    status='DONE',
    error=messages.Operation.ErrorValue(
        errors=[
            messages.Operation.ErrorValue.ErrorsValueListEntry(message='bad')]))


class UpdaterTestBase(cli_test_base.CliTestBase):
  """Base class for all Updater tests."""


class UpdaterMockTest(UpdaterTestBase):
  """Base class for all Updater tests."""

  def Project(self):
    """Override default which is None."""
    return 'test-updater-project'

  def SetUp(self):
    self.mock_http = self.StartPatch(
        'googlecloudsdk.core.credentials.http.Http', autospec=True)

    self.mocked_client_v1beta1 = mock.Client(
        core_apis.GetClientClass('replicapoolupdater', 'v1beta1'))
    self.mocked_client_v1beta1.Mock()
    self.addCleanup(self.mocked_client_v1beta1.Unmock)
