# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

ENVIRONMENT_DIMENSIONS = [
    TOOLRESULTS_MESSAGES.EnvironmentDimensionValueEntry(
        key='Model', value='Nexus'),
    TOOLRESULTS_MESSAGES.EnvironmentDimensionValueEntry(
        key='Locale', value='en'),
    TOOLRESULTS_MESSAGES.EnvironmentDimensionValueEntry(
        key='Version', value='v1'),
    TOOLRESULTS_MESSAGES.EnvironmentDimensionValueEntry(
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
INCONCLUSIVE_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(summary=INCONCLUSIVE)
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
SKIPPED_OUTCOME = TOOLRESULTS_MESSAGES.Outcome(summary=SKIPPED)
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
FLAKY_OVERVIEW = TOOLRESULTS_MESSAGES.TestSuiteOverview(
    flakyCount=3, totalCount=4)


class ResultsSummaryTest(unit_base.AndroidMockClientTest):
  """Unit tests for the results summmary class."""

  def SetUp(self):
    console_attr.GetConsoleAttr(encoding='ascii')

  def TearDown(self):
    console_attr.ResetConsoleAttr()

  def testNoResultsAvailable(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    self._expectHistoriesExecutionsEnvironmentsList([])
    self._expectHistoriesExecutionsStepsList([])

    summary = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()

    self.assertEqual([], summary)
    self.AssertErrContains(
        """WARNING: Environment has no results, something went wrong. Displaying step outcomes instead."""
    )
    self.AssertErrContains(
        """WARNING: No test results found, something went wrong. Try re-running the tests."""
    )

  def testEnvironmentAndStepOutcomeIsMissing(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    # Create environment with missing outcome
    environment = self._createEnvironment(None, [EMPTY_OVERVIEW])
    self._expectHistoriesExecutionsEnvironmentsList([environment])
    self._expectHistoriesExecutionsStepsList([])

    outcomes = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()

    self.assertEqual(len(outcomes), 0)
    self.AssertErrContains('no outcome')
    self.AssertErrContains('Displaying step outcomes instead.')

  def testUseStepResultsIfNoEnvironmentResultsAreAvailable(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    self._expectHistoriesExecutionsEnvironmentsList([])

    step = self._createStep(FAILURE_TIMEOUT_OUTCOME, [FAIL_OVERVIEW1])
    self._expectHistoriesExecutionsStepsList([step])

    outcomes = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertErrContains(
        """WARNING: Environment has no results, something went wrong. Displaying step outcomes instead."""
    )
    self.AssertOutputContains('| OUTCOME | TEST_AXIS_VALUE | TEST_DETAILS |',
                              normalize_space=True)
    self.AssertOutputContains('| Failed | Nexus-v1-en-up | Test timed out |',
                              normalize_space=True)

  def testResultsForOneDimension(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    environment = self._createEnvironment(FAILURE_TIMEOUT_OUTCOME,
                                          [FAIL_OVERVIEW1])
    self._expectHistoriesExecutionsEnvironmentsList([environment])

    outcomes = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        '| OUTCOME | TEST_AXIS_VALUE | TEST_DETAILS |', normalize_space=True)
    self.AssertOutputContains(
        '| Failed | Nexus-v1-en-up | Test timed out |', normalize_space=True)
    self.AssertErrEquals('')

  def testResultsForFlakyEnvironment(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    environment = self._createEnvironment(FLAKY_OUTCOME, [FLAKY_OVERVIEW])
    self.tr_client.projects_histories_executions_environments.List.Expect(
        request=self._createEnvironmentsListRequest(None),
        response=self.toolresults_msgs.ListEnvironmentsResponse(
            environments=[environment]))

    outcomes = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        '| OUTCOME | TEST_AXIS_VALUE | TEST_DETAILS |', normalize_space=True)
    self.AssertOutputContains(
        '| Flaky | Nexus-v1-en-up | 3 test cases flaky, 1 passed |',
        normalize_space=True)
    self.AssertErrEquals('')

  def testResultsForPassedEnvironment(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    environment = self._createEnvironment(SUCCESS_OUTCOME, [PASS_OVERVIEW1])
    self._expectHistoriesExecutionsEnvironmentsList([environment])

    outcomes = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        '| OUTCOME | TEST_AXIS_VALUE | TEST_DETAILS |', normalize_space=True)
    self.AssertOutputContains(
        '| Passed | Nexus-v1-en-up | 8 test cases passed, 1 skipped |',
        normalize_space=True)
    self.AssertErrEquals('')

  def testResultsWithMultipleDimensions(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    environment1 = self._createEnvironment(FAILURE_CRASH_OUTCOME,
                                           [FAIL_OVERVIEW1])
    environment2 = self._createEnvironment(SUCCESS_OUTCOME, [PASS_OVERVIEW1])
    environment3 = self._createEnvironment(INCONCLUSIVE_INFRA_OUTCOME,
                                           [EMPTY_OVERVIEW])
    environment4 = self._createEnvironment(INCONCLUSIVE_OUTCOME,
                                           [EMPTY_OVERVIEW])
    environment5 = self._createEnvironment(FAILURE_INSTALL_OUTCOME,
                                           [EMPTY_OVERVIEW])
    self._expectHistoriesExecutionsEnvironmentsList(
        [environment1, environment2, environment3, environment4, environment5])

    outcomes = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        """Failed | Nexus-v1-en-up | App failed to install |
        | Failed | Nexus-v1-en-up | Application crashed |
        | Passed | Nexus-v1-en-up | 8 test cases passed, 1 skipped |
        | Inconclusive | Nexus-v1-en-up | Infrastructure failure |
        | Inconclusive | Nexus-v1-en-up | Unknown reason |""",
        normalize_space=True)
    self.AssertErrContains('Slack channel')
    self.AssertErrContains('[{0}]'.format(EXECUTION_ID))

  def testResultsWithSkippedDimensions(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    environment1 = self._createEnvironment(SUCCESS_OUTCOME, [PASS_OVERVIEW2])
    environment2 = self._createEnvironment(SKIPPED_DEVICE_OUTCOME,
                                           [EMPTY_OVERVIEW])
    environment3 = self._createEnvironment(INCONCLUSIVE_ABORTED_OUTCOME,
                                           [EMPTY_OVERVIEW])
    environment4 = self._createEnvironment(SKIPPED_VERSION_OUTCOME,
                                           [EMPTY_OVERVIEW])
    environment5 = self._createEnvironment(SKIPPED_ARCH_OUTCOME,
                                           [EMPTY_OVERVIEW])
    environment6 = self._createEnvironment(SKIPPED_OUTCOME, [EMPTY_OVERVIEW])
    self._expectHistoriesExecutionsEnvironmentsList([
        environment1, environment2, environment3, environment4, environment5,
        environment6
    ])

    outcomes = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        """Passed | Nexus-v1-en-up | 13 test cases passed |
        | Inconclusive | Nexus-v1-en-up | Test run aborted by user |
        | Skipped | Nexus-v1-en-up | App does not support the OS version |
        | Skipped | Nexus-v1-en-up | App does not support the device \
        architecture |
        | Skipped | Nexus-v1-en-up | Incompatible device/OS combination |
        | Skipped | Nexus-v1-en-up | Unknown reason |""",
        normalize_space=True)
    self.AssertErrEquals('')

  def testResultsSuccessWithNativeCrashOutcome(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    environment = self._createEnvironment(SUCCESS_NATIVE_CRASH_OUTCOME,
                                          [EMPTY_OVERVIEW])
    self._expectHistoriesExecutionsEnvironmentsList([environment])

    outcomes = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        'Passed | Nexus-v1-en-up | -- (Native crash)',
        normalize_space=True)
    self.AssertErrContains('native process crashed')

  def testResultsFailureWithNativeCrashOutcome(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    environment = self._createEnvironment(FAILURE_NATIVE_CRASH_OUTCOME,
                                          [FAIL_OVERVIEW1])
    self._expectHistoriesExecutionsEnvironmentsList([environment])

    outcomes = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        'Failed | Nexus-v1-en-up | Native crash',
        normalize_space=True)
    self.AssertErrContains('native process crashed')

  def testResultsFailureTimeoutWithNativeCrashOutcome(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    environment = self._createEnvironment(
        FAILURE_TIMEOUT_WITH_NATIVE_CRASH_OUTCOME, [EMPTY_OVERVIEW])
    self._expectHistoriesExecutionsEnvironmentsList([environment])

    outcomes = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        'Failed | Nexus-v1-en-up | Test timed out (Native crash)',
        normalize_space=True)
    self.AssertErrContains('native process crashed')

  def testResultsInconclusiveWithInfrastructureFailureOutcome(self):
    summary_fetcher = self._createResultsSummaryFetcher()
    environment = self._createEnvironment(INCONCLUSIVE_INFRA_OUTCOME,
                                          [EMPTY_OVERVIEW])
    self._expectHistoriesExecutionsEnvironmentsList([environment])

    outcomes = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        'Inconclusive | Nexus-v1-en-up | Infrastructure failure',
        normalize_space=True)
    self.AssertErrContains('Slack channel')
    self.AssertErrContains('[{0}]'.format(EXECUTION_ID))

  def testResultsWithPagination(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    environment1 = self._createEnvironment(FAILURE_OUTCOME, [FAIL_OVERVIEW1])
    environment2 = self._createEnvironment(FAILURE_OUTCOME, [FAIL_OVERVIEW2])
    self.tr_client.projects_histories_executions_environments.List.Expect(
        request=self._createEnvironmentsListRequest(None),
        response=self.toolresults_msgs.ListEnvironmentsResponse(
            nextPageToken='token', environments=[environment1]))
    self.tr_client.projects_histories_executions_environments.List.Expect(
        request=self._createEnvironmentsListRequest('token'),
        response=self.toolresults_msgs.ListEnvironmentsResponse(
            environments=[environment2]))

    outcomes = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        """Failed | Nexus-v1-en-up | 2 test cases failed, 3 passed |
        | Failed | Nexus-v1-en-up | 3 test cases failed, 2 passed, 2 errors, \
        1 skipped""",
        normalize_space=True)

  def testResultsWithMultipleTestSuites(self):
    summary_fetcher = self._createResultsSummaryFetcher()

    environment1 = self._createEnvironment(SUCCESS_OUTCOME,
                                           [PASS_OVERVIEW1, PASS_OVERVIEW2])
    environment2 = self._createEnvironment(FAILURE_OUTCOME,
                                           [FAIL_OVERVIEW1, FAIL_OVERVIEW2])
    self._expectHistoriesExecutionsEnvironmentsList(
        [environment1, environment2])

    outcomes = summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()
    resource_printer.Print(outcomes, TEST_OUTCOME_FORMAT)

    self.AssertOutputContains(
        """Failed | Nexus-v1-en-up | 5 test cases failed, 5 passed, 2 errors, \
        1 skipped |
        | Passed | Nexus-v1-en-up | 21 test cases passed, 1 skipped""",
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

  ### BELOW ARE HELPER METHODS ###

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

  def _createEnvironment(self, outcome, overviews):
    return self.toolresults_msgs.Environment(
        dimensionValue=ENVIRONMENT_DIMENSIONS,
        environmentResult=TOOLRESULTS_MESSAGES.MergedResult(
            outcome=outcome, testSuiteOverviews=overviews))

  def _createStepsListRequest(self, token):
    return (self.toolresults_msgs
            .ToolresultsProjectsHistoriesExecutionsStepsListRequest(
                projectId=self.PROJECT_ID,
                historyId=HISTORY_ID,
                executionId=EXECUTION_ID,
                pageSize=100,
                pageToken=token))

  def _createEnvironmentsListRequest(self, token):
    return (self.toolresults_msgs
            .ToolresultsProjectsHistoriesExecutionsEnvironmentsListRequest(
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

  def _expectHistoriesExecutionsEnvironmentsList(self, environments_list):
    self.tr_client.projects_histories_executions_environments.List.Expect(
        request=self._createEnvironmentsListRequest(None),
        response=self.toolresults_msgs.ListEnvironmentsResponse(
            environments=environments_list))

  def _expectHistoriesExecutionsStepsList(self, steps_list):
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self._createStepsListRequest(None),
        response=self.toolresults_msgs.ListStepsResponse(steps=steps_list))


if __name__ == '__main__':
  test_case.main()
