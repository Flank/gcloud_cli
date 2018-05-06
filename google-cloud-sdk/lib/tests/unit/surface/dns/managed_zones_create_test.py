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
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util
from tests.lib.surface.dns import util_beta


class ManagedZonesCreateTest(parameterized.TestCase,
                             base.DnsMockMultiTrackTest):

  @parameterized.named_parameters(
      ('GA', calliope_base.ReleaseTrack.GA, 'v1'),
      ('Beta', calliope_base.ReleaseTrack.BETA, 'v1beta2'),
  )
  def testCreate(self, track, api_version):
    self.SetUpForTrack(track, api_version)

    test_zone = util.GetManagedZoneBeforeCreation(api_version)
    zone_create_request = self.messages.DnsManagedZonesCreateRequest(
        managedZone=test_zone,
        project=self.Project())
    self.client.managedZones.Create.Expect(
        zone_create_request, test_zone)
    self.client.managedZones.Create.Expect(
        zone_create_request, test_zone)

    self.Run(
        'dns managed-zones create {0} --dns-name {1} --description {2}'.format(
            test_zone.name,
            test_zone.dnsName[:-1],
            test_zone.description))
    result = self.Run(
        'dns managed-zones create {0} --dns-name {1} --description {2} '
        '--format=disable'.format(
            test_zone.name,
            test_zone.dnsName,
            test_zone.description))
    self.assertEqual([test_zone], list(result))
    self.AssertOutputEquals('')
    self.AssertErrContains("""\
Created [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz].
""".format(self.api_version, self.Project()))

  @parameterized.named_parameters(
      ('GA', calliope_base.ReleaseTrack.GA, 'v1'),
      ('Beta', calliope_base.ReleaseTrack.BETA, 'v1beta2'),
  )
  def testCreateFormat(self, track, api_version):
    self.SetUpForTrack(track, api_version)

    test_zone = util.GetManagedZoneBeforeCreation(api_version)
    zone_create_request = self.messages.DnsManagedZonesCreateRequest(
        managedZone=test_zone,
        project=self.Project())
    self.client.managedZones.Create.Expect(
        zone_create_request, test_zone)
    self.client.managedZones.Create.Expect(
        zone_create_request, test_zone)

    self.Run(
        'dns managed-zones create {0} --dns-name {1} --description {2}'.format(
            test_zone.name,
            test_zone.dnsName[:-1],
            test_zone.description))
    self.Run(
        'dns managed-zones create {0} --dns-name {1} --description {2} '
        '--format=default'.format(
            test_zone.name,
            test_zone.dnsName,
            test_zone.description))
    self.AssertOutputContains("""\
description: Zone!
dnsName: zone.com.
kind: dns#managedZone
name: mz
""")
    self.AssertErrContains("""\
Created [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz].
""".format(self.api_version, self.Project()))

  @parameterized.named_parameters(
      ('GA', calliope_base.ReleaseTrack.GA, 'v1'),
      ('Beta', calliope_base.ReleaseTrack.BETA, 'v1beta2'),
  )
  def testCreateLabels(self, track, api_version):
    self.SetUpForTrack(track, api_version)

    test_zone = util.GetManagedZoneBeforeCreation(api_version)
    test_zone.labels = self.messages.ManagedZone.LabelsValue(
        additionalProperties=[
            self.messages.ManagedZone.LabelsValue.AdditionalProperty(key='a',
                                                                     value='b'),
            self.messages.ManagedZone.LabelsValue.AdditionalProperty(key='c',
                                                                     value='d'),
        ]
    )
    zone_create_request = self.messages.DnsManagedZonesCreateRequest(
        managedZone=test_zone,
        project=self.Project())
    self.client.managedZones.Create.Expect(
        zone_create_request, test_zone)

    self.Run(
        'dns managed-zones create {0} --dns-name {1} --description {2} '
        '    --labels a=b,c=d'.format(
            test_zone.name,
            test_zone.dnsName,
            test_zone.description))
    self.AssertOutputEquals('')
    self.AssertErrContains("""\
Created [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz].
""".format(self.api_version, self.Project()))

  @parameterized.named_parameters(
      ('GA', calliope_base.ReleaseTrack.GA, 'v1'),
      ('Beta', calliope_base.ReleaseTrack.BETA, 'v1beta2'),
  )
  def testCreateDnssec(self, track, api_version):
    self.SetUpForTrack(track, api_version)

    test_zone = util_beta.GetManagedZoneBeforeCreation(api_version)
    zone_create_request = self.messages.DnsManagedZonesCreateRequest(
        managedZone=test_zone,
        project=self.Project())
    self.client.managedZones.Create.Expect(
        zone_create_request, test_zone)

    result = self.Run(
        'dns managed-zones create {0} --dns-name {1} '
        '--description {2} --format=disable --dnssec-state=on '
        '--denial-of-existence=nsec3'.format(
            test_zone.name,
            test_zone.dnsName,
            test_zone.description))
    self.assertEqual([test_zone], list(result))
    self.AssertOutputEquals('')
    self.AssertErrContains("""\
Created [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz].
""".format(self.api_version, self.Project()))


if __name__ == '__main__':
  test_case.main()
