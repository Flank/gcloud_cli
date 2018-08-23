# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
from tests.lib.surface.firebase.test.android import commands
from tests.lib.surface.firebase.test.android import fake_catalogs
from tests.lib.surface.firebase.test.android import unit_base

PROJECT_ID = 'superbowl'
MATRIX_ID = 'matrix-123'
HISTORY_ID = 'hist-2'
TR_EXECUTION_ID = 'tr-3'
DEFAULT_BUCKET = 'a-bucket'
UNIQUE_OBJECT = 'unique-val'
REQUEST_ID = '12345678123456781234567812345678'
APP_APK = 'app.apk'
TEST_APK = 'test.apk'
APP_PATH = 'path/to/' + APP_APK
TEST_PATH = 'path/to/' + TEST_APK
APK_SIZE = 999
OBB_FILE = 'patch.123.foo.com.obb'

TESTING_V1 = apis.GetMessagesModule('testing', 'v1')
M_PENDING = TESTING_V1.TestMatrix.StateValueValuesEnum.PENDING
M_FINISHED = TESTING_V1.TestMatrix.StateValueValuesEnum.FINISHED
VALIDATING = TESTING_V1.TestExecution.StateValueValuesEnum.VALIDATING
PENDING = TESTING_V1.TestExecution.StateValueValuesEnum.PENDING
RUNNING = TESTING_V1.TestExecution.StateValueValuesEnum.RUNNING
FINISHED = TESTING_V1.TestExecution.StateValueValuesEnum.FINISHED
ORCHESTRATOR_ENUMS = (
    TESTING_V1.AndroidInstrumentationTest.OrchestratorOptionValueValuesEnum)

DEFAULT_DEVICE = TESTING_V1.AndroidDevice(
    androidModelId='Universe3',
    androidVersionId='F',
    locale='ro',
    orientation='askew')
DEVICE_1 = TESTING_V1.AndroidDevice(
    androidModelId='Nexus2099',
    androidVersionId='P',
    locale='ro',
    orientation='askew')
DEVICE_2 = TESTING_V1.AndroidDevice(
    androidModelId='EsperiaXYZ',
    androidVersionId='C',
    locale='kl',
    orientation='wonky')

GOOD_ARGS = os.path.join(unit_base.TEST_DATA_PATH, 'good_args')


class FirebaseTestAndroidRunTests(unit_base.AndroidMockClientTest):
  """Unit tests for `gcloud firebase test android run` command."""

  def BuildRoboTestSpec(self, timeout='900s', video=False, metrics=False):
    """Build a TestSpecification for an AndroidRoboTest."""
    return self.testing_msgs.TestSpecification(
        androidRoboTest=self.testing_msgs.AndroidRoboTest(
            appApk=self.testing_msgs.FileReference(
                gcsPath='gs://{rb}/{uo}/{aa}'.format(
                    rb=self.results_bucket, uo=self.results_dir, aa=APP_APK)),
            maxDepth=50,
            maxSteps=-1),
        testSetup=self.testing_msgs.TestSetup(
            account=self.testing_msgs.Account(
                googleAuto=self.testing_msgs.GoogleAuto())),
        disableVideoRecording=video,
        disablePerformanceMetrics=metrics,
        testTimeout=timeout)

  def BuildInstrumentationTestSpec(self,
                                   timeout='900s',
                                   video=False,
                                   metrics=False,
                                   auto_login=False,
                                   obb_file=None):
    """Build a TestSpecification for an AndroidInstrumentationTest."""
    spec = self.testing_msgs.TestSpecification(
        androidInstrumentationTest=self.testing_msgs.AndroidInstrumentationTest(
            appApk=self.testing_msgs.FileReference(
                gcsPath='gs://{rb}/{uo}/{aa}'.format(
                    rb=self.results_bucket, uo=self.results_dir, aa=APP_APK)),
            testApk=self.testing_msgs.FileReference(
                gcsPath='gs://{rb}/{uo}/{ta}'.format(
                    rb=self.results_bucket, uo=self.results_dir, ta=TEST_APK)),
            orchestratorOption=ORCHESTRATOR_ENUMS.DO_NOT_USE_ORCHESTRATOR),
        testSetup=self.testing_msgs.TestSetup(),
        disableVideoRecording=video,
        disablePerformanceMetrics=metrics,
        testTimeout=timeout)

    if auto_login:
      spec.testSetup.account = self.testing_msgs.Account(
          googleAuto=self.testing_msgs.GoogleAuto())
    if obb_file:
      device_file = self.testing_msgs.DeviceFile(
          obbFile=self.testing_msgs.ObbFile(
              obbFileName=obb_file,
              obb=self.testing_msgs.
              FileReference(gcsPath='gs://{rb}/{uo}/{o}'.format(
                  rb=self.results_bucket, uo=self.results_dir, o=obb_file))))
      spec.testSetup.filesToPush = [device_file]
    return spec

  def BuildTestLoopSpec(self, scenarios, labels):
    """Build a TestSpecification for an AndroidTestLoop test."""
    return self.testing_msgs.TestSpecification(
        androidTestLoop=self.testing_msgs.AndroidTestLoop(
            appApk=self.testing_msgs.FileReference(
                gcsPath='gs://{rb}/{uo}/{aa}'.format(
                    rb=self.results_bucket, uo=self.results_dir, aa=APP_APK)),
            scenarios=scenarios,
            scenarioLabels=labels),
        testSetup=self.testing_msgs.TestSetup(),
        disableVideoRecording=False,
        disablePerformanceMetrics=False,
        testTimeout='900s')

  def BuildRequestMatrix(self, project, devices, spec):
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
            androidDeviceList=self.testing_msgs.AndroidDeviceList(
                androidDevices=devices)),
        resultStorage=self.testing_msgs.ResultStorage(
            googleCloudStorage=self.testing_msgs.GoogleCloudStorage(
                gcsPath='gs://{rb}/{uo}/'.format(
                    rb=self.results_bucket, uo=self.results_dir)),
            toolResultsHistory=self.testing_msgs.ToolResultsHistory(
                projectId=project)),
        testSpecification=spec)

  def BuildResponseMatrix(self, request_matrix, m_id, m_state):
    """Build a server-side TestMatrix from a client-side TestMatrix proto."""
    new_matrix = copy.deepcopy(request_matrix)
    devices = new_matrix.environmentMatrix.androidDeviceList.androidDevices
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
        environment=self.testing_msgs.Environment(androidDevice=device),
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
                         spec,
                         devices,
                         project=PROJECT_ID,
                         matrix_state=M_FINISHED):
    """Set expectations for testMatrices.Create; return the response matrix."""
    req_matrix = self.BuildRequestMatrix(project, devices, spec)
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
    file_obj = self.storage_msgs.Object(kind='storage#object', size=APK_SIZE)
    self.storage_client.objects.Insert.Expect(
        request=self.storage_msgs.StorageObjectsInsertRequest(
            bucket=self.results_bucket,
            name='{uo}/{tz}'.format(uo=self.results_dir, tz=file_path),
            object=file_obj),
        response=file_obj)
    self.StartPatch(
        'apitools.base.py.transfer.Upload.FromFile', return_value=file_obj)

  def SetUp(self):
    """Set up patches/mocks for an Android catalog, results bucket & uploads."""
    self.results_bucket = DEFAULT_BUCKET
    self.results_dir = UNIQUE_OBJECT
    self.StartPatch('uuid.uuid4', return_value=uuid.UUID(REQUEST_ID))
    self.StartPatch(
        ('googlecloudsdk.api_lib.firebase.test.arg_validate'
         '._GenerateUniqueGcsObjectName'),
        return_value=UNIQUE_OBJECT)
    self.ExpectCatalogGet(fake_catalogs.FakeAndroidCatalog())
    self.StartPatch('os.path.getsize', return_value=APK_SIZE)
    properties.VALUES.test.matrix_status_interval.Set(1)

  # =========== Start of unit tests ============

  def testRoboTest_AllDefaultArgs_MatrixFinishedImmediately(self):
    self.ExpectInitializeSettings()
    self.ExpectFileUpload(APP_APK)
    spec = self.BuildRoboTestSpec()
    matrix = self.ExpectMatrixCreate(spec, [DEFAULT_DEVICE])
    self.ExpectMatrixGet(matrix, M_FINISHED, [FINISHED])
    self.ExpectMatrixGet(matrix, M_FINISHED, [FINISHED])
    self.ExpectToolResults()

    self.Run('{run} --app {aa}'.format(
        run=commands.ANDROID_TEST_RUN, aa=APP_PATH))

    self.AssertErrMatches(r'Upload.*app.apk')
    self.AssertErrContains('[matrix-123] has been created')
    self.AssertErrContains('robo test on 1 device(s)')
    self.AssertErrMatches(r'available.*\[https://.*/histories/hist-2.*/tr-3')

  def testRoboTest_AllDefaultArgs_MatrixNotFinishedImmediately(self):
    self.ExpectInitializeSettings()
    self.ExpectFileUpload(APP_APK)
    spec = self.BuildRoboTestSpec()
    matrix = self.ExpectMatrixCreate(spec, [DEFAULT_DEVICE])
    self.ExpectMatrixGet(matrix, M_PENDING, [VALIDATING])
    self.ExpectMatrixGet(matrix, M_PENDING, [PENDING])
    self.ExpectMatrixGet(matrix, M_PENDING, [RUNNING])
    self.ExpectMatrixGet(matrix, M_FINISHED, [FINISHED])
    self.ExpectMatrixGet(matrix, M_FINISHED, [FINISHED])
    self.ExpectToolResults()

    self.Run('{run} --app {aa}'.format(
        run=commands.ANDROID_TEST_RUN, aa=APP_PATH))

    self.AssertErrContains('[matrix-123] has been created')
    self.AssertErrContains('Test is Validating')
    self.AssertErrContains('Test is Pending')
    self.AssertErrContains('Test is Running')
    self.AssertErrContains('Test is Finished')

  def testRoboTest_ExplicitTestType_TwoDevices_Async(self):
    self.ExpectInitializeSettings()
    self.ExpectFileUpload(APP_APK)
    spec = self.BuildRoboTestSpec(timeout='300s')
    self.ExpectMatrixCreate(spec, [DEVICE_1, DEVICE_2])

    self.Run('{run} --type robo --app {aa} --timeout 5m --async '
             '--device model=Nexus2099,version=P '
             '--device model=EsperiaXYZ,version=C,locale=kl,orientation=wonky '
             .format(run=commands.ANDROID_TEST_RUN, aa=APP_PATH))

    self.AssertErrContains('[matrix-123] has been created')
    self.AssertErrContains('robo test on 2 device(s)')
    self.AssertErrNotContains('Robo testing complete')
    self.AssertOutputMatches(r'results.*\[https://.*/histories/hist-2.*tr-3')

  def testRoboTest_CustomResultsBucketAndDir(self):
    self.results_bucket = 'pail'
    self.results_dir = 'dir9'
    self.ExpectBucketGet('pail')
    self.ExpectFileUpload(APP_APK)
    spec = self.BuildRoboTestSpec()
    self.ExpectMatrixCreate(spec, [DEFAULT_DEVICE])

    self.Run('{run} --app={aa} --results-bucket=pail --results-dir=dir9 '
             '--async '.format(run=commands.ANDROID_TEST_RUN, aa=APP_PATH))

    self.AssertErrMatches(r'bucket.*/storage/browser/pail/dir9/]')

  def testInstrumentationTest_OneDevice_MostArgsReadFromYamlFile(self):
    self.results_bucket = 'bucket-list'
    self.results_dir = 'duh'
    self.ExpectBucketGet('bucket-list')
    self.ExpectFileUpload(APP_APK)
    self.ExpectFileUpload(TEST_APK)
    spec = self.BuildInstrumentationTestSpec(timeout='600s')
    self.ExpectMatrixCreate(spec, [DEFAULT_DEVICE])

    self.Run('{run} {argfile}:android-instr --app={aa}'.format(
        run=commands.ANDROID_TEST_RUN, argfile=GOOD_ARGS, aa=APP_PATH))

    self.AssertErrContains('[matrix-123] has been created')
    self.AssertErrMatches(r'Upload.*path/to/app.apk')
    self.AssertErrMatches(r'Upload.*path/to/test.apk')
    self.AssertErrMatches(r'--app .*app.apk" overrides.* other-app.apk')
    self.AssertErrNotContains('Instrumentation testing complete')

  def testInstrumentationTest_ThreeDevices_MatrixNotFinishedImmediately(self):
    self.ExpectInitializeSettings()
    self.ExpectFileUpload(APP_APK)
    self.ExpectFileUpload(TEST_APK)
    self.ExpectFileUpload(OBB_FILE)
    spec = self.BuildInstrumentationTestSpec(
        video=True, metrics=True, auto_login=True, obb_file=OBB_FILE)
    matrix = self.ExpectMatrixCreate(spec, [DEVICE_2, DEVICE_1, DEFAULT_DEVICE])
    self.ExpectMatrixGet(matrix, M_PENDING, [VALIDATING])
    self.ExpectMatrixGet(matrix, M_PENDING, [PENDING])
    self.ExpectMatrixGet(matrix, M_PENDING, [RUNNING])
    self.ExpectMatrixGet(matrix, M_PENDING, [FINISHED])
    self.ExpectMatrixGet(matrix, M_FINISHED, [FINISHED])
    self.ExpectToolResults()

    self.Run(commands.ANDROID_TEST_RUN +
             '--type instrumentation  --app {aa} --test {ta} --obb-files={ob} '
             '--device model=EsperiaXYZ,version=C,locale=kl,orientation=wonky '
             '--device model=Nexus2099,version=P,locale=ro '
             '--device orientation=askew '
             '--no-record-video --no-performance-metrics --no-use-orchestrator'
             .format(aa=APP_PATH, ta=TEST_PATH, ob=OBB_FILE))

    self.AssertErrContains('instrumentation test on 3 device(s)')
    self.AssertErrContains('Instrumentation testing complete')

  def testLoopTest_AllDefaultArgs(self):
    self.ExpectInitializeSettings()
    self.ExpectFileUpload(APP_APK)
    spec = self.BuildTestLoopSpec([1, 5, 2], ['group1', 'group2'])
    self.ExpectMatrixCreate(spec, [DEFAULT_DEVICE])

    self.Run('{run} --type=game-loop  --app {aa} '
             '--async --no-auto-google-login '
             '--scenario-numbers=1,5,2  --scenario-labels=group1,group2 '
             .format(run=commands.ANDROID_TEST_RUN, aa=APP_PATH))

    self.AssertErrMatches(r'Upload.*app.apk')
    self.AssertErrContains('[matrix-123] has been created')
    self.AssertErrContains('game-loop test on 1 device(s)')


if __name__ == '__main__':
  test_case.main()
