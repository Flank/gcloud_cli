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
"""Base classes for all 'gcloud test' unit tests."""

import datetime

from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.firebase.test import history_picker
from googlecloudsdk.api_lib.firebase.test import matrix_ops
from googlecloudsdk.api_lib.firebase.test.android import matrix_creator
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error

_PROJECT_ID = 'superbowl'
TEST_DATA_PATH = sdk_test_base.SdkBase.Resource('tests', 'unit', 'surface',
                                                'firebase', 'test', 'testdata')

TESTING_V1_MSGS = core_apis.GetMessagesModule('testing', 'v1')
CATALOG_GET_REQUEST = TESTING_V1_MSGS.TestingTestEnvironmentCatalogGetRequest(
    environmentType=(TESTING_V1_MSGS.TestingTestEnvironmentCatalogGetRequest.
                     EnvironmentTypeValueValuesEnum.ANDROID),
    projectId=_PROJECT_ID)
NETWORK_GET_REQUEST = TESTING_V1_MSGS.TestingTestEnvironmentCatalogGetRequest(
    environmentType=(TESTING_V1_MSGS.TestingTestEnvironmentCatalogGetRequest.
                     EnvironmentTypeValueValuesEnum.NETWORK_CONFIGURATION),
    projectId=_PROJECT_ID)

ALL_GA_TEST_RUN_ARGS = [
    'app', 'app_initial_activity', 'app_package', 'async', 'auto_google_login',
    'device', 'device_ids', 'directories_to_pull', 'environment_variables',
    'locales', 'max_depth', 'max_steps', 'network_profile', 'obb_files',
    'orientations', 'os_version_ids', 'performance_metrics', 'record_video',
    'results_bucket', 'results_dir', 'results_history_name', 'robo_directives',
    'test', 'test_package', 'test_runner_class', 'test_targets', 'timeout',
    'type', 'use_orchestrator'
]

ALL_TEST_RUN_ARGS = {
    'ga':
        ALL_GA_TEST_RUN_ARGS,
    'beta':
        ALL_GA_TEST_RUN_ARGS +
        ['scenario_numbers', 'scenario_labels', 'robo_script']
}


def FakeDateTime():
  return datetime.datetime(2015, 3, 14, 9, 26, 53, 589793)


class _Base(cli_test_base.CliTestBase):
  """Base class for all 'gcloud test' unit tests.

  Attributes:
    PROJECT_ID: a default cloud project ID for unit tests.
  """
  PROJECT_ID = _PROJECT_ID


class TestUnitTestBase(_Base, sdk_test_base.WithFakeAuth,
                       sdk_test_base.WithOutputCapture):
  """Base class for all 'gcloud test' unit tests."""

  def NewTestArgs(self, release_track='ga', **kwargs):
    """Create a Namespace containing attributes for all `test run` args.

    All args, for the specified release track, except those appearing in
    **kwargs are set to None by default so that unit tests won't get missing
    attribute errors.

    Args:
      release_track: a map of release track (ga or beta) to all `test run` args.
      **kwargs: a map of any args which should have values other than None.
    Returns:
      The created argparse.Namespace instance.
    """
    arg_dict = {arg: None for arg in ALL_TEST_RUN_ARGS[release_track]}
    arg_dict['argspec'] = None  # Positional args don't have a CLI flag name
    arg_dict.update(kwargs)
    return parser_extensions.Namespace(**arg_dict)


class TestMockClientTest(TestUnitTestBase):
  """Base class for all 'gcloud test' tests using mocked ApiTools clients.

  Attributes:
    testing_client: mocked ApiTools client for the Testing API.
    tr_client: mocked ApiTools client for the ToolResults API.
    context: the gcloud command context (a str:value dict) which holds common
      initialization values, such as the client and messages objects generated
      from the Testing API definition by ApiTools.
    args: an argparse.Namespace initialized with a minimal set of args required
      by the Testing service backend.
    picker: a ToolResultsHistoryPicker created with the mocked tr_client.
  """

  def SetUp(self):
    properties.VALUES.core.project.Set(self.PROJECT_ID)

    self.testing_client = api_mock.Client(
        core_apis.GetClientClass('testing', 'v1'))
    self.testing_client.Mock()
    self.addCleanup(self.testing_client.Unmock)
    self.testing_msgs = TESTING_V1_MSGS

    self.tr_client = api_mock.Client(
        core_apis.GetClientClass('toolresults', 'v1beta3'))
    self.tr_client.Mock()
    self.addCleanup(self.tr_client.Unmock)
    self.toolresults_msgs = core_apis.GetMessagesModule('toolresults',
                                                        'v1beta3')

    self.storage_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.storage_client.Mock()
    self.addCleanup(self.storage_client.Unmock)
    self.storage_msgs = core_apis.GetMessagesModule('storage', 'v1')

    self.context = {
        'testing_client': self.testing_client,
        'testing_messages': self.testing_msgs,
    }

    self.args = self.NewTestArgs(
        type='instrumentation',
        app='sea/hawks.apk',
        test='sea/hawks-test.apk',
        device_ids=['Nexus0'],
        os_version_ids=['10'],
        locales=['fr'],
        orientations=['portrait'],
        results_bucket='oak',
        results_dir='dir')

    self.picker = history_picker.ToolResultsHistoryPicker(
        self.PROJECT_ID, self.tr_client,
        core_apis.GetMessagesModule('toolresults', 'v1beta3'))

  def CreateMatrixCreator(self,
                          args,
                          history_id='hist1',
                          release_track=base.ReleaseTrack.GA.id):
    """Construct and return a MatrixCreator object with a mocked client.

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
        clock=FakeDateTime,
        status_interval_secs=0)

  def NewTestExecution(self, test_id, state, error_msg, progress_msgs):
    """Build a server-side version of a TestExecution message."""
    device = self.testing_msgs.AndroidDevice(
        androidModelId=self.args.device_ids[0],
        androidVersionId=self.args.os_version_ids[0],
        locale=self.args.locales[0],
        orientation=self.args.orientations[0])
    test_exec = self.testing_msgs.TestExecution(
        id=test_id,
        state=state,
        testSpecification=None,
        environment=self.testing_msgs.Environment(androidDevice=device))
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
                         hist_id='superbowl.49',
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

  def ExpectCatalogGet(self, mock_catalog):
    """Expect a testEnvironmentCatalog.Get call with a mock_catalog response."""
    self.testing_client.testEnvironmentCatalog.Get.Expect(
        request=CATALOG_GET_REQUEST,
        response=self.testing_msgs.TestEnvironmentCatalog(
            androidDeviceCatalog=mock_catalog))

  def ExpectCatalogGetError(self, error):
    """Expect a testEnvironmentCatalog.Get call with a mocked error response."""
    self.testing_client.testEnvironmentCatalog.Get.Expect(
        request=CATALOG_GET_REQUEST, exception=error)

  def ExpectNetworkCatalogGet(self, mock_catalog):
    """Expect a testEnvironmentCatalog.Get call with a mock_catalog response."""
    self.testing_client.testEnvironmentCatalog.Get.Expect(
        request=NETWORK_GET_REQUEST,
        response=self.testing_msgs.TestEnvironmentCatalog(
            networkConfigurationCatalog=mock_catalog))

  def ExpectNetworkCatalogGetError(self, error):
    """Expect a testEnvironmentCatalog.Get call with a mocked error response."""
    self.testing_client.testEnvironmentCatalog.Get.Expect(
        request=NETWORK_GET_REQUEST, exception=error)

  def CheckArgNamesForHyphens(self, arg_rules):
    args = (arg_rules['required'] + arg_rules['optional'] +
            arg_rules['defaults'].keys())
    for arg in args:
      self.assertNotIn('-', arg, 'arg names in rules should use underscores')


def MakeHttpError(reason, message, code=404):
  """Create an exceptions.HttpError with a specified reason and message.

  The HttpError is of the form that would be thrown by an apitools RPC.

  Args:
    reason: str, the specified reason
    message: str, the specified message
    code: int, the http error code

  Returns:
    the generated HttpError
  """
  individual_error = {
      'reason': reason,
      'message': message,
      'location': '<dummy location>',
      'debugInfo': '<dummy debug info>'
  }
  error_list_dict = {
      'errors': [individual_error],
      'code': code,
      'message': message
  }
  server_error = {'error': error_list_dict}
  return http_error.MakeHttpError(code=code, message=message, reason=reason,
                                  content=server_error)
