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

"""Unit tests for the help search filter expression rewrite module."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.command_lib.search_help import filter_rewrite
from tests.lib import subtests
from tests.lib import test_case


class SearchHelpFilterRewriteTest(subtests.Base):

  def SetUp(self):
    self.rewrite = filter_rewrite.SearchTerms().Rewrite

  def RunSubTest(self, expression):
    return self.rewrite(expression)[1]

  def testResourceFilterBackend(self):

    def T(expected, expression, exception=None):
      self.Run(expected, expression, depth=2, exception=exception)

    T(None,
      '')

    T([{'a': None}],
      'a')
    T(['AND', {'a': None}, {'b': None}],
      'a b')
    T(['AND', {'a': None}, {'b': None}, {'c': None}],
      'a b c')

    T([{'a': None}],
      'a')
    T(['OR', {'a': None}, {'b': None}],
      'a OR b')
    T(['OR', {'a': None}, {'b': None}, {'c': None}],
      'a OR b OR c')

    T(['AND', {'a': None}, ['OR', {'b': None}, {'c': None}]],
      'a b OR c')
    T(['OR', ['AND', {'a': None}, {'b': None}], {'c': None}],
      '( a AND b ) OR c')

    T(['AND', ['OR', {'a': None}, {'b': None}], {'c': None}],
      'a OR b c')
    T(['OR', {'a': None}, ['AND', {'b': None}, {'c': None}]],
      'a OR (b AND c)')

    T(['AND', {'a': None}, {'b': None}, {'c': None}],
      '(a AND b) AND c')
    T(['AND',
       ['OR', {'a': None}, {'b': None}],
       ['OR', {'c': None}, {'d': None}]],
      '(a OR b) AND ( c OR d)')
    T(['AND', {'a': None}, {'b': None}, ['OR', {'c': None}, {'d': None}]],
      '(a AND b) AND (c OR d)')
    T(['AND', {'a': None}, {'b': None}, {'c': None}, {'d': None}],
      '(a AND b) AND (c AND d)')
    T(['AND', {'a': None}, {'b': None}, {'c': None}],
      '(a AND b) AND c')

    T(['AND', {'zone': 'flag'}, {'alpha': 'release'}],
      'flag:zone release:alpha')
    T(['OR', {'zone': 'flag'}, {'alpha': 'release'}],
      'flag:zone OR release:alpha')

    T(['AND', ['OR', {'zone': 'flag'}, {'alpha': 'release'}], {'iam': None}],
      '(flag:zone OR release:alpha) AND iam')
    T(['OR', ['AND', {'zone': 'flag'}, {'alpha': 'release'}], {'iam': None}],
      '(flag:zone AND release:alpha) OR iam')

    T(None,
      'a=b',
      filter_rewrite.OperatorNotSupportedError)
    T(None,
      'NOT a',
      filter_rewrite.OperatorNotSupportedError)


if __name__ == '__main__':
  test_case.main()
