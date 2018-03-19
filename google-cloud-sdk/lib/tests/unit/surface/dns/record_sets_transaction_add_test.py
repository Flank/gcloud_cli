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

"""Tests for the 'gcloud dns record-sets transaction add' command."""

import os
import shutil
from googlecloudsdk.api_lib.dns import transaction_util
from googlecloudsdk.calliope.exceptions import ToolException
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util
from tests.lib.surface.dns import util_beta


class RecordSetsTransactionAddTest(base.DnsMockTest):

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

  def testTransactionAddBeforeStart(self):
    test_zone = util.GetManagedZones()[0]
    test_record = util.GetRecordSets()[0]
    with self.assertRaises(ToolException) as context:
      self.Run(
          'dns record-sets transaction add -z {0} --name {1} --ttl {2} --type '
          '{3} {4}'.format(test_zone.name, test_record.name,
                           test_record.ttl, test_record.type,
                           test_record.rrdatas[0]))
      self.assertEquals(context.exception.message,
                        'transaction not found at [{0}]'.format(
                            transaction_util.DEFAULT_PATH))

  def testTransactionAddUnsupportedType(self):
    shutil.copyfile(
        self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util.GetManagedZones()[0]
    test_record = util.GetMGRecord()
    with self.assertRaises(ToolException) as context:
      self.Run(
          'dns record-sets transaction add -z {0} --name {1} --ttl {2} --type '
          '{3} {4}'.format(test_zone.name, test_record.name,
                           test_record.ttl, test_record.type,
                           test_record.rrdatas[0]))
      self.assertEquals(
          context.exception.message,
          'unsupported record-set type [{0}]'.format(test_record.type))

  def _RunTestRaisesCorruptedTransactionFileError(self):
    test_zone = util.GetManagedZones()[0]
    test_record = util.GetMGRecord()
    with self.assertRaisesRegexp(transaction_util.CorruptedTransactionFileError,
                                 'Corrupted transaction file.'):
      self.Run(
          'dns record-sets transaction add -z {0} --name {1} --ttl {2} --type '
          '{3} {4}'.format(test_zone.name, test_record.name,
                           test_record.ttl, test_record.type,
                           test_record.rrdatas[0]))

  def testTransactionAddCorruptedTransaction(self):
    shutil.copyfile(
        self.corrupt_transaction, transaction_util.DEFAULT_PATH)
    self._RunTestRaisesCorruptedTransactionFileError()

  def testTransactionAddEmptyTransaction(self):
    self.Touch('', transaction_util.DEFAULT_PATH, contents='')
    self._RunTestRaisesCorruptedTransactionFileError()

  def testTransactionAddInvalidYaml(self):
    self.Touch('', transaction_util.DEFAULT_PATH, contents='%')
    self._RunTestRaisesCorruptedTransactionFileError()

  def testTransactionAddDatum(self):
    shutil.copyfile(
        self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util.GetManagedZones()[0]
    test_record = util.GetRecordSets()[0]
    self.Run(
        'dns record-sets transaction add -z {0} --name {1} --ttl {2} --type '
        '{3} {4}'.format(test_zone.name, test_record.name,
                         test_record.ttl, test_record.type,
                         test_record.rrdatas[0]))
    self.AssertErrContains(
        'Record addition appended to transaction at [{0}].'.format(
            transaction_util.DEFAULT_PATH))

    with open(self.initial_transaction) as expected:
      expected_change = transaction_util.ChangeFromYamlFile(expected)
      expected_change.additions.append(test_record)
    with open(transaction_util.DEFAULT_PATH) as actual:
      actual_change = transaction_util.ChangeFromYamlFile(actual)
      self.assertEquals(expected_change, actual_change)

  def testTransactionAddData(self):
    shutil.copyfile(
        self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util.GetManagedZones()[0]
    test_record = util.GetRecordSetsForExport()[5]
    self.Run(
        'dns record-sets transaction add -z {0} --name {1} --ttl {2} --type '
        '{3} {4}'.format(test_zone.name, test_record.name,
                         test_record.ttl, test_record.type,
                         ' '.join(test_record.rrdatas)))
    self.AssertErrContains(
        'Record addition appended to transaction at [{0}].'.format(
            transaction_util.DEFAULT_PATH))

    with open(self.initial_transaction) as expected:
      expected_change = transaction_util.ChangeFromYamlFile(expected)
      expected_change.additions.append(test_record)
    with open(transaction_util.DEFAULT_PATH) as actual:
      actual_change = transaction_util.ChangeFromYamlFile(actual)
      self.assertEquals(expected_change, actual_change)


class RecordSetsTransactionAddBetaTest(base.DnsMockBetaTest):

  def SetUp(self):
    self.initial_transaction = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data', 'v2beta1',
        'zone.com-initial-transaction.yaml')

  def TearDown(self):
    try:
      os.remove(transaction_util.DEFAULT_PATH)
    except OSError:
      pass

  def testTransactionAddBeforeStart(self):
    test_zone = util_beta.GetManagedZones()[0]
    test_record = util_beta.GetRecordSets()[0]
    with self.assertRaises(ToolException) as context:
      self.Run(
          'dns record-sets transaction add -z {0} --name {1} --ttl {2} --type '
          '{3} {4}'.format(test_zone.name, test_record.name,
                           test_record.ttl, test_record.type,
                           test_record.rrdatas[0]))
      self.assertEquals(context.exception.message,
                        'transaction not found at [{0}]'.format(
                            transaction_util.DEFAULT_PATH))

  def testTransactionAddUnsupportedType(self):
    shutil.copyfile(
        self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util_beta.GetManagedZones()[0]
    test_record = util_beta.GetMGRecord()
    with self.assertRaises(ToolException) as context:
      self.Run(
          'dns record-sets transaction add -z {0} --name {1} --ttl {2} --type '
          '{3} {4}'.format(test_zone.name, test_record.name,
                           test_record.ttl, test_record.type,
                           test_record.rrdatas[0]))
      self.assertEquals(
          context.exception.message,
          'unsupported record-set type [{0}]'.format(test_record.type))

  def _RunTestRaisesCorruptedTransactionFileError(self):
    test_zone = util_beta.GetManagedZones()[0]
    test_record = util_beta.GetMGRecord()
    with self.assertRaisesRegexp(transaction_util.CorruptedTransactionFileError,
                                 'Corrupted transaction file.'):
      self.Run(
          'dns record-sets transaction add -z {0} --name {1} --ttl {2} --type '
          '{3} {4}'.format(test_zone.name, test_record.name,
                           test_record.ttl, test_record.type,
                           test_record.rrdatas[0]))

  def testTransactionAddEmptyTransaction(self):
    self.Touch('', transaction_util.DEFAULT_PATH, contents='')
    self._RunTestRaisesCorruptedTransactionFileError()

  def testTransactionAddInvalidYaml(self):
    self.Touch('', transaction_util.DEFAULT_PATH, contents='%')
    self._RunTestRaisesCorruptedTransactionFileError()

  def testTransactionAddDatum(self):
    shutil.copyfile(
        self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util_beta.GetManagedZones()[0]
    test_record = util_beta.GetRecordSets()[0]
    self.Run(
        'dns record-sets transaction add -z {0} --name {1} --ttl {2} --type '
        '{3} {4}'.format(test_zone.name, test_record.name,
                         test_record.ttl, test_record.type,
                         test_record.rrdatas[0]))
    self.AssertErrContains(
        'Record addition appended to transaction at [{0}].'.format(
            transaction_util.DEFAULT_PATH))

    with open(self.initial_transaction) as expected:
      expected_change = transaction_util.ChangeFromYamlFile(
          expected, api_version=self.api_version)
      expected_change.additions.append(test_record)
    with open(transaction_util.DEFAULT_PATH) as actual:
      actual_change = transaction_util.ChangeFromYamlFile(
          actual, api_version=self.api_version)
      self.assertEquals(expected_change, actual_change)

  def testTransactionAddData(self):
    shutil.copyfile(
        self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util_beta.GetManagedZones()[0]
    test_record = util_beta.GetRecordSetsForExport()[5]
    self.Run(
        'dns record-sets transaction add -z {0} --name {1} --ttl {2} --type '
        '{3} {4}'.format(test_zone.name, test_record.name,
                         test_record.ttl, test_record.type,
                         ' '.join(test_record.rrdatas)))
    self.AssertErrContains(
        'Record addition appended to transaction at [{0}].'.format(
            transaction_util.DEFAULT_PATH))

    with open(self.initial_transaction) as expected:
      expected_change = transaction_util.ChangeFromYamlFile(
          expected, api_version=self.api_version)
      expected_change.additions.append(test_record)
    with open(transaction_util.DEFAULT_PATH) as actual:
      actual_change = transaction_util.ChangeFromYamlFile(
          actual, api_version=self.api_version)
      self.assertEquals(expected_change, actual_change)


if __name__ == '__main__':
  test_case.main()
