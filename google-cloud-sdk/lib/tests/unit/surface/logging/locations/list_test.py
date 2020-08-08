# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""Tests of the 'locations' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class LocationsListTestBase(base.LoggingTestBase):

  def SetUp(self):
    self._locations = [
        self.msgs.Location(locationId='location1'),
        self.msgs.Location(locationId='location2')]

  def _setProjectLocationsListResponse(self, locations):
    self.mock_client_v2.projects_locations.List.Expect(
        self.msgs.LoggingProjectsLocationsListRequest(
            name='projects/my-project'),
        self.msgs.ListLocationsResponse(locations=locations))


class ProjectLocationsListTest(LocationsListTestBase):

  def testListLimit(self):
    self._setProjectLocationsListResponse(self._locations)
    self.RunLogging(
        'locations list --limit 1', calliope_base.ReleaseTrack.ALPHA)
    self.AssertOutputContains(self._locations[0].locationId)
    self.AssertOutputNotContains(self._locations[1].locationId)

  def testList(self):
    self._setProjectLocationsListResponse(self._locations)
    self.RunLogging('locations list', calliope_base.ReleaseTrack.ALPHA)
    for location in self._locations:
      self.AssertOutputContains(location.locationId)

  def testListNoPerms(self):
    self.mock_client_v2.projects_locations.List.Expect(
        self.msgs.LoggingProjectsLocationsListRequest(
            name='projects/my-project'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('locations list', calliope_base.ReleaseTrack.ALPHA)

  def testListNoProject(self):
    self.RunWithoutProject('locations list', calliope_base.ReleaseTrack.ALPHA)

  def testListNoAuth(self):
    self.RunWithoutAuth('locations list', calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
