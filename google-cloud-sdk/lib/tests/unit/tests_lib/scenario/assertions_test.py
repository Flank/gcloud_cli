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

"""Tests for the mock_http module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.scenario import assertions
from tests.lib.scenario import updates


class AssertionTests(test_case.TestCase, parameterized.TestCase):
  @parameterized.parameters([
      (assertions.EqualsAssertion(''), '', True),
      (assertions.EqualsAssertion(''), 'asdf', False),
      (assertions.EqualsAssertion('asdf'), 'asdf', True),
      (assertions.EqualsAssertion('asdf'), 'qwer', False),

      (assertions.MatchesAssertion('asdf'), 'asdf', True),
      (assertions.MatchesAssertion('a.*'), 'asdf', True),
      (assertions.MatchesAssertion('b.*'), 'asdf', False),
      (assertions.MatchesAssertion(''), 'asdf', False),
      (assertions.MatchesAssertion('.*'), 'asdf', True),

      (assertions.IsNoneAssertion(True), None, True),
      (assertions.IsNoneAssertion(True), 'asdf', False),
      (assertions.IsNoneAssertion(True), True, False),
      (assertions.IsNoneAssertion(True), False, False),
      (assertions.IsNoneAssertion(True), 1, False),
      (assertions.IsNoneAssertion(False), None, False),
      (assertions.IsNoneAssertion(False), 'asdf', True),
      (assertions.IsNoneAssertion(False), True, True),
      (assertions.IsNoneAssertion(False), False, True),
      (assertions.IsNoneAssertion(False), 1, True),

      (assertions.InAssertion({1, 2, 3}), 1, True),
      (assertions.InAssertion({1, 2, 3}), 4, False),
      (assertions.InAssertion({1, 2, 3}), 'a', False),
      (assertions.InAssertion({1, 2, 3}), None, False),
      (assertions.InAssertion({'a', 'b', 'c'}), 'a', True),
      (assertions.InAssertion({'a', 'b', 'c'}), 'd', False),
      (assertions.InAssertion({'a', 'b', 'c'}), 1, False),
      (assertions.InAssertion({'a', 'b', 'c'}), None, False),

      (assertions.DictAssertion(), {}, True),
      (assertions.DictAssertion().Equals('a', 'b'), {}, False),
      (assertions.DictAssertion().Equals('a', 'b'), {'a': 'b'}, True),
      (assertions.DictAssertion().Equals('a', 'b'), {'a': 'c'}, False),

      (assertions.DictAssertion().Matches('a', 'b'), {}, False),
      (assertions.DictAssertion().Matches('a', 'b'), {'a': 'b'}, True),
      (assertions.DictAssertion().Matches('a', 'b'), {'a': 'c'}, False),
      (assertions.DictAssertion().Matches('a', '.*'), {'a': 'c'}, True),
      (assertions.DictAssertion().Matches(
          'a', 'as.*df'), {'a': 'asqwerdf'}, True),

      (assertions.DictAssertion().IsNone('a'), {}, True),
      (assertions.DictAssertion().IsNone('a'), {'a': 'b'}, False),

      (assertions.DictAssertion().In('a', ['1', '2', '3']), {}, False),
      (assertions.DictAssertion().In('a', ['1', '2', '3']), {'a': 'b'}, False),
      (assertions.DictAssertion().In('a', ['1', '2', '3']), {'a': '1'}, True),
  ])
  def testAssertion(self, assertion, actual, matches):
    if matches:
      with assertions.FailureCollector([]) as f:
        f.AddAll(assertion.Check(updates.Context.Empty(), actual))
    else:
      with self.assertRaises(assertions.Error):
        with assertions.FailureCollector([]) as f:
          f.AddAll(assertion.Check(updates.Context.Empty(), actual))

  @parameterized.parameters([
      (assertions.JsonAssertion().Matches('', {}), True),
      (assertions.JsonAssertion().Matches('', {'a': {}}), True),
      (assertions.JsonAssertion().Matches('', {'a': {'b': 'c'}}), True),
      (assertions.JsonAssertion().Matches('', {'a': {'b': 'c', 'f': 1}}), True),
      (assertions.JsonAssertion().Matches('', {'a': {'b': 'd'}}), False),
      (assertions.JsonAssertion().Matches('a.f', 1), True),
      (assertions.JsonAssertion().Matches('a.f', 2), False),
      (assertions.JsonAssertion().Matches('a.g', True), True),
      (assertions.JsonAssertion().Matches('a.g', False), False),
      (assertions.JsonAssertion().Matches('h.o.p', 'q'), True),
      (assertions.JsonAssertion().Matches('h.o.p', 'z'), False),
      (assertions.JsonAssertion().Matches('h.o', {'p': 'q'}), True),
      (assertions.JsonAssertion().Matches('list', {}), False),
      (assertions.JsonAssertion().Matches('list', []), False),
      (assertions.JsonAssertion().Matches('list', [1, 2]), False),
      (assertions.JsonAssertion().Matches('list', [{}, {}]), True),
      (assertions.JsonAssertion().Matches('list',
                                          [{'s': 't'}, {'y': 'z'}]), True),
      (assertions.JsonAssertion().Matches('list',
                                          [{'s': 't'}, {'y': 'x'}]), False),
      (assertions.JsonAssertion().Matches('list',
                                          [{'s': 't'}, {'z': 'asdf'}]), False),
      (assertions.JsonAssertion().Matches('list',
                                          [{'s': 't'}, {'y': 'z'},
                                           {'asdf', 'asdf'}]), False),
      (assertions.JsonAssertion().Matches('a.f', 1).Matches('a.b', 'c'), True),
      (assertions.JsonAssertion().Matches('a.f', 1).IsAbsent('a.x'), True),
      (assertions.JsonAssertion().Matches('a.f', 1).IsAbsent('a.d'), False),
      (assertions.JsonAssertion().Matches('n_l.l.a', [1, 3, 5]), True),
      (assertions.JsonAssertion().Matches('n_l.l.b', [2, 3]), False),
      (assertions.JsonAssertion().Matches('n_l.l.c', [0, 0]), False),
      (assertions.JsonAssertion().Matches('n_l.l', [{'a': 1, 'b': 2},
                                                    {'a': 3, 'b': 4},
                                                    {'a': 5, 'b': 6}]), True),
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
        'n_l': {'l': [
            {'a': 1, 'b': 2}, {'a': 3, 'b': 4}, {'a': 5, 'b': 6}
        ]}
    }
    if matches:
      with assertions.FailureCollector([]) as f:
        f.AddAll(assertion.Check(updates.Context.Empty(), actual))
    else:
      with self.assertRaises(assertions.Error):
        with assertions.FailureCollector([]) as f:
          f.AddAll(assertion.Check(updates.Context.Empty(), actual))


class FailureCollectionTests(test_case.TestCase):

  def testBasic(self):
    # No errors is OK.
    with assertions.FailureCollector([]):
      pass

    # Error is an error
    with self.assertRaises(assertions.Error):
      with assertions.FailureCollector([]) as f:
        f.Add(assertions.Failure.ForScalar(
            updates.Context.Empty(), 'expected', 'actual'))

  def testUpdateMode(self):
    context = updates.Context({}, 'field', updates.Mode.RESULT)

    # Fail if not in update mode.
    with self.assertRaises(assertions.Error):
      with assertions.FailureCollector([]) as f:
        f.Add(assertions.Failure.ForScalar(context, 'expected', 'actual'))

    # Updates without failures
    with assertions.FailureCollector([updates.Mode.RESULT]) as f:
      f.Add(assertions.Failure.ForScalar(context, 'expected', 'actual'))


if __name__ == '__main__':
  test_case.main()
