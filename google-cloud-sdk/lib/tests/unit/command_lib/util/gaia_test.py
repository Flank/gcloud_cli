# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests for googlecloudsdk.command_lib.util.gaia."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.command_lib.util import gaia
from tests.lib import test_case


class GaiaUtilsTest(test_case.TestCase):

  def testSimpleUsername(self):
    self.assertEqual('user', gaia.
                     MapGaiaEmailToDefaultAccountName('user@google.com'))

  def testComplexUsername(self):
    self.assertEqual('user1_3_4_test', gaia.
                     MapGaiaEmailToDefaultAccountName(
                         'user1.3#4_TEST@google.com'))

  def testLongUsername(self):
    self.assertEqual('a' * 32, gaia.
                     MapGaiaEmailToDefaultAccountName(
                         'a' * 32 + 'thiswill@betruncated.com'))

  def testSymbolsUsername(self):
    self.assertEqual('g_______test_', gaia.
                     MapGaiaEmailToDefaultAccountName(
                         '!#$%^&*TEST_@google.com'))

  def testMalicious(self):
    with self.assertRaisesRegex(gaia.GaiaException,
                                re.escape('Invalid email address [@test].')):
      gaia.MapGaiaEmailToDefaultAccountName('@test')

  def testNoAt(self):
    self.assertEqual('test', gaia.
                     MapGaiaEmailToDefaultAccountName('test'))

  def testEmpty(self):
    with self.assertRaisesRegex(gaia.GaiaException,
                                re.escape('Invalid email address [].')):
      gaia.MapGaiaEmailToDefaultAccountName('')


if __name__ == '__main__':
  test_case.main()
