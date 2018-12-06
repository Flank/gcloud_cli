# -*- coding: utf-8 -*- #
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
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util_beta


class ManagedZonesUpdateTest(base.DnsMockMultiTrackTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.SetUpForTrack(self.track, self.api_version)

  def _MakeZone(self):
    states_enum = self.messages.ManagedZoneDnsSecConfig.StateValueValuesEnum
    return self.messages.ManagedZone(
        creationTime=None,
        description=None,
        dnsName=None,
        dnssecConfig=self.messages.ManagedZoneDnsSecConfig(
            defaultKeySpecs=[],
            kind='dns#managedZoneDnsSecConfig',
            nonExistence=None,
            state=states_enum.off,
        ),
        id=None,
        kind='dns#managedZone',
        name='mz',
        nameServerSet=None,
        nameServers=[],
    )

  def testUpdate(self):
    expected_zone = self._MakeZone()
    op = self.messages.Operation(id='myop')

    zone_update_request = self.messages.DnsManagedZonesPatchRequest(
        managedZone=expected_zone.name,
        managedZoneResource=expected_zone,
        project=self.Project())
    self.client.managedZones.Patch.Expect(zone_update_request, op)
    update_result = self.Run('dns managed-zones update '
                             '--format=disable --dnssec-state=off {0}'.format(
                                 expected_zone.name))
    self.assertEqual(op, update_result)
    self.AssertOutputEquals('')

  def testUpdate_Labels(self):
    original_zone = self._MakeZone()
    original_zone.labels = self.messages.ManagedZone.LabelsValue(
        additionalProperties=[
            self.messages.ManagedZone.LabelsValue.AdditionalProperty(
                key='a', value='b')
        ])
    updated_zone = self._MakeZone()
    updated_zone.labels = self.messages.ManagedZone.LabelsValue(
        additionalProperties=[
            self.messages.ManagedZone.LabelsValue.AdditionalProperty(
                key='a', value='b'),
            self.messages.ManagedZone.LabelsValue.AdditionalProperty(
                key='c', value='d')
        ])
    zone_update = self.messages.ManagedZone(
        name=original_zone.name, labels=updated_zone.labels)
    self.client.managedZones.Get.Expect(
        self.messages.DnsManagedZonesGetRequest(
            managedZone=original_zone.name, project=self.Project()),
        original_zone)
    zone_update_request = self.messages.DnsManagedZonesPatchRequest(
        managedZone=original_zone.name,
        managedZoneResource=zone_update,
        project=self.Project())
    op = self.messages.Operation(id='myop')
    self.client.managedZones.Patch.Expect(zone_update_request, op)
    result = self.Run('dns managed-zones update '
                      '--format=disable --update-labels c=d {}'.format(
                          original_zone.name))
    self.assertEqual(op, result)
    self.AssertOutputEquals('')

  def testUpdate_WithKeys(self):
    expected_zone = self._MakeZone()
    spec_class = self.messages.DnsKeySpec
    key_specs = [
        spec_class(
            keyType=spec_class.KeyTypeValueValuesEnum.keySigning,
            algorithm=spec_class.AlgorithmValueValuesEnum.ecdsap384sha384,
            keyLength=1),
        spec_class(
            keyType=spec_class.KeyTypeValueValuesEnum.zoneSigning,
            algorithm=spec_class.AlgorithmValueValuesEnum.rsasha256,
            keyLength=2)
    ]
    expected_zone.dnssecConfig.defaultKeySpecs = key_specs

    # zone_update = self.messages.ManagedZone(
    #     name=expected_zone.name, dnssecConfig=expected_zone.dnssecConfig)
    zone_update_request = self.messages.DnsManagedZonesPatchRequest(
        managedZone=expected_zone.name,
        managedZoneResource=expected_zone,
        project=self.Project())
    op = self.messages.Operation(id='myop')
    self.client.managedZones.Patch.Expect(zone_update_request, op)
    result = self.Run('dns managed-zones update {} --dnssec-state=off '
                      '--ksk-algorithm ecdsap384sha384 --ksk-key-length 1 '
                      '--zsk-algorithm RSASHA256 --zsk-key-length 2 '
                      '--format=disable'.format(expected_zone.name))
    self.assertEqual(op, result)
    self.AssertOutputEquals('')


class BetaManagedZonesUpdateTest(ManagedZonesUpdateTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'v1beta2'

  def testUpdate_Networks(self):
    visibility_settings = util_beta.GetDnsVisibilityDict(
        self.api_version,
        visibility='private',
        network_urls=['1.0.1.1', '1.2.1.1'])
    zone = self.messages.ManagedZone(
        creationTime=None,
        description=None,
        dnsName=None,
        id=None,
        kind='dns#managedZone',
        name='mz',
        nameServerSet=None,
        nameServers=[],
    )
    zone.privateVisibilityConfig = visibility_settings[
        'privateVisibilityConfig']
    zone_update_request = self.messages.DnsManagedZonesPatchRequest(
        managedZone=zone.name, managedZoneResource=zone, project=self.Project())
    op = self.messages.Operation(id='myop')
    self.client.managedZones.Patch.Expect(zone_update_request, op)
    update_result = self.Run(
        'dns managed-zones update --networks 1.0.1.1,1.2.1.1 '
        '--format=disable {0}'.format(zone.name))
    self.assertEqual(op, update_result)
    self.AssertOutputEquals('')

  def testUpdate_NetworksAddForwarding(self):
    visibility_settings = util_beta.GetDnsVisibilityDict(
        self.api_version,
        visibility='private',
        network_urls=['1.0.1.1', '1.2.1.1'])
    forwarding_config = util_beta.ParseManagedZoneForwardingConfig(
        ['1.0.1.1', '1.2.1.1'])
    zone = self.messages.ManagedZone(
        creationTime=None,
        description=None,
        dnsName=None,
        id=None,
        kind='dns#managedZone',
        name='mz',
        nameServerSet=None,
        nameServers=[],
        forwardingConfig=forwarding_config)
    zone.privateVisibilityConfig = visibility_settings[
        'privateVisibilityConfig']
    zone_update_request = self.messages.DnsManagedZonesPatchRequest(
        managedZone=zone.name, managedZoneResource=zone, project=self.Project())
    op = self.messages.Operation(id='myop')
    self.client.managedZones.Patch.Expect(zone_update_request, op)
    update_result = self.Run(
        'dns managed-zones update --networks 1.0.1.1,1.2.1.1 '
        '--format=disable {0} --forwarding-targets 1.0.1.1,1.2.1.1'.format(
            zone.name))
    self.assertEqual(op, update_result)
    self.AssertOutputEquals('')


if __name__ == '__main__':
  test_case.main()
