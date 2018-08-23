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

import os

from googlecloudsdk.api_lib.firebase.test import arg_file
from googlecloudsdk.api_lib.firebase.test import arg_util
from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test.android import arg_manager
from googlecloudsdk.api_lib.firebase.test.android import catalog_manager
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import fake_args
from tests.lib.surface.firebase.test.android import unit_base
import six

GOOD_ARGS = os.path.join(unit_base.TEST_DATA_PATH, 'good_args')
BAD_ARGS = os.path.join(unit_base.TEST_DATA_PATH, 'bad_args')
INTEGERS = os.path.join(unit_base.TEST_DATA_PATH, 'integers')
STR_LISTS = os.path.join(unit_base.TEST_DATA_PATH, 'str_lists')
TEST_TYPES = os.path.join(unit_base.TEST_DATA_PATH, 'test_types')
INCLUDES = os.path.join(unit_base.TEST_DATA_PATH, 'include_groups')


class AndroidArgFileTests(unit_base.AndroidUnitTestBase):
  """Unit tests for Android-specific use of api_lib/test/arg_file.py."""

  def SetUp(self):
    self.android_args_set = arg_manager.AllArgsSet()

  # Valid Android argument file tests

  def testGoodArgFile_FileArgsMergedWithCliArgs(self):
    args = self.NewTestArgs(app='jill.apk', results_bucket='jack')
    file_args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':my-group',
                                            self.android_args_set)
    arg_util.ApplyLowerPriorityArgs(args, file_args, True)

    self.AssertErrContains('')
    # Simulated args from CLI
    self.assertEqual(args.app, 'jill.apk')
    self.assertEqual(args.results_bucket, 'jack')
    # Args merged from GOOD_ARGS file
    self.assertEqual(args.type, 'instrumentation')
    self.assertEqual(args.test, 'startrek.apk')
    self.assertEquals(sorted(args.locales), sorted(['klingon', 'romulan']))
    self.assertEqual(args.max_steps, 333)
    self.assertEqual(args.results_dir, 'my/results/dir')
    self.assertEqual(args.robo_directives, {
        'resource1': 'value1',
        'text:resource2': '2',
        'click:resource3': ''
    })
    self.assertEqual(args.test_targets,
                     ['package kirk', 'class enterprise.spock'])

  # Test type arg validation tests

  def testType_InstrumentationIsValid(self):
    args = self.NewTestArgs(
        app='app',
        test='test',  # Required args
        argspec=TEST_TYPES + ':type-instr')
    PrepareAndroidArgs(args)
    self.assertEqual(args.type, 'instrumentation')

  def testType_RoboIsValid(self):
    args = self.NewTestArgs(app='app', argspec=TEST_TYPES + ':type-robo')
    PrepareAndroidArgs(args)
    self.assertEqual(args.type, 'robo')

  def testType_Misspelled(self):
    args = self.NewTestArgs(argspec=TEST_TYPES + ':type-misspell')
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      PrepareAndroidArgs(args)
    self.assertIn("'robot' is not a valid test type.",
                  six.text_type(e.exception))

  def testType_IntIsInvalid(self):
    args = self.NewTestArgs(argspec=TEST_TYPES + ':type-int')
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      PrepareAndroidArgs(args)
    self.assertIn('Invalid value for [type]:', six.text_type(e.exception))
    self.assertIn("'42' is not a valid test type.", six.text_type(e.exception))

  def testType_BoolIsInvalid(self):
    args = self.NewTestArgs(argspec=TEST_TYPES + ':type-bool')
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      PrepareAndroidArgs(args)
    self.assertIn('Invalid value for [type]:', six.text_type(e.exception))
    self.assertIn("'True' is not a valid test type.",
                  six.text_type(e.exception))

  # Integer arg validation tests

  def testIntegers_ValidNumber(self):
    args = arg_file.GetArgsFromArgFile(INTEGERS + ':max-depth-1',
                                       self.android_args_set)
    self.assertEqual(args['max_depth'], 1)

  def testIntegers_LargeValidNumber(self):
    args = arg_file.GetArgsFromArgFile(INTEGERS + ':large-steps',
                                       self.android_args_set)
    self.assertEqual(args['max_steps'], 1234567890)

  def testIntegers_NumberAsStringNotValid(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':int-string',
                                  self.android_args_set)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [max-depth]: 2', msg)

  def testIntegers_PositiveParamIsZero(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':not-positive',
                                  self.android_args_set)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [max-depth]:', msg)
    self.assertIn('Value must be greater than or equal to 1; received: 0', msg)

  def testIntegers_NonNegativeParamIsNegative(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':delay-neg1',
                                  self.android_args_set)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [max-steps]:', msg)
    self.assertIn('Value must be greater than or equal to 0; received: -1', msg)

  def testIntegers_InvalidNumberContainsAlphaChar(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':max-depth-10x',
                                  self.android_args_set)
    self.assertEqual('Invalid value for [max-depth]: 10x',
                     six.text_type(e.exception))

  def testIntegers_InvalidNumberWithComma(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':comma-steps',
                                  self.android_args_set)
    self.assertEqual('Invalid value for [max-steps]: 123,456',
                     six.text_type(e.exception))

  def testIntegers_InvalidFloatNumber(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':float-steps',
                                  self.android_args_set)
    self.assertEqual('Invalid value for [max-steps]: 12.34',
                     six.text_type(e.exception))

  def testIntegers_InvalidNumberList(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':list-steps',
                                  self.android_args_set)
    self.assertEqual('Invalid value for [max-steps]: [1234]',
                     six.text_type(e.exception))

  # Various int-list arg validation tests

  def testIntList_ValidNumber(self):
    args = arg_file.GetArgsFromArgFile(INTEGERS + ':scenario1',
                                       self.android_args_set)
    self.assertListEqual(args['scenario_numbers'], [2000])

  def testIntList_ListWithFourElements(self):
    args = arg_file.GetArgsFromArgFile(INTEGERS + ':scenario4',
                                       self.android_args_set)
    self.assertListEqual(args['scenario_numbers'], [1, 3, 13, 77])

  def testIntList_ZeroIsNotAPositiveInt(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-zero',
                                  self.android_args_set)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [scenario-numbers]:', msg)
    self.assertIn('Value must be greater than or equal to 1; received: 0', msg)

  def testIntList_InvalidNegativeInt(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-neg',
                                  self.android_args_set)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [scenario-numbers]:', msg)
    self.assertIn('must be greater than or equal to 1; received: -1024', msg)

  def testIntList_InvalidNegativeIntInList(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-neg-in-list',
                                  self.android_args_set)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [scenario-numbers]:', msg)
    self.assertIn('must be greater than or equal to 1; received: -1', msg)

  def testIntList_InvalidFloat(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-float',
                                  self.android_args_set)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [scenario-numbers]: 3.14', msg)

  def testIntList_InvalidSingleString(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-str',
                                  self.android_args_set)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [scenario-numbers]: 1a', msg)

  def testIntList_InvalidListOfStrings(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-str-list',
                                  self.android_args_set)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [scenario-numbers]: 1', msg)

  def testIntList_InvalidDictValue(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INTEGERS + ':scenario-dict',
                                  self.android_args_set)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [scenario-numbers]: {', msg)
    self.assertIn("'foo'", msg)

  # Various string-list arg validation tests

  def testOsVersionList_ValidList(self):
    args = arg_file.GetArgsFromArgFile(STR_LISTS + ':vers-intlist',
                                       self.android_args_set)
    self.assertListEqual(args['os_version_ids'], ['15', '16'])

  def testOsVersionList_ValidSingleInt(self):
    args = arg_file.GetArgsFromArgFile(STR_LISTS + ':vers-int',
                                       self.android_args_set)
    self.assertListEqual(args['os_version_ids'], ['10'])

  def testOsVersionList_ValidMixedList(self):
    args = arg_file.GetArgsFromArgFile(STR_LISTS + ':vers-mixedints',
                                       self.android_args_set)
    self.assertListEqual(args['os_version_ids'], ['18', '19', '20', 'v21'])

  def testOsVersionList_ValidVersionStringList(self):
    args = arg_file.GetArgsFromArgFile(STR_LISTS + ':vers-strs',
                                       self.android_args_set)
    self.assertListEqual(args['os_version_ids'], ['5.1.x', '19', '4.2.x'])

  def testOrientationList_ValidSingleItem(self):
    args = arg_file.GetArgsFromArgFile(STR_LISTS + ':ori-port',
                                       self.android_args_set)
    self.assertListEqual(args['orientations'], ['portrait'])

  def testOrientationList_ValidListOfOne(self):
    args = arg_file.GetArgsFromArgFile(STR_LISTS + ':ori-land',
                                       self.android_args_set)
    self.assertListEqual(args['orientations'], ['landscape'])

  def testOrientationList_ValidListOfDefault(self):
    args = arg_file.GetArgsFromArgFile(STR_LISTS + ':ori-def',
                                       self.android_args_set)
    self.assertListEqual(args['orientations'], ['default'])

  def testOrientationList_ValidListOfAll(self):
    args = arg_file.GetArgsFromArgFile(STR_LISTS + ':ori-all',
                                       self.android_args_set)
    self.assertListEqual(args['orientations'],
                         ['landscape', 'portrait', 'default'])

  def testOrientationList_InvalidName(self):
    with self.assertRaises(exceptions.OrientationNotFoundError) as e:
      arg_file.GetArgsFromArgFile(STR_LISTS + ':ori-vert',
                                  self.android_args_set)
    self.assertEqual("'vert' is not a valid device orientation",
                     six.text_type(e.exception))

  def testOrientationList_InvalidNameInList(self):
    with self.assertRaises(exceptions.OrientationNotFoundError) as e:
      arg_file.GetArgsFromArgFile(STR_LISTS + ':ori-horiz',
                                  self.android_args_set)
    self.assertEqual("'horiz' is not a valid device orientation",
                     six.text_type(e.exception))

  def testOrientationList_DuplicateCase1(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(STR_LISTS + ':ori-dup1',
                                  self.android_args_set)
    self.assertEqual(
        'Invalid value for [orientations]: orientations may not be repeated.',
        six.text_type(e.exception))

  def testOrientationList_DuplicateCase2(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(STR_LISTS + ':ori-dup2',
                                  self.android_args_set)
    self.assertEqual(
        'Invalid value for [orientations]: orientations may not be repeated.',
        six.text_type(e.exception))

  def testDeviceIdList_NestedList(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(STR_LISTS + ':dev-nestedlist',
                                  self.android_args_set)
    self.assertEqual("Invalid value for [device-ids]: ['Nexus6', 'Nexus7']",
                     six.text_type(e.exception))

  def testScenarioLabels_ValidLabelList(self):
    args = arg_file.GetArgsFromArgFile(STR_LISTS + ':labels-good',
                                       self.android_args_set)
    self.assertListEqual(args['scenario_labels'], ['label2', 'label5'])

  def testScenarioLabels_InvalidDictValue(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(STR_LISTS + ':labels-dict',
                                  self.android_args_set)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [scenario-labels]: {', msg)
    self.assertIn("'label1': 'foo'", msg)

  def testScenarioLabels_InvalidNestedListValue(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(STR_LISTS + ':labels-nested-list',
                                  self.android_args_set)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [scenario-labels]:', msg)
    self.assertIn("['label2', 'label3']", msg)

  # Tests for obb-files arg

  def testObbFiles_OneFileOK(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':one.obb',
                                       self.android_args_set)
    self.assertEqual(args['obb_files'], ['gs://dir1/dir2/file.obb'])

  def testObbFiles_TwoFilesOK(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':two.obb',
                                       self.android_args_set)
    self.assertEqual(args['obb_files'], ['file1.obb', 'file2.obb'])

  def testObbFiles_ThreeFilesNotAllowed(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':three-OBBs',
                                  self.android_args_set)

  # Tests for robo-directives arg

  def testRoboDirectives_ListInput(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':robo-directives.list',
                                  self.android_args_set)

  def testRoboDirectives_StringInput(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':robo-directives.string',
                                  self.android_args_set)

  def testRoboDirectives_IntInput(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':robo-directives.int',
                                  self.android_args_set)

  # Tests for robo-script arg

  def testRoboScript_LocalFileOK(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':robo-script.local',
                                       self.android_args_set)
    self.assertEqual(args['robo_script'], 'local/dir/robo_script.json')

  def testRoboScript_GcsFileOK(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':robo-script.gcs',
                                       self.android_args_set)
    self.assertEqual(args['robo_script'], 'gs://bucket/robo_script.json')

  def testRoboScript_MultipleFilesNotAllowed(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':robo-script.multiple',
                                  self.android_args_set)

  # Tests for additional-apks arg

  def testAdditionalApks_MultipleFilesOk(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':additional-apks.two',
                                       self.android_args_set)
    self.assertEqual(args['additional_apks'],
                     ['local/dir/apk1.apk', 'gs://bucket/apk2.apk'])

  def testAdditionalApks_EmptyFileNotAllowed(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':additional-apks.empty',
                                  self.android_args_set)

  # Tests for environment-variables arg

  def testEnvironmentVariables_GoodInput(self):
    args = arg_file.GetArgsFromArgFile(
        GOOD_ARGS + ':environment-variables.good', self.android_args_set)
    self.assertEqual(args['environment_variables'],
                     {'e1': 'value1',
                      'e2': 'value2'})

  def testEnvironmentVariables_ListInput(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':environment-variables.list',
                                  self.android_args_set)

  def testEnvironmentVariables_StringInput(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':environment-variables.string',
                                  self.android_args_set)

  def testEnvironmentVariables_IntInput(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':environment-variables.int',
                                  self.android_args_set)

  # Tests for other-files arg

  def testOtherFiles_GoodInput(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':other-files.good',
                                       self.android_args_set)
    self.assertEqual(args['other_files'], {
        'local/dir/file1': '/sdcard/dir1',
        'gs://bucket/file2': '/sdcard/dir2'
    })

  def testOtherFiles_ListInput(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':other-files.list',
                                  self.android_args_set)

  def testOtherFiles_StringInput(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':other-files.string',
                                  self.android_args_set)

  def testOtherFiles_IntInput(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':other-files.int',
                                  self.android_args_set)

  # Tests for directories-to-pull arg

  def testDirectoriesToPull_GoodInput(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':directories-to-pull.list',
                                       self.android_args_set)
    self.assertEqual(args['directories_to_pull'],
                     ['/sdcard/tempDirUno', '/sdcard/tempDirDos'])

    args = arg_file.GetArgsFromArgFile(
        GOOD_ARGS + ':directories-to-pull.string', self.android_args_set)
    self.assertEqual(args['directories_to_pull'], ['/singleStringPath'])

  # Tests for --device (alternate sparse-matrix syntax)

  def testDevice_ValidSparseMatrix_TerseSyntax1(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':sparse-terse1',
                                       self.android_args_set)
    self.assertEqual(len(args['device']), 3)
    self.assertDictEqual(args['device'][0], {'model': 'Nexus5'})
    self.assertDictEqual(args['device'][1], {'model': 'sailfish'})
    self.assertDictEqual(args['device'][2], {'model': 'shamu'})

  def testDevice_ValidSparseMatrix_TerseSyntax2(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':sparse-terse2',
                                       self.android_args_set)
    self.assertEqual(len(args['device']), 3)
    d1 = args['device'][0]
    d2 = args['device'][1]
    d3 = args['device'][2]
    self.assertDictEqual(
        d1, {
            'model': 'NexusLowRes',
            'version': '23',
            'locale': 'es',
            'orientation': 'landscape'
        })
    self.assertDictEqual(d2, {'model': 'shamu'})
    self.assertDictEqual(d3, {'version': '5.1.x', 'locale': 'zh'})

  def testDevice_ValidSparseMatrix_VerboseSyntax(self):
    args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':sparse-verbose',
                                       self.android_args_set)
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
                                       self.android_args_set)
    self.assertEqual(len(args['device']), 1)
    d1 = args['device'][0]
    self.assertDictEqual(d1, {})

  def testDevice_InvalidSparseMatrix_1(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':sparse1', self.android_args_set)
    self.assertIn('Invalid value for [device]:', six.text_type(e.exception))

  def testDevice_InvalidSparseMatrix_2(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':sparse2', self.android_args_set)
    self.assertIn('Invalid value for [device]:', six.text_type(e.exception))

  def testDevice_InvalidSparseMatrix_3(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':sparse3', self.android_args_set)
    self.assertIn('Invalid value for [model]:', six.text_type(e.exception))

  def testDevice_InvalidSparseMatrix_4(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':sparse4', self.android_args_set)
    self.assertIn('Invalid value for [model]:', six.text_type(e.exception))

  # Tests of include: keyword

  def testInclude_SimpleCase(self):
    args = arg_file.GetArgsFromArgFile(INCLUDES + ':group3',
                                       self.android_args_set)
    self.assertEqual(args['async'], True)  # Value from includer
    self.assertEqual(args['type'], 'instrumentation')  # Value from includee
    self.assertListEqual(args['locales'], ['de', 'en', 'it'])  # From includer
    self.assertListEqual(args['os_version_ids'], ['21'])  # From includee

  def testInclude_MoreComplexCase(self):
    args = arg_file.GetArgsFromArgFile(INCLUDES + ':top-group',
                                       self.android_args_set)
    # Check that topmost group value with no matching included values is used
    self.assertEqual(args['app'], 'path/to/peekaboo.apk')
    # Check that topmost group value not overridden by directly included value
    self.assertEqual(args['timeout'], 600)
    # Check that topmost group value not overridden by indirectly included value
    self.assertEqual(args['type'], 'robo')
    # Check that included groups in a list are processed left-to-right
    self.assertEqual(args['async'], False)
    # Check that 2-levels-deep includee doesn't override 1-level-deep includee
    self.assertListEqual(args['locales'], ['de', 'en', 'it'])
    # Check that value from 2-levels-deep includee is used if no overrides
    self.assertListEqual(args['os_version_ids'], ['21'])

  def testInclude_GroupNameIsInt(self):
    with self.assertRaises(calliope_exceptions.BadFileException) as e:
      arg_file.GetArgsFromArgFile(INCLUDES + ':incl-int', self.android_args_set)
    self.assertIn('Could not find argument group [1] in argument file.',
                  six.text_type(e.exception))

  def testInclude_GroupNameIsBool(self):
    with self.assertRaises(calliope_exceptions.BadFileException) as e:
      arg_file.GetArgsFromArgFile(INCLUDES + ':incl-bool',
                                  self.android_args_set)
    self.assertIn('Could not find argument group [False] in argument file.',
                  six.text_type(e.exception))

  def testInclude_GroupIsNestedList(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INCLUDES + ':incl-nested',
                                  self.android_args_set)
    self.assertEqual("Invalid value for [include]: ['group3', 'group4']",
                     six.text_type(e.exception))

  def testInclude_GroupNameIsMissing(self):
    with self.assertRaises(calliope_exceptions.BadFileException) as e:
      arg_file.GetArgsFromArgFile(INCLUDES + ':incl-missing',
                                  self.android_args_set)
    self.assertIn('Could not find argument group [missing] in argument file.',
                  six.text_type(e.exception))

  def testInclude_GroupNameIsSelf(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INCLUDES + ':incl-self',
                                  self.android_args_set)
    self.assertIn(
        '[include]: Detected cyclic reference to arg group [incl-self]',
        six.text_type(e.exception))

  def testInclude_FormsAGraphCycle(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(INCLUDES + ':incl-cycle-a',
                                  self.android_args_set)
    self.assertIn(
        '[include]: Detected cyclic reference to arg group [incl-cycle-a]',
        six.text_type(e.exception))


def PrepareAndroidArgs(args):
  cat_mgr = catalog_manager.AndroidCatalogManager(fake_args.AndroidCatalog())
  arg_manager.AndroidArgsManager(cat_mgr).Prepare(args)


if __name__ == '__main__':
  test_case.main()
