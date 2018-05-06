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

"""Tests for the 'gcloud dns record-sets transaction abort' command."""

import os
from googlecloudsdk.api_lib.dns import transaction_util
from googlecloudsdk.calliope.exceptions import ToolException
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util
from tests.lib.surface.dns import util_beta


class RecordSetsTransactionAbortTest(base.DnsMockTest):

  def testTransactionAbortBeforeStart(self):
    test_zone = util.GetManagedZones()[0]
    with self.assertRaises(ToolException) as context:
      self.Run(
          'dns record-sets transaction abort -z {0}'.format(test_zone.name))
      self.assertEqual(context.exception.message,
                       'transaction not found at [{0}]'.format(
                           transaction_util.DEFAULT_PATH))

  def testTransactionAbort(self):
    open(transaction_util.DEFAULT_PATH, 'w').close()
    test_zone = util.GetManagedZones()[0]
    self.Run('dns record-sets transaction abort -z {0}'.format(test_zone.name))
    self.AssertErrContains(
        'Aborted transaction [{0}].'.format(
            transaction_util.DEFAULT_PATH))
    self.assertFalse(os.path.isfile(transaction_util.DEFAULT_PATH))


class RecordSetsTransactionAbortBetaTest(base.DnsMockBetaTest):

  def testTransactionAbortBeforeStart(self):
    test_zone = util_beta.GetManagedZones()[0]
    with self.assertRaises(ToolException) as context:
      self.Run(
          'dns record-sets transaction abort -z {0}'.format(test_zone.name))
      self.assertEqual(context.exception.message,
                       'transaction not found at [{0}]'.format(
                           transaction_util.DEFAULT_PATH))

  def testTransactionAbort(self):
    open(transaction_util.DEFAULT_PATH, 'w').close()
    test_zone = util_beta.GetManagedZones()[0]
    self.Run('dns record-sets transaction abort -z {0}'.format(test_zone.name))
    self.AssertErrContains(
        'Aborted transaction [{0}].'.format(
            transaction_util.DEFAULT_PATH))
    self.assertFalse(os.path.isfile(transaction_util.DEFAULT_PATH))


if __name__ == '__main__':
  test_case.main()
