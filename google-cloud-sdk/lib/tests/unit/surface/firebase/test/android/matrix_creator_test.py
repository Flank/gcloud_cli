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

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.android import unit_base

TESTING_V1_MESSAGES = apis.GetMessagesModule('testing', 'v1')


class MatrixCreatorTests(unit_base.AndroidMockClientTest):
  """Unit tests for api_lib/test/android/matrix_creator.MatrixCreator."""

  def testMatrixCreator_ValidateTestMatrixRequest_NoHistoryId(self):
    creator = self.CreateMatrixCreator(self.args, history_id=None)
    req = creator._BuildTestMatrixRequest('id-1')
    self.assertEqual(req.testMatrix.resultStorage.toolResultsHistory.historyId,
                     None)

  def testMatrixCreator_ValidateTestMatrixRequest_HaveHistoryId(self):
    creator = self.CreateMatrixCreator(self.args, history_id='superbowl.48')
    req = creator._BuildTestMatrixRequest('id-2')
    self.assertEqual(req.testMatrix.resultStorage.toolResultsHistory.historyId,
                     'superbowl.48')

  def testMatrixCreator_ValidateTestMatrixRequest_OtherFields(self):
    args = self.NewTestArgs(
        type='instrumentation',
        app='sea/hawks.apk',
        test='sea/hawks-test.apk',
        device_ids=['football'],
        locales=['en_SEA'],
        orientations=['I-formation'],
        os_version_ids=['10'],
        auto_google_login=True,
        app_package='com.sea.hawks',
        test_package='com.sea.hawks.test',
        test_runner_class='beast.mode.runner',
        test_targets=['class d.baldwin', 'pkg j.kearse'],
        results_bucket='gatorade',
        results_dir='2015-02-24',
        results_history_name='superbowl.48',
        directories_to_pull=['/sdcard/lebron', '/sdcard/darius'],
        environment_variables={
            'coverage': 'true',
            'coverageFile': '/sdcard/tempDir'
        },
        obb_files=['gs://sea/hawks.obb', 'r/wilson.obb'],
        timeout=321,
        additional_apks=['gs://sea/apk1.apk', 'r/apk2.apk'],
        other_files={
            'gs://sea/file1': '/sdcard/dir1',
            'r/file2': '/sdcard/dir2'
        },
        num_flaky_test_attempts=1,
    )
    creator = self.CreateMatrixCreator(args)
    req = creator._BuildTestMatrixRequest('id-3')

    matrix = req.testMatrix
    self.assertEqual(req.projectId, self.PROJECT_ID)
    self.assertEqual(matrix.clientInfo.name, 'gcloud')
    self.assertEqual(matrix.resultStorage.googleCloudStorage.gcsPath,
                     'gs://gatorade/2015-02-24/')
    self.assertEqual(matrix.flakyTestAttempts, 1)

    spec = matrix.testSpecification
    self.assertEqual(spec.testTimeout, '321s')
    self.assertIsNotNone(spec.testSetup.account)
    self.assertIsNotNone(spec.testSetup.account.googleAuto)

    files_to_push = spec.testSetup.filesToPush
    self.assertEqual(len(files_to_push), 4)
    self.assertIn(
        self._BuildObbDeviceFile(
            'hawks.obb', 'gs://gatorade/2015-02-24/hawks.obb'), files_to_push)
    self.assertIn(
        self._BuildObbDeviceFile(
            'wilson.obb', 'gs://gatorade/2015-02-24/wilson.obb'), files_to_push)
    self.assertIn(
        self._BuildRegularDeviceFile('gs://gatorade/2015-02-24/file1',
                                     '/sdcard/dir1'), files_to_push)
    self.assertIn(
        self._BuildRegularDeviceFile('gs://gatorade/2015-02-24/file2',
                                     '/sdcard/dir2'), files_to_push)

    additional_apks = spec.testSetup.additionalApks
    self.assertEqual(len(additional_apks), 2)
    self.assertEqual(additional_apks[0].location.gcsPath,
                     'gs://gatorade/2015-02-24/apk1.apk')
    self.assertEqual(additional_apks[1].location.gcsPath,
                     'gs://gatorade/2015-02-24/apk2.apk')

    environment_variables = spec.testSetup.environmentVariables
    self.assertEqual(len(environment_variables), 2)

    env_var1 = TESTING_V1_MESSAGES.EnvironmentVariable(
        key='coverage', value='true')
    env_var2 = TESTING_V1_MESSAGES.EnvironmentVariable(
        key='coverageFile', value='/sdcard/tempDir')

    self.assertIn(env_var1, environment_variables)
    self.assertIn(env_var2, environment_variables)

    directories_to_pull = spec.testSetup.directoriesToPull
    self.assertEqual(directories_to_pull[0], '/sdcard/lebron')
    self.assertEqual(directories_to_pull[1], '/sdcard/darius')

    test = spec.androidInstrumentationTest
    self.assertEqual(test.appApk.gcsPath, 'gs://gatorade/2015-02-24/hawks.apk')
    self.assertEqual(test.testApk.gcsPath,
                     'gs://gatorade/2015-02-24/hawks-test.apk')
    self.assertEqual(test.appPackageId, 'com.sea.hawks')
    self.assertEqual(test.testPackageId, 'com.sea.hawks.test')
    self.assertEqual(test.testRunnerClass, 'beast.mode.runner')
    self.assertEqual(test.testTargets, ['class d.baldwin', 'pkg j.kearse'])

    devices = matrix.environmentMatrix.androidMatrix
    self.assertEqual(devices.androidModelIds, ['football'])
    self.assertEqual(devices.androidVersionIds, ['10'])
    self.assertEqual(devices.locales, ['en_SEA'])
    self.assertEqual(devices.orientations, ['I-formation'])

  def testMatrixCreator_AndroidRoboTest_ValidateRequestFields(self):
    args = self.NewTestArgs(
        type='robo',
        app='sea/hawks.apk',
        device=[{
            'model': 'bronco',
            'locale': 'NJ',
            'orientation': 'underdog',
            'version': '48'
        }],
        results_bucket='tin',
        results_dir='pail',
        obb_files=['/foo/bar.obb'],
        robo_directives={
            'click:resource1': '',
            'resource2': 'val2',
            'text:resource3': 'val3',
            'ignore:resource4': ''
        },
        robo_script='sea/HawksActivity_robo_script.json',
        timeout=321)
    creator = self.CreateMatrixCreator(args)

    req = creator._BuildTestMatrixRequest('id-5')

    devices = req.testMatrix.environmentMatrix.androidDeviceList.androidDevices
    self.assertEqual(len(devices), 1)
    self.assertEqual(devices[0].androidModelId, 'bronco')
    self.assertEqual(devices[0].androidVersionId, '48')
    self.assertEqual(devices[0].locale, 'NJ')
    self.assertEqual(devices[0].orientation, 'underdog')

    spec = req.testMatrix.testSpecification
    self.assertEqual(spec.testTimeout, '321s')

    test = spec.androidRoboTest
    robo_directives = test.roboDirectives
    action_types = TESTING_V1_MESSAGES.RoboDirective.ActionTypeValueValuesEnum
    self.assertEqual(len(robo_directives), 4)
    self.assertIn(
        TESTING_V1_MESSAGES.RoboDirective(
            resourceName='resource1',
            inputText='',
            actionType=action_types.SINGLE_CLICK), robo_directives)
    self.assertIn(
        TESTING_V1_MESSAGES.RoboDirective(
            resourceName='resource2',
            inputText='val2',
            actionType=action_types.ENTER_TEXT), robo_directives)
    self.assertIn(
        TESTING_V1_MESSAGES.RoboDirective(
            resourceName='resource3',
            inputText='val3',
            actionType=action_types.ENTER_TEXT), robo_directives)
    self.assertIn(
        TESTING_V1_MESSAGES.RoboDirective(
            resourceName='resource4',
            inputText='',
            actionType=action_types.IGNORE), robo_directives)

    self.assertEqual(test.roboScript.gcsPath,
                     'gs://tin/pail/HawksActivity_robo_script.json')

    obb_files = spec.testSetup.filesToPush
    self.assertEqual(len(obb_files), 1)
    self.assertEqual(
        self._BuildObbDeviceFile('bar.obb', 'gs://tin/pail/bar.obb'),
        obb_files[0])

  def testMatrixCreator_ValidateTestMatrixRequest_Fields(self):
    args = self.NewTestArgs(
        type='instrumentation',
        app='sea/hawks.apk',
        test='sea/hawks-test.apk',
        device_ids=['football'],
        locales=['en_SEA'],
        orientations=['I-formation'],
        os_version_ids=['10'],
        app_package='com.sea.hawks',
        test_package='com.sea.hawks.test',
        results_bucket='gatorade',
        results_dir='2015-02-24',
        timeout=321,
        network_profile='some-network-profile')
    creator = self.CreateMatrixCreator(args)
    req = creator._BuildTestMatrixRequest('id-3')

    matrix = req.testMatrix
    self.assertEqual(req.projectId, self.PROJECT_ID)
    self.assertEqual(matrix.clientInfo.name, 'gcloud')
    self.assertEqual(matrix.resultStorage.googleCloudStorage.gcsPath,
                     'gs://gatorade/2015-02-24/')

    spec = matrix.testSpecification
    self.assertEqual(spec.testTimeout, '321s')

    self.assertEqual(spec.testSetup.networkProfile, 'some-network-profile')

    test = spec.androidInstrumentationTest
    self.assertEqual(test.appApk.gcsPath, 'gs://gatorade/2015-02-24/hawks.apk')
    self.assertEqual(test.testApk.gcsPath,
                     'gs://gatorade/2015-02-24/hawks-test.apk')
    self.assertEqual(test.appPackageId, 'com.sea.hawks')
    self.assertEqual(test.testPackageId, 'com.sea.hawks.test')

    devices = matrix.environmentMatrix.androidMatrix
    self.assertEqual(devices.androidModelIds, ['football'])
    self.assertEqual(devices.androidVersionIds, ['10'])
    self.assertEqual(devices.locales, ['en_SEA'])
    self.assertEqual(devices.orientations, ['I-formation'])

  def testMatrixCreator_AndroidGameLoop_ValidateRequestFields(self):
    args = self.NewTestArgs(
        type='game-loop',
        app='seahawks.apk',
        app_package='com.sea.hawks',
        device=[{
            'model': 'bronco',
            'locale': 'DEN',
            'orientation': 'prone',
            'version': '48'
        }, {
            'model': 'beast',
            'version': 'mode',
            'locale': 'SEA',
            'orientation': 'supine'
        }],
        results_bucket='the',
        results_dir='great',
        scenario_numbers=[3, 42],
        scenario_labels=['Winners', 'Losers'],
        timeout=100)

    creator = self.CreateMatrixCreator(args)
    req = creator._BuildTestMatrixRequest('id-6')

    devices = req.testMatrix.environmentMatrix.androidDeviceList.androidDevices
    self.assertEqual(len(devices), 2)
    spec = req.testMatrix.testSpecification
    self.assertEqual(spec.testTimeout, '100s')

    test = spec.androidTestLoop
    self.assertEqual(test.appApk.gcsPath, 'gs://the/great/seahawks.apk')
    self.assertEqual(test.appPackageId, 'com.sea.hawks')
    self.assertListEqual(test.scenarios, [3, 42])
    self.assertListEqual(test.scenarioLabels, ['Winners', 'Losers'])

  def testMatrixCreator_CreateTestMatrix_GetsHttpError(self):
    creator = self.CreateMatrixCreator(self.args)
    self.testing_client.projects_testMatrices.Create.Expect(
        request=creator._BuildTestMatrixRequest('id-6'),
        exception=test_utils.MakeHttpError(
            'zergFailure', 'Simulated failure to create test execution.'))

    # An HttpError from the rpc should be converted to an HttpException
    with self.assertRaises(exceptions.HttpException):
      creator.CreateTestMatrix('id-6')
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testMatrixCreator_CreateTestMatrix_Succeeds(self):
    creator = self.CreateMatrixCreator(self.args)
    spec = creator._BuildAndroidInstrumentationTestSpec()
    test_exec = self.NewTestExecution('russell', None, None, None)
    matrix = self.NewTestMatrix('seahawks', spec, None, [test_exec], None, None)

    self.testing_client.projects_testMatrices.Create.Expect(
        request=creator._BuildTestMatrixRequest('id-7'), response=matrix)

    creator.CreateTestMatrix('id-7')

    self.AssertOutputEquals('')
    self.AssertErrContains('Test [seahawks] has been created')

  def testMatrixCreator_BuildGenericTestSpec_disablesVideoWhenFlagIsFalse(self):
    self.args.record_video = False
    creator = self.CreateMatrixCreator(self.args)
    spec = creator._BuildGenericTestSpec()
    self.assertEqual(spec.disableVideoRecording, True)

  def testMatrixCreator_BuildGenericTestSpec_enablesVideoWhenFlagIsTrue(self):
    self.args.record_video = True
    creator = self.CreateMatrixCreator(self.args)
    spec = creator._BuildGenericTestSpec()
    self.assertEqual(spec.disableVideoRecording, False)

  def testMatrixCreator_BuildGenericTestSpec_disablesPerfMetricsWhenFlagIsFalse(
      self):
    self.args.performance_metrics = False
    creator = self.CreateMatrixCreator(self.args)
    spec = creator._BuildGenericTestSpec()
    self.assertEqual(spec.disablePerformanceMetrics, True)

  def testMatrixCreator_BuildGenericTestSpec_enablesPerfMetricsWhenFlagIsTrue(
      self):
    self.args.performance_metrics = True
    creator = self.CreateMatrixCreator(self.args)
    spec = creator._BuildGenericTestSpec()
    self.assertEqual(spec.disablePerformanceMetrics, False)

  def _BuildObbDeviceFile(self, obb_file_name, obb_gcs_path):
    """Build a DeviceFile with ObbFile."""
    return TESTING_V1_MESSAGES.DeviceFile(
        obbFile=TESTING_V1_MESSAGES.ObbFile(
            obbFileName=obb_file_name,
            obb=TESTING_V1_MESSAGES.FileReference(gcsPath=obb_gcs_path)))

  def _BuildRegularDeviceFile(self, regular_file_gcs_path,
                              regular_file_device_path):
    """Build a DeviceFile with RegularFile."""
    return TESTING_V1_MESSAGES.DeviceFile(
        regularFile=TESTING_V1_MESSAGES.RegularFile(
            content=TESTING_V1_MESSAGES.FileReference(
                gcsPath=regular_file_gcs_path),
            devicePath=regular_file_device_path))


if __name__ == '__main__':
  test_case.main()
