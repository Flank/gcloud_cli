# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Unit tests for operations delete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.data_fusion import base


class OperationsDeleteBetaTest(base.OperationsUnitTest):

  def testSuccessfulDeleteSingle(self):
    self.WriteInput('y\n')
    self.ExpectOperationDelete(self.TEST_PROJECT, self.TEST_LOCATION,
                               self.TEST_OPERATION_UUID)

    self.RunOperations('delete', '--project', self.TEST_PROJECT, '--location',
                       self.TEST_LOCATION, self.TEST_OPERATION_UUID)

  def testDeleteOperationNotFound(self):
    self.WriteInput('y\n')
    self.ExpectOperationDelete(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        exception=http_error.MakeHttpError(code=404, message='NOT_FOUND'))
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: NOT_FOUND'):
      self.RunOperations('delete', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_OPERATION_UUID)
    self.AssertErrContains('NOT_FOUND')

  def testDeleteOperationDecline(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           'Deletion aborted by user'):
      self.RunOperations('delete', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_OPERATION_UUID)

  def testDeleteInsufficentPermissions(self):
    self.WriteInput('y\n')
    self.ExpectOperationDelete(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        exception=http_error.MakeHttpError(
            code=403, message='PERMISSION_DENIED'))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: PERMISSION_DENIED'):
      self.RunOperations('delete', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_OPERATION_UUID)


if __name__ == '__main__':
  test_case.main()
