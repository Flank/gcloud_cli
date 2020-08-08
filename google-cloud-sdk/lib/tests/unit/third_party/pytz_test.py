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
"""Unit test to check sanity of pytz setup."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case

import pytz

VALID_TZ = 'America/Los_Angeles'
INVALID_TZ = 'America/Bad_Timezone'


class TimezoneTest(test_case.TestCase):

  def testCanValidateTimezone(self):
    tz = pytz.timezone(VALID_TZ)
    self.assertEqual(tz.zone, VALID_TZ)

  def testDoesNotValidateBadTimezone(self):
    with self.assertRaises(pytz.exceptions.UnknownTimeZoneError):
      _ = pytz.timezone(INVALID_TZ)

  def testHasUTC(self):
    utc = pytz.utc
    self.assertEqual(utc.zone, 'UTC')
