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

import argparse

from googlecloudsdk.api_lib.firebase.test import arg_validate
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import fake_args
from tests.lib.surface.firebase.test import unit_base
import six


class CommonArgValidateTests(unit_base.TestUnitTestBase):
  """Unit tests for generic/shared arg validation."""

  # Validation of args for different test types using fake args.

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
    self.assertIn('may not be used with test type [ab-negative]',
                  six.text_type(ex))

  def testValidateArgsForTestType_OptionalArgNotValidWithTestType(self):
    args = argparse.Namespace(donate='yes', blood='one pint', tomorrow='maybe')
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      self._ValidateFakeArgsForTestType(args, 'o-positive')
    ex = e.exception
    self.assertEqual(ex.parameter_name, 'tomorrow')
    self.assertIn('may not be used with test type [o-positive]',
                  six.text_type(ex))

  def testValidateArgsForTestType_RequiredArgIsMissing(self):
    args = argparse.Namespace(donate='yes')
    with self.assertRaises(exceptions.RequiredArgumentException) as e:
      self._ValidateFakeArgsForTestType(args, 'o-positive')
    ex = e.exception
    self.assertEqual(ex.parameter_name, 'blood')
    self.assertIn('must be specified with test type [o-positive]',
                  six.text_type(ex))

  def testValidateArgsForTestType_RequiredArgEqualsNone(self):
    args = argparse.Namespace(donate='yes', platelets=None)
    with self.assertRaises(exceptions.RequiredArgumentException) as e:
      self._ValidateFakeArgsForTestType(args, 'ab-negative')
    ex = e.exception
    self.assertEqual(ex.parameter_name, 'platelets')
    self.assertIn('must be specified with test type [ab-negative]',
                  six.text_type(ex))

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
    self.assertIn('Invalid bucket name', six.text_type(ex))

  def testArgValidation_ResultsBucketPrefixMissingGsColon(self):
    args = argparse.Namespace(results_bucket='//bucket-with-extra-slashes')
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateResultsBucket(args)
    ex = e.exception
    self.assertEqual(ex.parameter_name, 'results-bucket')
    self.assertIn('Invalid bucket name', six.text_type(ex))

  def testArgValidation_ResultsBucketNameIncludesObject(self):
    args = argparse.Namespace(
        results_bucket='gs://bucket-name/includes-an-object')
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateResultsBucket(args)
    ex = e.exception
    self.assertEqual(ex.parameter_name, 'results-bucket')
    self.assertIn('Invalid bucket name', six.text_type(ex))

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
    self.assertIn('results-dir', six.text_type(e.exception))
    self.assertIn('may not contain newline or linefeed',
                  six.text_type(e.exception))

  def testArgValidation_ResultsDirContainsNewline(self):
    args = argparse.Namespace(results_dir='no_\n_allowed_in_value')
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateResultsDir(args)
    self.assertIn('results-dir', six.text_type(e.exception))
    self.assertIn('may not contain newline or linefeed',
                  six.text_type(e.exception))

  def testArgValidation_ResultsDirLongerThan512Chars(self):
    args = argparse.Namespace(results_dir='x' * 513)
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_validate.ValidateResultsDir(args)
    self.assertIn('results-dir', six.text_type(e.exception))
    self.assertIn('too long', six.text_type(e.exception))


if __name__ == '__main__':
  test_case.main()
