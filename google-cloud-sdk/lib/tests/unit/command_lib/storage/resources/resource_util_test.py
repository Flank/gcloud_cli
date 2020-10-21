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

"""Unit tests for resource_util.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.command_lib.storage.resources import resource_util
from tests.lib import test_case


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class ResourceUtilTest(test_case.TestCase):
  """Tests for resource_util.py."""

  def test_does_not_convert_json_parsable_type(self):
    self.assertEqual(resource_util.convert_to_json_parsable_type(1), 1)

  def test_converts_exception_to_string(self):
    exception = Exception('Salty cookies')
    self.assertEqual(resource_util.convert_to_json_parsable_type(exception),
                     'Salty cookies')

  def test_converts_date_to_string(self):
    time = datetime.date(1111, 1, 1)
    self.assertEqual(resource_util.convert_to_json_parsable_type(time),
                     '1111-01-01')

  def test_converts_datetime_to_string(self):
    time = datetime.datetime(1111, 1, 1, tzinfo=datetime.timezone.utc)
    self.assertEqual(resource_util.convert_to_json_parsable_type(time),
                     '1111-01-01T00:00:00+0000')

  def test_preserves_zero_int_metadata(self):
    self.assertTrue(resource_util.should_preserve_falsy_metadata_value(0))

  def test_preserves_zero_float_metadata(self):
    self.assertTrue(resource_util.should_preserve_falsy_metadata_value(0.0))

  def test_preserves_false_metadata(self):
    self.assertTrue(resource_util.should_preserve_falsy_metadata_value(False))

  def test_does_not_preserve_unexpected_falsy_metadata(self):
    self.assertFalse(resource_util.should_preserve_falsy_metadata_value([]))


if __name__ == '__main__':
  test_case.main()
