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

"""Tests that exercise the 'gcloud dns record-sets list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util
from tests.lib.surface.dns import util_beta


class RecordSetsListTest(base.DnsMockTest):

  def testZeroRecordSetsList(self):
    test_zone = util.GetManagedZones()[0]
    self.mocked_dns_v1.resourceRecordSets.List.Expect(
        self.messages.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            maxResults=100),
        self.messages.ResourceRecordSetsListResponse(rrsets=[]))

    self.Run('dns record-sets list -z {0}'.format(test_zone.name))
    self.AssertErrContains('Listed 0 items.')

  def testOneRecordSetList(self):
    test_zone = util.GetManagedZones()[0]
    self.mocked_dns_v1.resourceRecordSets.List.Expect(
        self.messages.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            maxResults=100),
        self.messages.ResourceRecordSetsListResponse(
            rrsets=[util.GetBaseARecord()]))

    self.Run('dns record-sets list -z {0}'.format(test_zone.name))
    self.AssertOutputContains("""\
    NAME       TYPE  TTL    DATA
    zone.com.  A     21600  1.2.3.4
    """, normalize_space=True)

  def testMultipleRecordSetsList(self):
    test_zone = util.GetManagedZones()[0]
    self.mocked_dns_v1.resourceRecordSets.List.Expect(
        self.messages.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            maxResults=100),
        self.messages.ResourceRecordSetsListResponse(
            rrsets=util.GetRecordSets()))

    self.Run('dns record-sets list -z {0}'.format(test_zone.name))
    self.AssertOutputContains("""\
    NAME            TYPE   TTL    DATA
    zone.com.       A      21600  1.2.3.4
    zone.com.       NS     21600  ns-cloud-e1.googledomains.com.,ns-cloud-e2.googledomains.com.,ns-cloud-e3.googledomains.com.,ns-cloud-e4.googledomains.com.
    zone.com.       SOA    21601  ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 21600 3600 1209600 300
    mail.zone.com.  A      21600  5.6.7.8
    www.zone.com.   CNAME  21600  zone.com.
    """, normalize_space=True)

  def testRecordSetsListWithLimit(self):
    test_zone = util.GetManagedZones()[0]
    self.mocked_dns_v1.resourceRecordSets.List.Expect(
        self.messages.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            maxResults=3),
        self.messages.ResourceRecordSetsListResponse(
            rrsets=util.GetRecordSets()))

    self.Run('dns record-sets list -z {0} --limit=3'.format(test_zone.name))
    self.AssertOutputContains("""\
    NAME       TYPE  TTL    DATA
    zone.com.  A     21600  1.2.3.4
    zone.com.  NS    21600  ns-cloud-e1.googledomains.com.,ns-cloud-e2.googledomains.com.,ns-cloud-e3.googledomains.com.,ns-cloud-e4.googledomains.com.
    zone.com.  SOA   21601  ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 21600 3600 1209600 300
    """, normalize_space=True)

  def testRecordSetsListWithNameFilter(self):
    test_zone = util.GetManagedZones()[0]
    test_name = util.GetCNameRecord().name

    list_request = self.messages.DnsResourceRecordSetsListRequest(
        project=self.Project(),
        managedZone=test_zone.name,
        name=test_name,
        maxResults=100)
    self.mocked_dns_v1.resourceRecordSets.List.Expect(
        list_request,
        self.messages.ResourceRecordSetsListResponse(
            rrsets=[util.GetCNameRecord()]))
    self.mocked_dns_v1.resourceRecordSets.List.Expect(
        list_request,
        self.messages.ResourceRecordSetsListResponse(
            rrsets=[util.GetCNameRecord()]))

    self.Run('dns record-sets list -z {0} --name {1}'.format(
        test_zone.name,
        # Test omission of trailing dot in the DNS name parameter
        test_name[:-1]))
    self.Run('dns record-sets list -z {0} --name {1}'.format(
        test_zone.name, test_name))
    self.AssertOutputContains("""\
    NAME           TYPE   TTL    DATA
    www.zone.com.  CNAME  21600  zone.com.
    """, normalize_space=True)

  def testRecordSetsListWithNameAndTypeFilter(self):
    test_zone = util.GetManagedZones()[0]
    test_name = util.GetSOARecord().name
    test_type = util.GetSOARecord().type
    self.mocked_dns_v1.resourceRecordSets.List.Expect(
        self.messages.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            name=test_name,
            type=test_type,
            maxResults=100),
        self.messages.ResourceRecordSetsListResponse(
            rrsets=[util.GetSOARecord()]))

    self.Run('dns record-sets list -z {0} --name {1} --type {2}'.format(
        test_zone.name, test_name, test_type))
    self.AssertOutputContains("""\
    NAME       TYPE  TTL    DATA
    zone.com.  SOA   21601  ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 21600 3600 1209600 300
    """, normalize_space=True)

  def testBadRecordSetsList(self):
    test_zone = util.GetManagedZones()[0]
    test_name = util.GetSOARecord().name
    test_type = util.GetSOARecord().type
    self.mocked_dns_v1.resourceRecordSets.List.Expect(
        self.messages.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            name=test_name,
            type=test_type,
            maxResults=100),
        exception=http_error.MakeHttpError(404),
    )
    with self.AssertRaisesHttpExceptionMatches('Resource not found.'):
      self.Run('dns record-sets list -z {0} --name {1} --type {2}'.format(
          test_zone.name, test_name, test_type))


class RecordSetsListBetaTest(base.DnsMockBetaTest):

  def testMultipleRecordSetsList(self):
    test_zone = util_beta.GetManagedZones()[0]
    self.mocked_dns_client.resourceRecordSets.List.Expect(
        self.messages_beta.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            maxResults=100),
        self.messages_beta.ResourceRecordSetsListResponse(
            rrsets=util_beta.GetRecordSets()))

    self.Run('dns record-sets list -z {0}'.format(test_zone.name))
    self.AssertOutputContains("""\
    NAME            TYPE   TTL    DATA
    zone.com.       A      21600  1.2.3.4
    zone.com.       NS     21600  ns-cloud-e1.googledomains.com.,ns-cloud-e2.googledomains.com.,ns-cloud-e3.googledomains.com.,ns-cloud-e4.googledomains.com.
    zone.com.       SOA    21601  ns-cloud-e1.googledomains.com. dns-admin.google.com. 2 21600 3600 1209600 300
    mail.zone.com.  A      21600  5.6.7.8
    www.zone.com.   CNAME  21600  zone.com.
    """, normalize_space=True)


if __name__ == '__main__':
  test_case.main()
