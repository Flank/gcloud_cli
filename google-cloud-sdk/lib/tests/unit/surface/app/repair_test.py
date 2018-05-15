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

"""Tests for app repair command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.app import api_test_util


class RepairTest(api_test_util.ApiTestBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('appengine', 'v1beta')
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass('appengine', 'v1beta'),
        real_client=core_apis.GetClientInstance(
            'appengine', 'v1beta', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def testRepair(self):
    self.ExpectRepairApplicationRequest(self.Project())

    self.Run('beta app repair')
    self.AssertErrContains('Repairing the app [fake-project]')

  def testRepair_PollUntilComplete(self):
    self.ExpectRepairApplicationRequest(self.Project(), num_retries=2)

    self.Run('beta app repair')
    # Explicitly check for the nesting of the trackers.
    self.AssertErrEquals("""\
<START PROGRESS TRACKER>Repairing the app [fake-project]
<START PROGRESS TRACKER>Waiting for operation [apps/fake-project/operations/12345] to complete
<END PROGRESS TRACKER>SUCCESS
<END PROGRESS TRACKER>SUCCESS
""")


if __name__ == '__main__':
  test_case.main()
