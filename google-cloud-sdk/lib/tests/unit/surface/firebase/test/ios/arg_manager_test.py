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

import argparse
import datetime

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test.ios import arg_manager
from googlecloudsdk.api_lib.firebase.test.ios import catalog_manager
from googlecloudsdk.calliope import exceptions as core_exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test.ios import fake_catalogs
from tests.lib.surface.firebase.test.ios import unit_base


class IosArgsTests(unit_base.IosMockClientTest):
  """Unit tests for api_lib/firebase/test/ios/arg_manager.py."""

  # Tests on arg rules data structures

  def testGetSetOfAllTestArgs_OnActualRules(self):
    all_args = arg_manager.AllArgsSet()
    # arg_manager tests include GA and beta args
    self.assertItemsEqual(set(unit_base.ALL_TEST_RUN_ARGS['beta']), all_args)

  def testArgNamesInRulesAreInternalNames(self):
    # Verify that ArgRules use internal arg names with underscores, not hyphens
    for arg_rules in arg_manager.TypedArgRules().itervalues():
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

  def testPrepareArgs_MissingRequiredArg(self):
    # gcloud test run invoked with no args, but --test is always required
    args = self.NewTestArgs(test=None)
    arg_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(core_exceptions.RequiredArgumentException) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertEqual(ex_ctx.exception.parameter_name, 'test')

  def testPrepareArgs_UsesDimensionDefaultsWhenNoDeviceSpecified(self):
    args = self.NewTestArgs(test='a.zip')
    arg_mgr = _IosArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    # We should get one sparse-matrix device with all default dimension values.
    self.assertEqual(len(args.device), 1)
    self.assertDictEqual(
        args.device[0],
        {
            'model': 'iPen2',
            'version': '6.0',
            # TODO(b/78015882): add proper support for locales and orientations
            # 'locale': 'en',
            # 'orientation': 'portrait'
        })

  # TODO(b/78015882): eventually replace this test with the one below
  def testPrepareArgs_SparseMatrixFillsInModelVersionDefaultsWhereNeeded(self):
    args = self.NewTestArgs(
        test='a', device=[{
            'model': 'iPencil1'
        }, {
            'version': '5.1'
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
        })
    self.assertDictEqual(
        args.device[1],
        {
            'model': 'iPen2',  # default value
            'version': '5.1',
        })

  @test_case.Filters.skip('Need ios locale/orientation support.', 'b/78015882')
  def testPrepareArgs_SparseMatrixFillsInDimensionDefaultsWhereNeeded(self):
    args = self.NewTestArgs(
        test='a',
        device=[{
            'model': 'iPencil1',
            'locale': 'en'
        }, {
            'version': '5.1',
            'orientation': 'landscape'
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
            'locale': 'en',
            'orientation': 'portrait'  # default value
        })
    self.assertDictEqual(
        args.device[1],
        {
            'model': 'iPen2',  # default value
            'version': '5.1',
            'locale': 'en',  # default value
            'orientation': 'landscape'
        })

  def testPrepareArgs_SparseMatrix_InvalidModel(self):
    args = self.NewTestArgs(test='a', device=[{'model': 'iPadBad'}])
    arg_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.ModelNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertIn("'iPadBad' is not a valid model", ex_ctx.exception.message)

  def testPrepareArgs_SparseMatrix_InvalidVersion(self):
    args = self.NewTestArgs(test='a', device=[{'version': 'v9'}])
    arg_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.VersionNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertIn("'v9' is not a valid OS version", ex_ctx.exception.message)

  @test_case.Filters.skip('Need ios locale/orientation support.', 'b/78015882')
  def testPrepareArgs_SparseMatrix_InvalidLocale(self):
    args = self.NewTestArgs(test='a', device=[{'locale': 'here'}])
    arg_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.LocaleNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertIn("'here' is not a valid locale", ex_ctx.exception.message)

  @test_case.Filters.skip('Need ios locale/orientation support.', 'b/78015882')
  def testPrepareArgs_SparseMatrix_InvalidOrientation(self):
    args = self.NewTestArgs(test='a', device=[{'orientation': 'down'}])
    arg_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.OrientationNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    msg = ex_ctx.exception.message
    self.assertIn("'down' is not a valid device orientation", msg)

  def testPrepareArgs_SparseMatrix_InvalidDimensionName(self):
    args = self.NewTestArgs(test='a', device=[{'ver': '5'}])
    arg_mgr = _IosArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidIosDimensionNameError) as ex_ctx:
      arg_mgr.Prepare(args)
    msg = ex_ctx.exception.message
    self.assertIn("'ver' is not a valid dimension name", msg)

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


def _IosArgManagerWithFakeCatalog():
  cat_mgr = catalog_manager.IosCatalogManager(fake_catalogs.FakeIosCatalog())
  return arg_manager.IosArgsManager(cat_mgr)


if __name__ == '__main__':
  test_case.main()
