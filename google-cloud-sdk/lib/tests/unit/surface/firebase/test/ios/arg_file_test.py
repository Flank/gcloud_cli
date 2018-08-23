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
from googlecloudsdk.api_lib.firebase.test.ios import arg_manager
from googlecloudsdk.api_lib.firebase.test.ios import catalog_manager
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test.ios import fake_catalogs
from tests.lib.surface.firebase.test.ios import unit_base

GOOD_ARGS = os.path.join(unit_base.TEST_DATA_PATH, 'good_args')
BAD_ARGS = os.path.join(unit_base.TEST_DATA_PATH, 'bad_args')
TEST_TYPES = os.path.join(unit_base.TEST_DATA_PATH, 'test_types')


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

  # Test type arg validation tests

  def testType_XctestIsValid(self):
    args = self.NewTestArgs(test='test', argspec=TEST_TYPES + ':type-xctest')
    PrepareIosArgs(args)
    self.assertEqual(args.type, 'xctest')

  def testType_CannotBeAndroidType(self):
    args = self.NewTestArgs(argspec=TEST_TYPES + ':type-robo')
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      PrepareIosArgs(args)
    self.assertIn("'robo' is not a valid test type.", str(e.exception))

  def testType_IntIsInvalid(self):
    args = self.NewTestArgs(argspec=TEST_TYPES + ':type-int')
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      PrepareIosArgs(args)
    self.assertIn('Invalid value for [type]:', str(e.exception))
    self.assertIn("'42' is not a valid test type.", str(e.exception))

  def testType_BoolIsInvalid(self):
    args = self.NewTestArgs(argspec=TEST_TYPES + ':type-bool')
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      PrepareIosArgs(args)
    self.assertIn('Invalid value for [type]:', str(e.exception))
    self.assertIn("'True' is not a valid test type.", str(e.exception))

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
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':sparse1', self.ios_args_set)
    self.assertIn('Invalid value for [device]:', str(e.exception))

  def testDevice_InvalidSparseMatrix_2(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':sparse2', self.ios_args_set)
    self.assertIn('Invalid value for [device]:', str(e.exception))

  def testDevice_InvalidSparseMatrix_3(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':sparse3', self.ios_args_set)
    self.assertIn('Invalid value for [model]:', str(e.exception))

  def testDevice_InvalidSparseMatrix_4(self):
    with self.assertRaises(calliope_exceptions.InvalidArgumentException) as e:
      arg_file.GetArgsFromArgFile(BAD_ARGS + ':sparse4', self.ios_args_set)
    self.assertIn('Invalid value for [model]:', str(e.exception))


def PrepareIosArgs(args):
  cat_mgr = catalog_manager.IosCatalogManager(fake_catalogs.FakeIosCatalog())
  arg_manager.IosArgsManager(cat_mgr).Prepare(args)


if __name__ == '__main__':
  test_case.main()
