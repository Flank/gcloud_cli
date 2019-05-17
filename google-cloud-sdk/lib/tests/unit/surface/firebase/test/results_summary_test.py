# -*- coding: utf-8 -*- #
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

"""Tests for googlecloudsdk.api_lib.firebase.test.results_summary."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import exit_code
from googlecloudsdk.api_lib.firebase.test import results_summary
from googlecloudsdk.api_lib.firebase.test import tool_results
from googlecloudsdk.api_lib.firebase.test import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import resource_printer
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.android import unit_base


TOOLRESULTS_MESSAGES = apis.GetMessagesModule('toolresults', 'v1beta3')

TEST_OUTCOME_FORMAT = util.OUTCOMES_FORMAT
FLAKY_ATTEMPTS_OUTCOME_FORMAT = util.FLAKY_ATTEMPTS_OUTCOMES_FORMAT

HISTORY_ID = 'bh.1'
EXECUTION_ID = '5'

DIMENSIONS = [
    TOOLRESULTS_MESSAGES.StepDimensionValueEntry(
        key='Model', value='Nexus'),
    TOOLRESULTS_MESSAGES.StepDimensionValueEntry(
        key='Locale', value='en'),
    TOOLRESULTS_MESSAGES.StepDimensionValueEntry(
        key='Version', value='v1'),
    TOOLRESULTS_MESSAGES.StepDimensionValueEntry(
        key='Orientation', value='up'),
    ]

MULTI_STEP_0 = TOOLRESULTS_MESSAGES.MultiStep(
    multistepNumber=0,
    primaryStep=TOOLRESULTS_MESSAGES.PrimaryStep(
        rollUp=TOOLRESULTS_MESSAGES.PrimaryStep.RollUpValueValuesEnum.flaky
    )
)
MULTI_STEP_1 = TOOLRESULTS_MESSAGES.MultiStep(multistepNumber=1)

SUMMARY_ENUM = TOOLRESULTS_MESSAGES.Outcome.SummaryValueValuesEnum
SUCCESS = SUMMARY_ENUM.success
FLAKY = SUMMARY_ENUM.flaky
FAILURE = SUMMARY_ENUM.failure
INCONCLUSIVE = SUMMARY_ENUM.inconclusive
SKIPPED = SUMMARY_ENUM.skipped

SUCCESS_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=SUCCESS)
SUCCESS_NATIVE_CRASH_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=SUCCESS,
    successDetail=TOOLRESULTS_MESSAGES.SuccessDetail(otherNativeCrash=True))
FLAKY_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(summary=FLAKY)
FAILURE_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=FAILURE,
    failureDetail=TOOLRESULTS_MESSAGES.FailureDetail())
FAILURE_CRASH_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=FAILURE,
    failureDetail=TOOLRESULTS_MESSAGES.FailureDetail(crashed=True))
FAILURE_NATIVE_CRASH_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=FAILURE,
    failureDetail=TOOLRESULTS_MESSAGES.FailureDetail(otherNativeCrash=True))
FAILURE_TIMEOUT_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=FAILURE,
    failureDetail=TOOLRESULTS_MESSAGES.FailureDetail(timedOut=True))
FAILURE_TIMEOUT_WITH_NATIVE_CRASH_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=FAILURE,
    failureDetail=TOOLRESULTS_MESSAGES.FailureDetail(timedOut=True,
                                                     otherNativeCrash=True))
FAILURE_INSTALL_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=FAILURE,
    failureDetail=TOOLRESULTS_MESSAGES.FailureDetail(notInstalled=True))
INCONCLUSIVE_INFRA_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=INCONCLUSIVE,
    inconclusiveDetail=TOOLRESULTS_MESSAGES.InconclusiveDetail(
        infrastructureFailure=True))
INCONCLUSIVE_ABORTED_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=INCONCLUSIVE,
    inconclusiveDetail=TOOLRESULTS_MESSAGES.InconclusiveDetail(
        abortedByUser=True))
SKIPPED_DEVICE_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=SKIPPED,
    skippedDetail=TOOLRESULTS_MESSAGES.SkippedDetail(incompatibleDevice=True))
SKIPPED_VERSION_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=SKIPPED,
    skippedDetail=TOOLRESULTS_MESSAGES.SkippedDetail(
        incompatibleAppVersion=True))
SKIPPED_ARCH_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=SKIPPED,
    skippedDetail=TOOLRESULTS_MESSAGES.SkippedDetail(
        incompatibleArchitecture=True))
UNSET_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(
    summary=SUMMARY_ENUM.unset)

EMPTY_OVERVIEW = TOOLRESULTS_MESSAGES.TestSuiteOverview()
PASS_OVERVIEW1 = TOOLRESULTS_MESSAGES.TestSuiteOverview(
    skippedCount=1,
    totalCount=9)
PASS_OVERVIEW2 = TOOLRESULTS_MESSAGES.TestSuiteOverview(
    totalCount=13)
FAIL_OVERVIEW1 = TOOLRESULTS_MESSAGES.TestSuiteOverview(
    failureCount=2,
    totalCount=5)
FAIL_OVERVIEW2 = TOOLRESULTS_MESSAGES.TestSuiteOverview(
    failureCount=3,
    errorCount=2,
    skippedCount=1,
    totalCount=8)


class ResultsSummaryTest(unit_base.AndroidMockClientTest):
  """Unit tests for the results summmary class."""

  def SetUp(self):
    console_attr.GetConsoleAttr(encoding='ascii')

  def TearDown(self):
    console_attr.ResetConsoleAttr()

  def testNoResultsAvailable(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(steps=[]))

    summary = summary_fetcher.CreateMatrixOutcomeSummary()

    self.assertEqual([], summary)
    self.AssertErrEquals("""\
WARNING: No results found, something went wrong. Try re-running the tests.
""")

  def testStepOutcomeIsMissing(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    # Create step with missing outcome
    step = self._createStep(None, [EMPTY_OVERVIEW])
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(steps=[step]))

    outcomes = summary_fetcher.CreateMatrixOutcomeSummary()

    self.assertEqual(len(outcomes), 0)
    self.AssertErrContains('no outcome')

  def testResultsForOneDimension(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    step = self._createStep(FAILURE_TIMEOUT_OUTCOME, [FAIL_OVERVIEW1])
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(steps=[step]))

    outcomes = summary_fetcher.CreateMatrixOutcomeSummary()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains('| OUTCOME | TEST_AXIS_VALUE | TEST_DETAILS |',
                              normalize_space=True)
    self.AssertOutputContains('| Failed | Nexus-v1-en-up | Test timed out |',
                              normalize_space=True)
    self.AssertErrEquals('')

  def testResultsForFlakyAttempts(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    step1 = self._createPrimaryStep(FAILURE_OUTCOME, [FAIL_OVERVIEW1])
    step2 = self._createRerunStep(SUCCESS_OUTCOME, [PASS_OVERVIEW1])
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(steps=[step1, step2]))

    outcomes = summary_fetcher.CreateFlakyAttemptsMatrixOutcomeSummary()
    resource_printer.Print(outcomes, FLAKY_ATTEMPTS_OUTCOME_FORMAT)

    self.AssertOutputContains(
        '| OUTCOME | TEST_AXIS_VALUE | PASSED_EXECUTIONS |',
        normalize_space=True)
    self.AssertOutputContains('| Flaky | Nexus-v1-en-up | 50% (1 of 2) |',
                              normalize_space=True)
    self.AssertErrEquals('')

  def testResultsForPassedFlakyAttempts(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    step = self._createStep(SUCCESS_OUTCOME, [PASS_OVERVIEW1])
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(steps=[step]))

    outcomes = summary_fetcher.CreateFlakyAttemptsMatrixOutcomeSummary()
    resource_printer.Print(outcomes, FLAKY_ATTEMPTS_OUTCOME_FORMAT)

    self.AssertOutputContains(
        '| OUTCOME | TEST_AXIS_VALUE | PASSED_EXECUTIONS |',
        normalize_space=True)
    self.AssertOutputContains('| Passed | Nexus-v1-en-up | 100% (1 of 1) |',
                              normalize_space=True)
    self.AssertErrEquals('')

  def testResultsWithMultipleDimensions(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    step1 = self._createStep(FAILURE_CRASH_OUTCOME, [FAIL_OVERVIEW1])
    step2 = self._createStep(SUCCESS_OUTCOME, [PASS_OVERVIEW1])
    step3 = self._createStep(INCONCLUSIVE_INFRA_OUTCOME, [EMPTY_OVERVIEW])
    step4 = self._createStep(FAILURE_INSTALL_OUTCOME, [EMPTY_OVERVIEW])
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(
            steps=[step1, step2, step3, step4]))

    outcomes = summary_fetcher.CreateMatrixOutcomeSummary()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        """Failed | Nexus-v1-en-up | App failed to install |
        | Failed | Nexus-v1-en-up | Application crashed |
        | Passed | Nexus-v1-en-up | 9 test cases passed |
        | Inconclusive | Nexus-v1-en-up | Infrastructure failure |""",
        normalize_space=True)
    self.AssertErrContains('Slack channel')
    self.AssertErrContains('[{0}]'.format(EXECUTION_ID))

  def testResultsWithSkippedDimensions(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    step1 = self._createStep(SUCCESS_OUTCOME, [PASS_OVERVIEW2])
    step2 = self._createStep(SKIPPED_DEVICE_OUTCOME, [EMPTY_OVERVIEW])
    step3 = self._createStep(INCONCLUSIVE_ABORTED_OUTCOME, [EMPTY_OVERVIEW])
    step4 = self._createStep(SKIPPED_VERSION_OUTCOME, [EMPTY_OVERVIEW])
    step5 = self._createStep(SKIPPED_ARCH_OUTCOME, [EMPTY_OVERVIEW])
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(
            steps=[step1, step2, step3, step4, step5]))

    outcomes = summary_fetcher.CreateMatrixOutcomeSummary()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        """Passed | Nexus-v1-en-up | 13 test cases passed |
        | Inconclusive | Nexus-v1-en-up | Test run aborted by user |
        | Skipped | Nexus-v1-en-up | App does not support the OS version |
        | Skipped | Nexus-v1-en-up | App does not support the device \
        architecture |
        | Skipped | Nexus-v1-en-up | Incompatible device/OS combination |""",
        normalize_space=True)
    self.AssertErrEquals('')

  def testResultsSuccessWithNativeCrashOutcome(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    step = self._createStep(SUCCESS_NATIVE_CRASH_OUTCOME, [EMPTY_OVERVIEW])
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(
            steps=[step]))

    outcomes = summary_fetcher.CreateMatrixOutcomeSummary()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        'Passed | Nexus-v1-en-up | -- (Native crash)',
        normalize_space=True)
    self.AssertErrContains('native process crashed')

  def testResultsFailureWithNativeCrashOutcome(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    step = self._createStep(FAILURE_NATIVE_CRASH_OUTCOME, [FAIL_OVERVIEW1])
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(
            steps=[step]))

    outcomes = summary_fetcher.CreateMatrixOutcomeSummary()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        'Failed | Nexus-v1-en-up | Native crash',
        normalize_space=True)
    self.AssertErrContains('native process crashed')

  def testResultsFailureTimeoutWithNativeCrashOutcome(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    step = self._createStep(FAILURE_TIMEOUT_WITH_NATIVE_CRASH_OUTCOME,
                            [EMPTY_OVERVIEW])
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(
            steps=[step]))

    outcomes = summary_fetcher.CreateMatrixOutcomeSummary()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        'Failed | Nexus-v1-en-up | Test timed out (Native crash)',
        normalize_space=True)
    self.AssertErrContains('native process crashed')

  def testResultsInconclusiveWithInfrastructureFailureOutcome(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    step = self._createStep(INCONCLUSIVE_INFRA_OUTCOME, [EMPTY_OVERVIEW])
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(steps=[step]))

    outcomes = summary_fetcher.CreateMatrixOutcomeSummary()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        'Inconclusive | Nexus-v1-en-up | Infrastructure failure',
        normalize_space=True)
    self.AssertErrContains('Slack channel')
    self.AssertErrContains('[{0}]'.format(EXECUTION_ID))

  def testResultsWithPagination(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    step1 = self._createStep(FAILURE_OUTCOME, [FAIL_OVERVIEW1])
    step2 = self._createStep(FAILURE_OUTCOME, [FAIL_OVERVIEW2])
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(
            nextPageToken='token', steps=[step1]))
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest('token'),
        response=self.toolresults_msgs.ListStepsResponse(steps=[step2]))

    outcomes = summary_fetcher.CreateMatrixOutcomeSummary()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        """Failed | Nexus-v1-en-up | 2 test cases failed, 3 passed |
        | Failed | Nexus-v1-en-up | 3 test cases failed, 2 passed, 2 errors, \
        1 skipped""",
        normalize_space=True)

  def testResultsWithMultipleTestSuites(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    step1 = self._createStep(SUCCESS_OUTCOME, [PASS_OVERVIEW1, PASS_OVERVIEW2])
    step2 = self._createStep(FAILURE_OUTCOME, [FAIL_OVERVIEW1, FAIL_OVERVIEW2])
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(steps=[step1, step2]))

    outcomes = summary_fetcher.CreateMatrixOutcomeSummary()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        """Failed | Nexus-v1-en-up | 5 test cases failed, 5 passed, 2 errors, \
        1 skipped |
        | Passed | Nexus-v1-en-up | 22 test cases passed""",
        normalize_space=True)

  def testFetchTestRollupOutcome_HttpErrorOccurs(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    self.tr_client.projects_histories_executions.Get.Expect(
        request=self._createHistoriesExecutionsRequest(),
        exception=test_utils.MakeHttpError(
            'kablooie', "Outcome? We don't need no stinkin' rollup outcome."))

    with self.assertRaises(calliope_exceptions.HttpException):
      summary_fetcher.FetchMatrixRollupOutcome()

  def testFetchTestRollupOutcome_Success(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    self.tr_client.projects_histories_executions.Get.Expect(
        request=self._createHistoriesExecutionsRequest(),
        response=self.toolresults_msgs.Execution(
            executionId=EXECUTION_ID, outcome=SUCCESS_OUTCOME))

    outcome = summary_fetcher.FetchMatrixRollupOutcome()

    self.assertEqual(outcome, SUCCESS_OUTCOME)

  def testFetchTestRollupOutcome_Success_VerifyExitCode(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    self._expectHistoriesExecutionsGet(SUCCESS_OUTCOME)

    exc = exit_code.ExitCodeFromRollupOutcome(
        summary_fetcher.FetchMatrixRollupOutcome(), SUMMARY_ENUM)

    self.assertEqual(exc, exit_code.ROLLUP_SUCCESS)

  def testFetchTestRollupOutcome_Flaky_VerifyExitCode(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    self._expectHistoriesExecutionsGet(FLAKY_OUTCOME)

    exc = exit_code.ExitCodeFromRollupOutcome(
        summary_fetcher.FetchMatrixRollupOutcome(), SUMMARY_ENUM)

    self.assertEqual(exc, exit_code.ROLLUP_SUCCESS)

  def testFetchTestRollupOutcome_SuccessWithNativeCrash_VerifyExitCode(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    self._expectHistoriesExecutionsGet(SUCCESS_NATIVE_CRASH_OUTCOME)

    exc = exit_code.ExitCodeFromRollupOutcome(
        summary_fetcher.FetchMatrixRollupOutcome(), SUMMARY_ENUM)

    self.assertEqual(exc, exit_code.ROLLUP_SUCCESS)

  def testFetchTestRollupOutcome_Failure_VerifyExitCode(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    self._expectHistoriesExecutionsGet(FAILURE_CRASH_OUTCOME)

    exc = exit_code.ExitCodeFromRollupOutcome(
        summary_fetcher.FetchMatrixRollupOutcome(), SUMMARY_ENUM)

    self.assertEqual(exc, exit_code.ROLLUP_FAILURE)

  def testFetchTestRollupOutcome_InconclusiveInfra_VerifyExitCode(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    self._expectHistoriesExecutionsGet(INCONCLUSIVE_INFRA_OUTCOME)

    exc = exit_code.ExitCodeFromRollupOutcome(
        summary_fetcher.FetchMatrixRollupOutcome(), SUMMARY_ENUM)

    self.assertEqual(exc, exit_code.INCONCLUSIVE)

  def testFetchTestRollupOutcome_UnsetOutcome_ThrowsToolOutcomeError(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    self._expectHistoriesExecutionsGet(UNSET_OUTCOME)

    with self.assertRaises(exit_code.TestOutcomeError):
      exit_code.ExitCodeFromRollupOutcome(
          summary_fetcher.FetchMatrixRollupOutcome(), SUMMARY_ENUM)

  def testFetchTestRollupOutcome_MissingOutcome(self):
    exc = exit_code.ExitCodeFromRollupOutcome(None, SUMMARY_ENUM)

    self.assertEqual(exc, exit_code.INCONCLUSIVE)
    self.AssertErrContains('did not provide a roll-up')

  def _createResultsSummaryFetcher(self):
    return results_summary.ToolResultsSummaryFetcher(
        self.PROJECT_ID,
        self.tr_client,
        self.toolresults_msgs,
        tool_results.ToolResultsIds(HISTORY_ID, EXECUTION_ID))

  def _createStep(self, outcome, overviews):
    execution_step = self.toolresults_msgs.TestExecutionStep(
        testSuiteOverviews=overviews)
    return self.toolresults_msgs.Step(name='Bonobo test',
                                      dimensionValue=DIMENSIONS,
                                      outcome=outcome,
                                      testExecutionStep=execution_step)

  def _createPrimaryStep(self, outcome, overviews):
    execution_step = self.toolresults_msgs.TestExecutionStep(
        testSuiteOverviews=overviews)
    return self.toolresults_msgs.Step(name='Bonobo test',
                                      dimensionValue=DIMENSIONS,
                                      outcome=outcome,
                                      testExecutionStep=execution_step,
                                      multiStep=MULTI_STEP_0)

  def _createRerunStep(self, outcome, overviews):
    execution_step = self.toolresults_msgs.TestExecutionStep(
        testSuiteOverviews=overviews)
    return self.toolresults_msgs.Step(name='Bonobo test',
                                      dimensionValue=DIMENSIONS,
                                      outcome=outcome,
                                      testExecutionStep=execution_step,
                                      multiStep=MULTI_STEP_1)

  def _createStepsListRequest(self, token):
    return (self.toolresults_msgs
            .ToolresultsProjectsHistoriesExecutionsStepsListRequest(
                projectId=self.PROJECT_ID,
                historyId=HISTORY_ID,
                executionId=EXECUTION_ID,
                pageSize=100,
                pageToken=token))

  def _createHistoriesExecutionsRequest(self):
    return (
        self.toolresults_msgs.ToolresultsProjectsHistoriesExecutionsGetRequest(
            projectId=self.PROJECT_ID,
            historyId=HISTORY_ID,
            executionId=EXECUTION_ID))

  def _expectHistoriesExecutionsGet(self, outcome):
    self.tr_client.projects_histories_executions.Get.Expect(
        request=self._createHistoriesExecutionsRequest(),
        response=self.toolresults_msgs.Execution(executionId=EXECUTION_ID,
                                                 outcome=outcome))


if __name__ == '__main__':
  test_case.main()
