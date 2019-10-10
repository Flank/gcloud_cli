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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os
import uuid
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.firebase.test.ios import commands
from tests.lib.surface.firebase.test.ios import fake_catalogs
from tests.lib.surface.firebase.test.ios import unit_base

PROJECT_ID = 'superbowl'
MATRIX_ID = 'matrix-ios1'
HISTORY_ID = 'hist-2'
TR_EXECUTION_ID = 'tr-3'
DEFAULT_BUCKET = 'ios-bucket'
UNIQUE_OBJECT = 'unique-val'
REQUEST_ID = '12345678123456781234567812345678'
TEST_ZIP = 'bundle.zip'
TEST_PATH = 'path/to/' + TEST_ZIP
ZIP_SIZE = 999

TESTING_MESSAGES = apis.GetMessagesModule('testing', 'v1')
M_PENDING = TESTING_MESSAGES.TestMatrix.StateValueValuesEnum.PENDING
M_FINISHED = TESTING_MESSAGES.TestMatrix.StateValueValuesEnum.FINISHED
FINISHED = TESTING_MESSAGES.TestExecution.StateValueValuesEnum.FINISHED
RUNNING = TESTING_MESSAGES.TestExecution.StateValueValuesEnum.RUNNING
VALIDATING = TESTING_MESSAGES.TestExecution.StateValueValuesEnum.VALIDATING

DEFAULT_DEVICE = TESTING_MESSAGES.IosDevice(
    iosModelId='iPen2', iosVersionId='6.0', locale='ro', orientation='askew')
DEVICE_1 = TESTING_MESSAGES.IosDevice(
    iosModelId='iPencil1', iosVersionId='6.0', locale='ro', orientation='askew')
DEVICE_2 = TESTING_MESSAGES.IosDevice(
    iosModelId='iPen3', iosVersionId='7.2', locale='kl', orientation='askew')

GOOD_ARGS = os.path.join(unit_base.TEST_DATA_PATH, 'good_args')


class FirebaseTestIosRunTests(unit_base.IosMockClientTest):
  """Unit tests for `gcloud firebase test ios run` command."""

  def BuildRequestMatrix(self, project, devices, timeout, xcode_version):
    """Build a client-side version of a TestMatrix proto."""
    return self.testing_msgs.TestMatrix(
        clientInfo=self.testing_msgs.ClientInfo(
            name='gcloud',
            clientInfoDetails=[
                self.testing_msgs.ClientInfoDetail(
                    key='Cloud SDK Version', value=config.CLOUD_SDK_VERSION),
                self.testing_msgs.ClientInfoDetail(
                    key='Release Track', value=str('GA')),
            ]),
        environmentMatrix=self.testing_msgs.EnvironmentMatrix(
            iosDeviceList=self.testing_msgs.IosDeviceList(iosDevices=devices)),
        resultStorage=self.testing_msgs.ResultStorage(
            googleCloudStorage=self.testing_msgs.GoogleCloudStorage(
                gcsPath='gs://{db}/{uo}/'.format(
                    db=self.results_bucket, uo=self.results_dir)),
            toolResultsHistory=self.testing_msgs.ToolResultsHistory(
                projectId=project)),
        testSpecification=self.testing_msgs.TestSpecification(
            iosXcTest=self.testing_msgs.IosXcTest(
                testsZip=self.testing_msgs
                .FileReference(gcsPath='gs://{db}/{uo}/{tz}'.format(
                    db=self.results_bucket, uo=self.results_dir, tz=TEST_ZIP)),
                xcodeVersion=xcode_version),
            iosTestSetup=self.testing_msgs.IosTestSetup(),
            disableVideoRecording=False,
            testTimeout=timeout),
        flakyTestAttempts=0)

  def BuildResponseMatrix(self, request_matrix, m_id, m_state):
    """Build a server-side TestMatrix from a client-side TestMatrix proto."""
    new_matrix = copy.deepcopy(request_matrix)
    devices = new_matrix.environmentMatrix.iosDeviceList.iosDevices
    executions = []
    for i, device in enumerate(devices):
      exec_id = '{m}_test{n}'.format(m=new_matrix.testMatrixId, n=i)
      executions.append(self.BuildTestExecution(exec_id, device))
    new_matrix.testExecutions = executions
    new_matrix.testMatrixId = m_id
    new_matrix.state = m_state
    new_matrix.resultStorage.toolResultsExecution = \
      self.testing_msgs.ToolResultsExecution(
          projectId=new_matrix.projectId,
          historyId=HISTORY_ID,
          executionId=TR_EXECUTION_ID)
    return new_matrix

  def BuildTestExecution(self, test_id, device, state=FINISHED):
    """Build a server-side version of a TestExecution proto."""
    return self.testing_msgs.TestExecution(
        id=test_id,
        environment=self.testing_msgs.Environment(iosDevice=device),
        state=state,
        testSpecification=None)

  def ExpectMatrixGet(self, old_matrix, new_matrix_state, new_exec_states):
    """Add a modified mock response to a TestMatrices.Get request."""
    new_matrix = copy.deepcopy(old_matrix)
    new_matrix.state = new_matrix_state
    for i, new_exec_state in enumerate(new_exec_states):
      new_matrix.testExecutions[i].state = new_exec_state
    self.testing_client.projects_testMatrices.Get.Expect(
        request=self.testing_msgs.TestingProjectsTestMatricesGetRequest(
            projectId=self.PROJECT_ID, testMatrixId=new_matrix.testMatrixId),
        response=new_matrix)

  def ExpectMatrixCreate(self,
                         devices,
                         project=PROJECT_ID,
                         matrix_state=M_FINISHED,
                         timeout='900s',
                         xcode_version=None):
    """Set expectations for iOS matrix creation; return the response matrix."""
    req_matrix = self.BuildRequestMatrix(project, devices, timeout,
                                         xcode_version)
    res_matrix = self.BuildResponseMatrix(req_matrix, MATRIX_ID, matrix_state)

    self.testing_client.projects_testMatrices.Create.Expect(
        request=self.testing_msgs.TestingProjectsTestMatricesCreateRequest(
            projectId=project, requestId=REQUEST_ID, testMatrix=req_matrix),
        response=res_matrix)
    return res_matrix

  def ExpectToolResults(self,
                        history_id=HISTORY_ID,
                        execution_id=TR_EXECUTION_ID):
    """Set expectations for ToolResults execution history Get/List rpcs."""
    self.tr_client.projects_histories_executions.Get.Expect(
        request=self.toolresults_msgs.
        ToolresultsProjectsHistoriesExecutionsGetRequest(
            projectId=PROJECT_ID,
            historyId=history_id,
            executionId=execution_id),
        response=self.toolresults_msgs.Execution(
            outcome=self.toolresults_msgs.Outcome(
                summary=self.toolresults_msgs.Outcome.SummaryValueValuesEnum.
                success)))
    self.tr_client.projects_histories_executions_steps.List.Expect(
        request=self.toolresults_msgs.
        ToolresultsProjectsHistoriesExecutionsStepsListRequest(
            projectId=PROJECT_ID,
            historyId=history_id,
            executionId=execution_id,
            pageSize=100),
        response=self.toolresults_msgs.ListStepsResponse())

  def ExpectInitializeSettings(self):
    """Expect a call to InitializeSettings rpc if default bucket is used."""
    self.tr_client.projects.InitializeSettings.Expect(
        request=self.toolresults_msgs.
        ToolresultsProjectsInitializeSettingsRequest(projectId=PROJECT_ID),
        response=self.toolresults_msgs.ProjectSettings(
            defaultBucket=self.results_bucket, name=''))

  def ExpectBucketGet(self, bucket_name):
    """Expect a call to storage Buckets.Get if a custom bucket is used."""
    self.storage_client.buckets.Get.Expect(
        request=self.storage_msgs.StorageBucketsGetRequest(bucket=bucket_name),
        response=self.storage_msgs.Bucket())

  def ExpectFileUpload(self, file_path):
    """Expect that the tests zip file is uploaded to GCS."""
    file_obj = self.storage_msgs.Object(kind='storage#object', size=ZIP_SIZE)
    self.storage_client.objects.Insert.Expect(
        request=self.storage_msgs.StorageObjectsInsertRequest(
            bucket=self.results_bucket,
            name='{uo}/{tz}'.format(uo=self.results_dir, tz=file_path),
            object=file_obj),
        response=file_obj)
    self.StartPatch(
        'apitools.base.py.transfer.Upload.FromFile', return_value=file_obj)

  def SetUp(self):
    """Set up patches/mocks for UUIDs, iOS catalog, results bucket & uploads."""
    self.results_bucket = DEFAULT_BUCKET
    self.results_dir = UNIQUE_OBJECT
    self.StartPatch('uuid.uuid4', return_value=uuid.UUID(REQUEST_ID))
    self.StartPatch(
        ('googlecloudsdk.api_lib.firebase.test.arg_validate'
         '._GenerateUniqueGcsObjectName'),
        return_value=UNIQUE_OBJECT)
    self.ExpectIosCatalogGet(fake_catalogs.FakeIosCatalog())
    self.StartPatch('os.path.getsize', return_value=ZIP_SIZE)
    properties.VALUES.test.matrix_status_interval.Set(1)

  # =========== Start of unit tests ============

  def testXcTest_AllDefaultArgs_MatrixFinishedImmediately(self):
    self.ExpectInitializeSettings()
    self.ExpectFileUpload(TEST_ZIP)
    matrix = self.ExpectMatrixCreate([DEFAULT_DEVICE])
    self.ExpectMatrixGet(matrix, M_FINISHED, [FINISHED])
    self.ExpectMatrixGet(matrix, M_FINISHED, [FINISHED])
    self.ExpectToolResults()

    self.Run('{run} --test {tz}'.format(
        run=commands.IOS_TEST_RUN, tz=TEST_PATH))
    self.AssertErrMatches(r'Upload.*bundle.zip')
    self.AssertErrContains('[matrix-ios1] has been created')
    self.AssertErrContains('test on 1 device(s)')
    self.AssertErrMatches(r'available.*\[https://.*/histories/hist-2.*/tr-3')

  def testXcTest_AllDefaultArgs_MatrixNotFinishedImmediately(self):
    self.ExpectInitializeSettings()
    self.ExpectFileUpload(TEST_ZIP)
    matrix = self.ExpectMatrixCreate([DEFAULT_DEVICE])
    self.ExpectMatrixGet(matrix, M_PENDING, [VALIDATING])
    self.ExpectMatrixGet(matrix, M_PENDING, [RUNNING])
    self.ExpectMatrixGet(matrix, M_FINISHED, [FINISHED])
    self.ExpectMatrixGet(matrix, M_FINISHED, [FINISHED])
    self.ExpectToolResults()

    self.Run('{run} --test {tz}'.format(
        run=commands.IOS_TEST_RUN, tz=TEST_PATH))
    self.AssertErrContains('[matrix-ios1] has been created')
    self.AssertErrContains('test on 1 device(s)')

  def testXcTest_ExplicitTestType_TwoDevices_Async(self):
    self.ExpectInitializeSettings()
    self.ExpectFileUpload(TEST_ZIP)
    self.ExpectMatrixCreate([DEVICE_1, DEVICE_2], timeout='300s')

    self.Run('{run} --type xctest --test {test} --timeout 5m --async '
             '--device model=iPencil1 '
             '--device model=iPen3,version=7.2,locale=kl'.format(
                 run=commands.IOS_TEST_RUN, test=TEST_PATH))
    self.AssertErrContains('[matrix-ios1] has been created')
    self.AssertErrContains('test on 2 device(s)')
    self.AssertErrNotContains('Xctest testing complete')
    self.AssertOutputMatches(r'results.*\[https://.*/histories/hist-2.*tr-3')

  def testXcTest_CustomResultsBucketAndDir(self):
    self.results_bucket = 'pail'
    self.results_dir = 'dir9'
    self.ExpectBucketGet('pail')
    self.ExpectFileUpload(TEST_ZIP)
    self.ExpectMatrixCreate([DEFAULT_DEVICE])

    self.Run('{run} --test={tz} --results-bucket=pail --results-dir=dir9 '
             '--async '.format(run=commands.IOS_TEST_RUN, tz=TEST_PATH))
    self.AssertErrMatches(r'Upload.*bundle.zip')
    self.AssertErrMatches(r'bucket.*/storage/browser/pail/dir9/]')
    self.AssertErrContains('[matrix-ios1] has been created')

  def testXcTest_SpecificXcodeVersion(self):
    self.ExpectInitializeSettings()
    self.ExpectFileUpload(TEST_ZIP)
    self.ExpectMatrixCreate([DEFAULT_DEVICE], xcode_version='9.2.0')

    self.Run('{run} --test={tz} --async --xcode-version=9.2.0'.format(
        run=commands.IOS_TEST_RUN, tz=TEST_PATH))
    self.AssertErrMatches(r'Upload.*bundle.zip')
    self.AssertErrContains('[matrix-ios1] has been created')

  def testXcTest_MostArgsReadFromYamlFile(self):
    self.results_dir = 'dir9'
    self.ExpectInitializeSettings()
    self.ExpectFileUpload(TEST_ZIP)
    self.ExpectMatrixCreate([DEVICE_2], timeout='600s')

    self.Run('{run} {argfile}:ios-xctest --test {test}'.format(
        run=commands.IOS_TEST_RUN, argfile=GOOD_ARGS, test=TEST_PATH))
    self.AssertErrContains('[matrix-ios1] has been created')
    self.AssertErrMatches(r'--test .*bundle.zip" overrides.* my_bundle.zip')


if __name__ == '__main__':
  test_case.main()
