# Lint as: python3
# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for google3.third_party.py.tests.unit.command_lib.privateca.filter_rewrite."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.privateca import filter_rewrite
from tests.lib import test_case


class FilterRewriteTest(test_case.TestCase):

  def testNoClientSide(self):
    rewriter = filter_rewrite.BackendFilterRewrite()
    for expression in [
        'a >= foo', 'a.b:foo', 'a="foo" OR b="foo bar"', 'a=10 AND b="foo"'
    ]:
      client_filter, server_filter = rewriter.Rewrite(expression)
      self.assertIsNone(client_filter)
      self.assertIsNotNone(server_filter)

  def testAllStringsAreQuoted(self):
    rewriter = filter_rewrite.BackendFilterRewrite()

    for expression, expected in [['a.b=foo', 'a.b="foo"'],
                                 ['a:foo.bar', 'a:"foo.bar"'],
                                 ['a="foo.bar"', 'a="foo.bar"']]:
      _, server_filter = rewriter.Rewrite(expression)
      self.assertEqual(server_filter, expected)

  def testIntegerNotQuoted(self):
    rewriter = filter_rewrite.BackendFilterRewrite()
    _, server_filter = rewriter.Rewrite('a=100')
    self.assertEqual(server_filter, 'a=100')


if __name__ == '__main__':
  test_case.main()
