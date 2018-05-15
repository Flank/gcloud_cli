# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Tests of the 'functions regions list' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.functions import base


class FunctionsRegionsListTest(base.FunctionsTestBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('cloudfunctions', 'v1')

  def testList(self):
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
    properties.VALUES.core.user_output_enabled.Set(False)
    result = self.Run('functions regions list')
    self.assertEqual(result, locations)


if __name__ == '__main__':
  test_case.main()
