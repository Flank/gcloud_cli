# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Unit tests for operations list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.data_fusion import base
import six

LOCATION1 = 'us-central1'


class OperationsListBetaTest(base.OperationsUnitTest):

  def SetUp(self):
    # Disable user output to not exhaust the generator returned by RunOperations
    properties.VALUES.core.user_output_enabled.Set(False)

  def testSuccessfulListSingleLocation(self):
    location = [LOCATION1]
    expected_list_response = self._GenerateExpectedList(location)
    actual_list_response = self.RunOperations(
        'list',
        '--project', self.TEST_PROJECT,
        '--location', ','.join(location))
    six.assertCountEqual(self, expected_list_response, actual_list_response)

  def _GenerateExpectedList(self, locations):
    responses_by_location = self._GenerateResponsesByLocation(locations)
    expected_list_response = []
    for location, responses in six.iteritems(responses_by_location):
      self.ExpectOperationsList(
          self.TEST_PROJECT,
          location,
          response_list=responses)
      for r in responses:
        expected_list_response += r.operations
    return expected_list_response

  def _GenerateResponsesByLocation(self, location_ids):
    responses_by_location = collections.OrderedDict()
    for location in location_ids:
      result = []
      for next_page_token in ['foo', 'bar', None]:
        result.append(self.messages.ListOperationsResponse(
            operations=[
                self.MakeOperation(self.TEST_PROJECT, location,
                                   str(i) + (next_page_token or 'baz'))
                for i in range(5)
            ],
            nextPageToken=next_page_token))

      responses_by_location[location] = result
    return responses_by_location


if __name__ == '__main__':
  test_case.main()
