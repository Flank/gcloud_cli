# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Base classes for all 'gcloud firebase test ios' unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import matrix_ops
from googlecloudsdk.api_lib.firebase.test.ios import matrix_creator
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test import unit_base

TEST_DATA_PATH = sdk_test_base.SdkBase.Resource('tests', 'unit', 'surface',
                                                'firebase', 'test', 'testdata')

TESTING_V1_MSGS = core_apis.GetMessagesModule('testing', 'v1')
IOS_ENV = (
    TESTING_V1_MSGS.TestingTestEnvironmentCatalogGetRequest.
    EnvironmentTypeValueValuesEnum.IOS)
IOS_CATALOG_GET = (
    TESTING_V1_MSGS.TestingTestEnvironmentCatalogGetRequest(
        environmentType=IOS_ENV,
        projectId=unit_base.TestUnitTestBase.PROJECT_ID))

ALL_GA_TEST_RUN_ARGS = [
    'app', 'async_', 'device', 'network_profile', 'num_flaky_test_attempts',
    'record_video', 'results_bucket', 'results_dir', 'results_history_name',
    'scenario_numbers', 'test', 'timeout', 'type', 'xcode_version',
    'xctestrun_file'
]

ALL_TEST_RUN_ARGS = {
    calliope_base.ReleaseTrack.GA:
        ALL_GA_TEST_RUN_ARGS,
    calliope_base.ReleaseTrack.BETA:
        ALL_GA_TEST_RUN_ARGS +
        ['client_details', 'test_special_entitlements', 'additional_ipas']
}


class IosUnitTestBase(unit_base.TestUnitTestBase):
  """Base class for all 'gcloud firebase test ios' unit tests."""

  def NewTestArgs(self, **kwargs):
    """Create a Namespace containing attributes for all `test ios run` args.

    All args, for the specified release track, except those appearing in
    **kwargs are set to None by default so that unit tests won't get missing
    attribute errors.

    Args:
      **kwargs: a map of any args which should have values other than None.
    Returns:
      The created argparse.Namespace instance.
    """
    return test_utils.NewNameSpace(ALL_TEST_RUN_ARGS[self.track], **kwargs)


class IosMockClientTest(unit_base.TestMockClientTest):
  """Base class for 'firebase test ios' tests using mocked ApiTools clients.

  Attributes:
    testing_client: mocked ApiTools client for the Testing API.
    tr_client: mocked ApiTools client for the ToolResults API.
    context: the gcloud command context (a str:value dict) which holds common
      initialization values, such as the client and messages objects generated
      from the Testing API definition by ApiTools.
    args: an argparse.Namespace initialized with a minimal set of args required
      by the Testing service backend.
  """

  def SetUp(self):
    self.CreateMockedClients()

    self.args = self.NewTestArgs(
        type='xctest',
        test='ios-test.zip',
        device=[{
            'model': 'ipod9',
            'version': 'ios2',
            'locale': 'en',
            'orientation': 'portrait'
        }],
        results_bucket='oak',
        results_dir='dir')

  def NewTestArgs(self, **kwargs):
    return test_utils.NewNameSpace(ALL_TEST_RUN_ARGS[self.track], **kwargs)

  def CreateMatrixCreator(self,
                          args,
                          history_id='hist1',
                          release_track=calliope_base.ReleaseTrack.GA.id):
    """Construct and return an iOS MatrixCreator object with a mocked client.

    Args:
      args: the argparse namespace holding all the command-line arg values.
      history_id: string containing the Tool Results history ID.
      release_track: the release track that the command is invoked from.

    Returns:
      The constructed MatrixCreator object.
    """
    gcs_results_root = ('gs://{b}/{o}/'.format(
        b=args.results_bucket, o=args.results_dir))
    return matrix_creator.MatrixCreator(args, self.context, history_id,
                                        gcs_results_root, release_track)

  def CreateMatrixMonitor(self, matrix_id, args):
    """Construct and return a MatrixMonitor object with a mocked client.

    Args:
      matrix_id: the unique ID of the test matrix.
      args: the argparse namespace holding all the command-line arg values.

    Returns:
      The constructed MatrixMonitor object.
    """
    return matrix_ops.MatrixMonitor(
        matrix_id,
        args.type,
        self.context,
        clock=test_utils.FakeDateTime,
        status_interval_secs=0)

  def NewTestExecution(self, test_id, state, error_msg, progress_msgs):
    """Build a server-side version of a TestExecution message."""
    device = self.testing_msgs.IosDevice(
        iosModelId=self.args.device[0]['model'],
        iosVersionId=self.args.device[0]['version'])
    test_exec = self.testing_msgs.TestExecution(
        id=test_id,
        state=state,
        testSpecification=None,
        environment=self.testing_msgs.Environment(iosDevice=device))
    if error_msg or progress_msgs:
      test_exec.testDetails = self.testing_msgs.TestDetails(
          errorMessage=error_msg, progressMessages=progress_msgs)
    else:
      test_exec.testDetails = None
    return test_exec

  def ExpectMatrixStatus(self,
                         matrix_id,
                         matrix_state,
                         test_states,
                         hist_id='hist1',
                         exec_id='id-1'):
    """Add a mocked response to a TestMatrices.Get request."""
    test_list = []
    for i, state in enumerate(test_states):
      test_id = '{m}_test{n}'.format(m=matrix_id, n=i)
      test_list.append(self.NewTestExecution(test_id, state, None, None))

    matrix = self.NewTestMatrix(matrix_id, None, matrix_state, test_list,
                                hist_id, exec_id)

    self.testing_client.projects_testMatrices.Get.Expect(
        request=self.testing_msgs.TestingProjectsTestMatricesGetRequest(
            projectId=self.PROJECT_ID, testMatrixId=matrix_id),
        response=matrix)

  def NewTestMatrix(self, matrix_id, spec, matrix_state, test_list, hist_id,
                    exec_id):
    """Create a minimal TestMatrix proto containing a list of TestExecutions."""
    creator = self.CreateMatrixCreator(self.args, history_id=hist_id)
    execution = self.testing_msgs.ToolResultsExecution(
        executionId=exec_id, historyId=hist_id)
    matrix = creator._BuildTestMatrix(spec)  # pylint: disable=protected-access
    matrix.testMatrixId = matrix_id
    matrix.projectId = self.PROJECT_ID
    matrix.state = matrix_state
    matrix.testExecutions = test_list
    matrix.resultStorage.toolResultsExecution = execution
    return matrix

  def ExpectIosCatalogGet(self, mock_catalog):
    """Expect an iOS testEnvironmentCatalog.Get with a mock_catalog response."""
    self.testing_client.testEnvironmentCatalog.Get.Expect(
        request=IOS_CATALOG_GET,
        response=self.testing_msgs.TestEnvironmentCatalog(
            iosDeviceCatalog=mock_catalog))

  def ExpectIosCatalogGetError(self, error):
    """Expect an iOS testEnvironmentCatalog.Get with a mocked error response."""
    self.testing_client.testEnvironmentCatalog.Get.Expect(
        request=IOS_CATALOG_GET, exception=error)
