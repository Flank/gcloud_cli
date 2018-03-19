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

from googlecloudsdk.api_lib.firebase.test import arg_validate
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import fake_args
from tests.lib.surface.firebase.test import unit_base

import mock


class ArgValidateTests(unit_base.TestUnitTestBase):
  """Unit tests for api_lib/test/arg_validate.py."""

  # Validation of args for different test types

  def _ValidateFakeArgsForTestType(self, args, test_type):
    arg_validate.ValidateArgsForTestType(args, test_type,
                                         fake_args.TypedArgRules(),
                                         fake_args.SharedArgRules(),
                                         fake_args.AllArgsSet())

  def testValidateArgsForTestType_RequiredArgNotValidWithTestType(self):
    args = argparse.Namespace(
        donate='yes', blood='one pint', platelets='clotting')
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      self._ValidateFakeArgsForTestType(args, 'ab-negative')
    ex = e.exception
    self.assertEqual(ex.parameter_name, 'blood')
    self.assertIn('may not be used with test type [ab-negative]', ex.message)

  def testValidateArgsForTestType_OptionalArgNotValidWithTestType(self):
    args = argparse.Namespace(donate='yes', blood='one pint', tomorrow='maybe')
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      self._ValidateFakeArgsForTestType(args, 'o-positive')
    ex = e.exception
    self.assertEqual(ex.parameter_name, 'tomorrow')
    self.assertIn('may not be used with test type [o-positive]', ex.message)

  def testValidateArgsForTestType_RequiredArgIsMissing(self):
    args = argparse.Namespace(donate='yes')
    with self.assertRaises(exceptions.RequiredArgumentException) as e:
      self._ValidateFakeArgsForTestType(args, 'o-positive')
    ex = e.exception
    self.assertEqual(ex.parameter_name, 'blood')
    self.assertIn('must be specified with test type [o-positive]', ex.message)

  def testValidateArgsForTestType_RequiredArgEqualsNone(self):
    args = argparse.Namespace(donate='yes', platelets=None)
    with self.assertRaises(exceptions.RequiredArgumentException) as e:
      self._ValidateFakeArgsForTestType(args, 'ab-negative')
    ex = e.exception
    self.assertEqual(ex.parameter_name, 'platelets')
    self.assertIn('must be specified with test type [ab-negative]', ex.message)

  # Validation of results-bucket

  def testArgValidation_ResultsBucketWellFormed(self):
    args = argparse.Namespace(results_bucket='gs://well-formed-bucket-name')
    arg_validate.ValidateResultsBucket(args)
    self.assertEqual(args.results_bucket, 'well-formed-bucket-name')

  def testArgValidation_ResultsBucketHasNoPrefix(self):
    args = argparse.Namespace(results_bucket='good-bucket-with-no-prefix')
    arg_validate.ValidateResultsBucket(args)
    self.assertEqual(args.results_bucket, 'good-bucket-with-no-prefix')

  def testArgValidation_ResultsBucketWithEndingSlash(self):
    args = argparse.Namespace(
        results_bucket='gs://good-bucket-with-ending-slash/')
    arg_validate.ValidateResultsBucket(args)
    self.assertEqual(args.results_bucket, 'good-bucket-with-ending-slash')

  def testArgValidation_ResultsBucketPrefixWithSlashMissing(self):
    args = argparse.Namespace(results_bucket='gs:/bucket-with-bad-gs-prefix')
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateResultsBucket(args)
    ex = e.exception
    self.assertEqual(ex.parameter_name, 'results-bucket')
    self.assertIn('Invalid bucket name', ex.message)

  def testArgValidation_ResultsBucketPrefixMissingGsColon(self):
    args = argparse.Namespace(results_bucket='//bucket-with-extra-slashes')
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateResultsBucket(args)
    ex = e.exception
    self.assertEqual(ex.parameter_name, 'results-bucket')
    self.assertIn('Invalid bucket name', ex.message)

  def testArgValidation_ResultsBucketNameIncludesObject(self):
    args = argparse.Namespace(
        results_bucket='gs://bucket-name/includes-an-object')
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateResultsBucket(args)
    ex = e.exception
    self.assertEqual(ex.parameter_name, 'results-bucket')
    self.assertIn('Invalid bucket name', ex.message)

  # Validation of results-dir

  def testArgValidation_ResultsDirWellFormed(self):
    args = argparse.Namespace(results_dir='well-formed-GCS-object-name')
    arg_validate.ValidateResultsDir(args)
    self.assertEqual(args.results_dir, 'well-formed-GCS-object-name')

  def testArgValidation_ResultsDirHasTrailingSlashesStripped(self):
    args = argparse.Namespace(results_dir='my/results/dir//')
    arg_validate.ValidateResultsDir(args)
    self.assertEqual(args.results_dir, 'my/results/dir')

  def testArgValidation_ResultsDirContainsLinefeed(self):
    args = argparse.Namespace(results_dir='no_\r_allowed_in_value')
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateResultsDir(args)
    self.assertIn('results-dir', e.exception.message)
    self.assertIn('may not contain newline or linefeed', e.exception.message)

  def testArgValidation_ResultsDirContainsNewline(self):
    args = argparse.Namespace(results_dir='no_\n_allowed_in_value')
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateResultsDir(args)
    self.assertIn('results-dir', e.exception.message)
    self.assertIn('may not contain newline or linefeed', e.exception.message)

  def testArgValidation_ResultsDirLongerThan512Chars(self):
    args = argparse.Namespace(results_dir='x' * 513)
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateResultsDir(args)
    self.assertIn('results-dir', e.exception.message)
    self.assertIn('too long', e.exception.message)

  # Validation of OBB file names

  def testNormalizeAndValidateObbFileNames_NoExceptionIfNoObbFilesSpecified(
      self):
    arg_validate.NormalizeAndValidateObbFileNames(None)
    arg_validate.NormalizeAndValidateObbFileNames([])

  def testNormalizeAndValidateObbFileNames_SucceedsWithValidNames(self):
    # Valid OBB file names should not raise an InvalidArgException
    arg_validate.NormalizeAndValidateObbFileNames(
        ['main.1234.com.google.app.obb'])
    arg_validate.NormalizeAndValidateObbFileNames(
        ['patch.4321.com.google.app.obb'])
    arg_validate.NormalizeAndValidateObbFileNames(
        ['gs://bucket/a/object/main.1.com.a.obb'])
    arg_validate.NormalizeAndValidateObbFileNames(
        ['/my/path/to/patch.555.Google.App.obb'])
    # Valid, albeit not useful posix path
    arg_validate.NormalizeAndValidateObbFileNames(
        ['//path/main.999.COM.G00_GL3_.obb'])
    arg_validate.NormalizeAndValidateObbFileNames(
        ['gs://bucket/patch.6.a.B.c.D.e.f_g.obb'])
    arg_validate.NormalizeAndValidateObbFileNames(
        ['C:\\aa\\bb\\patch.1234567.com.app.obb'])
    # Multiple file names
    arg_validate.NormalizeAndValidateObbFileNames(
        ['main.12.a.b1.obb', 'patch.34.c.d2.obb'])

  def testNormalizeAndValidateObbFileNames_ExpandsUserDir(self):
    # Linux shell does not convert "~" to home directory, we need to do it
    obb_files_map = {
        '~/main.12.a.b1.obb': '/home/user/main.12.a.b1.obb',
        '~/spam/main.34.c.d1.obb': '/home/user/spam/main.34.c.d1.obb',
        # Only affects paths starting with "~"
        'spam/~/main.34.c.d1.obb': 'spam/~/main.34.c.d1.obb',
    }
    with mock.patch.dict('os.environ', {'HOME': '/home/user'}):
      for obb_test, obb_test_expect in obb_files_map.items():
        obb_files = [obb_test]
        arg_validate.NormalizeAndValidateObbFileNames(obb_files)
        self.assertEqual([obb_test_expect], obb_files)

  def testObbValidation_WithInvalidNames(self):
    # Invalid OBB file names should raise an InvalidArgException
    # Assume blanks are unintentional user error (e.g. undefined script var)
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames([''])
    # Version # in wrong position
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['main.a.123.b.obb'])
    # Missing package name
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['patch.123.obb'])
    # Doesn't start with main. or patch.
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['Main.123.a.b.obb'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(
          ['path/to/mmain.123.a.b.obb'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['patch3.456.a.b.obb'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['ppatch.456.a.b.obb'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['foo.main.789.a.b.obb'])
    # Package name part doesn't start with a letter
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['main.456.a._b_.obb'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['main.456.a.b.8c.obb'])
    # Misplaced or missing periods
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['patch.456.a..b.obb'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['patch.456a.b.obb'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['patch.456.a.b.obb.'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['main.45.6.a.b.obb'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['main.456.a.bobb'])
    # Contains invalid characters
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['main.999:a.b.obb'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['main.999.a@.b.obb'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateObbFileNames(['main.999.a.b$.obb'])

  # Validation of robo-directives

  def testValidateRoboDirectivesList_NoExceptionIfNoneSpecified(self):
    arg_validate.ValidateRoboDirectivesList(
        argparse.Namespace(robo_directives=None))
    arg_validate.ValidateRoboDirectivesList(
        argparse.Namespace(robo_directives=[]))

  def testValidateRoboDirectivesList_WithValidRoboDirectives(self):
    args = argparse.Namespace(robo_directives={
        'resource1': 'value1',
        'text:resource2': 2,
        'click:resource3': ''
    })
    arg_validate.ValidateRoboDirectivesList(args)

  def testValidateRoboDirectivesList_WithInvalidResourceName(self):
    args = argparse.Namespace(robo_directives={'text:resource:name': 'value'})
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateRoboDirectivesList(args)
    self.assertIn('robo-directives', e.exception.message)
    self.assertIn('Invalid format for key [text:resource:name]. '
                  'Use a colon only to separate action type and resource name.',
                  e.exception.message)

  def testValidateRoboDirectivesList_WithEmptyResourceName(self):
    args = argparse.Namespace(robo_directives={'text:': 'value'})
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateRoboDirectivesList(args)
    self.assertIn('robo-directives', e.exception.message)
    self.assertIn('Missing resource_name for key', e.exception.message)

  def testValidateRoboDirectivesList_WithInvalidActionType(self):
    args = argparse.Namespace(robo_directives={'badtype:resource': 'value'})
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateRoboDirectivesList(args)
    self.assertIn('robo-directives', e.exception.message)
    self.assertIn('Unsupported action type [badtype]', e.exception.message)

  def testValidateRoboDirectivesList_WithEmptyResourceType(self):
    args = argparse.Namespace(robo_directives={':resource': 'value'})
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateRoboDirectivesList(args)
    self.assertIn('robo-directives', e.exception.message)
    self.assertIn('Unsupported action type []', e.exception.message)

  def testValidateRoboDirectivesList_WithClickActionAndInputText(self):
    args = argparse.Namespace(robo_directives={'click:resource': 'value'})
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateRoboDirectivesList(args)
    self.assertIn('robo-directives', e.exception.message)
    self.assertIn(
        'Input value not allowed for click action: [click:resource=value]',
        e.exception.message)

  def testValidateRoboDirectivesList_WithDuplicateResourceNames(self):
    # Default duplicate validation for maps won't catch when a directive is
    # specified for the same resource_name but for different types.
    args = argparse.Namespace(
        robo_directives={'click:resource': '',
                         'text:resource': 'value'})
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateRoboDirectivesList(args)
    self.assertIn('robo-directives', e.exception.message)
    self.assertIn('Duplicate resource names are not allowed: [resource]',
                  e.exception.message)

  # Validation of environment-variables

  def testValidateEnvironmentVariablesList_NoExceptionIfNoneSpecified(self):
    arg_validate.ValidateEnvironmentVariablesList(
        argparse.Namespace(environment_variables=None))
    arg_validate.ValidateEnvironmentVariablesList(
        argparse.Namespace(environment_variables=[]))

  def testValidateEnvironmentVariablesList_WithValidEnvironmentVariables(self):
    environment_vars = {
        'coverage': 'true',
        'coverageFile': '/sdcard/tempDir',
        'not_a_real_env_var': 'true'
    }
    args = argparse.Namespace(environment_variables=environment_vars)
    arg_validate.ValidateEnvironmentVariablesList(args)

  def testValidateEnvironmentVariablesList_WithInvalidVariables(self):
    args = argparse.Namespace(environment_variables={'bad:key': 'value'})
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.ValidateEnvironmentVariablesList(args)

    args = argparse.Namespace(environment_variables={'bad-key': 'value'})
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.ValidateEnvironmentVariablesList(args)

    args = argparse.Namespace(environment_variables={'bad key': 'value'})
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.ValidateEnvironmentVariablesList(args)

    args = argparse.Namespace(environment_variables={'bad~key': 'value'})
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.ValidateEnvironmentVariablesList(args)

    args = argparse.Namespace(environment_variables={'0badkey': 'value'})
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.ValidateEnvironmentVariablesList(args)

  # Validation of directories-to-pull

  def testNormalizeAndValidateDirectoriesToPullList_NoExceptionIfNoneSpecified(
      self):
    arg_validate.NormalizeAndValidateDirectoriesToPullList(None)
    arg_validate.NormalizeAndValidateDirectoriesToPullList([])

  def testNormalizeAndValidateDirectoriesToPullList_SucceedsWithValidList(self):
    dirs_orig = [
        '/sdcard/tempUno', '/sdcard/tempDos', '//sdcard/tempQuatro'
        '/data/local/tmp/temp-Dir_Cin.co/Cin+co/Se is'
    ]
    dirs = dirs_orig[:]
    arg_validate.NormalizeAndValidateDirectoriesToPullList(dirs)
    self.assertItemsEqual(dirs_orig, dirs)
    dirs = ['/sdcard/spam/', '//sdcard/spam/']
    arg_validate.NormalizeAndValidateDirectoriesToPullList(dirs)
    # Same as before normalization, but trailing slash is removed
    self.assertEqual(['/sdcard/spam', '//sdcard/spam'], dirs)

  def testNormalizeAndValidateDirectoriesToPullList_FailsWithInvalidPath(self):
    tests = (
        'noforwardslash',
        'relative/path',
        '~/homedir',
        'gs://gcspath',
        '',  # blank
    )
    for test_dir in tests:
      with self.assertRaises(exceptions.InvalidArgumentException):
        arg_validate.NormalizeAndValidateDirectoriesToPullList([test_dir])

  def testNormalizeAndValidateDirectoriesToPullList_FailsWithNonWhitelistedPath(
      self):
    tests = ('/', '/default.prop', '/sdcard/../etc/hosts', '/sdcardFakeDir',
             '/data/local', '/sdcard/../spam', '~/sdcard', '~sdcard')
    for test_dir in tests:
      with self.assertRaises(exceptions.InvalidArgumentException):
        arg_validate.NormalizeAndValidateDirectoriesToPullList([test_dir])

  def testNormalizeAndValidateDirectoriesToPullList_FailsWithInvalidCharacter(
      self):
    dirs = ['/sdcard/Pretty%Fly', '/sdcard/For@', '/data/local/tmp/$WhiteGuy']
    with self.assertRaises(exceptions.InvalidArgumentException):
      arg_validate.NormalizeAndValidateDirectoriesToPullList(dirs)

  def testNormalizeAndValidateDirectoriesToPullList_CollapsesFSModifiers(self):
    dirs_orig = [
        '/sdcard/../data/local/tmp', '/sdcard/./spam', '//sdcard//spam//'
    ]
    dirs_expect = ['/data/local/tmp', '/sdcard/spam', '//sdcard/spam']

    arg_validate.NormalizeAndValidateDirectoriesToPullList(dirs_orig)
    self.assertEqual(dirs_expect, dirs_orig)


if __name__ == '__main__':
  test_case.main()
