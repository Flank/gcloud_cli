# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Unit tests for environments describe."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.composer import base


class EnvironmentsDescribeTest(base.EnvironmentsUnitTest):

  def testSuccessfulDescribe(self):
    expected = self.MakeEnvironment(self.TEST_PROJECT, self.TEST_LOCATION,
                                    self.TEST_ENVIRONMENT_ID)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=expected)
    actual = self.RunEnvironments('describe', '--project', self.TEST_PROJECT,
                                  '--location', self.TEST_LOCATION,
                                  self.TEST_ENVIRONMENT_ID)
    self.assertEqual(expected, actual)

  def testDescribeEnvironmentNotFound(self):
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        exception=http_error.MakeHttpError(code=404, message='NOT_FOUND'))
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: NOT_FOUND'):
      self.RunEnvironments('describe', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION,
                           self.TEST_ENVIRONMENT_ID)

  def testDescribeEnvironmentInsufficientPermissions(self):
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        exception=http_error.MakeHttpError(
            code=403, message='PERMISSION_DENIED'))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: PERMISSION_DENIED'):
      self.RunEnvironments('describe', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION,
                           self.TEST_ENVIRONMENT_ID)


if __name__ == '__main__':
  test_case.main()
