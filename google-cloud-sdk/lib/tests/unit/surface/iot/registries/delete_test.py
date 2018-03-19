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
"""Tests for `gcloud iot registries delete`."""
from googlecloudsdk.api_lib.cloudiot import registries as registries_api
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class RegistriesDeleteTest(base.CloudIotBase):

  def SetUp(self):
    self.registries_client = registries_api.RegistriesClient(self.client,
                                                             self.messages)

  def testDelete(self, track):
    self.track = track
    self.client.projects_locations_registries.Delete.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDeleteRequest(
            name='projects/{}/locations/us-central1/registries/{}'.format(
                self.Project(), 'my-registry')),
        self.messages.Empty())

    self.WriteInput('y\n')
    self.Run('iot registries delete my-registry --region us-central1')
    self.AssertErrContains('You are about to delete registry [my-registry]')
    self.AssertLogContains('Deleted registry [my-registry].')

  def testDelete_RelativeName(self, track):
    self.track = track
    registry_name = ('projects/{}/'
                     'locations/us-central1/'
                     'registries/my-registry').format(self.Project())
    self.client.projects_locations_registries.Delete.Expect(
        self.messages.CloudiotProjectsLocationsRegistriesDeleteRequest(
            name=registry_name),
        self.messages.Empty())

    self.WriteInput('y\n')
    self.Run('iot registries delete {}'.format(registry_name))
    self.AssertErrContains('You are about to delete registry [my-registry]')
    self.AssertLogContains('Deleted registry [my-registry].')


if __name__ == '__main__':
  test_case.main()
