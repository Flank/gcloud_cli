# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for 'gcloud compute networks vpc-access locations list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.networks.vpc_access import base


class LocationsListTest(base.VpcAccessUnitTestBase):

  def testZeroLocationsList(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.locations_client.List.Expect(
        self.messages.VpcaccessProjectsLocationsListRequest(
            name=self.project_relative_name),
        self.messages.ListLocationsResponse(locations=[]))

    self.Run('compute networks vpc-access locations list')
    self.AssertErrContains('Listed 0 items.')

  def testLocationsList(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self._ExpectList()
    self.Run('compute networks vpc-access locations list')
    self.AssertOutputEquals(
        """\
        REGION
        us-central1
        us-east1
        """,
        normalize_space=True)

  def testLocationsListUri(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self._ExpectList()
    self.Run('compute networks vpc-access locations list --uri')

    # pylint: disable=line-too-long
    self.AssertOutputEquals(
        """\
        https://vpcaccess.googleapis.com/{api_version}/projects/{project}/locations/us-east1
        https://vpcaccess.googleapis.com/{api_version}/projects/{project}/locations/us-central1
        """.format(
            api_version=self.api_version,
            project=self.project_id),
        normalize_space=True)
    # pylint: enable=line-too-long

  def _ExpectList(self):
    location_prefix = 'projects/{}/locations/'.format(self.project_id)
    self.locations_client.List.Expect(
        self.messages.VpcaccessProjectsLocationsListRequest(
            name=self.project_relative_name),
        self.messages.ListLocationsResponse(locations=[
            self.messages.Location(name=location_prefix + 'us-east1'),
            self.messages.Location(name=location_prefix + 'us-central1'),
        ]))


if __name__ == '__main__':
  test_case.main()
