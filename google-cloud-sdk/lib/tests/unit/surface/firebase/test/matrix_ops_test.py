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

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.android import unit_base
import six

TESTING_V1_MESSAGES = apis.GetMessagesModule('testing', 'v1')

# TestExecution states
_TEST_EXECUTION_STATES = TESTING_V1_MESSAGES.TestExecution.StateValueValuesEnum
VALID = _TEST_EXECUTION_STATES.VALIDATING
PENDING = _TEST_EXECUTION_STATES.PENDING
RUNNING = _TEST_EXECUTION_STATES.RUNNING
FINISHED = _TEST_EXECUTION_STATES.FINISHED
ERROR = _TEST_EXECUTION_STATES.ERROR
SKIP = _TEST_EXECUTION_STATES.UNSUPPORTED_ENVIRONMENT
CANCEL = _TEST_EXECUTION_STATES.CANCELLED
INVALID = _TEST_EXECUTION_STATES.INVALID

# TestMatrix states
M_VALID = TESTING_V1_MESSAGES.TestMatrix.StateValueValuesEnum.VALIDATING
M_PENDING = TESTING_V1_MESSAGES.TestMatrix.StateValueValuesEnum.PENDING
M_RUNNING = TESTING_V1_MESSAGES.TestMatrix.StateValueValuesEnum.RUNNING
M_FINISHED = TESTING_V1_MESSAGES.TestMatrix.StateValueValuesEnum.FINISHED
M_ERROR = TESTING_V1_MESSAGES.TestMatrix.StateValueValuesEnum.ERROR
M_CANCEL = TESTING_V1_MESSAGES.TestMatrix.StateValueValuesEnum.CANCELLED
M_INVALID = TESTING_V1_MESSAGES.TestMatrix.StateValueValuesEnum.INVALID


class MatrixMonitorTests(unit_base.AndroidMockClientTest):
  """Unit tests for api_lib/test/matrix_ops.MatrixMonitor."""

  def testMatrixMonitor_GetTestMatrixStatus_GetsHttpError(self):
    matrix_id = 'kam'
    monitor = self.CreateMatrixMonitor(matrix_id, self.args)

    self.testing_client.projects_testMatrices.Get.Expect(
        request=TESTING_V1_MESSAGES.TestingProjectsTestMatricesGetRequest(
            projectId=self.PROJECT_ID, testMatrixId=matrix_id),
        exception=test_utils.MakeHttpError(
            'notFound', 'Simulated failure to get test matrix status.'))

    # An HttpError from the rpc should be converted to an HttpException
    with self.assertRaises(calliope_exceptions.HttpException):
      monitor.GetTestMatrixStatus()

  def testMatrixMonitor_GetTestExecutionStatus_GetsHttpError(self):
    matrix_id = 'kam'
    monitor = self.CreateMatrixMonitor(matrix_id, self.args)

    self.testing_client.projects_testMatrices.Get.Expect(
        request=TESTING_V1_MESSAGES.TestingProjectsTestMatricesGetRequest(
            projectId=self.PROJECT_ID, testMatrixId=matrix_id),
        exception=test_utils.MakeHttpError(
            'notFound', 'Simulated failure to get test execution status.'))

    # An HttpError from the rpc should be converted to an HttpException
    with self.assertRaises(calliope_exceptions.HttpException):
      monitor._GetTestExecutionStatus('legion-of-boom-test-id')

  def testMatrixMonitor_GetTestExecutionStatus_TestIdNotFound(self):
    matrix_id = 'kam'
    self.ExpectMatrixStatus(matrix_id, M_PENDING, [PENDING, PENDING])
    monitor = self.CreateMatrixMonitor(matrix_id, self.args)

    with self.assertRaises(exceptions.TestExecutionNotFoundError) as ex_ctx:
      monitor._GetTestExecutionStatus('kam_test9')
    self.assertEqual(
        six.text_type(ex_ctx.exception),
        'Test execution [kam_test9] not found in matrix [kam].')

  def testMatrixMonitor_MonitorMatrixProgress_ExitsIfMatrixFinished(self):
    m_id = 'matrix9'
    self.ExpectMatrixStatus(m_id, M_FINISHED, [FINISHED, FINISHED, FINISHED])
    monitor = self.CreateMatrixMonitor(m_id, self.args)

    monitor.MonitorTestMatrixProgress()

    self.AssertStatusEquals(['Finished:3 '])
    self.AssertOutputEquals('')

  def testMatrixMonitor_MonitorMatrixProgress_ExitsIfMatrixInvalid(self):
    m_id = 'matrix9'
    self.ExpectMatrixStatus(m_id, M_INVALID, [INVALID, INVALID])
    monitor = self.CreateMatrixMonitor(m_id, self.args)

    monitor.MonitorTestMatrixProgress()

    self.AssertStatusEquals(['Invalid:2 '])
    self.AssertOutputEquals('')

  def testMatrixMonitor_MonitorMatrixProgress_ExitsIfMatrixCancelled(self):
    m_id = 'matrix9'
    self.ExpectMatrixStatus(m_id, M_PENDING, [PENDING, PENDING])
    self.ExpectMatrixStatus(m_id, M_PENDING, [PENDING, RUNNING])
    self.ExpectMatrixStatus(m_id, M_RUNNING, [RUNNING, RUNNING])
    self.ExpectMatrixStatus(m_id, M_RUNNING, [RUNNING, CANCEL])
    self.ExpectMatrixStatus(m_id, M_CANCEL, [CANCEL, CANCEL])
    monitor = self.CreateMatrixMonitor(m_id, self.args)

    monitor.MonitorTestMatrixProgress()

    self.AssertStatusEquals(['Pending:2 ',
                             'Pending:1 Running:1 ',
                             'Running:2           ',
                             'Cancelled:1 Running:1 ',
                             'Cancelled:2           '])
    self.AssertOutputEquals('')

  def testMatrixMonitor_MonitorMatrixProgress_ExitsIfMatrixError(self):
    m_id = 'matrix9'
    self.ExpectMatrixStatus(m_id, M_PENDING, [PENDING, PENDING, PENDING])
    self.ExpectMatrixStatus(m_id, M_PENDING, [PENDING, ERROR, PENDING])
    self.ExpectMatrixStatus(m_id, M_ERROR, [ERROR, ERROR, ERROR])
    monitor = self.CreateMatrixMonitor(m_id, self.args)

    monitor.MonitorTestMatrixProgress()

    self.AssertStatusEquals(['Pending:3 ',
                             'Error:1 Pending:2 ',
                             'Error:3           '])
    self.AssertOutputEquals('')

  def testMatrixMonitor_MonitorMatrixProgress_SimpleProgression(self):
    m_id = 'matrix9'
    self.ExpectMatrixStatus(m_id, M_PENDING, [PENDING, PENDING, PENDING])
    self.ExpectMatrixStatus(m_id, M_PENDING, [PENDING, RUNNING, PENDING])
    self.ExpectMatrixStatus(m_id, M_PENDING, [RUNNING, RUNNING, PENDING])
    self.ExpectMatrixStatus(m_id, M_RUNNING, [RUNNING, FINISHED, RUNNING])
    self.ExpectMatrixStatus(m_id, M_FINISHED, [FINISHED, FINISHED, FINISHED])
    monitor = self.CreateMatrixMonitor(m_id, self.args)

    monitor.MonitorTestMatrixProgress()

    self.AssertStatusEquals(['Pending:3 ',
                             'Pending:2 Running:1 ',
                             'Pending:1 Running:2 ',
                             'Finished:1 Running:2 ',
                             'Finished:3           '])
    self.AssertOutputEquals('')

  def testMatrixMonitor_MonitorMatrixProgress_ComplicatedProgression(self):
    m_id = 'matrix9'
    self.ExpectMatrixStatus(m_id, M_VALID, [PENDING, PENDING, SKIP, VALID])
    self.ExpectMatrixStatus(m_id, M_PENDING, [RUNNING, RUNNING, SKIP, PENDING])
    self.ExpectMatrixStatus(m_id, M_RUNNING, [RUNNING, RUNNING, SKIP, ERROR])
    self.ExpectMatrixStatus(m_id, M_RUNNING, [RUNNING, RUNNING, SKIP, ERROR])
    self.ExpectMatrixStatus(m_id, M_RUNNING, [RUNNING, FINISHED, SKIP, ERROR])
    self.ExpectMatrixStatus(m_id, M_FINISHED, [CANCEL, FINISHED, SKIP, ERROR])
    monitor = self.CreateMatrixMonitor(m_id, self.args)

    monitor.MonitorTestMatrixProgress()

    self.AssertStatusEquals(['Pending:2 Unsupported:1 Validating:1 ',
                             'Pending:1 Running:2 Unsupported:1    ',
                             'Error:1 Running:2 Unsupported:1      ',
                             'Error:1 Running:2 Unsupported:1      ',
                             'Error:1 Finished:1 Running:1 Unsupported:1 ',
                             'Cancelled:1 Error:1 Finished:1 Unsupported:1 ',
                            ])
    self.AssertOutputEquals('')

  def testMatrixMonitor_MonitorTestProgress_TestErrorImmediately(self):
    m_id = 'the-matrix'
    test_id = 'pats'
    progress1 = ['handoff']
    self.ExpectTestStatus(m_id, M_PENDING, test_id, ERROR, 'fumble', progress1)
    monitor = self.CreateMatrixMonitor(m_id, self.args)

    with self.assertRaises(exceptions.TestLabInfrastructureError) as ex_ctx:
      monitor.MonitorTestExecutionProgress(test_id)

    self.AssertOutputEquals('')
    self.AssertErrEquals('09:26:53 handoff\n')
    self.assertEqual(
        six.text_type(ex_ctx.exception),
        'Firebase Test Lab infrastructure failure: fumble')

  def testMatrixMonitor_MonitorTestProgress_TestErrorLater(self):
    """Simulate the test state going from PENDING to RUNNING to ERROR."""
    m_id = 'the-matrix'
    test_id = 'brady'
    progress1 = ['Huddle\n']
    progress2 = ['Huddle\n', 'Hike\n']
    progress3 = ['Huddle\n', 'Hike\n', 'Pass\n']
    error1 = 'interception'
    self.ExpectTestStatus(m_id, M_PENDING, test_id, PENDING, None, None)
    self.ExpectTestStatus(m_id, M_PENDING, test_id, PENDING, None, progress1)
    self.ExpectTestStatus(m_id, M_PENDING, test_id, RUNNING, None, progress2)
    self.ExpectTestStatus(m_id, M_PENDING, test_id, RUNNING, None, progress3)
    self.ExpectTestStatus(m_id, M_PENDING, test_id, ERROR, error1, progress3)
    monitor = self.CreateMatrixMonitor(m_id, self.args)

    with self.assertRaises(exceptions.TestLabInfrastructureError) as ex_ctx:
      monitor.MonitorTestExecutionProgress(test_id)

    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
09:26:53 Test is Pending
09:26:53 Huddle
09:26:53 Hike
09:26:53 Test is Running
09:26:53 Pass
""")
    self.assertEqual(
        six.text_type(ex_ctx.exception),
        'Firebase Test Lab infrastructure failure: interception')

  def testMatrixMonitor_MonitorTestProgress_EnvironmentIsUnsupported(self):
    m_id = 'the-matrix'
    test_id = 'cardinals'
    self.ExpectTestStatus(m_id, M_PENDING, test_id, SKIP, None, ['lateral'])
    monitor = self.CreateMatrixMonitor(m_id, self.args)

    with self.assertRaises(exceptions.AllDimensionsIncompatibleError) as ex_ctx:
      monitor.MonitorTestExecutionProgress(test_id)

    self.AssertOutputEquals('')
    self.AssertErrEquals('09:26:53 lateral\n')
    self.assertIn('dimensions are not compatible',
                  six.text_type(ex_ctx.exception))
    self.assertIn('[OS-version 10 on Nexus0]', six.text_type(ex_ctx.exception))

  def testMatrixMonitor_MonitorTestProgress_TestFinishes(self):
    """Simulate the test state going from PENDING to RUNNING to FINISHED.

    Note: some of the intermediate states having unchanged progress details.
    """
    m_id = 'the-matrix'
    test_id = 'wilson'
    progress1 = ['Huddle']
    progress2 = ['Huddle', 'Hike\n']
    progress3 = ['Huddle', 'Hike\n', 'Scramble']
    progress4 = ['Huddle', 'Hike\n', 'Scramble', 'Pass\n']
    progress5 = ['Huddle', 'Hike\n', 'Scramble', 'Pass', 'Touchdown!', 'Spike']
    self.ExpectTestStatus(m_id, M_PENDING, test_id, PENDING, None, None)
    self.ExpectTestStatus(m_id, M_PENDING, test_id, PENDING, None, progress1)
    self.ExpectTestStatus(m_id, M_PENDING, test_id, PENDING, None, progress1)
    self.ExpectTestStatus(m_id, M_PENDING, test_id, PENDING, None, progress2)
    self.ExpectTestStatus(m_id, M_PENDING, test_id, RUNNING, None, progress2)
    self.ExpectTestStatus(m_id, M_PENDING, test_id, RUNNING, None, progress3)
    self.ExpectTestStatus(m_id, M_PENDING, test_id, RUNNING, None, progress4)
    self.ExpectTestStatus(m_id, M_PENDING, test_id, FINISHED, None, progress5)
    self.ExpectTestStatus(m_id, M_PENDING, test_id, FINISHED, None, progress5)
    self.ExpectTestStatus(m_id, M_FINISHED, test_id, FINISHED, None, progress5)
    monitor = self.CreateMatrixMonitor(m_id, self.args)

    monitor.MonitorTestExecutionProgress(test_id)

    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
09:26:53 Test is Pending
09:26:53 Huddle
09:26:53 Hike
09:26:53 Test is Running
09:26:53 Scramble
09:26:53 Pass
09:26:53 Touchdown!
09:26:53 Spike
09:26:53 Test is Finished

Instrumentation testing complete.
""")

  def testMatrixMonitor_CancelTestMatrix_GetsHttpError(self):
    matrix_id = 'matrix-206'
    monitor = self.CreateMatrixMonitor(matrix_id, self.args)
    self.testing_client.projects_testMatrices.Cancel.Expect(
        request=self.testing_msgs.TestingProjectsTestMatricesCancelRequest(
            projectId=self.PROJECT_ID, testMatrixId=matrix_id),
        exception=test_utils.MakeHttpError('oops', 'Simulated cancel failure'))

    # An HttpError from the rpc should be converted to an HttpException
    with self.assertRaises(calliope_exceptions.HttpException) as ex_ctx:
      monitor.CancelTestMatrix()
    self.assertIn('Simulated cancel failure', ex_ctx.exception.message)

  def testMatrixMonitor_CancelTestMatrix_Succeeds(self):
    matrix_id = 'matrix-425'
    monitor = self.CreateMatrixMonitor(matrix_id, self.args)
    self.testing_client.projects_testMatrices.Cancel.Expect(
        request=self.testing_msgs.TestingProjectsTestMatricesCancelRequest(
            projectId=self.PROJECT_ID,
            testMatrixId=matrix_id),
        response=self.testing_msgs.CancelTestMatrixResponse())

    monitor.CancelTestMatrix()

    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def ExpectTestStatus(self, matrix_id, matrix_state,
                       test_id, state, error, progress_msgs):
    """Add a mocked response for a single test execution in a matrix."""
    test_exec = self.NewTestExecution(test_id, state, error, progress_msgs)
    matrix = self.NewTestMatrix(matrix_id, None, matrix_state,
                                [test_exec], None, None)

    self.testing_client.projects_testMatrices.Get.Expect(
        request=self.testing_msgs.TestingProjectsTestMatricesGetRequest(
            projectId=self.PROJECT_ID,
            testMatrixId=matrix_id),
        response=matrix)

  def AssertStatusEquals(self, status_list):
    prefix = '\r09:26:53 Test matrix status: '
    end = '\nInstrumentation testing complete.\n'
    status_str = ''
    for status in status_list:
      status_str += prefix + status
    self.AssertErrEquals(status_str + end)


if __name__ == '__main__':
  test_case.main()
