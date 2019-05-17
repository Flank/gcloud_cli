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
"""Tests for Cloud Filestore location describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.filestore import base


class CloudFilestoreLocationsDescribeTest(base.CloudFilestoreUnitTestBase):

  def SetUp(self):
    self.SetUpTrack(calliope_base.ReleaseTrack.GA)

  def RunDescribe(self, *args):
    return self.Run(['filestore', 'locations', 'describe'] + list(args))

  def testDescribeValidFilestoreLocation(self):
    test_location = self.GetTestCloudFilestoreLocation()
    name = 'projects/{}/locations/location_name'.format(self.Project())
    self.mock_client.projects_locations.Get.Expect(
        self.messages.FileProjectsLocationsGetRequest(name=name), test_location)
    result = self.RunDescribe('location_name')
    self.assertEquals(result, test_location)

  def testMissingLocationName(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunDescribe()


class CloudFilestoreLocationsDescribeBetaTest(
    CloudFilestoreLocationsDescribeTest):

  def SetUp(self):
    self.SetUpTrack(calliope_base.ReleaseTrack.BETA)


class CloudFilestoreLocationsDescribeAlphaTest(
    CloudFilestoreLocationsDescribeTest):

  def SetUp(self):
    self.SetUpTrack(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
