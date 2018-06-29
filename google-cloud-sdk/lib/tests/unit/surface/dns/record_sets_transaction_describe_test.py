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

"""Tests for the 'gcloud dns record-sets transaction describe' command."""

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


class RecordSetsTransactionDescribeTest(base.DnsMockTest):

  def SetUp(self):
    self.transaction_file = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data',
        'zone.com-transaction.yaml')

  def testTransactionDescribeBeforeStart(self):
    test_zone = util.GetManagedZones()[0]
    with self.assertRaises(ToolException) as context:
      self.Run(
          'dns record-sets transaction describe -z {0}'.format(test_zone.name))
      self.assertEqual(context.exception.message,
                       'transaction not found at [{0}]'.format(
                           transaction_util.DEFAULT_PATH))

  def testTransactionDescribe(self):
    shutil.copyfile(self.transaction_file, transaction_util.DEFAULT_PATH)

    test_zone = util.GetManagedZones()[0]
    self.Run(
        'dns record-sets transaction describe -z {0}'.format(test_zone.name))
    os.remove(transaction_util.DEFAULT_PATH)

    with open(self.transaction_file) as expected:
      self.AssertOutputContains(''.join(expected.readlines()[1:]))


class RecordSetsTransactionDescribeBetaTest(base.DnsMockBetaTest):

  def SetUp(self):
    self.transaction_file = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data', 'v2beta1',
        'zone.com-transaction.yaml')

  def testTransactionDescribeBeforeStart(self):
    test_zone = util_beta.GetManagedZones()[0]
    with self.assertRaises(ToolException) as context:
      self.Run(
          'dns record-sets transaction describe -z {0}'.format(test_zone.name))
      self.assertEqual(context.exception.message,
                       'transaction not found at [{0}]'.format(
                           transaction_util.DEFAULT_PATH))

  def testTransactionDescribe(self):
    shutil.copyfile(self.transaction_file, transaction_util.DEFAULT_PATH)

    test_zone = util_beta.GetManagedZones()[0]
    self.Run(
        'dns record-sets transaction describe -z {0}'.format(test_zone.name))
    os.remove(transaction_util.DEFAULT_PATH)

    with open(self.transaction_file) as expected:
      self.AssertOutputContains(''.join(expected.readlines()[1:]))


if __name__ == '__main__':
  test_case.main()
