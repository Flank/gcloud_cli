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
"""Unit tests for the actions module."""
import argparse

from googlecloudsdk.calliope import actions as calliope_actions
from googlecloudsdk.calliope import parser_errors
from tests.lib import sdk_test_base
from tests.lib.calliope import util


class PreActionHookTest(sdk_test_base.WithLogCapture):

  def SetUp(self):
    action_call_stack = []

    class CustomTestAction(argparse.Action):

      def __call__(self, parser, namespace, value, option_string=None):
        action_call_stack.append('customTestAction')
        setattr(namespace, self.dest, value)

    def func_test(val):
      action_call_stack.append('Calling Wrapper on {0}'.format(val))

    self.func_test = func_test
    self.custom_action = CustomTestAction
    self.parser = util.ArgumentParser()
    self.action_call_stack = action_call_stack

  def testInvalidAction(self):
    error_str = ('action should be either a subclass of argparse.Action or a '
                 'string representing one of the default argparse Action Types')

    with self.assertRaisesRegexp(TypeError, error_str):
      self.parser.add_argument(
          'test-arg',
          action=calliope_actions._PreActionHook(object, lambda _: False),
          help='Test help')

  def testInvalidActionString(self):
    with self.assertRaisesRegexp(ValueError, 'unknown action "foo"'):
      self.parser.add_argument(
          'test_arg',
          action=calliope_actions._PreActionHook('foo', lambda _: False),
          help='Test help')

  def testInvalidFunction(self):
    error_str = r'func should be a callable of the form func\(value\)'
    with self.assertRaisesRegexp(TypeError, error_str):
      self.parser.add_argument(
          '--testarg',
          action=calliope_actions._PreActionHook(self.custom_action,
                                                 'non-func'),
          help='Test help')

  def testMalformedFunction(self):
    with self.assertRaises(TypeError):
      self.parser.add_argument(
          '--testarg',
          action=calliope_actions._PreActionHook(self.custom_action,
                                                 lambda x, y, z: True),
          help='Test help')
      self.parser.parse_args(['--testarg', 'foo'])

  def testPreActionHook(self):
    self.parser.add_argument(
        '--testarg',
        action=calliope_actions._PreActionHook(self.custom_action,
                                               self.func_test),
        help='Test help')
    self.parser.parse_args(['--testarg', 'foo'])
    self.assertEquals(self.action_call_stack[0], 'Calling Wrapper on foo')
    self.assertEquals(self.action_call_stack[1], 'customTestAction')

  def testAdditionalHelp(self):
    arg = self.parser.add_argument(
        '--testarg',
        action=calliope_actions._PreActionHook(
            self.custom_action, self.func_test,
            calliope_actions._AdditionalHelp(label='TESTING',
                                             message='Test Additional Help')),
        help='Test help')
    self.parser.parse_args(['--testarg', 'foo'])
    help_str = r'TESTING Test help.[+\s]*Test Additional Help'
    self.assertRegexpMatches(arg.help.replace('\n', ' '), help_str)


class DeprecationActionTest(sdk_test_base.WithLogCapture):

  def SetUp(self):
    action_call_stack = []

    class CustomTestAction(argparse.Action):

      def __call__(self, parser, namespace, value, option_string=None):
        action_call_stack.append('customTestAction')
        setattr(namespace, self.dest, value)

    def custom_validation(value):
      action_call_stack.append('Calling Validation on {0}'.format(value))
      return True

    self.custom_action = CustomTestAction
    self.custom_validation_func = custom_validation
    self.parser = util.ArgumentParser()
    self.action_call_stack = action_call_stack

  def testDeprecateDefaults(self):
    self.parser.add_argument(
        '--testarg',
        action=calliope_actions.DeprecationAction('testarg'),
        help='Test help')
    self.parser.parse_args(['--testarg', 'foo'])
    self.AssertLogContains('Flag testarg is deprecated.')

  def testRemoveDefaults(self):
    error_str = 'Flag testarg has been removed.'
    with self.assertRaises(SystemExit):
      self.parser.add_argument(
          '--testarg',
          action=calliope_actions.DeprecationAction('testarg', removed=True),
          help='Test help')
      self.parser.parse_args(['--testarg', 'foo'])
    self.AssertErrContains(error_str)

  def testDeprecateCustomAction(self):
    warning = 'Custom Test Warning.'
    self.parser.add_argument(
        '--testarg',
        action=calliope_actions.DeprecationAction('testarg',
                                                  warn=warning,
                                                  action=self.custom_action),
        help='Test help')
    self.parser.parse_args(['--testarg', 'foo'])
    self.AssertLogContains('Custom Test Warning.')
    self.assertEquals(self.action_call_stack[0], 'customTestAction')
    self.assertEquals(len(self.action_call_stack), 1)

  def testRemoveCustomAction(self):
    error_str = 'Custom Test Error.'
    with self.assertRaises(SystemExit):
      self.parser.add_argument(
          '--testarg',
          action=calliope_actions.DeprecationAction('testarg',
                                                    removed=True,
                                                    error=error_str,
                                                    action=self.custom_action),
          help='Test help')
      self.parser.parse_args(['--testarg', 'foo'])
    self.AssertErrContains(error_str)

  def testDeprecateCustomValidation(self):
    warning = 'Custom Test Warning.'
    self.parser.add_argument(
        '--testarg',
        action=calliope_actions.DeprecationAction(
            'testarg',
            show_message=self.custom_validation_func,
            warn=warning,
            action=self.custom_action),
        help='Test help')

    self.parser.parse_args(['--testarg', 'foo'])
    self.AssertLogContains('Custom Test Warning.')
    self.assertEquals(self.action_call_stack[0], 'Calling Validation on foo')
    self.assertEquals(self.action_call_stack[1], 'customTestAction')

  def testRemoveCustomValidation(self):
    error_str = 'Custom Test Error.'
    with self.assertRaises(SystemExit):
      self.parser.add_argument(
          'test_arg',
          action=calliope_actions.DeprecationAction(
              'testarg',
              removed=True,
              show_message=self.custom_validation_func,
              error=error_str,
              action=self.custom_action),
          help='Test help')
      self.parser.parse_args(['--testarg', 'foo'])
    self.AssertErrContains(error_str)

  def testDeprecateHelp(self):
    warning = 'Custom Test Warning.'
    with self.assertRaises(SystemExit):
      self.parser.add_argument(
          '--testarg',
          action=calliope_actions.DeprecationAction(
              'testarg',
              show_message=self.custom_validation_func,
              warn=warning,
              action=self.custom_action),
          help='Test help.')
      self.parser.parse_args(['-h'])

    # NOTICE: This test triggers the argparse -h action directly and bypasses
    # the calliope markdown intercept. This means that markdown, like \n+\n,
    # leaks to the output.
    self.AssertOutputContains(
        '--testarg TESTARG  (DEPRECATED) Test help. + Custom Test Warning.')

  def testRemoveHelp(self):
    error_str = 'Custom Test Error.'
    with self.assertRaises(SystemExit):
      self.parser.add_argument(
          '--testarg',
          action=calliope_actions.DeprecationAction(
              'testarg',
              show_message=self.custom_validation_func,
              error=error_str,
              removed=True,
              action=self.custom_action),
          help='Test help.')
      self.parser.parse_args(['-h'])

    # NOTICE: This test triggers the argparse -h action directly and bypasses
    # the calliope markdown intercept. This means that markdown, like \n+\n,
    # leaks to the output.
    self.AssertOutputContains(
        '--testarg TESTARG  (REMOVED) Test help. + Custom Test Error.')


class DeprecationActionDefaultActionTests(sdk_test_base.WithLogCapture):

  def SetUp(self):
    action_calls = []

    def custom_validation(value):
      action_calls.append(value)
      return True

    self.parser = util.ArgumentParser()
    self.custom_func = custom_validation
    self.action_calls = action_calls

  def testDefaultFlagBehavior(self):
    self.parser.add_argument(
        '--testconst',
        action=calliope_actions.DeprecationAction(
            'testconst', action=argparse._StoreConstAction),
        const=85,
        help='Test Const help')

    self.parser.add_argument(
        '--default-test',
        action='store_true',
        help='Test Default Parser Test')
    namespace = self.parser.parse_args(['--default-test'])
    self.assertTrue(namespace.default_test)
    self.assertIsNone(namespace.testconst)
    self.AssertLogNotContains('Flag testconst is deprecated.')

  def testInvalidPositionalName(self):
    with self.assertRaisesRegexp(parser_errors.ArgumentException,
                                 "Positional arguments cannot contain a '-'."):
      self.parser.add_argument(
          'default-test',
          help='Invalid positional name test.')

  def testDeprecateStoreConstAction(self):
    self.parser.add_argument(
        '--testconst',
        action=calliope_actions.DeprecationAction(
            'testconst', action=argparse._StoreConstAction),
        const=75,
        help='Test Const help')
    namespace = self.parser.parse_args(['--testconst'])
    self.assertEquals(namespace.testconst, 75)
    self.AssertLogContains('Flag testconst is deprecated.')

  def testDeprecateStoreTrueAction(self):
    self.parser.add_argument(
        '--testtrue',
        action=calliope_actions.DeprecationAction(
            'testtrue', action='store_true'),
        help='Test True help')
    namespace = self.parser.parse_args(['--testtrue'])
    self.assertTrue(namespace.testtrue)
    self.AssertLogContains('Flag testtrue is deprecated.')

  def testDeprecateStoreFalseAction(self):
    self.parser.add_argument(
        '--testfalse',
        action=calliope_actions.DeprecationAction(
            'testfalse', action=argparse._StoreFalseAction),
        help='Test False help')
    namespace = self.parser.parse_args(['--testfalse'])
    self.assertFalse(namespace.testfalse)
    self.AssertLogContains('Flag testfalse is deprecated.')

  def testDeprecateAppendAction(self):
    self.parser.add_argument(
        '--testappend',
        action=calliope_actions.DeprecationAction(
            'testappend', action='append', show_message=self.custom_func),
        help='Test Append help')
    namespace = self.parser.parse_args(
        ['--testappend', 'Foo', '--testappend', 'Foo1'])
    self.assertEquals(namespace.testappend, ['Foo', 'Foo1'])
    self.AssertLogContains('Flag testappend is deprecated.')
    self.assertEquals(len(self.action_calls), 1)

  def testDeprecateAppendConstAction(self):
    self.parser.add_argument(
        '--testappendcnst',
        action=calliope_actions.DeprecationAction(
            'testappendcnst',
            action=argparse._AppendConstAction,
            show_message=self.custom_func),
        const='Bar',
        help='Test Append Const help')
    namespace = self.parser.parse_args(['--testappendcnst', '--testappendcnst'])
    self.assertEquals(namespace.testappendcnst, ['Bar', 'Bar'])
    self.AssertLogContains('Flag testappendcnst is deprecated.')
    self.assertEquals(len(self.action_calls), 1)

  def testDeprecateCountAction(self):
    self.parser.add_argument(
        '--testcount',
        action=calliope_actions.DeprecationAction(
            'testcount', action='count'),
        help='Test Count help')
    namespace = self.parser.parse_args(['--testcount'])
    self.assertEquals(namespace.testcount, 1)
    self.AssertLogContains('Flag testcount is deprecated.')
