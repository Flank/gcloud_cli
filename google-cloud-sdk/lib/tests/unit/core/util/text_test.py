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
"""Tests for googlecloudsdk.core.util.text."""

from __future__ import absolute_import
from __future__ import unicode_literals
import datetime

from googlecloudsdk.core.util import text
from tests.lib import test_case

from six.moves import range  # pylint: disable=redefined-builtin


class PluralizeTest(test_case.TestCase):

  def testPluralize_StandardWord(self):
    self.assertEqual(text.Pluralize(1, 'dog'), 'dog')
    for num in [0] + list(range(2, 100)):
      self.assertEqual(text.Pluralize(num, 'dog'), 'dogs')

  def testPluralize_UnusualWord(self):
    self.assertEqual(text.Pluralize(1, 'kitty', 'kitties'), 'kitty')
    for num in [0] + list(range(2, 100)):
      self.assertEqual(text.Pluralize(num, 'kitty', 'kitties'), 'kitties')


class PrettyTimeDeltaTest(test_case.TestCase):

  def testPrettyTimeDelta_Seconds(self):
    self.assertEqual(text.PrettyTimeDelta(datetime.timedelta(seconds=1)),
                     '1 second')
    for num in [0] + list(range(2, 60)):
      self.assertEqual(text.PrettyTimeDelta(datetime.timedelta(seconds=num)),
                       str(num) + ' seconds')

  def testPrettyTimeDelta_Minutes(self):
    self.assertEqual(
        text.PrettyTimeDelta(datetime.timedelta(minutes=1)),
        '1 minute')
    self.assertEqual(
        text.PrettyTimeDelta(datetime.timedelta(minutes=1, seconds=59)),
        '1 minute')
    for num in range(2, 60):
      self.assertEqual(
          text.PrettyTimeDelta(datetime.timedelta(minutes=num)),
          str(num) + ' minutes')
      self.assertEqual(
          text.PrettyTimeDelta(datetime.timedelta(minutes=num, seconds=59)),
          str(num) + ' minutes')

  def testPrettyTimeDelta_Hours(self):
    self.assertEqual(
        text.PrettyTimeDelta(datetime.timedelta(hours=1)),
        '1 hour')
    self.assertEqual(
        text.PrettyTimeDelta(datetime.timedelta(hours=1, minutes=59,
                                                seconds=59)),
        '1 hour')
    for num in range(2, 24):
      self.assertEqual(
          text.PrettyTimeDelta(datetime.timedelta(hours=num)),
          str(num) + ' hours')
      self.assertEqual(
          text.PrettyTimeDelta(datetime.timedelta(hours=num, minutes=59,
                                                  seconds=59)),
          str(num) + ' hours')

  def testPrettyTimeDelta_Days(self):
    self.assertEqual(
        text.PrettyTimeDelta(datetime.timedelta(days=1)),
        '1 day')
    self.assertEqual(
        text.PrettyTimeDelta(datetime.timedelta(days=1, hours=23, minutes=59,
                                                seconds=59)),
        '1 day')
    for num in range(2, 1000):
      self.assertEqual(
          text.PrettyTimeDelta(datetime.timedelta(days=num)),
          str(num) + ' days')
      self.assertEqual(
          text.PrettyTimeDelta(datetime.timedelta(days=num, hours=23,
                                                  minutes=59, seconds=59)),
          str(num) + ' days')

if __name__ == '__main__':
  test_case.main()
