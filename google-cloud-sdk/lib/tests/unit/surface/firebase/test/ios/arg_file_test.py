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

import os
import re

from googlecloudsdk.api_lib.firebase.test import arg_file
from googlecloudsdk.api_lib.firebase.test import arg_util
from googlecloudsdk.api_lib.firebase.test.ios import arg_manager
from googlecloudsdk.api_lib.firebase.test.ios import catalog_manager
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test.ios import fake_catalogs
from tests.lib.surface.firebase.test.ios import unit_base

GOOD_ARGS = os.path.join(unit_base.TEST_DATA_PATH, 'good_args')
BAD_ARGS = os.path.join(unit_base.TEST_DATA_PATH, 'bad_args')
TEST_TYPES = os.path.join(unit_base.TEST_DATA_PATH, 'test_types')
INTEGERS = os.path.join(unit_base.TEST_DATA_PATH, 'integers')


class IosArgFileTests(unit_base.IosUnitTestBase):
  """Unit tests for iOS-specific use of api_lib/test/arg_file.py."""

  def SetUp(self):
    self.ios_args_set = arg_manager.AllArgsSet()

  # Valid iOS argument file tests

  def testGoodArgFile_FileArgsMergedWithCliArgs(self):
    args = self.NewTestArgs(test='iosapp.zip', results_bucket='bucket1')
    file_args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':ios-group',
                                            self.ios_args_set)
    arg_util.ApplyLowerPriorityArgs(args, file_args, True)

    self.AssertErrContains('')
    # Simulated args from CLI
    self.assertEqual(args.test, 'iosapp.zip')
    self.assertEqual(args.results_bucket, 'bucket1')
    # Args merged from GOOD_ARGS file
    self.assertEqual(args.type, 'xctest')
    self.assertEqual(args.results_dir, 'my/ios/results')
    self.assertEqual(args.results_history_name, 'history2')
    self.assertEqual(args.timeout, 25 * 60)
    self.assertEqual(args.xctestrun_file, '.xctestrun2')
    self.assertEqual(args.xcode_version, '9.1.1')
    self.assertEqual(args.test_special_entitlements, False)

  # Test type arg validation tests

  def testType_XctestIsValid(self):
    args = self.NewTestArgs(test='test', argspec=TEST_TYPES + ':type-xctest')
    PrepareIosArgs(args)
    self.assertEqual(args.type, 'xctest')

  def testType_XctestNoTestIsInvalid(self):
    args = self.NewTestArgs(argspec=TEST_TYPES + ':type-xctest')
    with self.assertRaisesRegex(calliope_exceptions.RequiredArgumentException,
                                re.escape('Missing required argument [test]')):
      PrepareIosArgs(args)

  def testType_GameLoopIsValid(self):
    args = self.NewTestArgs(app='app', argspec=TEST_TYPES + ':type-game-loop')
    PrepareIosArgs(args)
    self.assertEqual(args.type, 'game-loop')

  def testType_GameLoopNoAppIsInvalid(self):
    args = self.NewTestArgs(argspec=TEST_TYPES + ':type-game-loop')
    with self.assertRaisesRegex(calliope_exceptions.RequiredArgumentException,
                                re.escape('Missing required argument [app]')):
      PrepareIosArgs(args)

  def testType_TestSpecifiedNotType(self):
    args = self.NewTestArgs(test='test')
    PrepareIosArgs(args)
    self.assertEqual(args.type, 'xctest')

  def testType_AppSpecifiedNotTypeInvalid(self):
    args = self.NewTestArgs(app='app')
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        re.escape('[app]: may not be used with test type [xctest]')):
      PrepareIosArgs(args)

  def testType_CannotBeAndroidType(self):
    args = self.NewTestArgs(argspec=TEST_TYPES + ':type-robo')
    with self.assertRaisesRegex(calliope_exceptions.InvalidArgumentException,
                                "'robo' is not a valid test type."):
      PrepareIosArgs(args)

  def testType_IntIsInvalid(self):
    args = self.NewTestArgs(argspec=TEST_TYPES + ':type-int')
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        re.escape("[type]: '42' is not a valid test type.")):
      PrepareIosArgs(args)

  def testType_BoolIsInvalid(self):
    args = self.NewTestArgs(argspec=TEST_TYPES + ':type-bool')
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        re.escape("[type]: 'True' is not a valid test type.")):
      PrepareIosArgs(args)

  # Tests for --device arg

  def testDevice_ValidSparseMatrix_TerseSyntax1(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':ios-terse',
                                       self.ios_args_set)
    self.assertEqual(len(args['device']), 2)
    self.assertDictEqual(args['device'][0], {'model': 'iphone8se'})
    self.assertDictEqual(args['device'][1], {
        'model': 'ipad',
        'version': 'ios9'
    })

  def testDevice_ValidSparseMatrix_VerboseSyntax(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':sparse-verbose',
                                       self.ios_args_set)
    self.assertEqual(len(args['device']), 2)
    d1 = args['device'][0]
    d2 = args['device'][1]
    self.assertDictEqual(d1, {
        'model': 'm1',
        'version': 'v1',
        'locale': 'l1',
        'orientation': 'o1'
    })
    self.assertDictEqual(d2, {
        'model': 'm2',
        'version': 'v2',
        'locale': 'l2',
        'orientation': 'o2'
    })

  def testDevice_ValidSparseMatrix_EmptyDevice(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':sparse-empty',
                                       self.ios_args_set)
    self.assertEqual(len(args['device']), 1)
    d1 = args['device'][0]
    self.assertDictEqual(d1, {})

  def testDevice_InvalidSparseMatrix_1(self):
    with self.assertRaisesRegex(calliope_exceptions.InvalidArgumentException,
                                re.escape('Invalid value for [device]:')):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':sparse1', self.ios_args_set)

  def testDevice_InvalidSparseMatrix_2(self):
    with self.assertRaisesRegex(calliope_exceptions.InvalidArgumentException,
                                re.escape('Invalid value for [device]:')):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':sparse2', self.ios_args_set)

  def testDevice_InvalidSparseMatrix_3(self):
    with self.assertRaisesRegex(calliope_exceptions.InvalidArgumentException,
                                re.escape('Invalid value for [model]:')):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':sparse3', self.ios_args_set)

  def testDevice_InvalidSparseMatrix_4(self):
    with self.assertRaisesRegex(calliope_exceptions.InvalidArgumentException,
                                re.escape('Invalid value for [model]:')):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':sparse4', self.ios_args_set)

  # Tests for --additional-ipas arg

  def testAdditionalApks_MultipleFilesOk(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':additional-ipas.two',
                                       self.ios_args_set)
    self.assertEqual(len(args['additional_ipas']), 2)

  def testAdditionalApks_EmptyFileNotAllowed(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':additional-ipas.empty',
                                  self.ios_args_set)

  # Tests for --other-files arg

  def testOtherFiles_GoodInput(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':other-files-ios.good',
                                       self.ios_args_set)
    self.assertEqual(
        args['other_files'], {
            '/private/var/mobile/Media/myfile.txt': 'local/dir/file1.txt',
            'com.google:/Documents/myfile2.txt': 'gs://bucket/file2.txt'
        })

  def testOtherFiles_ListInput(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':other-files.list',
                                  self.ios_args_set)

  def testOtherFiles_StringInput(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':other-files.string',
                                  self.ios_args_set)

  def testOtherFiles_IntInput(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':other-files.int',
                                  self.ios_args_set)

  # Tests for --directories-to-pull arg

  def testDirsToPull_GoodInput(self):
    args = arg_file.GetArgsFromArgFile(
        GOOD_ARGS + ':directories-to-pull-ios.good', self.ios_args_set)
    self.assertEqual(args['directories_to_pull'], [
        '/private/var/mobile/Media/my_output',
        'com.my.app:/Documents/my_other_output'
    ])

  def testDirsToPull_DictInput(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':directories-to-pull-ios.dict',
                                  self.ios_args_set)

  # Various int-list arg validation tests

  def testIntList_ValidNumber(self):
    args = arg_file.GetArgsFromArgFile(INTEGERS + ':scenario1',
                                       self.ios_args_set)
    self.assertListEqual(args['scenario_numbers'], [2000])

  def testIntList_ListWithFourElements(self):
    args = arg_file.GetArgsFromArgFile(INTEGERS + ':scenario4',
                                       self.ios_args_set)
    self.assertListEqual(args['scenario_numbers'], [1, 3, 13, 77])

  def testIntList_ZeroIsNotAPositiveInt(self):
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        re.escape(
            '[scenario-numbers]: Value must be greater than or equal to 1; received: 0'
        )):
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-zero',
                                  self.ios_args_set)

  def testIntList_InvalidNegativeInt(self):
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        re.escape(
            '[scenario-numbers]: Value must be greater than or equal to 1; received: -1024'
        )):
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-neg', self.ios_args_set)

  def testIntList_InvalidNegativeIntInList(self):
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        re.escape(
            '[scenario-numbers]: Value must be greater than or equal to 1; received: -1'
        )):
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-neg-in-list',
                                  self.ios_args_set)

  def testIntList_InvalidFloat(self):
    with self.assertRaisesRegex(calliope_exceptions.InvalidArgumentException,
                                re.escape('[scenario-numbers]: 3.14')):
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-float',
                                  self.ios_args_set)

  def testIntList_InvalidSingleString(self):
    with self.assertRaisesRegex(calliope_exceptions.InvalidArgumentException,
                                re.escape('[scenario-numbers]: 1a')):
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-str', self.ios_args_set)

  def testIntList_InvalidListOfStrings(self):
    with self.assertRaisesRegex(calliope_exceptions.InvalidArgumentException,
                                re.escape('[scenario-numbers]: 1')):
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-str-list',
                                  self.ios_args_set)

  def testIntList_InvalidDictValue(self):
    with self.assertRaisesRegex(calliope_exceptions.InvalidArgumentException,
                                re.escape('[scenario-numbers]: {')):
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-dict',
                                  self.ios_args_set)


def PrepareIosArgs(args):
  cat_mgr = catalog_manager.IosCatalogManager(fake_catalogs.FakeIosCatalog())
  arg_manager.IosArgsManager(cat_mgr).Prepare(args)


if __name__ == '__main__':
  test_case.main()
