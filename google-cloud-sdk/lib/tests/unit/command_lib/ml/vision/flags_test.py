# -*- coding: utf-8 -*- #
# # Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unit tests ml vision flags."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.ml.vision import flags
from tests.lib import parameterized
from tests.lib import sdk_test_base


class FlagTest(sdk_test_base.SdkBase, parameterized.TestCase):

  @parameterized.parameters(
      ('1', 1),
      ('1.0', 1),
      ('1.5', 1.5),
      ('2:1', 2),
      ('3:4', 0.75)
  )
  def testGood(self, value, parsed_value):
    self.assertEqual(flags.AspectRatioType(value), parsed_value)

  @parameterized.parameters(
      ['a', '1:a', 'a:1', 'a:a', ':1', '1:', ':', '1:1:1']
  )
  def testBad(self, value):
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      flags.AspectRatioType(value)


if __name__ == '__main__':
  sdk_test_base.main()
