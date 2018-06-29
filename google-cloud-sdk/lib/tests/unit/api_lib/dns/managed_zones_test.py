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
"""Tests for the Cloud DNS managed zones library."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import managed_zones
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dns import base


@parameterized.named_parameters(
    ('Beta', calliope_base.ReleaseTrack.BETA, 'v1beta2'),
)
class ManagedZonesTest(base.DnsMockMultiTrackTest):

  def testGet(self, track, api_version):
    self.SetUpForTrack(track, api_version)

    zones_client = managed_zones.Client.FromApiVersion(api_version)

    states_enum = self.messages.ManagedZoneDnsSecConfig.StateValueValuesEnum
    zone = self.messages.ManagedZone(
        creationTime=None,
        description=None,
        dnsName=None,
        dnssecConfig=self.messages.ManagedZoneDnsSecConfig(
            defaultKeySpecs=[
            ],
            kind='dns#managedZoneDnsSecConfig',
            nonExistence=None,
            state=states_enum.off,
        ),
        id=None,
        kind='dns#managedZone',
        name='mz',
        nameServerSet=None,
        nameServers=[
        ],
    )
    self.client.managedZones.Get.Expect(
        self.messages.DnsManagedZonesGetRequest(project='my-project',
                                                managedZone='my-zone'),
        zone)
    zone_ref = resources.REGISTRY.Create(
        'dns.managedZones', managedZone='my-zone', project='my-project')

    result = zones_client.Get(zone_ref)

    self.assertEqual(result, zone)


if __name__ == '__main__':
  test_case.main()
