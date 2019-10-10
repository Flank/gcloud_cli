# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Unit tests for operations wait."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.composer import util as command_util
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.composer import base

ERROR_DESCRIPTION = 'ERROR_DESCRIPTION'


class OperationsWaitGATest(base.OperationsUnitTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.GA)

  # Must be called after self.SetTrack() for self.messages to be present
  def _SetTestMessages(self):
    self.running_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=False)
    self.successful_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=True)
    self.errored_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=True,
        error=self.messages.Status(message=ERROR_DESCRIPTION))

  def testSuccessfulOperation(self):
    self._SetTestMessages()
    for response in [self.running_op, self.successful_op]:
      self.ExpectOperationGet(
          self.TEST_PROJECT,
          self.TEST_LOCATION,
          self.TEST_OPERATION_UUID,
          response=response)
    self.RunOperations('wait', '--project', self.TEST_PROJECT, '--location',
                       self.TEST_LOCATION, self.TEST_OPERATION_UUID)

  def testErroredOperation(self):
    self._SetTestMessages()
    for response in [self.running_op, self.errored_op]:
      self.ExpectOperationGet(
          self.TEST_PROJECT,
          self.TEST_LOCATION,
          self.TEST_OPERATION_UUID,
          response=response)
    with self.AssertRaisesExceptionMatches(
        command_util.OperationError, 'Operation [{}] failed: {}'.format(
            self.TEST_OPERATION_NAME, ERROR_DESCRIPTION)):
      self.RunOperations('wait', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_OPERATION_UUID)

  def testOperationNotFound(self):
    self._SetTestMessages()
    self._testHttpError(
        http_error.MakeHttpError(code=404, message='NOT_FOUND'),
        'Resource not found API reason: NOT_FOUND')

  def testOperationInsufficientPermissions(self):
    self._SetTestMessages()
    self._testHttpError(
        http_error.MakeHttpError(code=403, message='PERMISSION_DENIED'),
        'Permission denied API reason: PERMISSION_DENIED')

  def _testHttpError(self, exception, expected_message):
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        exception=exception)
    with self.AssertRaisesHttpExceptionMatches(expected_message):
      self.RunOperations('wait', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_OPERATION_UUID)


class OperationsWaitBetaTest(OperationsWaitGATest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.BETA)


class OperationsWaitAlphaTest(OperationsWaitBetaTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
