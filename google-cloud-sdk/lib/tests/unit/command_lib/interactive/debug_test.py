# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Unit tests for the gcloud interactive debug module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

from googlecloudsdk.command_lib.interactive import debug
from tests.lib import test_case


class DebugTests(test_case.TestCase):

  def SetUp(self):
    self.debug = debug.Debug()
    self._time = 1234.5678
    self._time_increment = 0.1

  def _Time(self):
    self._time += self._time_increment
    self._time_increment *= 1.2
    return self._time

  def testDebugNone(self):
    self.assertEqual([], self.debug.contents())

  def testDebugCountOne(self):
    self.debug.abc.count()
    self.debug.abc.count()
    self.debug.abc.count()
    self.assertEqual(['abc:3'], self.debug.contents())

  def testDebugCountTwo(self):
    self.debug.xyz.count()
    self.debug.abc.count()
    self.debug.abc.count()
    self.debug.abc.count()
    self.assertEqual(['abc:3', 'xyz:1'], self.debug.contents())

  def testDebugTextTwo(self):
    self.debug.xyz.text('X junk')
    self.debug.abc.text('[A stuff]')
    self.assertEqual(['abc:[A stuff]', 'xyz:"X junk"'], self.debug.contents())

  def testDebugCountAndTextTwo(self):
    self.debug.abc.count()
    self.debug.xyz.text('{X junk}')
    self.debug.abc.count()
    self.debug.abc.text('stuff')
    self.debug.abc.count()
    self.debug.pdq.text('')
    self.assertEqual(['abc:3:stuff', 'pdq:""', 'xyz:{X junk}'],
                     self.debug.contents())

  def testDebugTextQuote(self):
    self.debug.a.text('')
    self.debug.b.text(' ')
    self.debug.c.text('[ ]')
    self.debug.d.text('{ ]')
    self.assertEqual(['a:""', 'b:" "', 'c:[ ]', 'd:"{ ]"'],
                     self.debug.contents())

  def testDebugIntervalTwo(self):
    self.StartObjectPatch(time, 'time', side_effect=self._Time)

    for i in range(8):
      self.debug.completions.start()
      self.debug.completions.stop()
      if i % 2:
        self.debug.commands.start()
        self.debug.commands.stop()

    self.assertEqual(['commands:4:2.458797', 'completions:8:1.446630'],
                     self.debug.contents())
