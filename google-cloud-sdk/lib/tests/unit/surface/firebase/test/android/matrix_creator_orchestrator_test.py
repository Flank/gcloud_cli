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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import uuid
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import config
from tests.lib import test_case
from tests.lib.surface.firebase.test.android import commands
from tests.lib.surface.firebase.test.android import fake_catalogs
from tests.lib.surface.firebase.test.android import unit_base

PROJECT_ID = 'superbowl'
DEFAULT_BUCKET = 'default-bucket'
UNIQUE_OBJECT_NAME = 'unique-object-name'
REQUEST_ID = '12345678123456781234567812345678'
APP = 'path/to/app.apk'
TEST = 'path/to/test.apk'
APK_SIZE = 1000
ORCHESTRATOR_OPTION_ENUMS = (apis.GetMessagesModule(
    'testing',
    'v1').AndroidInstrumentationTest.OrchestratorOptionValueValuesEnum)

GOOD_ARGS = os.path.join(unit_base.TEST_DATA_PATH, 'good_args')


class MatrixCreatorOrchestratorTests(unit_base.AndroidMockClientTest):
  """Unit tests for converting orchestrator flag to OrchestratorOption."""

  def BuildMatrix(self, orchestrator_option, test_matrix_id=None):
    return self.testing_msgs.TestMatrix(
        testMatrixId=test_matrix_id,
        clientInfo=self.testing_msgs.ClientInfo(
            name='gcloud',
            clientInfoDetails=[
                self.testing_msgs.ClientInfoDetail(
                    key='Cloud SDK Version', value=config.CLOUD_SDK_VERSION),
                self.testing_msgs.ClientInfoDetail(
                    key='Release Track',
                    value=calliope_base.ReleaseTrack.GA.id),
            ]),
        environmentMatrix=self.testing_msgs.EnvironmentMatrix(
            androidMatrix=self.testing_msgs.AndroidMatrix(
                androidModelIds=['Nexus5'],
                androidVersionIds=['F'],
                locales=['ro'],
                orientations=['askew'])),
        resultStorage=self.testing_msgs.ResultStorage(
            googleCloudStorage=self.testing_msgs.GoogleCloudStorage(
                gcsPath='gs://{db}/{ub}/'.format(
                    db=DEFAULT_BUCKET, ub=UNIQUE_OBJECT_NAME)),
            toolResultsHistory=self.testing_msgs.ToolResultsHistory(
                projectId=PROJECT_ID)),
        testSpecification=self.testing_msgs.TestSpecification(
            androidInstrumentationTest=self.testing_msgs
            .AndroidInstrumentationTest(
                appApk=self.testing_msgs.FileReference(
                    gcsPath='gs://{db}/{ub}/app.apk'.format(
                        db=DEFAULT_BUCKET, ub=UNIQUE_OBJECT_NAME)),
                orchestratorOption=orchestrator_option,
                testApk=self.testing_msgs.FileReference(
                    gcsPath='gs://{db}/{ub}/test.apk'.format(
                        db=DEFAULT_BUCKET, ub=UNIQUE_OBJECT_NAME))),
            testSetup=self.testing_msgs.TestSetup(
                account=self.testing_msgs.Account(
                    googleAuto=self.testing_msgs.GoogleAuto())),
            disableVideoRecording=False,
            disablePerformanceMetrics=False,
            testTimeout='900s'))

  def ExpectMatrixOrchestratorOption(self, orchestrator_option):
    test_matrix_id = 'test-matrix-id'
    history_id = 'history-id'
    execution_id = 'execution-id'
    self.testing_client.projects_testMatrices.Create.Expect(
        request=self.testing_msgs.TestingProjectsTestMatricesCreateRequest(
            projectId=PROJECT_ID,
            requestId=REQUEST_ID,
            testMatrix=self.BuildMatrix(orchestrator_option)),
        response=self.BuildMatrix(
            orchestrator_option, test_matrix_id=test_matrix_id))
    self.ExpectMatrixStatus(
        test_matrix_id,
        self.testing_msgs.TestMatrix.StateValueValuesEnum.FINISHED,
        [self.testing_msgs.TestExecution.StateValueValuesEnum.FINISHED],
        hist_id=history_id,
        exec_id=execution_id)
    self.ExpectMatrixStatus(
        test_matrix_id,
        self.testing_msgs.TestMatrix.StateValueValuesEnum.FINISHED,
        [self.testing_msgs.TestExecution.StateValueValuesEnum.FINISHED],
        hist_id=history_id,
        exec_id=execution_id)
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

  def SetUp(self):
    self.ExpectCatalogGet(fake_catalogs.FakeAndroidCatalog())
    self.StartPatch(
        ('googlecloudsdk.api_lib.firebase.test.arg_validate'
         '._GenerateUniqueGcsObjectName'),
        return_value=UNIQUE_OBJECT_NAME)
    self.StartPatch('os.path.getsize', return_value=APK_SIZE)
    app_object = self.storage_msgs.Object(kind='storage#object', size=APK_SIZE)
    self.StartPatch(
        'apitools.base.py.transfer.Upload.FromFile', return_value=app_object)
    self.tr_client.projects.InitializeSettings.Expect(
        request=self.toolresults_msgs.
        ToolresultsProjectsInitializeSettingsRequest(projectId=PROJECT_ID),
        response=self.toolresults_msgs.ProjectSettings(
            defaultBucket=DEFAULT_BUCKET, name=''))
    self.storage_client.objects.Insert.Expect(
        request=self.storage_msgs.StorageObjectsInsertRequest(
            bucket=DEFAULT_BUCKET,
            name='{b}/app.apk'.format(b=UNIQUE_OBJECT_NAME),
            object=app_object),
        response=app_object)
    test_object = self.storage_msgs.Object(kind='storage#object', size=APK_SIZE)
    self.storage_client.objects.Insert.Expect(
        request=self.storage_msgs.StorageObjectsInsertRequest(
            bucket=DEFAULT_BUCKET,
            name='{b}/test.apk'.format(b=UNIQUE_OBJECT_NAME),
            object=test_object),
        response=test_object)
    self.StartPatch('uuid.uuid4', return_value=uuid.UUID(REQUEST_ID))

  def testMatrixCreatorOrchestrator_UseOrchestrator(self):
    self.ExpectMatrixOrchestratorOption(
        ORCHESTRATOR_OPTION_ENUMS.USE_ORCHESTRATOR)
    self.Run('{cmd} --use-orchestrator --app {app} --test {test} '
             '--device-ids=Nexus5'.format(
                 cmd=commands.ANDROID_TEST_RUN, app=APP, test=TEST))

  def testMatrixCreatorOrchestrator_NoUseOrchestrator(self):
    self.ExpectMatrixOrchestratorOption(
        ORCHESTRATOR_OPTION_ENUMS.DO_NOT_USE_ORCHESTRATOR)
    self.Run('{cmd} --no-use-orchestrator --app {app} --test {test} '
             '--device-ids=Nexus5'.format(
                 cmd=commands.ANDROID_TEST_RUN, app=APP, test=TEST))

  def testMatrixCreatorOrchestrator_Unspecified(self):
    self.ExpectMatrixOrchestratorOption(
        ORCHESTRATOR_OPTION_ENUMS.ORCHESTRATOR_OPTION_UNSPECIFIED)
    self.Run('{cmd} --app {app} --test {test} --device-ids=Nexus5'.format(
        cmd=commands.ANDROID_TEST_RUN, app=APP, test=TEST))

  def testMatrixCreatorOrchestrator_UseOrchestratorTrueFromArgFile(self):
    self.ExpectMatrixOrchestratorOption(
        ORCHESTRATOR_OPTION_ENUMS.USE_ORCHESTRATOR)
    self.Run('{cmd} {argfile}:use-orchestrator-true --app {app} --test {test} '
             '--device-ids=Nexus5'.format(
                 cmd=commands.ANDROID_TEST_RUN,
                 argfile=GOOD_ARGS,
                 app=APP,
                 test=TEST))

  def testMatrixCreatorOrchestrator_UseOrchestratorFalseFromArgFile(self):
    self.ExpectMatrixOrchestratorOption(
        ORCHESTRATOR_OPTION_ENUMS.DO_NOT_USE_ORCHESTRATOR)
    self.Run('{cmd} {argfile}:use-orchestrator-false --app {app} --test {test} '
             '--device-ids=Nexus5'.format(
                 cmd=commands.ANDROID_TEST_RUN,
                 argfile=GOOD_ARGS,
                 app=APP,
                 test=TEST))

  def testMatrixCreatorOrchestrator_UnspecifiedFromArgFile(self):
    self.ExpectMatrixOrchestratorOption(
        ORCHESTRATOR_OPTION_ENUMS.ORCHESTRATOR_OPTION_UNSPECIFIED)
    self.Run('{cmd} {argfile}:use-orchestrator-unspecified --app {app} --test '
             '{test} --device-ids=Nexus5'.format(
                 cmd=commands.ANDROID_TEST_RUN,
                 argfile=GOOD_ARGS,
                 app=APP,
                 test=TEST))


if __name__ == '__main__':
  test_case.main()
