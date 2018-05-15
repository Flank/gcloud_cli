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

"""Tests for the mock_http module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.scenario import assertions


def _Empty():
  return assertions.Context.Empty()


class AssertionTests(test_case.TestCase, parameterized.TestCase):
  @parameterized.parameters([
      (assertions.ScalarAssertion(_Empty(), ''), '', True),
      (assertions.ScalarAssertion(_Empty(), ''), 'asdf', False),
      (assertions.ScalarAssertion(_Empty(), 'asdf'), 'asdf', True),
      (assertions.ScalarAssertion(_Empty(), 'asdf'), 'qwer', False),

      (assertions.ScalarRegexAssertion(_Empty(), 'asdf'), 'asdf', True),
      (assertions.ScalarRegexAssertion(_Empty(), 'a.*'), 'asdf', True),
      (assertions.ScalarRegexAssertion(_Empty(), 'b.*'), 'asdf', False),
      (assertions.ScalarRegexAssertion(_Empty(), ''), 'asdf', False),
      (assertions.ScalarRegexAssertion(_Empty(), '.*'), 'asdf', True),

      (assertions.DictAssertion(_Empty()), {}, True),
      (assertions.DictAssertion(_Empty()).KeyEquals(
          'a', 'b'), {}, False),
      (assertions.DictAssertion(_Empty()).KeyEquals(
          'a', 'b'), {b'a': b'b'}, True),
      (assertions.DictAssertion(_Empty()).KeyEquals(
          'a', 'b'), {b'a': b'c'}, False),

      (assertions.DictAssertion(_Empty()).KeyMatches(
          'a', 'b'), {}, False),
      (assertions.DictAssertion(_Empty()).KeyMatches(
          'a', 'b'), {b'a': b'b'}, True),
      (assertions.DictAssertion(_Empty()).KeyMatches(
          'a', 'b'), {b'a': b'c'}, False),
      (assertions.DictAssertion(_Empty()).KeyMatches(
          'a', '.*'), {b'a': b'c'}, True),
      (assertions.DictAssertion(_Empty()).KeyMatches(
          'a', 'as.*df'), {b'a': b'asqwerdf'}, True),

      (assertions.DictAssertion(_Empty()).KeyIsAbsent('a'), {}, True),
      (assertions.DictAssertion(_Empty()).KeyIsAbsent(
          'a'), {b'a': b'b'}, False),
  ])
  def testAssertion(self, assertion, actual, matches):
    if matches:
      with assertions.FailureCollector() as f:
        assertion.Check(f, actual)
    else:
      with self.assertRaises(assertions.Error):
        with assertions.FailureCollector() as f:
          assertion.Check(f, actual)

  @parameterized.parameters([
      (assertions.JsonAssertion(_Empty()).Matches('', {}), True),
      (assertions.JsonAssertion(_Empty()).Matches('', {'a': {}}), True),
      (assertions.JsonAssertion(_Empty()).Matches(
          '', {'a': {'b': 'c'}}), True),
      (assertions.JsonAssertion(_Empty()).Matches(
          '', {'a': {'b': 'c', 'f': 1}}), True),
      (assertions.JsonAssertion(_Empty()).Matches(
          '', {'a': {'b': 'd'}}), False),
      (assertions.JsonAssertion(_Empty()).Matches('a.f', 1), True),
      (assertions.JsonAssertion(_Empty()).Matches('a.f', 2), False),
      (assertions.JsonAssertion(_Empty()).Matches('a.g', True), True),
      (assertions.JsonAssertion(_Empty()).Matches('a.g', False), False),
      (assertions.JsonAssertion(_Empty()).Matches('h.o.p', 'q'), True),
      (assertions.JsonAssertion(_Empty()).Matches('h.o.p', 'z'), False),
      (assertions.JsonAssertion(_Empty()).Matches('h.o', {'p': 'q'}), True),
      (assertions.JsonAssertion(_Empty()).Matches('list', {}), False),
      (assertions.JsonAssertion(_Empty()).Matches('list', []), False),
      (assertions.JsonAssertion(_Empty()).Matches('list', [1, 2]), False),
      (assertions.JsonAssertion(_Empty()).Matches(
          'list', [{}, {}]), True),
      (assertions.JsonAssertion(_Empty()).Matches(
          'list', [{'s': 't'}, {'y': 'z'}]), True),
      (assertions.JsonAssertion(_Empty()).Matches(
          'list', [{'s': 't'}, {'y': 'x'}]), False),
      (assertions.JsonAssertion(_Empty()).Matches(
          'list', [{'s': 't'}, {'z': 'asdf'}]), False),
      (assertions.JsonAssertion(_Empty()).Matches(
          'list', [{'s': 't'}, {'y': 'z'}, {'asdf', 'asdf'}]), False),
      (assertions.JsonAssertion(_Empty())
       .Matches('a.f', 1)
       .Matches('a.b', 'c'), True),
      (assertions.JsonAssertion(_Empty())
       .Matches('a.f', 1)
       .IsAbsent('a.x'), True),
      (assertions.JsonAssertion(_Empty())
       .Matches('a.f', 1)
       .IsAbsent('a.d'), False),
  ])
  def testCheckJsonConent(self, assertion, matches):
    actual = {
        'a': {'b': 'c', 'd': 'e', 'f': 1, 'g': True},
        'h': {
            'i': {'j': 'k', 'l': 'm'},
            'o': {'p': 'q', 'r': 'r'},
        },
        'list': [
            {'s': 't', 'u': 'v'},
            {'w': 'x', 'y': 'z'},
        ],
    }
    actual_str = json.dumps(actual)
    if matches:
      with assertions.FailureCollector() as f:
        assertion.Check(f, actual_str)
    else:
      with self.assertRaises(assertions.Error):
        with assertions.FailureCollector() as f:
          assertion.Check(f, actual_str)


class FailureCollectionTests(test_case.TestCase):

  def testBasic(self):
    # No errors is OK.
    with assertions.FailureCollector():
      pass

    # Error is an error
    with self.assertRaises(assertions.Error):
      with assertions.FailureCollector() as f:
        f.Add(assertions.Failure.ForScalar(
            assertions.Context.Empty(), 'expected', 'actual'))

  def testUpdateMode(self):
    hook = assertions.UpdateHook(
        lambda _: None, assertions.UpdateMode.RESULT)

    # Fail if not in update mode.
    with self.assertRaises(assertions.Error):
      with assertions.FailureCollector(update_modes=[]) as f:
        f.Add(assertions.Failure.ForScalar(
            assertions.Context.Empty(custom_update_hook=hook),
            'expected', 'actual'))

    # Updates without failures
    with assertions.FailureCollector(
        update_modes=[assertions.UpdateMode.RESULT]) as f:
      f.Add(assertions.Failure.ForScalar(
          assertions.Context.Empty(custom_update_hook=hook),
          'expected', 'actual'))


if __name__ == '__main__':
  test_case.main()
