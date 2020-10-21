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

import argparse
import datetime

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test.ios import arg_manager
from googlecloudsdk.api_lib.firebase.test.ios import catalog_manager
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.firebase.test.ios import fake_catalogs
from tests.lib.surface.firebase.test.ios import unit_base
import six


class IosArgsTests(unit_base.IosMockClientTest):
  """Unit tests for api_lib/firebase/test/ios/arg_manager.py."""

  # Tests on arg rules data structures

  def testGetSetOfAllTestArgs_OnActualRules(self):
    all_args = arg_manager.AllArgsSet()
    # arg_manager tests include GA and beta args
    self.assertEqual(
        set(unit_base.ALL_TEST_RUN_ARGS[calliope_base.ReleaseTrack.BETA]),
        all_args)

  def testArgNamesInRulesAreInternalNames(self):
    # Verify that ArgRules use internal arg names with underscores, not hyphens
    for arg_rules in six.itervalues(arg_manager.TypedArgRules()):
      self.CheckArgNamesForHyphens(arg_rules)
    self.CheckArgNamesForHyphens(arg_manager.SharedArgRules())

  # Test type determination tests

  def testGetTestType_DefaultIsXctestIfNotSpecified(self):
    arg_mgr = _IosArgManagerWithFakeCatalog()
    args = argparse.Namespace(type=None, test='maps.zip')
    test_type = arg_mgr.GetTestTypeOrRaise(args)
    self.assertEqual(test_type, 'xctest')
    self.assertEqual(args.type, 'xctest')

  # Ios arg preparation tests

  def testPrepareArgs_UsesDimensionDefaultsWhenNoDeviceSpecified(self):
    args = self.NewTestArgs(test='a.zip')
    arg_mgr = _IosArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    # We should get one sparse-matrix device with all default dimension values.
    self.assertEqual(len(args.device), 1)
    self.assertDictEqual(args.device[0], {
        'model': 'iPen2',
        'version': '6.0',
        'locale': 'ro',
        'orientation': 'askew'
    })

  def testPrepareArgs_SparseMatrixFillsInDimensionDefaultsWhereNeeded(self):
    args = self.NewTestArgs(
        test='a',
        device=[{
            'model': 'iPencil1',
            'locale': 'kl'
        }, {
            'version': '5.1',
            'orientation': 'diagonal'
        }])
    arg_mgr = _IosArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    # We should get two sparse-matrix devices with "gaps" filled by defaults.
    self.assertEqual(len(args.device), 2)
    self.assertDictEqual(
        args.device[0],
        {
            'model': 'iPencil1',
            'version': '6.0',  # default value
            'locale': 'kl',
            'orientation': 'askew'  # default value
        })
    self.assertDictEqual(
        args.device[1],
        {
            'model': 'iPen2',  # default value
            'version': '5.1',
            'locale': 'ro',  # default value
            'orientation': 'diagonal'
        })

  def testPrepareArgs_SparseMatrix_InvalidModel(self):
    args = self.NewTestArgs(test='a', device=[{'model': 'iPadBad'}])
    arg_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.ModelNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertIn("'iPadBad' is not a valid model",
                  six.text_type(ex_ctx.exception))

  def testPrepareArgs_SparseMatrix_InvalidVersion(self):
    args = self.NewTestArgs(test='a', device=[{'version': 'v9'}])
    arg_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.VersionNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertIn("'v9' is not a valid OS version",
                  six.text_type(ex_ctx.exception))

  def testPrepareArgs_SparseMatrix_InvalidLocale(self):
    args = self.NewTestArgs(test='a', device=[{'locale': 'here'}])
    arg_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.LocaleNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertIn("'here' is not a valid locale",
                  six.text_type(ex_ctx.exception))

  def testPrepareArgs_SparseMatrix_InvalidOrientation(self):
    args = self.NewTestArgs(test='a', device=[{'orientation': 'down'}])
    arg_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.OrientationNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    msg = six.text_type(ex_ctx.exception)
    self.assertIn("'down' is not a valid device orientation", msg)

  def testPrepareArgs_SparseMatrix_InvalidDimensionName(self):
    args = self.NewTestArgs(test='a', device=[{'ver': '5'}])
    arg_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidDimensionNameError) as ex_ctx:
      arg_mgr.Prepare(args)
    msg = six.text_type(ex_ctx.exception)
    self.assertIn("'ver' is not a valid dimension name", msg)

  def testPrepareArgs_InvalidXcodeVersion(self):
    args = self.NewTestArgs(test='a', xcode_version='v99')
    arg_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.XcodeVersionNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    msg = six.text_type(ex_ctx.exception)
    self.assertIn("'v99' is not a supported Xcode version", msg)

  def testPrepareArgs_StripsOffResultsBucketGcsPrefix(self):
    args = self.NewTestArgs(results_bucket='gs://a-bucket', test='a')
    arg_mgr = _IosArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    self.assertEqual(args.results_bucket, 'a-bucket')

  def testPrepareArgs_ResultsDirGetsDefaultTimestamp(self):
    args = self.NewTestArgs(results_dir=None, test='a')
    arg_mgr = _IosArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    self.assertIn(str(datetime.datetime.now().year), args.results_dir)

  def testPrepareArgs_ResultsDirUsedIfGiven(self):
    args = self.NewTestArgs(results_dir='x/y/z', test='a')
    arg_mgr = _IosArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    self.assertEqual(args.results_dir, 'x/y/z')

  def testPrepareArgs_XctestAndAppAreInvalidTogether(self):
    args = self.NewTestArgs(type='xctest', app='app')
    args_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidArgException) as ex_ctx:
      args_mgr.Prepare(args)
    self.assertIn('[app]: may not be used with test type [xctest]',
                  six.text_type(ex_ctx.exception))

  def testPrepareArgs_GameLoopAndTestAreInvalidTogether(self):
    args = self.NewTestArgs(type='game-loop', test='test')
    args_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidArgException) as ex_ctx:
      args_mgr.Prepare(args)
    self.assertIn('[test]: may not be used with test type [game-loop]',
                  six.text_type(ex_ctx.exception))

  def testPrepareArgs_GameLoopAndTestSpecialEntitlementsAreInvalidTogether(
      self):
    args = self.NewTestArgs(type='game-loop', test_special_entitlements=True)
    args_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidArgException) as ex_ctx:
      args_mgr.Prepare(args)
    self.assertIn(
        '[test-special-entitlements]: may not be used with test type '
        '[game-loop]', six.text_type(ex_ctx.exception))

  def testPrepareArgs_GameLoopNegativeScenarioInvalid(self):
    args = self.NewTestArgs(
        type='game-loop', app='app', scenario_numbers=[1, -1])
    args_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidArgException) as ex_ctx:
      args_mgr.Prepare(args)
    self.assertIn(
        '[scenario-numbers]: Value must be greater than or equal to 1; received: -1',
        six.text_type(ex_ctx.exception))

  def testPrepareArgs_GameLoopZeroScenarioInvalid(self):
    args = self.NewTestArgs(
        type='game-loop', app='app', scenario_numbers=[0])
    args_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidArgException) as ex_ctx:
      args_mgr.Prepare(args)
    self.assertIn(
        '[scenario-numbers]: Value must be greater than or equal to 1; received: 0',
        six.text_type(ex_ctx.exception))

  def testPrepareArgs_DirsToPullValidInput(self):
    args = self.NewTestArgs(
        test='a',
        directories_to_pull=[
            'com.my.app:/Documents/outputdir',
            '/private/var/mobile/Media/outputdir'
        ])
    args_mgr = _IosArgManagerWithFakeCatalog()
    args_mgr.Prepare(args)

  def testPrepareArgs_DirsToPullInvalidBundleIdInvalid(self):
    args = self.NewTestArgs(
        test='a', directories_to_pull=['b@d.bundle.!d:/Documents/outputdir'])
    args_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidArgException) as ex_ctx:
      args_mgr.Prepare(args)
    self.assertIn('Invalid value for [directories-to-pull]',
                  six.text_type(ex_ctx.exception))

  def testPrepareArgs_DirsToPullEmptyBundleIdInvalid(self):
    args = self.NewTestArgs(
        test='a', directories_to_pull=[':/Documents/outputdir'])
    args_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidArgException) as ex_ctx:
      args_mgr.Prepare(args)
    self.assertIn('Invalid value for [directories-to-pull]',
                  six.text_type(ex_ctx.exception))

  def testPrepareArgs_DirsToPullMissingBundleIdInvalid(self):
    args = self.NewTestArgs(
        test='a', directories_to_pull=['/Documents/outputdir'])
    args_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidArgException) as ex_ctx:
      args_mgr.Prepare(args)
    self.assertIn('Invalid value for [directories-to-pull]',
                  six.text_type(ex_ctx.exception))

  def testPrepareArgs_DirsToPullNotSharedFolderInvalid(self):
    args = self.NewTestArgs(
        test='a',
        directories_to_pull=['/private/var/mobile/NotMedia/outputdir'])
    args_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidArgException) as ex_ctx:
      args_mgr.Prepare(args)
    self.assertIn('Invalid value for [directories-to-pull]',
                  six.text_type(ex_ctx.exception))

  def testPrepareArgs_DirsToPullAppFolderNotDocuments(self):
    args = self.NewTestArgs(
        test='a', directories_to_pull=['com.my.app:/NotDocuments/outputdir'])
    args_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidArgException) as ex_ctx:
      args_mgr.Prepare(args)
    self.assertIn('Invalid value for [directories-to-pull]',
                  six.text_type(ex_ctx.exception))

  def testPrepareArgs_DirsToPullEmptyInvalid(self):
    args = self.NewTestArgs(
        test='a', directories_to_pull=[''])
    args_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidArgException) as ex_ctx:
      args_mgr.Prepare(args)
    self.assertIn('Invalid value for [directories-to-pull]',
                  six.text_type(ex_ctx.exception))


def _IosArgManagerWithFakeCatalog():
  cat_mgr = catalog_manager.IosCatalogManager(fake_catalogs.FakeIosCatalog())
  return arg_manager.IosArgsManager(cat_mgr)


if __name__ == '__main__':
  test_case.main()
