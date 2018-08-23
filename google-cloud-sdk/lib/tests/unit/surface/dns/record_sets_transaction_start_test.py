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

"""Tests for the 'gcloud dns record-sets transaction start' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from googlecloudsdk.api_lib.dns import transaction_util
from googlecloudsdk.calliope.exceptions import ToolException
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util
from tests.lib.surface.dns import util_beta


class RecordSetsTransactionStartTest(base.DnsMockTest):

  def SetUp(self):
    self.initial_transaction = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data',
        'zone.com-initial-transaction.yaml')

  def testTransactionStartAlreadyExists(self):
    open(transaction_util.DEFAULT_PATH, 'w').close()
    test_zone = util.GetManagedZones()[0]
    with self.assertRaises(ToolException) as context:
      self.Run(
          'dns record-sets transaction start -z {0}'.format(test_zone.name))
      self.assertEqual(context.exception.message,
                       'transaction already exists at [{0}]'.format(
                           transaction_util.DEFAULT_PATH))
      os.remove(transaction_util.DEFAULT_PATH)

    os.remove(transaction_util.DEFAULT_PATH)

  def testTransactionStart(self):
    test_zone = util.GetManagedZones()[0]
    self.mocked_dns_v1.managedZones.Get.Expect(
        self.messages.DnsManagedZonesGetRequest(
            managedZone=test_zone.name,
            project=self.Project()),
        test_zone)

    self.mocked_dns_v1.resourceRecordSets.List.Expect(
        self.messages.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            name=test_zone.dnsName,
            type='SOA',
            maxResults=100),
        self.messages.ResourceRecordSetsListResponse(
            rrsets=util.GetRecordSets()[2:3]))

    self.Run('dns record-sets transaction start -z {0} '.format(test_zone.name))
    self.AssertErrContains(
        'Transaction started [{0}].'.format(transaction_util.DEFAULT_PATH))

    with open(transaction_util.DEFAULT_PATH) as results:
      with open(self.initial_transaction) as expected:
        self.assertEqual(expected.readlines(), results.readlines())
    os.remove(transaction_util.DEFAULT_PATH)


class RecordSetsTransactionStartBetaTest(base.DnsMockBetaTest):

  def SetUp(self):
    self.initial_transaction = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data', 'v2beta1',
        'zone.com-initial-transaction.yaml')

  def testTransactionStartAlreadyExists(self):
    open(transaction_util.DEFAULT_PATH, 'w').close()
    test_zone = util_beta.GetManagedZones()[0]
    with self.assertRaises(ToolException) as context:
      self.Run(
          'dns record-sets transaction start -z {0}'.format(test_zone.name))
      self.assertEqual(context.exception.message,
                       'transaction already exists at [{0}]'.format(
                           transaction_util.DEFAULT_PATH))
      os.remove(transaction_util.DEFAULT_PATH)

    os.remove(transaction_util.DEFAULT_PATH)

  def testTransactionStart(self):
    test_zone = util_beta.GetManagedZones()[0]
    self.mocked_dns_client.managedZones.Get.Expect(
        self.messages_beta.DnsManagedZonesGetRequest(
            managedZone=test_zone.name,
            project=self.Project()),
        test_zone)

    self.mocked_dns_client.resourceRecordSets.List.Expect(
        self.messages_beta.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            name=test_zone.dnsName,
            type='SOA',
            maxResults=100),
        self.messages_beta.ResourceRecordSetsListResponse(
            rrsets=util_beta.GetRecordSets()[2:3]))

    self.Run('dns record-sets transaction start -z {0} '.format(test_zone.name))
    self.AssertErrContains(
        'Transaction started [{0}].'.format(transaction_util.DEFAULT_PATH))

    with open(transaction_util.DEFAULT_PATH) as results:
      with open(self.initial_transaction) as expected:
        self.assertEqual(expected.readlines(), results.readlines())
    os.remove(transaction_util.DEFAULT_PATH)


if __name__ == '__main__':
  test_case.main()
