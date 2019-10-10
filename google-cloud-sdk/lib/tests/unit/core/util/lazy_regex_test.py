# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Unit tests for googlecloudsdk.core.util.parallel."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core.util import lazy_regex
from tests.lib import test_case

import mock


class LazyRegexTest(test_case.TestCase):

  def testLazySREPattern(self):
    lazy_pattern = lazy_regex._Lazy_SRE_Pattern('test .*')
    actual = lazy_pattern.search('foobar test input').group(0)
    expected = 'test input'
    self.assertEqual(expected, actual)

  @mock.patch('googlecloudsdk.core.util.lazy_regex_patterns.PATTERNS',
              frozenset(('test_pattern',)))
  def testLazyCompile_Lazy(self):
    regex = lazy_regex._lazy_compile('test_pattern')
    self.assertIsInstance(regex, lazy_regex._Lazy_SRE_Pattern)

  def testLazyCompile_NotLazy(self):
    regex = lazy_regex._lazy_compile('test_pattern_not_in_lazy_regex')
    self.assertNotIsInstance(regex, lazy_regex._Lazy_SRE_Pattern)

  @mock.patch('re.compile')
  def testInitializeLazyCompile(self, compile_mock):
    lazy_regex.initialize_lazy_compile()
    self.assertNotEqual(compile_mock, re.compile)
    self.assertEqual(lazy_regex._lazy_compile, re.compile)


if __name__ == '__main__':
  test_case.main()
