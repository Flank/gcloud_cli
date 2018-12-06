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
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util
from tests.lib.surface.dns import util_beta


class ManagedZonesCreateTest(base.DnsMockMultiTrackTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.SetUpForTrack(self.track, self.api_version)

  def testCreate(self):
    test_zone = util.GetManagedZoneBeforeCreation(self.messages)
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

  def testCreateFormat(self):
    test_zone = util.GetManagedZoneBeforeCreation(self.messages)
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

  def testCreateLabels(self):
    test_zone = util.GetManagedZoneBeforeCreation(self.messages)
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

  def testCreateDnssec(self):
    test_zone = util.GetManagedZoneBeforeCreation(self.messages,
                                                  dns_sec_config=True)
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

  def testCreateWithKeys(self):
    test_zone = util.GetManagedZoneBeforeCreation(self.messages,
                                                  dns_sec_config=True)
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
    test_zone.dnssecConfig.defaultKeySpecs = key_specs
    zone_create_request = self.messages.DnsManagedZonesCreateRequest(
        managedZone=test_zone,
        project=self.Project())
    self.client.managedZones.Create.Expect(
        zone_create_request, test_zone)

    result = self.Run(
        'dns managed-zones create {0} --dns-name {1} '
        '--description {2} --format=disable --dnssec-state=on '
        '--denial-of-existence=nsec3 '
        '--ksk-algorithm ecdsap384sha384 --ksk-key-length 1 '
        '--zsk-algorithm RSASHA256 --zsk-key-length 2'.format(
            test_zone.name,
            test_zone.dnsName,
            test_zone.description))
    self.assertEqual([test_zone], list(result))
    self.AssertOutputEquals('')
    self.AssertErrContains("""\
Created [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz].
""".format(self.api_version, self.Project()))


class BetaManagedZonesCreateTest(ManagedZonesCreateTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'v1beta2'

  def testCreateWithPrivateVisibility(self):
    visibility_settings = util_beta.GetDnsVisibilityDict(
        self.api_version,
        visibility='private',
        network_urls=['1.0.1.1', '1.2.1.1'])
    test_zone = util_beta.GetManagedZoneBeforeCreation(
        self.messages,
        dns_sec_config=False,
        visibility_dict=visibility_settings)
    zone_create_request = self.messages.DnsManagedZonesCreateRequest(
        managedZone=test_zone, project=self.Project())
    self.client.managedZones.Create.Expect(zone_create_request, test_zone)

    result = self.Run(
        'dns managed-zones create {0} --dns-name {1} --description {2} '
        '--format=disable --visibility private --networks {3}'.format(
            test_zone.name, test_zone.dnsName, test_zone.description,
            ','.join(['1.0.1.1', '1.2.1.1'])))
    self.assertEqual([test_zone], list(result))
    self.AssertOutputEquals('')
    self.AssertErrContains("""\
Created [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz].
""".format(self.api_version, self.Project()))

  def testCreateWithPrivateVisibilityAndMissingNetworks(self):
    visibility_settings = util_beta.GetDnsVisibilityDict(
        self.api_version, visibility='private')
    test_zone = util_beta.GetManagedZoneBeforeCreation(
        self.messages,
        dns_sec_config=False, visibility_dict=visibility_settings)
    with self.assertRaises(exceptions.RequiredArgumentException):
      self.Run(
          'dns managed-zones create {0} --dns-name {1} --description {2} '
          '--format=disable --visibility private'.format(
              test_zone.name, test_zone.dnsName, test_zone.description))

  def testCreateWithPrivateVisibilityErrors(self):
    visibility_settings = util_beta.GetDnsVisibilityDict(
        self.api_version,
        visibility='private',
        network_urls=[])
    test_zone = util_beta.GetManagedZoneBeforeCreation(
        self.messages,
        dns_sec_config=False,
        visibility_dict=visibility_settings)

    with self.assertRaisesRegexp(exceptions.RequiredArgumentException,
                                 r'Missing required argument \[--networks\]'):
      self.Run('dns managed-zones create {0} --dns-name {1} --description {2} '
               '--format=disable --visibility private'.format(
                   test_zone.name, test_zone.dnsName, test_zone.description))

    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run('dns managed-zones create {0} --dns-name {1} --description {2} '
               '--format=disable --visibility public --networks 1.0.0.1'.format(
                   test_zone.name, test_zone.dnsName, test_zone.description))

  def testCreateWithPublicVisibility(self):
    visibility_settings = util_beta.GetDnsVisibilityDict(self.api_version)
    test_zone = util_beta.GetManagedZoneBeforeCreation(
        self.messages,
        dns_sec_config=False, visibility_dict=visibility_settings)
    zone_create_request = self.messages.DnsManagedZonesCreateRequest(
        managedZone=test_zone, project=self.Project())
    self.client.managedZones.Create.Expect(zone_create_request, test_zone)
    result = self.Run(
        'dns managed-zones create {0} --dns-name {1} --description {2} '
        '--format=disable --visibility public'.format(
            test_zone.name, test_zone.dnsName, test_zone.description))
    self.assertEqual([test_zone], list(result))
    self.AssertOutputEquals('')
    self.AssertErrContains("""\
Created [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz].
""".format(self.api_version, self.Project()))

  def testCreateWithForwardingTargetsAndPrivateVisibility(self):
    forwarding_servers = ['1.0.1.1', '1.2.1.1']
    forwarding_config = util_beta.ParseManagedZoneForwardingConfig(
        target_servers=forwarding_servers)

    visibility_settings = util_beta.GetDnsVisibilityDict(
        self.api_version,
        visibility='private',
        network_urls=['1.0.2.1', '1.2.2.1'])
    test_zone = util_beta.GetManagedZoneBeforeCreation(
        self.messages,
        dns_sec_config=False,
        visibility_dict=visibility_settings,
        forwarding_config=forwarding_config)

    zone_create_request = self.messages.DnsManagedZonesCreateRequest(
        managedZone=test_zone, project=self.Project())
    self.client.managedZones.Create.Expect(zone_create_request, test_zone)
    result = self.Run(
        'dns managed-zones create {0} --dns-name {1} --description {2} '
        '--format=disable --visibility private --forwarding-targets {3} '
        '--networks {4}'.format(
            test_zone.name, test_zone.dnsName, test_zone.description,
            ','.join(forwarding_servers), ','.join(['1.0.2.1', '1.2.2.1'])))

    self.assertEqual([test_zone], list(result))
    self.AssertOutputEquals('')
    self.AssertErrContains("""\
Created [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz].
""".format(self.api_version, self.Project()))

  def testCreateWithForwardingTargetsandPublicVisibility(self):
    visibility_settings = util_beta.GetDnsVisibilityDict(
        self.api_version, visibility='private', network_urls=[])
    test_zone = util_beta.GetManagedZoneBeforeCreation(
        self.messages,
        dns_sec_config=False,
        visibility_dict=visibility_settings)
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run('dns managed-zones create {0} --dns-name {1} --description {2} '
               '--format=disable --visibility public '
               '--forwarding-targets 1.0.0.1 --networks 1.0.0.1'.format(
                   test_zone.name, test_zone.dnsName, test_zone.description))


if __name__ == '__main__':
  test_case.main()
