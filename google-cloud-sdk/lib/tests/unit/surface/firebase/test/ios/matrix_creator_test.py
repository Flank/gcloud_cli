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

"""Unit tests for the iOS MatrixCreator."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.ios import unit_base

TESTING_V1_MESSAGES = apis.GetMessagesModule('testing', 'v1')


class IosMatrixCreatorTests(unit_base.IosMockClientTest):
  """Unit tests for api_lib/test/ios/matrix_creator.MatrixCreator."""

  def testMatrixCreator_ValidateIosTestMatrixRequest_NoHistoryId(self):
    creator = self.CreateMatrixCreator(self.args, history_id=None)
    req = creator._BuildTestMatrixRequest('id-1')
    history_id = req.testMatrix.resultStorage.toolResultsHistory.historyId
    self.assertEqual(history_id, None)

  def testMatrixCreator_ValidateIosTestMatrixRequest_HaveHistoryId(self):
    creator = self.CreateMatrixCreator(self.args, history_id='darkages.1')
    req = creator._BuildTestMatrixRequest('id-2')
    history_id = req.testMatrix.resultStorage.toolResultsHistory.historyId
    self.assertEqual(history_id, 'darkages.1')

  def testMatrixCreator_ValidateIosTestMatrixRequest_MainFields(self):
    args = self.NewTestArgs(
        type='xctest',
        test='ios-test.zip',
        device=[{
            'model': 'ipen9',
            'version': 'ios6',
            'locale': 'es_MX',
            'orientation': 'landscape'
        }, {
            'model': 'iPad0',
            'version': 'ios71',
            'locale': 'fr',
            'orientation': 'default'
        }],
        network_profile='barely-usable',
        results_bucket='kfc',
        results_dir='2018-02-24',
        results_history_name='darkages.1',
        timeout=321,
        xctestrun_file='myxctestrun',
        num_flaky_test_attempts=1,
        client_details={
            'branch': 'my-branch',
            'buildNumber': '1234',
        },
        test_special_entitlements=True,
        other_files={
            '/private/var/mobile/Media/myfile.txt': 'gs://sea/file1.txt',
            'com.google:/Documents/myfile2.txt': 'r/file2.txt'
        },
        directories_to_pull=[
            '/private/var/mobile/Media/outputdir',
            'com.my.app:/Documents/outputdir'
        ])

    creator = self.CreateMatrixCreator(args)
    req = creator._BuildTestMatrixRequest('request-id-123')

    matrix = req.testMatrix
    self.assertEqual(req.projectId, self.PROJECT_ID)
    self.assertEqual(matrix.clientInfo.name, 'gcloud')
    self.assertEqual(matrix.resultStorage.googleCloudStorage.gcsPath,
                     'gs://kfc/2018-02-24/')
    self.assertEqual(matrix.flakyTestAttempts, 1)

    devices = matrix.environmentMatrix.iosDeviceList.iosDevices
    self.assertEqual(len(devices), 2)
    self.assertEqual(devices[0].iosModelId, 'ipen9')
    self.assertEqual(devices[0].iosVersionId, 'ios6')
    self.assertEqual(devices[0].locale, 'es_MX')
    self.assertEqual(devices[0].orientation, 'landscape')
    self.assertEqual(devices[1].iosModelId, 'iPad0')
    self.assertEqual(devices[1].iosVersionId, 'ios71')
    self.assertEqual(devices[1].locale, 'fr')
    self.assertEqual(devices[1].orientation, 'default')

    spec = matrix.testSpecification
    self.assertEqual(spec.testTimeout, '321s')
    self.assertEqual(spec.iosTestSetup.networkProfile, 'barely-usable')

    test = spec.iosXcTest
    self.assertEqual(test.testsZip.gcsPath, 'gs://kfc/2018-02-24/ios-test.zip')
    self.assertEqual(test.xctestrun.gcsPath, 'gs://kfc/2018-02-24/myxctestrun')
    self.assertEqual(test.testSpecialEntitlements, True)

    setup = spec.iosTestSetup
    self.assertEqual(len(setup.pushFiles), 2)
    self.assertIn(
        TESTING_V1_MESSAGES.IosDeviceFile(
            devicePath='/private/var/mobile/Media/myfile.txt',
            bundleId=None,
            content=TESTING_V1_MESSAGES.FileReference(
                gcsPath='gs://kfc/2018-02-24/private/var/mobile/Media/myfile.txt'
            )), setup.pushFiles)
    self.assertIn(
        TESTING_V1_MESSAGES.IosDeviceFile(
            devicePath='/Documents/myfile2.txt',
            bundleId='com.google',
            content=TESTING_V1_MESSAGES.FileReference(
                gcsPath='gs://kfc/2018-02-24/Documents/myfile2.txt')),
        setup.pushFiles)
    self.assertEqual(len(setup.pullDirectories), 2)
    self.assertIn(
        TESTING_V1_MESSAGES.IosDeviceFile(
            devicePath='/private/var/mobile/Media/outputdir',
            bundleId=None,
            content=None), setup.pullDirectories)
    self.assertIn(
        TESTING_V1_MESSAGES.IosDeviceFile(
            devicePath='/Documents/outputdir',
            bundleId='com.my.app',
            content=None), setup.pullDirectories)

    client_details = matrix.clientInfo.clientInfoDetails
    client_detail1 = TESTING_V1_MESSAGES.ClientInfoDetail(
        key='branch', value='my-branch')
    client_detail2 = TESTING_V1_MESSAGES.ClientInfoDetail(
        key='buildNumber', value='1234')

    self.assertIn(client_detail1, client_details)
    self.assertIn(client_detail2, client_details)

  def testMatrixCreator_CreateIosTestMatrix_GetsHttpError(self):
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
    spec = creator._BuildIosXcTestSpec()
    test_exec = self.NewTestExecution('russell', None, None, None)
    matrix = self.NewTestMatrix('seahawks', spec, None, [test_exec], None, None)

    self.testing_client.projects_testMatrices.Create.Expect(
        request=creator._BuildTestMatrixRequest('id-7'), response=matrix)

    creator.CreateTestMatrix('id-7')

    self.AssertOutputEquals('')
    self.AssertErrContains('Test [seahawks] has been created')

  def testMatrixCreator_BuildIosXcTestSpec_disablesVideoWhenFlagIsFalse(self):
    self.args.record_video = False
    creator = self.CreateMatrixCreator(self.args)
    spec = creator._BuildIosXcTestSpec()
    self.assertEqual(spec.disableVideoRecording, True)

  def testMatrixCreator_BuildIosXcTestSpec_enablesVideoWhenFlagIsTrue(self):
    self.args.record_video = True
    creator = self.CreateMatrixCreator(self.args)
    spec = creator._BuildIosXcTestSpec()
    self.assertEqual(spec.disableVideoRecording, False)

  def testMatrixCreator_BuildIosXcTestSpec_xcodeVersionIsSpecified(self):
    self.args.xcode_version = '9.1.1'
    creator = self.CreateMatrixCreator(self.args)
    spec = creator._BuildIosXcTestSpec()
    self.assertEqual(spec.iosXcTest.xcodeVersion, '9.1.1')

  def testMatrixCreator_BuildIosXcTestSpec_xcodeVersionIsNotSpecified(self):
    creator = self.CreateMatrixCreator(self.args)
    spec = creator._BuildIosXcTestSpec()
    self.assertEqual(spec.iosXcTest.xcodeVersion, None)

  def testMatrixCreator_BuildTestLoopTestSpec_withScenarios(self):
    self.args.scenario_numbers = [3, 4]
    creator = self.CreateMatrixCreator(self.args)
    spec = creator._BuildIosTestLoopTestSpec()
    self.assertEqual(spec.iosTestLoop.scenarios, [3, 4])

  def testMatrixCreator_BuildTestLoopTestSpec_withAppIpa(self):
    self.args.app = 'app.ipa'
    self.args.scenario_numbers = [1]
    creator = self.CreateMatrixCreator(self.args)
    spec = creator._BuildIosTestLoopTestSpec()
    self.assertEqual(spec.iosTestLoop.appIpa.gcsPath, 'gs://oak/dir/app.ipa')


if __name__ == '__main__':
  test_case.main()
