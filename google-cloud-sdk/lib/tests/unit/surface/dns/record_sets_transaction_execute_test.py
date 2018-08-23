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

"""Tests for the 'gcloud dns record-sets transaction execute' command."""

from __future__ import absolute_import
from __future__ import division
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


class RecordSetsTransactionExecuteTest(base.DnsMockTest):

  def SetUp(self):
    self.initial_transaction = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data',
        'zone.com-initial-transaction.yaml')

  def testTransactionExecuteBeforeStart(self):
    test_zone = util.GetManagedZones()[0]
    with self.assertRaises(ToolException) as context:
      self.Run(
          'dns record-sets transaction execute -z {0}'.format(test_zone.name))
      self.assertEqual(context.exception.message,
                       'transaction not found at [{0}]'.format(
                           transaction_util.DEFAULT_PATH))

  def testTransactionExecuteEmpty(self):
    shutil.copyfile(
        self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util.GetManagedZones()[0]
    self.Run(
        'dns record-sets transaction execute -z {0}'.format(test_zone.name))
    self.AssertErrContains(
        'Nothing to do, empty transaction [{0}]'.format(
            transaction_util.DEFAULT_PATH))
    self.assertFalse(os.path.isfile(transaction_util.DEFAULT_PATH))

  def testTransactionExecute(self):
    with open(transaction_util.DEFAULT_PATH, 'w') as transaction_file:
      transaction_util.WriteToYamlFile(transaction_file, util.GetImportChange())

    test_zone = util.GetManagedZones()[0]
    self.mocked_dns_v1.changes.Create.Expect(
        self.messages.DnsChangesCreateRequest(
            change=util.GetImportChange(),
            managedZone=test_zone.name,
            project=self.Project()),
        util.GetImportChangeAfterCreation())

    self.Run(
        'dns record-sets transaction execute -z {0}'.format(test_zone.name))

    self.AssertErrContains(
        'Executed transaction [{0}] for managed-zone [{1}].'.format(
            transaction_util.DEFAULT_PATH, test_zone.name))
    self.AssertOutputContains("""\
ID  START_TIME  STATUS
1   today now   pending
""")
    self.AssertErrContains("""\
Created [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz/changes/1].
""".format(self.api_version, self.Project()))
    self.assertFalse(os.path.isfile(transaction_util.DEFAULT_PATH))


class RecordSetsTransactionExecuteBetaTest(base.DnsMockBetaTest):

  def SetUp(self):
    self.initial_transaction = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data', 'v2beta1',
        'zone.com-initial-transaction.yaml')

  def testTransactionExecuteBeforeStart(self):
    test_zone = util_beta.GetManagedZones()[0]
    with self.assertRaises(ToolException) as context:
      self.Run(
          'dns record-sets transaction execute -z {0}'.format(test_zone.name))
      self.assertEqual(context.exception.message,
                       'transaction not found at [{0}]'.format(
                           transaction_util.DEFAULT_PATH))

  def testTransactionExecuteEmpty(self):
    shutil.copyfile(
        self.initial_transaction, transaction_util.DEFAULT_PATH)

    test_zone = util_beta.GetManagedZones()[0]
    self.Run(
        'dns record-sets transaction execute -z {0}'.format(test_zone.name))
    self.AssertErrContains(
        'Nothing to do, empty transaction [{0}]'.format(
            transaction_util.DEFAULT_PATH))
    self.assertFalse(os.path.isfile(transaction_util.DEFAULT_PATH))

  def testTransactionExecute(self):
    with open(transaction_util.DEFAULT_PATH, 'w') as transaction_file:
      transaction_util.WriteToYamlFile(
          transaction_file, util_beta.GetImportChange())

    test_zone = util_beta.GetManagedZones()[0]
    self.mocked_dns_client.changes.Create.Expect(
        self.messages_beta.DnsChangesCreateRequest(
            change=util_beta.GetImportChange(),
            managedZone=test_zone.name,
            project=self.Project()),
        util_beta.GetImportChangeAfterCreation())

    self.Run(
        'dns record-sets transaction execute -z {0}'.format(test_zone.name))

    self.AssertErrContains(
        'Executed transaction [{0}] for managed-zone [{1}].'.format(
            transaction_util.DEFAULT_PATH, test_zone.name))
    self.AssertOutputContains("""\
ID  START_TIME  STATUS
1   today now   pending
""", normalize_space=True)
    self.AssertErrContains("""\
Created [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz/changes/1].
""".format(self.api_version, self.Project()), normalize_space=True)
    self.assertFalse(os.path.isfile(transaction_util.DEFAULT_PATH))


if __name__ == '__main__':
  test_case.main()
