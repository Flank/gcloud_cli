# Copyright 2017 Google Inc. All Rights Reserved.
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

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test import tool_results
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.firebase.test import unit_base


TESTING_V1_MESSAGES = apis.GetMessagesModule('testing', 'v1')
M_PENDING = TESTING_V1_MESSAGES.TestMatrix.StateValueValuesEnum.PENDING
M_INVALID = TESTING_V1_MESSAGES.TestMatrix.StateValueValuesEnum.INVALID
M_ERROR = TESTING_V1_MESSAGES.TestMatrix.StateValueValuesEnum.ERROR
DETAILS = TESTING_V1_MESSAGES.TestMatrix.InvalidMatrixDetailsValueValuesEnum


class ToolResultsTests(unit_base.TestMockClientTest):
  """Unit tests for test/lib/tool_results.py."""

  def testCreateToolResultsUiUrl_withProdUrl(self):
    properties.VALUES.test.results_base_url.Set('')
    tr_ids = tool_results.ToolResultsIds('h1', 'e1')

    url = tool_results.CreateToolResultsUiUrl('runway', tr_ids)

    self.assertEqual(url,
                     'https://console.firebase.google.com/project/runway/'
                     'testlab/histories/h1/matrices/e1')

  def testCreateToolResultsUiUrl_withBaseUrlOverride(self):
    properties.VALUES.test.results_base_url.Set('https://myservice-test.com')
    tr_ids = tool_results.ToolResultsIds('h2', 'e2')

    url = tool_results.CreateToolResultsUiUrl('runway', tr_ids)

    self.assertEqual(url,
                     'https://myservice-test.com/project/runway/'
                     'testlab/histories/h2/matrices/e2')

  def testGetToolResultsIds_IdsAvailableImmediately(self):
    name = 'matrix1'
    matrix = self.NewTestMatrixIds(name, 'hist1', 'exec1')
    monitor = self.CreateMatrixMonitor(name, self.args)

    ids = tool_results.GetToolResultsIds(matrix, monitor, status_interval=0)

    self.assertEqual('hist1', ids.history_id)
    self.assertEqual('exec1', ids.execution_id)
    self.AssertErrContains('Creating individual test executions')

  def testGetToolResultsIds_HistoryIdAvailableAfter3Checks(self):
    name = 'matrix2'
    matrix = self.NewTestMatrixIds(name, None, 'exec2')
    self.ExpectMatrixIds(name, None, 'exec2')
    self.ExpectMatrixIds(name, None, 'exec2')
    self.ExpectMatrixIds(name, 'hist2', 'exec2')
    monitor = self.CreateMatrixMonitor(name, self.args)

    ids = tool_results.GetToolResultsIds(matrix, monitor, status_interval=0)

    self.assertEqual('hist2', ids.history_id)
    self.assertEqual('exec2', ids.execution_id)
    self.AssertErrContains('Creating individual test executions')

  def testGetToolResultsIds_ExecutionIdAvailableAfter6Checks(self):
    name = 'matrix3'
    matrix = self.NewTestMatrixIds(name, None, None)
    self.ExpectMatrixIds(name, None, None)
    self.ExpectMatrixIds(name, None, None)
    self.ExpectMatrixIds(name, None, None)
    self.ExpectMatrixIds(name, 'hist3', None)
    self.ExpectMatrixIds(name, 'hist3', None)
    self.ExpectMatrixIds(name, 'hist3', 'exec3')
    monitor = self.CreateMatrixMonitor(name, self.args)

    ids = tool_results.GetToolResultsIds(matrix, monitor, status_interval=0)

    self.assertEqual('hist3', ids.history_id)
    self.assertEqual('exec3', ids.execution_id)
    self.AssertErrContains('Creating individual test executions')

  def testGetToolResultsIds_MatrixErrorsOutWithoutBothIds(self):
    name = 'matrix4'
    matrix = self.NewTestMatrixIds(name, None, None)
    self.ExpectMatrixStatus(name, M_PENDING, [], None, 'exec4')
    self.ExpectMatrixStatus(name, M_ERROR, [], 'hist4', None)
    monitor = self.CreateMatrixMonitor(name, self.args)

    with self.assertRaises(exceptions.BadMatrixError) as ex_ctx:
      tool_results.GetToolResultsIds(matrix, monitor, status_interval=0)

    self.assertIn('Matrix [matrix4] unexpectedly reached final status ERROR',
                  ex_ctx.exception.message)

  def testGetToolResultsIds_MatrixInvalidDetailsUnavailable(self):
    name = 'matrix5'
    matrix = self.NewTestMatrixIds(name, None, None)
    self.ExpectMatrixStatus(name, M_PENDING, [], None, None)
    self.ExpectMatrixInvalid(name, DETAILS.DETAILS_UNAVAILABLE)
    monitor = self.CreateMatrixMonitor(name, self.args)

    with self.assertRaises(exceptions.BadMatrixError) as ex_ctx:
      tool_results.GetToolResultsIds(matrix, monitor, status_interval=0)

    self.assertIn('Matrix [matrix5] unexpectedly reached final status INVALID',
                  ex_ctx.exception.message)

  def testGetToolResultsIds_MatrixInvalidDetailsUnset(self):
    name = 'matrix6'
    matrix = self.NewTestMatrixIds(name, None, None)
    self.ExpectMatrixStatus(name, M_PENDING, [], None, None)
    self.ExpectMatrixInvalid(name, None)
    monitor = self.CreateMatrixMonitor(name, self.args)

    with self.assertRaises(exceptions.BadMatrixError) as ex_ctx:
      tool_results.GetToolResultsIds(matrix, monitor, status_interval=0)

    self.assertIn('Matrix [matrix6] unexpectedly reached final status INVALID',
                  ex_ctx.exception.message)

  def testGetToolResultsIds_MatrixInvalidNoManifest(self):
    name = 'matrix7'
    matrix = self.NewTestMatrixIds(name, None, None)
    self.ExpectMatrixStatus(name, M_PENDING, [], None, None)
    self.ExpectMatrixInvalid(name, DETAILS.NO_MANIFEST)
    monitor = self.CreateMatrixMonitor(name, self.args)

    with self.assertRaises(exceptions.BadMatrixError) as ex_ctx:
      tool_results.GetToolResultsIds(matrix, monitor, status_interval=0)

    ex_msg = ex_ctx.exception.message
    self.assertIn('Matrix [matrix7] failed during validation', ex_msg)
    self.assertIn('APK is missing the manifest file', ex_msg)

  def testGetToolResultsIds_MatrixInvalidMissingScenarios(self):
    name = 'matrix8'
    matrix = self.NewTestMatrixIds(name, None, None)
    self.ExpectMatrixStatus(name, M_PENDING, [], None, None)
    self.ExpectMatrixInvalid(name, DETAILS.SCENARIO_NOT_DECLARED)
    monitor = self.CreateMatrixMonitor(name, self.args)

    with self.assertRaises(exceptions.BadMatrixError) as ex_ctx:
      tool_results.GetToolResultsIds(matrix, monitor, status_interval=0)

    ex_msg = ex_ctx.exception.message
    self.assertIn('Matrix [matrix8] failed during validation', ex_msg)
    self.assertIn('A scenario-number was not declared', ex_msg)

  def NewTestMatrixIds(self, matrix_id, hist_id, exec_id):
    return self.NewTestMatrix(matrix_id, None, None, [], hist_id, exec_id)

  def ExpectMatrixIds(self, matrix_id, hist_id, exec_id):
    """Add a mocked response to a TestMatrices.Get request."""
    self.ExpectMatrixStatus(matrix_id, None, [], hist_id, exec_id)

  def ExpectMatrixInvalid(self, matrix_id, invalid_details):
    """Add a mocked invalid matrix response to a TestMatrices.Get request."""
    matrix = self.NewTestMatrix(matrix_id, None, M_INVALID, [], None, None)
    matrix.invalidMatrixDetails = invalid_details

    self.testing_client.projects_testMatrices.Get.Expect(
        request=self.testing_msgs.TestingProjectsTestMatricesGetRequest(
            projectId=self.PROJECT_ID, testMatrixId=matrix_id),
        response=matrix)


if __name__ == '__main__':
  test_case.main()
