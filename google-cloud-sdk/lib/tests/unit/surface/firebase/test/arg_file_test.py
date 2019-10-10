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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.firebase.test import arg_file
from googlecloudsdk.api_lib.firebase.test import arg_util
from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import yaml
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test import unit_base
import six

MALFORMED1 = os.path.join(unit_base.TEST_DATA_PATH, 'malformed1')
MALFORMED2 = os.path.join(unit_base.TEST_DATA_PATH, 'malformed2')
MALFORMED3 = os.path.join(unit_base.TEST_DATA_PATH, 'malformed3')
MALFORMED4 = os.path.join(unit_base.TEST_DATA_PATH, 'malformed4')
EMPTY_DOC = os.path.join(unit_base.TEST_DATA_PATH, 'empty_doc')
EMPTY_FILE = os.path.join(unit_base.TEST_DATA_PATH, 'empty_file')
EMPTY_GROUP = os.path.join(unit_base.TEST_DATA_PATH, 'empty_group')
GOOD_ARGS = os.path.join(unit_base.TEST_DATA_PATH, 'good_args')
BAD_ARGS = os.path.join(unit_base.TEST_DATA_PATH, 'bad_args')
DURATIONS = os.path.join(unit_base.TEST_DATA_PATH, 'durations')
BOOLEANS = os.path.join(unit_base.TEST_DATA_PATH, 'booleans')
INCLUDES = os.path.join(unit_base.TEST_DATA_PATH, 'include_groups')

COMMON_ARGS = set(
    ['test', 'type', 'async_', 'results_bucket', 'timeout', 'timeout_us'])


class CommonArgFileTests(unit_base.TestUnitTestBase):
  """Unit tests for generic portions of api_lib/test/arg_file.py."""

  # Tests for correct arg-spec validation

  def testArgspec_IsNone(self):
    arg_dict = arg_file.GetArgsFromArgFile(None, COMMON_ARGS)
    self.assertEqual(arg_dict, {})

  def testArgspec_HasNoColon(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile('file;group', COMMON_ARGS)
    self.assertEqual(e.exception.parameter_name, 'arg-spec')
    self.assertIn('ARG_FILE:ARG_GROUP_NAME', six.text_type(e.exception))

  def testArgspec_OnlyColonIsInGcsPrefix(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile('gs://file;group', COMMON_ARGS)
    self.assertEqual(e.exception.parameter_name, 'arg-spec')
    self.assertIn('ARG_FILE:ARG_GROUP_NAME', six.text_type(e.exception))

  def testArgspec_FileDoesNotExist(self):
    with self.assertRaises(yaml.Error) as e:
      arg_file.GetArgsFromArgFile('missing-file:group', COMMON_ARGS)
    self.assertIn('No such file', six.text_type(e.exception))
    self.assertIn('missing-file', six.text_type(e.exception))

  # Tests on malformed YAML files

  def testYamlParsing_Malformed1(self):
    with self.assertRaises(calliope_exceptions.BadFileException) as e:
      arg_file.GetArgsFromArgFile(MALFORMED1 + ':foo', COMMON_ARGS)
    self.assertIn('Failed to parse YAML', six.text_type(e.exception))

  def testYamlParsing_Malformed2(self):
    with self.assertRaises(calliope_exceptions.BadFileException) as e:
      arg_file.GetArgsFromArgFile(MALFORMED2 + ':foo', COMMON_ARGS)
    self.assertIn('Failed to parse YAML', six.text_type(e.exception))

  def testYamlParsing_Malformed3(self):
    with self.assertRaises(yaml.YAMLParseError) as e:
      arg_file.GetArgsFromArgFile(MALFORMED3 + ':xxx', COMMON_ARGS)
    self.assertIn('Failed to parse YAML', six.text_type(e.exception))

  def testYamlParsing_Malformed4_GroupNameContainsInvalidChar(self):
    with self.assertRaises(calliope_exceptions.BadFileException) as e:
      arg_file.GetArgsFromArgFile(MALFORMED4 + '://xyz', COMMON_ARGS)
    self.assertIn('Invalid argument group name [//xyz]',
                  six.text_type(e.exception))

  def testYamlParsing_EmptyFile(self):
    with self.assertRaises(calliope_exceptions.BadFileException) as e:
      arg_file.GetArgsFromArgFile(EMPTY_FILE + ':xxx', COMMON_ARGS)
    self.assertIn('Could not find argument group [xxx]',
                  six.text_type(e.exception))

  def testYamlParsing_EmptyYamlDoc(self):
    arg_file.GetArgsFromArgFile(EMPTY_DOC + ':xxx', COMMON_ARGS)
    self.AssertErrContains('WARNING: Ignoring empty yaml document.')

  def testYamlParsing_EmptyGroup(self):
    arg_file.GetArgsFromArgFile(EMPTY_GROUP + ':xxx', COMMON_ARGS)
    self.AssertErrContains('WARNING: Argument group [xxx] is empty.')

  # Invalid arg file tests

  def testBadArgFile_GroupDoesNotExist(self):
    with self.assertRaises(calliope_exceptions.BadFileException) as e:
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':ghost', COMMON_ARGS)
    self.assertIn('Could not find argument group [ghost]',
                  six.text_type(e.exception))

  def testBadArgFile_ArgNameIsInvalid(self):
    with self.assertRaises(exceptions.InvalidTestArgError) as e:
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':bad-arg-name', COMMON_ARGS)
    self.assertIn('[appp] is not a valid argument name',
                  six.text_type(e.exception))

  def testBadArgFile_ArgValueIsMissing(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':missing-arg-value', COMMON_ARGS)
    self.assertIn('[type]: no argument value found', six.text_type(e.exception))

  def testBadArgFile_ArgIsDuplicated(self):
    args = arg_file.GetArgsFromArgFile(BAD_ARGS + ':dup-arg-name', COMMON_ARGS)
    self.assertEqual(args['type'], 'robo')

  # Valid argument file tests

  def testGoodArgFile_FileArgDoesNotOverrideCliArg(self):
    args = test_utils.NewNameSpace([], test='jill.apk', results_bucket='jack')
    file_args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':test-override',
                                            COMMON_ARGS)
    arg_util.ApplyLowerPriorityArgs(args, file_args, True)
    self.assertEqual(args.results_bucket, 'jack')
    self.AssertErrContains('"--results-bucket jack" overrides file argument ')
    self.AssertErrContains('"results-bucket: gs://arg-file-bucket"')

  def testGoodArgFile_FileArgUsedIfCliArgIsNone(self):
    args = test_utils.NewNameSpace([], test='jill.apk', results_bucket=None)
    file_args = arg_file.GetArgsFromArgFile(GOOD_ARGS + ':test-override',
                                            COMMON_ARGS)
    arg_util.ApplyLowerPriorityArgs(args, file_args, True)
    self.assertEqual(args.results_bucket, 'gs://arg-file-bucket')
    self.AssertErrContains('')

  # Duration arg validation tests

  def testDurations_ValidTimeout_NoUnits(self):
    args = arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-200', COMMON_ARGS)
    self.assertEqual(args['timeout'], 200)

  def testDurations_ValidTimeout_MicroSecondUnits(self):
    args = arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-500000000us',
                                       COMMON_ARGS)
    self.assertEqual(args['timeout'], 500)

  def testDurations_ValidTimeout_MilliSecondUnits(self):
    args = arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-500000ms',
                                       COMMON_ARGS)
    self.assertEqual(args['timeout'], 500)

  def testDurations_ValidTimeout_SecondUnits(self):
    args = arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-500s', COMMON_ARGS)
    self.assertEqual(args['timeout'], 500)

  def testDurations_ValidTimeout_MinuteUnits(self):
    args = arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-10m', COMMON_ARGS)
    self.assertEqual(args['timeout'], 600)

  def testDurations_ValidTimeout_HourUnits(self):
    args = arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-2h', COMMON_ARGS)
    self.assertEqual(args['timeout'], 7200)

  def testDurations_InvalidString(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-abcd', COMMON_ARGS)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [timeout]', msg)
    self.assertIn("Duration unit 'abcd' must be preceded by a number", msg)

  def testDurations_InvalidUnits(self):
    with self.assertRaises(exceptions.InvalidArgException) as e:
      arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-10e', COMMON_ARGS)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [timeout]', msg)
    self.assertIn("Unknown character 'E' in duration", msg)

  def testDurations_TimeoutBelowLowerBound(self):
    with self.assertRaises(exceptions.InvalidArgException) as e:
      arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-lower', COMMON_ARGS)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [timeout]', msg)
    self.assertIn('must be greater than or equal to 1m; received: 59s', msg)

  def testDurations_TimeoutAboveUpperBound(self):
    with self.assertRaises(exceptions.InvalidArgException) as e:
      arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-upper', COMMON_ARGS)
    msg = six.text_type(e.exception)
    self.assertIn('Invalid value for [timeout]', msg)
    self.assertIn('must be less than or equal to 6h; received: 7h', msg)

  def testDurations_TimeoutIsList(self):
    with self.assertRaises(exceptions.InvalidArgException) as e:
      arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-list', COMMON_ARGS)
    self.assertIn("Invalid value for [timeout]: ['15m',",
                  six.text_type(e.exception))

  def testDurationsUs_ValidTimeout_NoUnits(self):
    args = arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-us-200',
                                       COMMON_ARGS)
    self.assertEqual(args['timeout_us'], 200000000)

  def testDurationsUs_ValidTimeout_MicroSecondUnits(self):
    args = arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-us-500000000us',
                                       COMMON_ARGS)
    self.assertEqual(args['timeout_us'], 500000000)

  def testDurationsUs_ValidTimeout_MilliSecondUnits(self):
    args = arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-us-500000ms',
                                       COMMON_ARGS)
    self.assertEqual(args['timeout_us'], 500000000)

  def testDurationsUs_ValidTimeout_SecondUnits(self):
    args = arg_file.GetArgsFromArgFile(DURATIONS + ':timeout-us-500s',
                                       COMMON_ARGS)
    self.assertEqual(args['timeout_us'], 500000000)

  # Boolean arg validation tests

  def testBooleans_ValidString_LowerCaseTrue(self):
    args = arg_file.GetArgsFromArgFile(BOOLEANS + ':bool-true-lower',
                                       COMMON_ARGS)
    self.assertTrue(args['async_'])

  def testBooleans_ValidString_UpperCaseTrue(self):
    args = arg_file.GetArgsFromArgFile(BOOLEANS + ':bool-true-upper',
                                       COMMON_ARGS)
    self.assertTrue(args['async_'])

  def testBooleans_ValidString_LowerCaseFalse(self):
    args = arg_file.GetArgsFromArgFile(BOOLEANS + ':bool-false-lower',
                                       COMMON_ARGS)
    self.assertFalse(args['async_'])

  def testBooleans_ValidString_MixedCaseFalse(self):
    args = arg_file.GetArgsFromArgFile(BOOLEANS + ':bool-false-mixedcase',
                                       COMMON_ARGS)
    self.assertFalse(args['async_'])

  def testBooleans_ValidString_YesSameAsTrue(self):
    args = arg_file.GetArgsFromArgFile(BOOLEANS + ':bool-yes', COMMON_ARGS)
    self.assertTrue(args['async_'])

  def testBooleans_ValidString_OnSameAsTrue(self):
    args = arg_file.GetArgsFromArgFile(BOOLEANS + ':bool-on', COMMON_ARGS)
    self.assertTrue(args['async_'])

  def testBooleans_ValidString_NoSameAsFalse(self):
    args = arg_file.GetArgsFromArgFile(BOOLEANS + ':bool-no', COMMON_ARGS)
    self.assertFalse(args['async_'])

  def testBooleans_ValidString_OffSameAsFalse(self):
    args = arg_file.GetArgsFromArgFile(BOOLEANS + ':bool-off', COMMON_ARGS)
    self.assertFalse(args['async_'])

  def testBooleans_InvalidString(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(BOOLEANS + ':bool-xyz', COMMON_ARGS)
    self.assertEqual('Invalid value for [async]: xyz',
                     six.text_type(e.exception))

  def testBooleans_InvalidStringMisspelled(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(BOOLEANS + ':bool-misspell', COMMON_ARGS)
    self.assertEqual('Invalid value for [async]: fals',
                     six.text_type(e.exception))

  def testBooleans_InvalidIntegerType(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(BOOLEANS + ':bool-int', COMMON_ARGS)
    self.assertEqual('Invalid value for [async]: 0', six.text_type(e.exception))

  def testBooleans_InvalidListType(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(BOOLEANS + ':bool-list', COMMON_ARGS)
    self.assertIn('Invalid value for [async]: [', six.text_type(e.exception))

  # Tests for tab-completion of ARGSPECs

  def testArgSpecCompleter_EmptyPrefix(self):
    completions = arg_file.ArgSpecCompleter('', None)
    self.assertEqual([], completions)

  def testArgSpecCompleter_WithFilenameWithoutGroupPrefix(self):
    completions = arg_file.ArgSpecCompleter(INCLUDES, None)
    self.assertEqual([], completions)

  def testArgSpecCompleter_WithFilenameAndGroupPrefix_MatchOne(self):
    completions = arg_file.ArgSpecCompleter(INCLUDES + ':t', None)
    self.assertEquals([INCLUDES + ':top-group'], completions)

  def testArgSpecCompleter_WithFilenameAndGroupPrefix_MatchMany(self):
    completions = arg_file.ArgSpecCompleter(INCLUDES + ':gr', None)
    self.assertEquals(
        sorted([INCLUDES + g for g in [':group2', ':group3', ':group4']]),
        sorted(completions))


if __name__ == '__main__':
  test_case.main()
