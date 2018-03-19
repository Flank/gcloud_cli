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
"""Tests for the interconnect locations describe subcommand."""

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.interconnects import test_resource_util


class InterconnectLocationsDescribeTest(test_base.BaseTest):

  def Project(self):
    return 'my-project'

  def SetUp(self):
    self.track = base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.api_version = 'v1'
    self.apis_messages = core_apis.GetMessagesModule('compute',
                                                     self.api_version)
    self.message_version = self.compute_v1

    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.location_ref = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='eap-lga07',
        project=self.Project())

  def _MakeInterconnectLocation(self,
                                name='default-name',
                                description='Bell-Canada',
                                peeringdb_facility_id='38',
                                address='111 8th Ave',
                                facility_provider='google-partner-provider',
                                facility_provider_facility_id='111 8th',
                                location_ref=None):

    return self.apis_messages.InterconnectLocation(
        name=name,
        description=description,
        peeringdbFacilityId=peeringdb_facility_id,
        address=address,
        facilityProvider=facility_provider,
        facilityProviderFacilityId=facility_provider_facility_id,
        selfLink=location_ref.SelfLink(),
    )

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [
            test_resource_util.MakeInterconnectLocation(
                name='eap-lga07',
                address='Bell Canada 111 8th Ave, Suite 831 New York, '
                'NY 10011 New York United States',
                location_ref=self.location_ref)
        ],
    ])
    result = self.Run("""
          compute interconnects locations describe eap-lga07 --format=disable
          """)

    self.CheckRequests(
        [(self.message_version.interconnectLocations, 'Get',
          self.messages.ComputeInterconnectLocationsGetRequest(
              project='my-project', interconnectLocation='eap-lga07'))],)
    self.assertEquals(
        result.address,
        'Bell Canada 111 8th Ave, Suite 831 New York, NY 10011 New York '
        'United States')
    self.assertEquals(result.description, 'Bell-Canada')
    self.assertEquals(result.facilityProviderFacilityId, '111 8th')
    self.assertEquals(result.name, 'eap-lga07')
    self.assertEquals(result.peeringdbFacilityId, '38')
    self.assertEquals(result.selfLink, self.compute_uri + '/projects/'
                      'my-project/global/interconnectLocations/eap-lga07')


class InterconnectLocationsDescribeBetaTest(InterconnectLocationsDescribeTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.api_version = 'beta'
    self.apis_messages = core_apis.GetMessagesModule('compute',
                                                     self.api_version)
    self.message_version = self.compute_beta

    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.location_ref = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='eap-lga07',
        project=self.Project())


class InterconnectLocationsDescribeAlphaTest(InterconnectLocationsDescribeTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.api_version = 'alpha'
    self.apis_messages = core_apis.GetMessagesModule('compute',
                                                     self.api_version)
    self.message_version = self.compute_alpha

    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.location_ref = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='eap-lga07',
        project=self.Project())


if __name__ == '__main__':
  test_case.main()
