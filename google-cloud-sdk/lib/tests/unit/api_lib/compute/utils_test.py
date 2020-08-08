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
from googlecloudsdk.core import log
from tests.lib import parameterized
from tests.lib import test_case

import mock


class UtilsTest(parameterized.TestCase, test_case.TestCase):

  def testIsValidIPV4(self):
    self.assertTrue(utils.IsValidIPV4('127.0.0.1'))
    self.assertFalse(utils.IsValidIPV4('0.0.0.1'))
    self.assertFalse(utils.IsValidIPV4('127.0.0.'))
    self.assertFalse(utils.IsValidIPV4('127.0.0'))
    self.assertFalse(utils.IsValidIPV4('127.0. 0.1'))
    self.assertFalse(utils.IsValidIPV4('127.256.0.1'))

  @parameterized.named_parameters(
      ('small-pd-balanced', 9, 'pd-balanced', 10),
      ('small-pd-ssd', 9, 'pd-ssd', 10),
      ('small-pd-extreme', 9, 'pd-extreme', 10),
      ('small-pd-standard', 199, 'pd-standard', 200),
      ('small-unknown', 199, 'pd-unknown', 200))
  @mock.patch.object(log, 'warning', autospec=True)
  def testWarnIfDiskSizeIsTooSmallWithTooSmallDiskSize(self, input_size_gb,
                                                       disk_type_name,
                                                       warning_size_gb,
                                                       log_warning_mock):
    utils.WarnIfDiskSizeIsTooSmall(input_size_gb, disk_type_name)
    log_warning_mock.assert_has_calls(
        [mock.call(utils.WARN_IF_DISK_SIZE_IS_TOO_SMALL, warning_size_gb)])

  @parameterized.named_parameters(('large-pd-balanced', 11, 'pd-balanced'),
                                  ('large-pd-ssd', 11, 'pd-ssd'),
                                  ('large-pd-extreme', 11, 'pd-extreme'),
                                  ('large-pd-standard', 201, 'pd-standard'),
                                  ('large-unknown', 201, 'pd-unknown'))
  @mock.patch.object(log, 'warning', autospec=True)
  def testWarnIfDiskSizeIsTooSmallWithLargeDiskSize(self, input_size_gb,
                                                    disk_type_name,
                                                    log_warning_mock):
    utils.WarnIfDiskSizeIsTooSmall(input_size_gb, disk_type_name)
    self.assertFalse(log_warning_mock.called)


if __name__ == '__main__':
  test_case.main()
