# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests that exercise the 'gcloud active-peering-zones list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util_alpha


class ActivePeeringZonesListTest(base.DnsMockMultiTrackTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'v1alpha2'

  def SetUp(self):
    self.SetUpForTrack(self.track, self.api_version)

  def testListMultipleTargetedZones(self):
    test_zone = util_alpha.GetManagedZoneBeforeCreation(
        self.messages,
        peering_config=util_alpha.PeeringConfig('fake-project', 'tn'),
        zone_id=12345)
    test_zone_2 = util_alpha.GetManagedZoneBeforeCreation(
        self.messages,
        peering_config=util_alpha.PeeringConfig('fake-project', 'tn'),
        zone_id=54321)

    self.client.activePeeringZones.List.Expect(
        self.messages.DnsActivePeeringZonesListRequest(
            project=self.Project(), targetNetwork='tn'),
        self.messages.PeeringZonesListResponse(
            peeringZones=[test_zone, test_zone_2]))

    self.client.activePeeringZones.GetPeeringZoneInfo.Expect(
        self.messages.DnsActivePeeringZonesGetPeeringZoneInfoRequest(
            project=self.Project(), peeringZoneId=test_zone.id),
        test_zone)

    self.client.activePeeringZones.GetPeeringZoneInfo.Expect(
        self.messages.DnsActivePeeringZonesGetPeeringZoneInfoRequest(
            project=self.Project(), peeringZoneId=test_zone_2.id),
        test_zone_2)

    self.Run('dns active-peering-zones list --target-network=tn')
    self.AssertOutputContains('id: \'12345\'')
    self.AssertOutputContains('id: \'54321\'')

if __name__ == '__main__':
  test_case.main()
