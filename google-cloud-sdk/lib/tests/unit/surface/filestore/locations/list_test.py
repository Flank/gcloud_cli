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
"""Tests for Cloud Filestore locations list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.filestore import base


class CloudFilestoreLocationsListTest(base.CloudFilestoreUnitTestBase):

  def SetUp(self):
    self.SetUpTrack(calliope_base.ReleaseTrack.GA)

  def RunList(self, *args):
    return self.Run(['filestore', 'locations', 'list'] + list(args))

  def testListNoLocation(self):
    parent = 'projects/{}'.format(self.Project())
    self.mock_client.projects_locations.List.Expect(
        self.messages.FileProjectsLocationsListRequest(
            name=parent, pageSize=100),
        self.messages.ListLocationsResponse(locations=[]))
    results = list(self.RunList())
    self.assertEquals(len(results), 0)

  def testListOneCloudFilestoreLocation(self):
    test_location = self.GetTestCloudFilestoreLocation()
    parent = 'projects/{}'.format(self.Project())
    self.mock_client.projects_locations.List.Expect(
        self.messages.FileProjectsLocationsListRequest(
            name=parent, pageSize=100),
        self.messages.ListLocationsResponse(locations=[test_location]))
    results = list(self.RunList())
    self.assertEquals([test_location], results)

  def testListMultipleCloudFilestoreLocations(self):
    test_locations = self.GetTestCloudFilestoreLocationsList()
    parent = 'projects/{}'.format(self.Project())
    self.mock_client.projects_locations.List.Expect(
        self.messages.FileProjectsLocationsListRequest(
            name=parent, pageSize=100),
        self.messages.ListLocationsResponse(locations=test_locations))
    results = list(self.RunList())
    self.assertEquals(test_locations, results)

  def testListOutputUri(self):
    test_locations = self.GetTestCloudFilestoreLocationsList()
    parent = 'projects/{}'.format(self.Project())
    self.mock_client.projects_locations.List.Expect(
        self.messages.FileProjectsLocationsListRequest(
            name=parent, pageSize=100),
        self.messages.ListLocationsResponse(locations=test_locations))
    list(self.RunList('--uri'))
    self.AssertOutputContains(
        """\
        https://file.googleapis.com/{0}/projects/{1}/locations/Location1
        https://file.googleapis.com/{0}/projects/{1}/locations/Location2
        """.format(self.api_version, self.Project()),
        normalize_space=True)


class CloudFilestoreLocationsListBetaTest(CloudFilestoreLocationsListTest):

  def SetUp(self):
    self.SetUpTrack(calliope_base.ReleaseTrack.BETA)


class CloudFilestoreLocationsListAlphaTest(
    CloudFilestoreLocationsListTest):

  def SetUp(self):
    self.SetUpTrack(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
