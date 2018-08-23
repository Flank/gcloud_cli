# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.api_lib.firebase.test import arg_util
from googlecloudsdk.api_lib.firebase.test.android import arg_manager
from googlecloudsdk.api_lib.firebase.test.android import catalog_manager
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import fake_args
from tests.lib.surface.firebase.test import unit_base
import six


class ArgUtilTests(unit_base.TestMockClientTest):
  """Unit tests for api_lib/test/arg_util.py."""

  # Tests on arg rules data structures

  def testGetSetOfAllTestArgs_OnTestRules(self):
    all_args = arg_util.GetSetOfAllTestArgs(fake_args.TypedArgRules(),
                                            fake_args.SharedArgRules())
    self.assertEquals(fake_args.AllArgsSet(), all_args)

  def testArgNamesInRulesAreInternalNames(self):
    # Verify that ArgRules use internal arg names with underscores, not hyphens
    for arg_rules in six.itervalues(fake_args.TypedArgRules()):
      self.CheckArgNamesForHyphens(arg_rules)
    self.CheckArgNamesForHyphens(fake_args.SharedArgRules())

  # Test type determination tests

  def testGetTestType_ValidTypeIsLeftUnchanged(self):
    arg_mgr = _FakeArgManager()
    args = argparse.Namespace(type='ab-negative')
    test_type = arg_mgr.GetTestTypeOrRaise(args)
    self.assertEqual(test_type, 'ab-negative')

  def testGetTestType_TestTypeIsInvalid(self):
    arg_mgr = _FakeArgManager()
    args = argparse.Namespace(type='psych-test')
    with self.assertRaises(exceptions.InvalidArgumentException) as e:
      arg_mgr.GetTestTypeOrRaise(args)
    ex = e.exception
    self.assertEqual(ex.parameter_name, 'type')
    self.assertIn("'psych-test' is not a valid test type", six.text_type(ex))

  # Tests for applying default args

  def testApplyArgDefaults_SharedArgHasValue_NoDefaultApplied(self):
    args = argparse.Namespace(donate='yes')
    shared_defaults = fake_args.SharedArgRules()['defaults']
    typed_defaults = fake_args.TypedArgRules()['o-positive']['defaults']
    arg_util.ApplyLowerPriorityArgs(args, shared_defaults)
    arg_util.ApplyLowerPriorityArgs(args, typed_defaults)
    self.assertEqual(args.donate, 'yes')

  def testApplyArgDefaults_SharedArgHasNoValue_DefaultApplied(self):
    args = argparse.Namespace(donate=None)
    shared_defaults = fake_args.SharedArgRules()['defaults']
    typed_defaults = fake_args.TypedArgRules()['o-positive']['defaults']
    arg_util.ApplyLowerPriorityArgs(args, shared_defaults)
    arg_util.ApplyLowerPriorityArgs(args, typed_defaults)
    self.assertEqual(args.donate, 'feels-good')

  def testApplyArgDefaults_RequiredArgHasValue_NoDefaultApplied(self):
    args = argparse.Namespace(blood='1 gallon')
    shared_defaults = fake_args.SharedArgRules()['defaults']
    typed_defaults = fake_args.TypedArgRules()['o-positive']['defaults']
    arg_util.ApplyLowerPriorityArgs(args, shared_defaults)
    arg_util.ApplyLowerPriorityArgs(args, typed_defaults)
    self.assertEqual(args.blood, '1 gallon')

  def testApplyArgDefaults_RequiredArgHasNoValue_DefaultApplied(self):
    args = argparse.Namespace(blood=None)
    shared_defaults = fake_args.SharedArgRules()['defaults']
    typed_defaults = fake_args.TypedArgRules()['o-positive']['defaults']
    arg_util.ApplyLowerPriorityArgs(args, shared_defaults)
    arg_util.ApplyLowerPriorityArgs(args, typed_defaults)
    self.assertEqual(args.blood, '1 pint')

  def testApplyArgDefaults_OptionalArgHasValue_NoDefaultApplied(self):
    args = argparse.Namespace(tomorrow='2:00PM')
    shared_defaults = fake_args.SharedArgRules()['defaults']
    typed_defaults = fake_args.TypedArgRules()['ab-negative']['defaults']
    arg_util.ApplyLowerPriorityArgs(args, shared_defaults)
    arg_util.ApplyLowerPriorityArgs(args, typed_defaults)
    self.assertEqual(args.tomorrow, '2:00PM')

  def testApplyArgDefaults_OptionalArgHasNoValue_DefaultApplied(self):
    args = argparse.Namespace(tomorrow=None)
    shared_defaults = fake_args.SharedArgRules()['defaults']
    typed_defaults = fake_args.TypedArgRules()['ab-negative']['defaults']
    arg_util.ApplyLowerPriorityArgs(args, shared_defaults)
    arg_util.ApplyLowerPriorityArgs(args, typed_defaults)
    self.assertEqual(args.tomorrow, 'procrastinator')


def _FakeArgManager():
  return arg_manager.AndroidArgsManager(
      catalog_manager.AndroidCatalogManager(fake_args.AndroidCatalog()),
      fake_args.TypedArgRules(),
      fake_args.SharedArgRules())


if __name__ == '__main__':
  test_case.main()
