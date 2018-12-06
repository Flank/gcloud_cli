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

"""Tests for googlecloudsdk.command_lib.util.args.repeated."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.args import repeated
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope import util


class Obj(object):

  def __init__(self, values, extra_value):
    self.value_1 = [values.pop(0)]
    self.value_2 = [values.pop(0)]
    self.value_3 = [extra_value]


class CachedResultTest(test_case.TestCase):

  def testGet_OnlyCallsOnce(self):
    values = [1]
    result = repeated.CachedResult(values.pop)
    self.assertEqual(result.Get(), 1)
    self.assertEqual(result.Get(), 1)

  def testGet_FromFunc(self):
    values = [1, 2]
    result = repeated.CachedResult.FromFunc(values.pop, 0)
    self.assertEqual(result.Get(), 1)
    self.assertEqual(result.Get(), 1)

  def testGetAttrThunk(self):
    values = [1, 2]
    result = repeated.CachedResult.FromFunc(Obj, values, 3)
    self.assertEqual(result.GetAttrThunk('value_1')(), [1])
    self.assertEqual(result.GetAttrThunk('value_2')(), [2])
    self.assertEqual(result.GetAttrThunk('value_3')(), [3])

  def testGetAttrThunk_Transform(self):
    values = [1, 2]
    result = repeated.CachedResult.FromFunc(Obj, values, 3)
    negate = lambda x: -x
    self.assertEqual(result.GetAttrThunk('value_1', negate)(), [-1])
    self.assertEqual(result.GetAttrThunk('value_2', negate)(), [-2])
    self.assertEqual(result.GetAttrThunk('value_3', negate)(), [-3])


class AddAndParseListArgs(test_case.WithOutputCapture, parameterized.TestCase):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    repeated.AddPrimitiveArgs(self.parser, 'foo', 'bars', 'bars',
                              additional_help='Helps you bar.')

  def testHelp(self):
    with self.assertRaises(SystemExit):
      self.parser.parse_known_args(['--help'])

    self.AssertOutputContains(
        '--add-bars BARS Append the given values to the current bars',
        normalize_space=True)
    self.AssertOutputContains(
        '--clear-bars Empty the current bars.', normalize_space=True)
    self.AssertOutputContains(
        '--remove-bars BARS Remove the given values from the current bars',
        normalize_space=True)
    self.AssertOutputContains(
        '--set-bars BARS '
        'Completely replace the current bars with the given\nvalues',
        normalize_space=True)

  def testMutuallyExclusive(self):
    args, _ = self.parser.parse_known_args(
        '--clear-bars --set-bars a,b'.split(' '))
    with self.assertRaises(ValueError):
      # This should be caught at argument parse time, but in a test context full
      # argument parsing is hard to replicate.
      repeated.ParsePrimitiveArgs(args, 'bars', [].pop)

  @parameterized.named_parameters(
      ('Add', ['a'], '--add-bars b', ['a', 'b']),
      ('AddStartsEmpty', [], '--add-bars a,b', ['a', 'b']),
      ('AddNoop', ['a', 'b', 'c'], '--add-bars a,b', None),
      ('AddPartialNoop', ['a'], '--add-bars a,b', ['a', 'b']),
      ('AddNothing', ['a'], '--add-bars ', None),
      ('Remove', ['a', 'b', 'c'], '--remove-bars a,b', ['c']),
      ('RemoveNoop', [], '--remove-bars a,b', None),
      ('RemovePartialNoop', ['a', 'c'], '--remove-bars a,b', ['c']),
      ('RemoveRemoveNothing', ['a'], '--remove-bars ', None),
      ('SetBars', None, '--set-bars a,b', ['a', 'b']),
      ('SetBarsEmpty', None, '--set-bars ', []),
      ('ClearBars', None, '--clear-bars', []),
  )
  def testParse(self, before, flag_value, expected):
    if before is None:
      result = repeated.CachedResult([].pop)
    else:
      result = repeated.CachedResult([before].pop)

    args, _ = self.parser.parse_known_args(flag_value.split(' '))

    after = repeated.ParsePrimitiveArgs(args, 'bars', result.Get)
    self.assertEqual(after, expected)

  def _ParseResource(self, name):
    return resources.REGISTRY.Parse(
        name, params={'projectsId': 'fake-project'},
        collection='pubsub.projects.topics')

  @parameterized.named_parameters(
      ('Add', ['a'], '--add-bars b', ['a', 'b']),
      ('AddStartsEmpty', [], '--add-bars a,b', ['a', 'b']),
      ('AddNoop', ['a', 'b', 'c'], '--add-bars a,b', None),
      ('AddPartialNoop', ['a'], '--add-bars a,b', ['a', 'b']),
      ('AddNothing', ['a'], '--add-bars ', None),
      ('Remove', ['a', 'b', 'c'], '--remove-bars a,b', ['c']),
      ('RemoveNoop', [], '--remove-bars a,b', None),
      ('RemovePartialNoop', ['a', 'c'], '--remove-bars a,b', ['c']),
      ('RemoveRemoveNothing', ['a'], '--remove-bars ', None),
      ('SetBars', None, '--set-bars a,b', ['a', 'b']),
      ('SetBarsEmpty', None, '--set-bars ', []),
      ('ClearBars', None, '--clear-bars', []),
      ('AddWithRelativeName', ['a'],
       '--add-bars projects/fake-project/topics/b', ['a', 'b']),
  )
  def testParseResourceName(self, before, flag_value, expected):
    if before is None:
      result = repeated.CachedResult([].pop)
    else:
      before = ['projects/fake-project/topics/' + b for b in before]
      result = repeated.CachedResult([before].pop)

    args, _ = self.parser.parse_known_args(flag_value.split(' '))

    after = repeated.ParseResourceNameArgs(
        args, 'bars', result.Get, self._ParseResource)

    if expected:
      expected = ['projects/fake-project/topics/' + e for e in expected]
    self.assertEqual(after, expected)


class AddAndParseDictArgs(test_case.WithOutputCapture):

  def testHelp(self):
    parser = util.ArgumentParser()
    repeated.AddPrimitiveArgs(
        parser,
        'foo',
        'bars',
        'bars',
        additional_help='Helps you bar.',
        is_dict_args=True)

    with self.assertRaises(SystemExit):
      parser.parse_known_args(['--help'])

    self.AssertOutputContains("""\
--update-bars BARS Update the given key-value pairs in the current bars.
 """, normalize_space=True)
    self.AssertOutputContains(
        '--clear-bars Empty the current bars.', normalize_space=True)
    self.AssertOutputContains("""\
--remove-bars BARS Remove the key-value pairs from the current bars with
the given keys.
""", normalize_space=True)
    self.AssertOutputContains("""\
--set-bars BARS Completely replace the current bars with the given key-
value pairs.
""", normalize_space=True)


if __name__ == '__main__':
  test_case.main()
