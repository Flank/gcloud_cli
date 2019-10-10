# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Unit tests for environments list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.composer import base

import six
from six.moves import range  # pylint: disable=redefined-builtin

LOCATION1 = 'us-central1'
LOCATION2 = 'europe-west1'


class EnvironmentsListGATest(base.EnvironmentsUnitTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.GA)

  def SetUp(self):
    # Disable user output to not exhaust the generator returned by
    # RunEnvironments
    properties.VALUES.core.user_output_enabled.Set(False)

  def testSuccessfulListSingleLocation(self):
    locations = [LOCATION1]
    expected_list_response = self._GenerateExpectedList(locations)
    actual_list_response = self.RunEnvironments(
        'list',
        '--project', self.TEST_PROJECT,
        '--locations', ','.join(locations))
    six.assertCountEqual(self, expected_list_response, actual_list_response)

  def testSuccessfulListMultipleLocations(self):
    locations = [LOCATION1, LOCATION2]
    expected_list_response = self._GenerateExpectedList(locations)
    actual_list_response = self.RunEnvironments(
        'list',
        '--project', self.TEST_PROJECT,
        '--locations', ','.join(locations))
    six.assertCountEqual(self, expected_list_response, actual_list_response)

  def testListFromPropertyFallthroughLocation(self):
    properties.VALUES.composer.location.Set(LOCATION1)
    locations = [LOCATION1]
    expected_list_response = self._GenerateExpectedList(locations)
    actual_list_response = self.RunEnvironments(
        'list',
        '--project', self.TEST_PROJECT)
    six.assertCountEqual(self, expected_list_response, actual_list_response)

  def testListFromPropertyFallthroughLocationMissing(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.RequiredArgumentException,
        '--locations'):
      self.RunEnvironments('list', '--project', self.TEST_PROJECT)

  def _GenerateExpectedList(self, locations):
    responses_by_location = self._GenerateResponsesByLocation(locations)
    expected_list_response = []
    for location, responses in six.iteritems(responses_by_location):
      self.ExpectEnvironmentsList(
          self.TEST_PROJECT,
          location,
          page_size=api_util.DEFAULT_PAGE_SIZE,
          response_list=responses)
      for r in responses:
        expected_list_response += r.environments
    return expected_list_response

  def _GenerateResponsesByLocation(self, location_ids):
    responses_by_location = collections.OrderedDict()
    for location in location_ids:
      responses_by_location[location] = [
          self.messages.ListEnvironmentsResponse(
              environments=[
                  self.MakeEnvironment(self.TEST_PROJECT, location,
                                       str(i) + (next_page_token or 'baz'))
                  for i in range(5)
              ],
              nextPageToken=next_page_token)
          for next_page_token in ['foo', 'bar', None]
      ]
    return responses_by_location


class EnvironmentsListBetaTest(EnvironmentsListGATest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.BETA)


class EnvironmentsListAlphaTest(EnvironmentsListBetaTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
