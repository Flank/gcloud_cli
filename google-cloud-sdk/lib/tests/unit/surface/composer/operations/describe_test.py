# -*- coding: utf-8 -*- #
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
"""Unit tests for operations describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.composer import base


class OperationsDescribeGATest(base.OperationsUnitTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.GA)

  def testSuccessfulDescribe(self):
    expected = self.MakeOperation(self.TEST_PROJECT, self.TEST_LOCATION,
                                  self.TEST_OPERATION_UUID)
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        response=expected)
    actual = self.RunOperations('describe', '--project', self.TEST_PROJECT,
                                '--location', self.TEST_LOCATION,
                                self.TEST_OPERATION_UUID)
    self.assertEqual(expected, actual)

  def testDescribeOperationNotFound(self):
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        exception=http_error.MakeHttpError(code=404, message='NOT_FOUND'))
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: NOT_FOUND'):
      self.RunOperations('describe', '--project', self.TEST_PROJECT,
                         '--location', self.TEST_LOCATION,
                         self.TEST_OPERATION_UUID)

  def testDescribeEnvironmentInsufficientPermissions(self):
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        exception=http_error.MakeHttpError(
            code=403, message='PERMISSION_DENIED'))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: PERMISSION_DENIED'):
      self.RunOperations('describe', '--project', self.TEST_PROJECT,
                         '--location', self.TEST_LOCATION,
                         self.TEST_OPERATION_UUID)


class OperationsDescribeBetaTest(OperationsDescribeGATest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.BETA)


class OperationsDescribeAlphaTest(OperationsDescribeBetaTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
