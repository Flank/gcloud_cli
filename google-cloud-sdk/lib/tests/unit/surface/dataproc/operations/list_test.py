# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Test of the 'operations list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import unit_base


class OperationsListUnitTest(unit_base.DataprocUnitTestBase):

  OPERATION_IDS = [
      '564f9cac-e514-43e5-98de-e74442010cd3',
      'a0aa06f9-41b7-48f3-9694-18e31bb78685',
      '90471700-f11d-413a-8d60-012ba3de4aee']

  def SetUp(self):
    self.operation_names = [
        self.OperationName(op_id) for op_id in self.OPERATION_IDS]
    self.operations = [
        self.MakeCompletedOperation(
            name=name.format(self.Project()),
            metadata=collections.OrderedDict([
                ('labels', {'k1': 'v1'}),
                ('operationType', 'CREATE'),
                ('status', {'state': 'DONE'}),
                ('statusHistory', [
                    {'stateStartTime': '2018-09-21T18:18:32.143Z'}]),
                ('warnings', ['please stop whatever it is youre doing']),
            ])
        )
        for name in self.operation_names]
    self.base_name = 'projects/{0}/regions/{1}/operations'.format(
        self.Project(), self.REGION)

  def ExpectListOperations(
      self, operations=None, op_filter='{}', exception=None):
    response = None
    if not exception:
      response = self.messages.ListOperationsResponse(
          operations=operations)
    self.mock_client.projects_regions_operations.List.Expect(
        self.messages.DataprocProjectsRegionsOperationsListRequest(
            pageSize=100, name=self.base_name, filter=op_filter),
        response=response,
        exception=exception)

  def testListOperations(self):
    expected = self.operations
    self.ExpectListOperations(expected)
    result = self.RunDataproc('operations list')
    self.AssertMessagesEqual(expected, list(result))

  def testListOperationsOutput(self):
    expected = self.operations
    self.ExpectListOperations(expected)
    self.RunDataproc('operations list', output_format='')
    self.AssertOutputContains(
        'NAME TIMESTAMP TYPE STATE ERROR WARNINGS', normalize_space=True)
    self.AssertOutputContains(
        '{0} 2018-09-21T18:18:32.143Z CREATE DONE 1'.format(
            self.OPERATION_IDS[0]),
        normalize_space=True)

  def testListOperationsWithJsonFilter(self):
    expected = self.operations
    op_filter = '{"operation_state_matcher": "NON_ACTIVE"}'
    self.ExpectListOperations(expected, op_filter)
    result = self.RunDataproc('operations list --state-filter inactive')
    self.AssertMessagesEqual(expected, list(result))

  def testListOperationsWithOnePlatformFilter(self):
    self.ExpectListOperations(self.operations, op_filter='labels.k1:v1')
    result = self.RunDataproc('operations list --filter=labels.k1:v1')
    self.AssertMessagesEqual(self.operations, list(result))

  def testListOperationsWithCluster(self):
    expected = self.operations
    op_filter = '{"cluster_name": "my-cluster"}'
    self.ExpectListOperations(expected, op_filter)
    result = self.RunDataproc('operations list --cluster my-cluster')
    self.AssertMessagesEqual(expected, list(result))

  def testListOperationsPermissionsError(self):
    self.ExpectListOperations(
        exception=self.MakeHttpError(403))
    with self.AssertRaisesHttpErrorMatchesAsHttpException(
        'Permission denied API reason: Permission denied.'):
      next(self.RunDataproc('operations list'))

  def testListOperationsPagination(self):
    self.mock_client.projects_regions_operations.List.Expect(
        self.messages.DataprocProjectsRegionsOperationsListRequest(
            name=self.base_name,
            filter='{}',
            pageSize=2),
        response=self.messages.ListOperationsResponse(
            operations=self.operations[:1],
            nextPageToken='test-token'))
    self.mock_client.projects_regions_operations.List.Expect(
        self.messages.DataprocProjectsRegionsOperationsListRequest(
            name=self.base_name,
            filter='{}',
            pageSize=2,
            pageToken='test-token'),
        response=self.messages.ListOperationsResponse(
            operations=self.operations[1:]))

    result = self.RunDataproc('operations list --page-size=2 --limit=3')
    self.AssertMessagesEqual(self.operations, self.FilterOutPageMarkers(result))


class OperationsListUnitTestBeta(OperationsListUnitTest,
                                 base.DataprocTestBaseBeta):

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)


class OperationsListUnitTestAlpha(OperationsListUnitTestBeta,
                                  base.DataprocTestBaseAlpha):
  pass


if __name__ == '__main__':
  sdk_test_base.main()
