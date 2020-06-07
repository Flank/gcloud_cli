# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for utils for `gcloud domains registrations` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.command_lib.domains import dns_util
from googlecloudsdk.command_lib.domains import util
from googlecloudsdk.core import exceptions
from tests.lib import sdk_test_base


class NameServersEquivalentTest(sdk_test_base.WithFakeAuth,
                                sdk_test_base.SdkBase):

  def testGooglDomainsNameServersEquivalent(self):
    messages = registrations.GetMessagesModule()

    prev_dns_settings = messages.DnsSettings(
        googleDomainsDns=messages.GoogleDomainsDns(
            nameServers=['ns1.com', 'ns2.com'],
            dsState=messages.GoogleDomainsDns.DsStateValueValuesEnum
            .DS_RECORDS_PUBLISHED))
    new_dns_settings = messages.DnsSettings(
        googleDomainsDns=messages.GoogleDomainsDns(
            dsState=messages.GoogleDomainsDns.DsStateValueValuesEnum
            .DS_RECORDS_UNPUBLISHED))
    self.assertTrue(
        dns_util.NameServersEquivalent(prev_dns_settings, new_dns_settings))

  def testCustomNameServersEquivalent(self):
    messages = registrations.GetMessagesModule()

    prev_dns_settings = messages.DnsSettings(
        customDns=messages.CustomDns(
            nameServers=['ns1.com', 'ns2.com'],
            dsRecords=[messages.DsRecord(digest='hash')]))
    new_dns_settings = messages.DnsSettings(
        customDns=messages.CustomDns(
            nameServers=['ns1.com', 'ns2.com']))
    self.assertTrue(
        dns_util.NameServersEquivalent(prev_dns_settings, new_dns_settings))

  def testDifferentNameServersNotEquivalent(self):
    messages = registrations.GetMessagesModule()

    prev_dns_settings = messages.DnsSettings(
        customDns=messages.CustomDns(
            nameServers=['ns1.com', 'ns2.com']))
    new_dns_settings = messages.DnsSettings(
        customDns=messages.CustomDns(
            nameServers=['new.ns1.com', 'new.ns2.com']))
    self.assertFalse(
        dns_util.NameServersEquivalent(prev_dns_settings, new_dns_settings))

  def testDifferentDnsProvidersNotEquivalent(self):
    messages = registrations.GetMessagesModule()

    prev_dns_settings = messages.DnsSettings(
        googleDomainsDns=messages.GoogleDomainsDns(
            nameServers=['ns1.com', 'ns2.com'],
            dsState=messages.GoogleDomainsDns.DsStateValueValuesEnum
            .DS_RECORDS_PUBLISHED))
    new_dns_settings = messages.DnsSettings(
        customDns=messages.CustomDns(
            nameServers=['ns1.com', 'ns2.com']))
    self.assertFalse(
        dns_util.NameServersEquivalent(prev_dns_settings, new_dns_settings))


class ParseYearlyPriceTest(sdk_test_base.WithFakeAuth, sdk_test_base.SdkBase):

  def test12USD(self):
    messages = registrations.GetMessagesModule()
    expected = messages.Money(units=12, nanos=0, currencyCode='USD')

    for test_case in ['12USD', '12.00USD']:
      self.assertEqual(util.ParseYearlyPrice(test_case), expected)

  def test050PLN(self):
    messages = registrations.GetMessagesModule()
    expected = messages.Money(units=0, nanos=50 * 10**7, currencyCode='PLN')

    for test_case in ['0.50PLN']:
      self.assertEqual(util.ParseYearlyPrice(test_case), expected)

  def testIncorrect(self):
    for test_case in ['USD12', '12$', '$12.', '-34USD', '12', 'USD']:
      with self.assertRaises(exceptions.Error):
        util.ParseYearlyPrice(test_case)


class NormalizeDomainNameTest(sdk_test_base.WithFakeAuth,
                              sdk_test_base.SdkBase):

  def testNormalized(self):
    for (domain, normalized) in [
        ('foo.com', 'foo.com'), ('FoO.cOm.', 'foo.com'),
        ('Cześć.點看.com', 'xn--cze-spa33b.xn--c1yn36f.com')
    ]:
      self.assertEqual(util.NormalizeDomainName(domain), normalized)

  def testError(self):
    for domain in ['xn--ą.com', 'foo..', '.foo', 'x' * 70]:
      with self.assertRaises(exceptions.Error):
        util.NormalizeDomainName(domain)
