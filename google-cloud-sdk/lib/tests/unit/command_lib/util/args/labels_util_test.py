# -*- coding: utf-8 -*- #
# -*- coding: UTF-8 -*-
#
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Unit tests for the labels_util module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.util.args import labels_util
from tests.lib import parameterized
from tests.lib import subtests
from tests.lib import test_case


class LabelsUtilAddLabelsFlagsTest(test_case.TestCase):

  def testAddCreateLabelsFlags(self):
    parser = argparse.ArgumentParser()
    labels_util.AddCreateLabelsFlags(parser)
    args = parser.parse_args(['--labels=key1=value1,key2=value2'])

    self.assertTrue(hasattr(args, 'labels'))
    self.assertFalse(hasattr(args, 'update_labels'))
    self.assertFalse(hasattr(args, 'remove_labels'))

    expected_update = {
        'key1': 'value1',
        'key2': 'value2',
    }
    actual_update = labels_util.GetUpdateLabelsDictFromArgs(args)
    self.assertEqual(expected_update, actual_update)

  def testAddUpdateLabelsFlags(self):
    parser = argparse.ArgumentParser()
    labels_util.AddUpdateLabelsFlags(parser)
    args = parser.parse_args([
        '--update-labels=key1=value1,key2=value2',
        '--remove-labels=key3,key4',
    ])

    self.assertFalse(hasattr(args, 'labels'))
    self.assertTrue(hasattr(args, 'update_labels'))
    self.assertTrue(hasattr(args, 'remove_labels'))

    expected_update = {
        'key1': 'value1',
        'key2': 'value2',
    }
    actual_update = labels_util.GetUpdateLabelsDictFromArgs(args)
    self.assertEqual(expected_update, actual_update)

    expected_remove = [
        'key3',
        'key4',
    ]
    actual_remove = labels_util.GetRemoveLabelsListFromArgs(args)
    self.assertEqual(expected_remove, actual_remove)


class GetAndValidateArgsTest(test_case.TestCase):

  class Args(object):

    def __init__(self):
      self.remove_labels = None
      self.update_labels = None
      self.clear_labels = False

  def testMissingArguments(self):
    args = GetAndValidateArgsTest.Args()
    with self.assertRaisesRegex(
        calliope_exceptions.RequiredArgumentException,
        'At least one of --update-labels, --remove-labels, or '
        '--clear-labels must be specified.'):
      labels_util.GetAndValidateOpsFromArgs(args)

  def testUpdateLabelsArg(self):
    args = GetAndValidateArgsTest.Args()
    args.update_labels = {'a': 'b'}
    labels_util.GetAndValidateOpsFromArgs(args)
    diff = labels_util.GetAndValidateOpsFromArgs(args)
    self.assertEqual(diff._additions['a'], 'b')
    self.assertFalse(diff._subtractions)

  def testRemoveLabelsArg(self):
    args = GetAndValidateArgsTest.Args()
    args.remove_labels = ['xyz']
    labels_util.GetAndValidateOpsFromArgs(args)
    diff = labels_util.GetAndValidateOpsFromArgs(args)
    self.assertFalse(diff._additions)
    self.assertEqual(diff._subtractions[0], 'xyz')

  def testUpdateAndRemoveLabelsArg(self):
    args = GetAndValidateArgsTest.Args()
    args.update_labels = {'a': 'b'}
    args.remove_labels = ['xyz']
    diff = labels_util.GetAndValidateOpsFromArgs(args)
    self.assertEqual(diff._additions['a'], 'b')
    self.assertEqual(diff._subtractions[0], 'xyz')


class IsValidLabelKeyTest(subtests.Base, test_case.WithOutputCapture):

  def SetUp(self):
    self.SetEncoding('utf8')

  def RunSubTest(self, string):
    result = labels_util.IsValidLabelKey(string)
    try:
      valid = labels_util.KEY_FORMAT_VALIDATOR(string)
    except arg_parsers.ArgumentTypeError:
      valid = None
    if (valid is None) != (result is False):
      self.fail('For input string "{0}", IsValidLabelKey returned {1}, but '
                'KEY_FORMAT_VALIDATOR disagrees.'.format(string, result))
    return result

  def testIsValidLabelKey(self):

    def Test(expected, string, exception=None):
      self.Run(expected, string, depth=2, exception=exception)

    Test(False, '-est-')
    Test(False, '_est_')
    Test(False, '8語')
    Test(False, '-ö')

    Test(True, 'test')
    Test(True, 'test-')
    Test(True, 'test_')
    Test(True, '語')
    Test(True, 'test8')
    Test(True, 'test-_8')
    Test(True, 'ö')

    Test(False, 'tEst')
    Test(False, 'Test')
    Test(False, 't.')
    Test(False, 't?')
    Test(False, 't!')
    Test(False, 't>')
    Test(False, 'yÖ')


class IsValidLabelValueTest(subtests.Base, test_case.WithOutputCapture):

  def SetUp(self):
    self.SetEncoding('utf8')

  def RunSubTest(self, string):
    result = labels_util.IsValidLabelValue(string)
    try:
      valid = labels_util.VALUE_FORMAT_VALIDATOR(string)
    except arg_parsers.ArgumentTypeError:
      valid = None
    if (valid is None) != (result is False):
      self.fail('For input string "{0}", IsValidLabelValue returned {1}, but '
                'VALUE_FORMAT_VALIDATOR disagrees.'.format(string, result))
    return result

  def testIsValidLabelValue(self):

    def Test(expected, string, exception=None):
      self.Run(expected, string, depth=2, exception=exception)

    Test(True, '-est-')
    Test(True, '_est_')
    Test(True, '8語')
    Test(True, '-ö')

    Test(True, 'test')
    Test(True, 'test-')
    Test(True, 'test_')
    Test(True, '語')
    Test(True, 'test8')
    Test(True, 'test-_8')
    Test(True, 'ö')

    Test(False, 'tEst')
    Test(False, 'Test')
    Test(False, 't.')
    Test(False, 't?')
    Test(False, 't!')
    Test(False, 't>')
    Test(False, 'yÖ')


class DiffTest(parameterized.TestCase, test_case.TestCase):

  def SetUp(self):
    self.labels_cls = projects_util.GetMessages().Project.LabelsValue

  def _MakeLabels(self, labels):
    if labels is None:
      return None
    return self.labels_cls(additionalProperties=[
        self.labels_cls.AdditionalProperty(key=key, value=value)
        for key, value in labels])

  @parameterized.named_parameters(
      ('UpdateOnly',
       '--update-labels foo=bar,baz=qux',
       [('foo', 'bar')], [('baz', 'qux'), ('foo', 'bar')], True),
      ('NoOp', '--update-labels foo=bar',
       [('foo', 'bar')], [('foo', 'bar')], False),
      ('RemoveOnly',
       '--remove-labels baz',
       [('foo', 'bar'), ('baz', 'qux')], [('foo', 'bar')], True),
      ('RemoveAll',
       '--remove-labels foo,baz',
       [('foo', 'bar'), ('baz', 'qux')], [], True),
      ('RemoveNonExisting',
       '--remove-labels foo', [], [], False),
      ('NoArgsNoExistingLabels', '', None, [], False),
      ('NoArgsEmptyExistingLabels', '', [], [], False),
      ('NoArgsExistingLabels', '', [('foo', 'bar')], [('foo', 'bar')], False),
      ('UpdateAndRemoveSameLabel',
       '--update-labels foo=baz --remove-labels foo',
       [], [], False),
      ('UpdateAndRemoveSameLabelExists',
       '--update-labels foo=baz --remove-labels foo',
       [('foo', 'bar')], [], True),
      ('UpdateAndRemoveDifferentLabels',
       '--update-labels baz=qux --remove-labels foo',
       [('foo', 'bar')], [('baz', 'qux')], True),
  )
  def testFromUpdateArgs(self, args_string, original_labels, expected_labels,
                         needs_update):
    parser = argparse.ArgumentParser()
    labels_util.AddUpdateLabelsFlags(parser)
    args = parser.parse_args(args_string.split())
    original_value = self._MakeLabels(original_labels)

    result = labels_util.Diff.FromUpdateArgs(args).Apply(self.labels_cls,
                                                         original_value)

    expected = self._MakeLabels(expected_labels)
    self.assertEqual(result._labels, expected)
    self.assertEqual(result.needs_update, needs_update)

  @parameterized.named_parameters(
      ('UpdateOnly',
       '--update-labels foo=bar,baz=qux',
       [('foo', 'bar')], [('baz', 'qux'), ('foo', 'bar')], True),
      ('NoOp', '--update-labels foo=bar',
       [('foo', 'bar')], [('foo', 'bar')], False),
      ('RemoveOnly', '--remove-labels baz',
       [('foo', 'bar'), ('baz', 'qux')], [('baz', None), ('foo', 'bar')], True),
      ('RemoveAll', '--remove-labels foo,baz',
       [('foo', 'bar'), ('baz', 'qux')], [('baz', None), ('foo', None)], True),
      ('RemoveNonExisting',
       '--remove-labels foo', [], [], False),
      ('NoArgsNoExistingLabels', '', None, [], False),
      ('NoArgsEmptyExistingLabels', '', [], [], False),
      ('NoArgsExistingLabels', '', [('foo', 'bar')], [('foo', 'bar')], False),
      ('UpdateAndRemoveSameLabel',
       '--update-labels foo=baz --remove-labels foo', [], [], False),
      ('UpdateAndRemoveSameLabelExists',
       '--update-labels foo=baz --remove-labels foo',
       [('foo', 'bar')], [('foo', None)], True),
      ('UpdateAndRemoveDifferentLabels',
       '--update-labels baz=qux --remove-labels foo',
       [('foo', 'bar')], [('baz', 'qux'), ('foo', None)], True),
  )
  def testFromUpdateArgsExplicitlyNullify(self, args_string, original_labels,
                                          expected_labels, needs_update):
    parser = argparse.ArgumentParser()
    labels_util.AddUpdateLabelsFlags(parser)
    args = parser.parse_args(args_string.split())
    original_value = self._MakeLabels(original_labels)

    result = labels_util.ExplicitNullificationDiff.FromUpdateArgs(args).Apply(
        self.labels_cls, original_value)

    expected = self._MakeLabels(expected_labels)
    self.assertEqual(result._labels, expected)
    self.assertEqual(result.needs_update, needs_update)

  @parameterized.named_parameters(
      ('ClearOnly',
       '--clear-labels',
       [('foo', 'bar')], [], True),
      ('ClearNoExistingLabels',
       '--clear-labels',
       None, [], False),
      ('ClearEmptyExistingLabels',
       '--clear-labels',
       [], [], False),
      ('ClearAndUpdate',
       '--clear-labels --update-labels bar=qux',
       [('foo', 'bar')], [('bar', 'qux')], True),
      ('ClearBeforeUpdate',
       '--clear-labels --update-labels foo=baz,bar=qux',
       [('foo', 'bar')], [('bar', 'qux'), ('foo', 'baz')], True),
  )
  def testClear(self, args_string, original_labels, expected_labels,
                needs_update):
    parser = argparse.ArgumentParser()
    labels_util.AddUpdateLabelsFlags(parser, enable_clear=True)
    args = parser.parse_args(args_string.split())
    original_value = self._MakeLabels(original_labels)

    result = labels_util.Diff.FromUpdateArgs(args, enable_clear=True).Apply(
        self.labels_cls, original_value)

    expected = self._MakeLabels(expected_labels)
    self.assertEqual(result._labels, expected)
    self.assertEqual(result.needs_update, needs_update)

  @parameterized.named_parameters(
      ('ClearOnly',
       '--clear-labels',
       [('foo', 'bar')], [('foo', None)], True),
      ('ClearNoExistingLabels',
       '--clear-labels',
       None, [], False),
      ('ClearEmptyExistingLabels',
       '--clear-labels',
       [], [], False),
      ('ClearAndUpdate',
       '--clear-labels --update-labels bar=qux',
       [('foo', 'bar')], [('bar', 'qux'), ('foo', None)], True),
      ('ClearBeforeUpdate',
       '--clear-labels --update-labels foo=baz,bar=qux',
       [('foo', 'bar')], [('bar', 'qux'), ('foo', 'baz')], True),
  )
  def testClearExplicitNullification(self, args_string, original_labels,
                                     expected_labels, needs_update):
    parser = argparse.ArgumentParser()
    labels_util.AddUpdateLabelsFlags(parser, enable_clear=True)
    args = parser.parse_args(args_string.split())
    original_value = self._MakeLabels(original_labels)

    result = labels_util.ExplicitNullificationDiff.FromUpdateArgs(
        args, enable_clear=True).Apply(self.labels_cls, original_value)

    expected = self._MakeLabels(expected_labels)
    self.assertEqual(result._labels, expected)
    self.assertEqual(result.needs_update, needs_update)

  def testClearAndRemoveLabelsNotAllowed(self):
    parser = argparse.ArgumentParser()
    labels_util.AddUpdateLabelsFlags(parser, enable_clear=True)
    with self.assertRaises(SystemExit):
      parser.parse_args('--remove-labels foo --clear-labels'.split())
    with self.assertRaises(ValueError):
      labels_util.Diff(subtractions=['foo'], clear=True)


class CreationTest(parameterized.TestCase, test_case.TestCase):

  def SetUp(self):
    self.labels_cls = projects_util.GetMessages().Project.LabelsValue

  def _MakeLabels(self, labels):
    if labels is None:
      return None
    return self.labels_cls(additionalProperties=[
        self.labels_cls.AdditionalProperty(key=key, value=value)
        for key, value in labels])

  @parameterized.parameters(
      (['--labels', 'foo=bar,baz=qux'], [('baz', 'qux'), ('foo', 'bar')]),
      ([], None)
  )
  def testParseCreateArgs(self, args_list, expected_labels):
    parser = argparse.ArgumentParser()
    labels_util.AddCreateLabelsFlags(parser)
    args = parser.parse_args(args_list)

    result = labels_util.ParseCreateArgs(args, self.labels_cls)

    expected = self._MakeLabels(expected_labels)
    self.assertEqual(result, expected)

  @parameterized.named_parameters(
      ('NoArgs', '', None, [], False),
      ('UpdateEmpty', '--update-labels foo=bar', [], [('foo', 'bar')], True),
      ('Remove', '--remove-labels foo', [('foo', 'bar')], [], True),
      ('Clear', '--clear-labels', [('foo', 'bar')], [], True),
  )
  def testProcessUpdateArgsLazy(self, args_string, original_labels,
                                expected_labels, needs_update):
    parser = argparse.ArgumentParser()
    labels_util.AddUpdateLabelsFlags(parser)
    args = parser.parse_args(args_string.split())
    def _GetLabels():
      if original_labels is None:
        self.fail('Should not call the orig_labels_thunk.')
      return self._MakeLabels(original_labels)

    result = labels_util.ProcessUpdateArgsLazy(args, self.labels_cls,
                                               _GetLabels)
    expected = self._MakeLabels(expected_labels)
    self.assertEqual(result._labels, expected)
    self.assertEqual(result.needs_update, needs_update)


if __name__ == '__main__':
  test_case.main()
