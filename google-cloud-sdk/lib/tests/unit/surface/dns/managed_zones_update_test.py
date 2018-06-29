# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Tests that exercise the 'gcloud dns managed-zones create' command."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dns import base


@parameterized.named_parameters(
    ('GA', calliope_base.ReleaseTrack.GA, 'v1'),
    ('Beta', calliope_base.ReleaseTrack.BETA, 'v1beta2'),
)
class ManagedZonesUpdateTest(base.DnsMockMultiTrackTest):

  def _MakeZone(self):
    states_enum = self.messages.ManagedZoneDnsSecConfig.StateValueValuesEnum
    return self.messages.ManagedZone(
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

  def testUpdate(self, track, api_version):
    self.SetUpForTrack(track, api_version)

    expected_zone = self._MakeZone()

    zone_update_request = self.messages.DnsManagedZonesPatchRequest(
        managedZone=expected_zone.name,
        managedZoneResource=expected_zone,
        project=self.Project())
    self.client.managedZones.Patch.Expect(
        zone_update_request,
        expected_zone)
    update_result = self.Run(
        'dns managed-zones update '
        '--format=disable --dnssec-state=off {0}'.format(
            expected_zone.name))
    self.assertEqual(expected_zone, update_result)
    self.AssertOutputEquals('')

  def testUpdate_Labels(self, track, api_version):
    self.SetUpForTrack(track, api_version)

    original_zone = self._MakeZone()
    original_zone.labels = self.messages.ManagedZone.LabelsValue(
        additionalProperties=[
            self.messages.ManagedZone.LabelsValue.AdditionalProperty(key='a',
                                                                     value='b')
        ])
    updated_zone = self._MakeZone()
    updated_zone.labels = self.messages.ManagedZone.LabelsValue(
        additionalProperties=[
            self.messages.ManagedZone.LabelsValue.AdditionalProperty(key='a',
                                                                     value='b'),
            self.messages.ManagedZone.LabelsValue.AdditionalProperty(key='c',
                                                                     value='d')
        ])
    zone_update = self.messages.ManagedZone(name=original_zone.name,
                                            labels=updated_zone.labels)
    self.client.managedZones.Get.Expect(
        self.messages.DnsManagedZonesGetRequest(
            managedZone=original_zone.name,
            project=self.Project()
        ),
        original_zone)
    zone_update_request = self.messages.DnsManagedZonesPatchRequest(
        managedZone=original_zone.name,
        managedZoneResource=zone_update,
        project=self.Project())
    self.client.managedZones.Patch.Expect(
        zone_update_request,
        updated_zone)
    result = self.Run(
        'dns managed-zones update '
        '--format=disable --update-labels c=d {}'.format(
            original_zone.name))
    self.assertEqual(updated_zone, result)
    self.AssertOutputEquals('')


if __name__ == '__main__':
  test_case.main()
