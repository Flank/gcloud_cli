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

import argparse
import datetime

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test.android import arg_manager
from googlecloudsdk.api_lib.firebase.test.android import catalog_manager
from googlecloudsdk.calliope import exceptions as core_exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import fake_args
from tests.lib.surface.firebase.test import unit_base


class AndroidArgsTests(unit_base.TestMockClientTest):
  """Unit tests for api_lib/test/android/arg_manager.py."""

  # Tests on arg rules data structures

  def testGetSetOfAllTestArgs_OnActualRules(self):
    all_args = arg_manager.AllArgsSet()
    # arg_manager includes ga and beta args
    self.assertItemsEqual(set(unit_base.ALL_TEST_RUN_ARGS['beta']), all_args)

  def testArgNamesInRulesAreInternalNames(self):
    # Verify that ArgRules use internal arg names with underscores, not hyphens
    for arg_rules in arg_manager.TypedArgRules().itervalues():
      self.CheckArgNamesForHyphens(arg_rules)
    self.CheckArgNamesForHyphens(arg_manager.SharedArgRules())

  # Test type determination tests

  def testGetTestType_DefaultIsInstrumentationIfTestApkPresent(self):
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    args = argparse.Namespace(type=None, test='maps.apk')
    test_type = arg_mgr.GetTestTypeOrRaise(args)
    self.assertEqual(test_type, 'instrumentation')
    self.assertEqual(args.type, 'instrumentation')

  def testGetTestType_DefaultIsRoboIfTestApkNotPresent(self):
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    args = argparse.Namespace(type=None, test=None)
    test_type = arg_mgr.GetTestTypeOrRaise(args)
    self.assertEqual(test_type, 'robo')
    self.assertEqual(args.type, 'robo')

  # Android arg preparation tests

  def testPrepareArgs_MissingRequiredArg(self):
    # gcloud test run invoked with no args, but --app is always required
    args = self.NewTestArgs(app=None)
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(core_exceptions.RequiredArgumentException) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertEqual(ex_ctx.exception.parameter_name, 'app')

  def testPrepareArgs_IncompatibleArgsWithImplicitTestType(self):
    args = self.NewTestArgs(
        type=None, app='apk', test_runner_class='com.google.mtaas-runner')
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(core_exceptions.InvalidArgumentException) as ex_ctx:
      arg_mgr.Prepare(args)
    # --test-runner-class arg is not compatible with implicit test type 'robo'
    self.assertEqual(args.type, 'robo')
    self.assertEqual(ex_ctx.exception.parameter_name, 'test-runner-class')

  def testPrepareArgs_IncompatibleArgsWithExplicitTestType(self):
    args = self.NewTestArgs(
        type='instrumentation', app='a', test='t', max_depth=100)
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(core_exceptions.InvalidArgumentException) as ex_ctx:
      arg_mgr.Prepare(args)
    # --max-depth arg is only compatible with test type 'robo'
    self.assertEqual(ex_ctx.exception.parameter_name, 'max-depth')

  def testPrepareArgs_IncompatibleArgsWithRoboTestType(self):
    args = self.NewTestArgs(type='robo', app='a', scenario_numbers=[2, 5])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(core_exceptions.InvalidArgumentException) as ex_ctx:
      arg_mgr.Prepare(args)
    # --scenario-numbers arg is only compatible with test type 'game-loop'
    self.assertEqual(ex_ctx.exception.parameter_name, 'scenario-numbers')

  def testPrepareArgs_CatalogDefaultsUsedIfAnyMatrixDimensionIsSpecified(self):
    args = self.NewTestArgs(app='a', device_ids=['Nexus2'])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)

    self.assertEqual(args.device_ids, ['Nexus2'])
    self.assertEqual(args.os_version_ids, ['l'])  # default value
    self.assertEqual(args.locales, ['en'])  # default value
    self.assertEqual(args.orientations, ['portrait'])  # default value
    # Verify that sparse-matrix arg is not filled in by defaults.
    self.assertEqual(args.device, None)

    # Repeat above for a different matrix dimension: locales.
    args = self.NewTestArgs(app='a', locales=['de'])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)

    self.assertEqual(args.device_ids, ['Nexus2'])  # default value
    self.assertEqual(args.os_version_ids, ['l'])  # default value
    self.assertEqual(args.locales, ['de'])
    self.assertEqual(args.orientations, ['portrait'])  # default value
    # Verify that sparse-matrix arg is not filled in by defaults.
    self.assertEqual(args.device, None)

  def testPrepareArgs_CatalogDefaultsNotUsedIfMatrixDimensionsSpecified(self):
    args = self.NewTestArgs(
        app='a',
        device_ids=['Nexus1'],
        os_version_ids=['k'],
        locales=['fr'],
        orientations=['landscape'])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)

    self.assertEqual(args.device_ids, ['Nexus1'])
    self.assertEqual(args.os_version_ids, ['k'])
    self.assertEqual(args.locales, ['fr'])
    self.assertEqual(args.orientations, ['landscape'])
    # Verify that sparse-matrix arg is not filled in by defaults.
    self.assertEqual(args.device, None)

  def testPrepareArgs_UsesSparseMatrix_WhenNoDeviceOrDimensionsSpecified(self):
    args = self.NewTestArgs(app='a')
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    # All older matrix-cross-product args should be left unset (no defaults).
    self.assertEqual(args.device_ids, None)
    self.assertEqual(args.os_version_ids, None)
    self.assertEqual(args.locales, None)
    self.assertEqual(args.orientations, None)
    # We should get one sparse-matrix device with all default dimension values.
    self.assertEqual(len(args.device), 1)
    self.assertDictEqual(args.device[0], {
        'model': 'Nexus2',
        'version': 'l',
        'locale': 'en',
        'orientation': 'portrait'
    })

  def testPrepareArgs_SparseMatrix_FillsInDefaultsWhereNeeded(self):
    args = self.NewTestArgs(
        app='a', device=[{'model': 'Nexus1', 'locale': 'fr'},
                         {'version': 'k', 'orientation': 'landscape'}])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    # All older matrix-cross-product args should be left unset (no defaults).
    self.assertEqual(args.device_ids, None)
    self.assertEqual(args.os_version_ids, None)
    self.assertEqual(args.locales, None)
    self.assertEqual(args.orientations, None)
    # We should get two sparse-matrix devices with "gaps" filled by defaults.
    self.assertEqual(len(args.device), 2)
    self.assertDictEqual(args.device[0], {
        'model': 'Nexus1',
        'version': 'l',  # default value
        'locale': 'fr',
        'orientation': 'portrait'  # default value
    })
    self.assertDictEqual(args.device[1], {
        'model': 'Nexus2',  # default value
        'version': 'k',
        'locale': 'en',  # default value
        'orientation': 'landscape'
    })

  def testPrepareArgs_SparseMatrix_InvalidModel(self):
    args = self.NewTestArgs(app='a', device=[{'model': 'NexusBad'}])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.ModelNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertIn("'NexusBad' is not a valid model", ex_ctx.exception.message)

  def testPrepareArgs_SparseMatrix_InvalidVersion(self):
    args = self.NewTestArgs(app='a', device=[{'version': 'v9.9'}])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.VersionNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertIn("'v9.9' is not a valid OS version", ex_ctx.exception.message)

  def testPrepareArgs_SparseMatrix_InvalidLocale(self):
    args = self.NewTestArgs(app='a', device=[{'locale': 'here'}])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.LocaleNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertIn("'here' is not a valid locale", ex_ctx.exception.message)

  def testPrepareArgs_SparseMatrix_InvalidOrientation(self):
    args = self.NewTestArgs(app='a', device=[{'orientation': 'down'}])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.OrientationNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    msg = ex_ctx.exception.message
    self.assertIn("'down' is not a valid device orientation", msg)

  def testPrepareArgs_SparseMatrix_InvalidDimensionName(self):
    args = self.NewTestArgs(app='a', device=[{'fourth': 'wall'}])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.InvalidDimensionNameError) as ex_ctx:
      arg_mgr.Prepare(args)
    msg = ex_ctx.exception.message
    self.assertIn("'fourth' is not a valid dimension name", msg)

  def testPrepareArgs_StripsOffResultsBucketGcsPrefix(self):
    args = self.NewTestArgs(results_bucket='gs://a-bucket', app='a')
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    self.assertEqual(args.results_bucket, 'a-bucket')

  def testPrepareArgs_ResultsDirGetsDefaultTimestamp(self):
    args = self.NewTestArgs(results_dir=None, app='a')
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    self.assertIn(str(datetime.datetime.now().year), args.results_dir)

  def testPrepareArgs_ResultsDirUsedIfGiven(self):
    args = self.NewTestArgs(results_dir='x/y/z', app='a')
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    self.assertEqual(args.results_dir, 'x/y/z')

  def testPrepareArgs_ConvertsOsVersionNumbersToSortedVersionIds(self):
    args = self.NewTestArgs(os_version_ids=['5.0', '4.4'], app='a')
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    self.assertListEqual(args.os_version_ids, ['k', 'l'])

  def testPrepareArgs_InvalidOsVersionNumberRaisesIllegalArgument(self):
    args = self.NewTestArgs(os_version_ids=['5.0', '4.321'], app='a')
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.VersionNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertIn("'4.321' is not a valid OS version", ex_ctx.exception.message)

  def testPrepareArgs_InvalidOsVersionIdRaisesIllegalArgument(self):
    args = self.NewTestArgs(os_version_ids=['k', 'z'], app='a')
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(exceptions.VersionNotFoundError) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertIn("'z' is not a valid OS version", ex_ctx.exception.message)

  def testPrepareArgs_CatchesInvalidObbFilename(self):
    args = self.NewTestArgs(
        app='a',
        obb_files=[
            'gs://bucket/main.100.com.a.obb', 'gs://bucket/patch.100.com.a.oops'
        ])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(core_exceptions.InvalidArgumentException) as ex_ctx:
      arg_mgr.Prepare(args)
    self.assertEqual(ex_ctx.exception.parameter_name, 'obb-files')
    self.assertIn('oops', ex_ctx.exception.message)

  def testPrepareArgs_GameLoopArgDefaults(self):
    args = self.NewTestArgs(
        type='game-loop', app='a', scenario_numbers=None, scenario_labels=None)
    _AndroidArgManagerWithFakeCatalog().Prepare(args)
    # These game-loop args should receive no default values.
    self.assertEqual(args.scenario_numbers, None)
    self.assertEqual(args.scenario_labels, None)

  def testValidateScenarioNumbers_SingleInt(self):
    args = self.NewTestArgs(app='a', type='game-loop', scenario_numbers=[5])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    self.assertListEqual(args.scenario_numbers, [5])

  def testValidateScenarioNumbers_ValidIntList(self):
    args = self.NewTestArgs(
        app='a', type='game-loop', scenario_numbers=[2, 5, 7])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    arg_mgr.Prepare(args)
    self.assertListEqual(args.scenario_numbers, [2, 5, 7])

  def testValidateScenarioNumbers_InvalidNegativeInt(self):
    args = self.NewTestArgs(app='a', type='game-loop', scenario_numbers=[-3])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(core_exceptions.InvalidArgumentException) as e:
      arg_mgr.Prepare(args)
    self.assertIn('greater than or equal to 1; received: -3',
                  e.exception.message)

  def testValidateScenarioNumbers_InvalidString(self):
    args = self.NewTestArgs(app='a', type='game-loop', scenario_numbers='uno')
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(core_exceptions.InvalidArgumentException) as e:
      arg_mgr.Prepare(args)
    self.assertIn('Invalid value for [scenario-numbers]',
                  e.exception.message)

  def testValidateScenarioNumbers_InvalidIntString(self):
    args = self.NewTestArgs(
        app='a', type='game-loop', scenario_numbers=[1, '5'])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(core_exceptions.InvalidArgumentException) as e:
      arg_mgr.Prepare(args)
    self.assertIn('Invalid value for [scenario-numbers]: 5',
                  e.exception.message)

  def testValidateScenarioNumbers_InvalidLetter(self):
    args = self.NewTestArgs(
        app='a', type='game-loop', scenario_numbers=[4, 'z', 7])
    arg_mgr = _AndroidArgManagerWithFakeCatalog()
    with self.assertRaises(core_exceptions.InvalidArgumentException) as e:
      arg_mgr.Prepare(args)
    self.assertIn('Invalid value for [scenario-numbers]: z',
                  e.exception.message)


def _AndroidArgManagerWithFakeCatalog():
  cat_mgr = catalog_manager.AndroidCatalogManager(fake_args.AndroidCatalog())
  return arg_manager.AndroidArgsManager(cat_mgr)


if __name__ == '__main__':
  test_case.main()
