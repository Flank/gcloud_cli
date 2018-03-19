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
"""Tests that exercise the 'gcloud kms locations list' command."""

from tests.lib import test_case
from tests.lib.surface.kms import base


class LocationsListTest(base.KmsMockTest):

  def testNoLocationsList(self):
    self.kms.projects_locations.List.Expect(
        self.messages.CloudkmsProjectsLocationsListRequest(
            name='projects/'+self.Project(), pageSize=100),
        self.messages.ListLocationsResponse(locations=[]))

    self.Run('kms locations list')
    self.AssertErrContains('Listed 0 items.')

  def testRegularLocationsList(self):
    glbl = self.project_name.Child('global')
    east = self.project_name.Child('us-east1')

    self.kms.projects_locations.List.Expect(
        self.messages.CloudkmsProjectsLocationsListRequest(
            name='projects/'+self.Project(), pageSize=100),
        self.messages.ListLocationsResponse(locations=[
            self.messages.Location(
                locationId='global', name=glbl.RelativeName()),
            self.messages.Location(
                locationId='us-east1', name=east.RelativeName()),
        ]))

    self.Run('kms locations list')
    self.AssertOutputContains(
        """\
LOCATION_ID
global
us-east1
""", normalize_space=True)


if __name__ == '__main__':
  test_case.main()
