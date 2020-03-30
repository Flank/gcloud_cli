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
"""Tests that exercise the 'gcloud dns active-peering-zones deactivate' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util_alpha


class ActivePeeringZonesDeactivateTest(base.DnsMockMultiTrackTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'v1alpha2'

  def SetUp(self):
    self.SetUpForTrack(self.track, self.api_version)

  def testDeactivate(self):

    test_zone = util_alpha.GetManagedZoneBeforeCreation(
        self.messages,
        peering_config=util_alpha.PeeringConfig('tp', 'tn'), zone_id=12345)

    zone_deactivate_request = self.messages.DnsActivePeeringZonesDeactivateRequest(
        peeringZoneId=test_zone.id, project=self.Project())
    self.client.activePeeringZones.Deactivate.Expect(
        zone_deactivate_request, self.messages.PeeringZoneDeactivateResponse())

    self.Run(
        'dns active-peering-zones deactivate-zone --zone-id {0}'.format(
            test_zone.id))
    self.AssertOutputEquals('')

if __name__ == '__main__':
  test_case.main()
