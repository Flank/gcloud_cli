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

"""Tests for googlecloudsdk.api_lib.compute.utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import utils
from tests.lib import test_case


class UtilsTest(test_case.TestCase):

  def testIsValidIPV4(self):
    self.assertTrue(utils.IsValidIPV4('127.0.0.1'))
    self.assertFalse(utils.IsValidIPV4('0.0.0.1'))
    self.assertFalse(utils.IsValidIPV4('127.0.0.'))
    self.assertFalse(utils.IsValidIPV4('127.0.0'))
    self.assertFalse(utils.IsValidIPV4('127.0. 0.1'))
    self.assertFalse(utils.IsValidIPV4('127.256.0.1'))


if __name__ == '__main__':
  test_case.main()
