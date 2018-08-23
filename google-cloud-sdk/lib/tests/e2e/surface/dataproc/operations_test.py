# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Integration test for the 'dataproc operations' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import e2e_base


class OperationsIntegrationTest(e2e_base.DataprocIntegrationTestBase):
  """Integration test for all operations commands.

  This test does not mutate project state, and makes no assumptions about the
  contents of the project besides that operations are not commonly deleted.
  """

  def testOperationsList(self):
    self.RunDataproc('operations list --page-size=10 --limit=20')

  def testOperationsDescribe(self):
    operations = list(self.RunDataproc(
        'operations list --page-size=20 --limit=20 --state-filter=inactive'))
    if not operations:
      self.skipTest('No operations to describe')
    operation_id = operations[0].name
    operation = self.RunDataproc(
        'operations describe {0}'.format(operation_id))
    # TODO(b/36049789): Uncomment after fixing AssertMessagesEqual to handle
    # JsonValue field sorting.
    # self.AssertMessagesEqual(operations[0], operation)
    self.assertEqual(operation_id, operation.name)


class OperationsIntegrationTestBeta(OperationsIntegrationTest,
                                    base.DataprocTestBaseBeta):
  """Integration test for all operations commands.

  This test does not mutate project state, and makes no assumptions about the
  contents of the project besides that operations are not commonly deleted.
  """

  def testBeta(self):
    self.assertEqual(self.messages,
                     core_apis.GetMessagesModule('dataproc', 'v1beta2'))
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)

  def testOperationsGetSetIAMPolicy(self):
    operations = list(self.RunDataproc(
        'operations list --page-size=1 --limit=1 --state-filter=inactive'))
    if not operations:
      self.skipTest('No operations to get/set iam-policy on')
    operation_id = operations[0].name
    self.GetSetIAMPolicy('operations', operation_id)


if __name__ == '__main__':
  sdk_test_base.main()
