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

"""Tests for the 'gcloud dns record-sets transaction remove' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import os
import shutil
from googlecloudsdk.api_lib.dns import transaction_util
from googlecloudsdk.calliope.exceptions import ToolException
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util
from tests.lib.surface.dns import util_beta


class RecordSetsTransactionRemoveTest(base.DnsMockTest):

  def SetUp(self):
    self.initial_transaction = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data',
        'zone.com-initial-transaction.yaml')
    # This file is missing a 'deletions' section
    self.corrupt_transaction = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data',
        'zone.com-transaction-corrupt.yaml')

  def TearDown(self):
    try:
      os.remove(transaction_util.DEFAULT_PATH)
    except OSError:
      pass

  def testTransactionRemoveBeforeStart(self):
    test_zone = util.GetManagedZones()[0]
    test_record = util.GetRecordSets()[0]
    with self.assertRaises(ToolException) as context:
      self.Run('dns record-sets transaction remove -z {0} --name {1} --ttl {2}'
               ' --type {3} {4}'.format(test_zone.name, test_record.name,
                                        test_record.ttl, test_record.type,
                                        test_record.rrdatas[0]))
      self.assertEqual(context.exception.message,
                       'transaction not found at [{0}]'.format(
                           transaction_util.DEFAULT_PATH))

  def testTransactionRemoveUnsupportedType(self):
    shutil.copyfile(self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util.GetManagedZones()[0]
    test_record = util.GetMGRecord()
    with self.assertRaises(ToolException) as context:
      self.Run('dns record-sets transaction remove -z {0} --name {1} --ttl {2}'
               ' --type {3} {4}'.format(test_zone.name, test_record.name,
                                        test_record.ttl, test_record.type,
                                        test_record.rrdatas[0]))
      self.assertEqual(
          context.exception.message,
          'unsupported record-set type [{0}]'.format(test_record.type))

  def _RunTestRaisesCorruptedTransactionFileError(self):
    test_zone = util.GetManagedZones()[0]
    test_record = util.GetMGRecord()
    with self.assertRaisesRegex(transaction_util.CorruptedTransactionFileError,
                                'Corrupted transaction file.'):
      self.Run(
          'dns record-sets transaction remove -z {0} --name {1} --ttl {2} '
          '--type {3} {4}'.format(test_zone.name, test_record.name,
                                  test_record.ttl, test_record.type,
                                  test_record.rrdatas[0]))

  def testTransactionRemoveCorruptedTransaction(self):
    shutil.copyfile(
        self.corrupt_transaction, transaction_util.DEFAULT_PATH)
    self._RunTestRaisesCorruptedTransactionFileError()

  def testTransactionRemoveEmptyTransaction(self):
    self.Touch('', transaction_util.DEFAULT_PATH, contents='')
    self._RunTestRaisesCorruptedTransactionFileError()

  def testTransactionRemoveInvalidYaml(self):
    self.Touch('', transaction_util.DEFAULT_PATH, contents='%')
    self._RunTestRaisesCorruptedTransactionFileError()

  def _TransactionRemoveNonExistingHelper(
      self, record_to_remove, existing_records):
    shutil.copyfile(self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util.GetManagedZones()[0]
    test_record = record_to_remove
    self.mocked_dns_v1.resourceRecordSets.List.Expect(
        self.messages.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            name=test_record.name,
            type=test_record.type,
            maxResults=100),
        self.messages.ResourceRecordSetsListResponse(
            rrsets=existing_records))

    with self.AssertRaisesToolExceptionRegexp(
        'Record to be removed does not exist'):
      self.Run('dns record-sets transaction remove -z {0} --name {1} --ttl {2}'
               ' --type {3} {4}'.format(test_zone.name, test_record.name,
                                        test_record.ttl, test_record.type,
                                        test_record.rrdatas[0]))

  def testTransactionRemoveNonExistingRecord(self):
    self._TransactionRemoveNonExistingHelper(util.GetRecordSets()[0], [])

  def testTransactionRemoveDifferentRecord(self):
    self._TransactionRemoveNonExistingHelper(
        util.GetRecordSets()[0], util.GetRecordSetsForExport()[:1])

  def _TransactionRemoveHelper(self, record_to_remove,
                               domain_name_for_run=None):
    shutil.copyfile(self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util.GetManagedZones()[0]
    test_record = record_to_remove
    self.mocked_dns_v1.resourceRecordSets.List.Expect(
        self.messages.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            name=test_record.name,
            type=test_record.type,
            maxResults=100),
        self.messages.ResourceRecordSetsListResponse(
            rrsets=[test_record]))

    if not domain_name_for_run:
      domain_name_for_run = test_record.name

    self.Run('dns record-sets transaction remove -z {0} --name {1} --ttl {2}'
             ' --type {3} {4}'.format(test_zone.name, domain_name_for_run,
                                      test_record.ttl, test_record.type,
                                      ' '.join(test_record.rrdatas)))
    self.AssertErrContains(
        'Record removal appended to transaction at [{0}].'.format(
            transaction_util.DEFAULT_PATH))

    with open(self.initial_transaction) as expected:
      expected_change = transaction_util.ChangeFromYamlFile(expected)
      expected_change.deletions.append(test_record)
    with open(transaction_util.DEFAULT_PATH) as actual:
      actual_change = transaction_util.ChangeFromYamlFile(actual)
      self.assertEqual(expected_change, actual_change)

  def testTransactionRemoveDatum(self):
    self._TransactionRemoveHelper(util.GetRecordSets()[0])

  def testTransactionRemoveData(self):
    self._TransactionRemoveHelper(util.GetRecordSetsForExport()[5])

  def testDomainWithoutTrailingDot(self):
    self._TransactionRemoveHelper(util.GetRecordSets()[0],
                                  util.GetRecordSets()[0].name.rstrip('.'))


class RecordSetsTransactionRemoveBetaTest(base.DnsMockBetaTest):

  def SetUp(self):
    self.initial_transaction = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data', 'v2beta1',
        'zone.com-initial-transaction.yaml')

  def TearDown(self):
    try:
      os.remove(transaction_util.DEFAULT_PATH)
    except OSError:
      pass

  def testTransactionRemoveBeforeStart(self):
    test_zone = util_beta.GetManagedZones()[0]
    test_record = util_beta.GetRecordSets()[0]
    with self.assertRaises(ToolException) as context:
      self.Run('dns record-sets transaction remove -z {0} --name {1} --ttl {2}'
               ' --type {3} {4}'.format(test_zone.name, test_record.name,
                                        test_record.ttl, test_record.type,
                                        test_record.rrdatas[0]))
      self.assertEqual(context.exception.message,
                       'transaction not found at [{0}]'.format(
                           transaction_util.DEFAULT_PATH))

  def testTransactionRemoveUnsupportedType(self):
    shutil.copyfile(self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util_beta.GetManagedZones()[0]
    test_record = util_beta.GetMGRecord()
    with self.assertRaises(ToolException) as context:
      self.Run('dns record-sets transaction remove -z {0} --name {1} --ttl {2}'
               ' --type {3} {4}'.format(test_zone.name, test_record.name,
                                        test_record.ttl, test_record.type,
                                        test_record.rrdatas[0]))
      self.assertEqual(
          context.exception.message,
          'unsupported record-set type [{0}]'.format(test_record.type))

  def _RunTestRaisesCorruptedTransactionFileError(self):
    test_zone = util_beta.GetManagedZones()[0]
    test_record = util_beta.GetMGRecord()
    with self.assertRaisesRegex(transaction_util.CorruptedTransactionFileError,
                                'Corrupted transaction file.'):
      self.Run(
          'dns record-sets transaction remove -z {0} --name {1} --ttl {2} '
          '--type {3} {4}'.format(test_zone.name, test_record.name,
                                  test_record.ttl, test_record.type,
                                  test_record.rrdatas[0]))

  def testTransactionRemoveEmptyTransaction(self):
    self.Touch('', transaction_util.DEFAULT_PATH, contents='')
    self._RunTestRaisesCorruptedTransactionFileError()

  def testTransactionRemoveInvalidYaml(self):
    self.Touch('', transaction_util.DEFAULT_PATH, contents='%')
    self._RunTestRaisesCorruptedTransactionFileError()

  def _TransactionRemoveNonExistingHelper(
      self, record_to_remove, existing_records):
    shutil.copyfile(self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util_beta.GetManagedZones()[0]
    test_record = record_to_remove
    self.mocked_dns_client.resourceRecordSets.List.Expect(
        self.messages_beta.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            name=test_record.name,
            type=test_record.type,
            maxResults=100),
        self.messages_beta.ResourceRecordSetsListResponse(
            rrsets=existing_records))

    with self.AssertRaisesToolExceptionRegexp(
        'Record to be removed does not exist'):
      self.Run('dns record-sets transaction remove -z {0} --name {1} --ttl {2}'
               ' --type {3} {4}'.format(test_zone.name, test_record.name,
                                        test_record.ttl, test_record.type,
                                        test_record.rrdatas[0]))

  def testTransactionRemoveNonExistingRecord(self):
    self._TransactionRemoveNonExistingHelper(util_beta.GetRecordSets()[0], [])

  def testTransactionRemoveDifferentRecord(self):
    self._TransactionRemoveNonExistingHelper(
        util_beta.GetRecordSets()[0], util_beta.GetRecordSetsForExport()[:1])

  def _TransactionRemoveHelper(self, record_to_remove,
                               domain_name_for_run=None):
    shutil.copyfile(self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util_beta.GetManagedZones()[0]
    test_record = record_to_remove
    self.mocked_dns_client.resourceRecordSets.List.Expect(
        self.messages_beta.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            name=test_record.name,
            type=test_record.type,
            maxResults=100),
        self.messages_beta.ResourceRecordSetsListResponse(
            rrsets=[test_record]))

    if not domain_name_for_run:
      domain_name_for_run = test_record.name

    self.Run('dns record-sets transaction remove -z {0} --name {1} --ttl {2}'
             ' --type {3} {4}'.format(test_zone.name, domain_name_for_run,
                                      test_record.ttl, test_record.type,
                                      ' '.join(test_record.rrdatas)))
    self.AssertErrContains(
        'Record removal appended to transaction at [{0}].'.format(
            transaction_util.DEFAULT_PATH))

    with open(self.initial_transaction) as expected:
      expected_change = transaction_util.ChangeFromYamlFile(
          expected, api_version=self.api_version)
      expected_change.deletions.append(test_record)
    with open(transaction_util.DEFAULT_PATH) as actual:
      actual_change = transaction_util.ChangeFromYamlFile(
          actual, api_version=self.api_version)
      self.assertEqual(expected_change, actual_change)

  def testTransactionRemoveDatum(self):
    self._TransactionRemoveHelper(util_beta.GetRecordSets()[0])

  def testTransactionRemoveData(self):
    self._TransactionRemoveHelper(util_beta.GetRecordSetsForExport()[5])

  def testDomainWithoutTrailingDot(self):
    self._TransactionRemoveHelper(util_beta.GetRecordSets()[0],
                                  util_beta.GetRecordSets()[0].name.rstrip('.'))


if __name__ == '__main__':
  test_case.main()
