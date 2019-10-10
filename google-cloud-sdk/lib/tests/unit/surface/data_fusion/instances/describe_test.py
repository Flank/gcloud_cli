# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Unit tests for instances describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.data_fusion import base


class InstancesDescribeBetaTest(base.InstancesUnitTest):

  def testSuccessfulDescribe(self):
    expected = self.MakeInstance(
        self.TEST_ZONE,
        self.messages.Instance.TypeValueValuesEnum.ENTERPRISE,
        False, False)
    self.ExpectInstanceGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_INSTANCE,
        response=expected)
    actual = self.RunInstances('describe', '--project', self.TEST_PROJECT,
                               '--location', self.TEST_LOCATION,
                               self.TEST_INSTANCE)
    self.assertEqual(expected, actual)

  def testDescribeNotFound(self):
    self.ExpectInstanceGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_INSTANCE,
        exception=http_error.MakeHttpError(code=404, message='NOT_FOUND'))
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: NOT_FOUND'):
      self.RunInstances('describe', '--project', self.TEST_PROJECT,
                        '--location', self.TEST_LOCATION,
                        self.TEST_INSTANCE)

  def testDescribePermissionDenied(self):
    self.ExpectInstanceGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_INSTANCE,
        exception=http_error.MakeHttpError(
            code=403, message='PERMISSION_DENIED'))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: PERMISSION_DENIED'):
      self.RunInstances('describe', '--project', self.TEST_PROJECT,
                        '--location', self.TEST_LOCATION,
                        self.TEST_INSTANCE)

if __name__ == '__main__':
  test_case.main()
