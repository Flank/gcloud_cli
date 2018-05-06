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
"""Unit tests for operations delete."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.composer import base


class OperationsDeleteTest(base.OperationsUnitTest):

  def testSuccessfulDeleteSingle(self):
    self.WriteInput('y\n')
    self.ExpectOperationDelete(self.TEST_PROJECT, self.TEST_LOCATION,
                               self.TEST_OPERATION_UUID)

    self.RunOperations('delete', '--project', self.TEST_PROJECT, '--location',
                       self.TEST_LOCATION, self.TEST_OPERATION_UUID)

  def testSuccessfulDeleteMultiple(self):
    self.WriteInput('y\n')
    self.ExpectOperationDelete(self.TEST_PROJECT, self.TEST_LOCATION,
                               self.TEST_OPERATION_UUID)
    self.ExpectOperationDelete(self.TEST_PROJECT, self.TEST_LOCATION,
                               self.TEST_OPERATION_UUID2)

    self.RunOperations('delete', '--project', self.TEST_PROJECT, '--location',
                       self.TEST_LOCATION, self.TEST_OPERATION_UUID,
                       self.TEST_OPERATION_UUID2)

  def testSuccessfulDeleteMultipleWithSingleFailure(self):
    """Test that if some deletions fail, all deletions are attempted."""
    self.WriteInput('y\n')
    self.ExpectOperationDelete(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        exception=http_error.MakeHttpError(code=404, message='NOT_FOUND'))
    self.ExpectOperationDelete(self.TEST_PROJECT, self.TEST_LOCATION,
                               self.TEST_OPERATION_UUID2)

    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'Some deletions did not succeed.'):
      self.RunOperations('delete', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_OPERATION_UUID,
                         self.TEST_OPERATION_UUID2)
    self.AssertErrMatches(r'Failed to delete operation \S*{}'.format(
        self.TEST_OPERATION_UUID))
    self.AssertErrMatches(r'^Deleted operation \S*{}]\.$'.format(
        self.TEST_OPERATION_UUID2))

  def testDeleteOperationNotFound(self):
    self.WriteInput('y\n')
    self.ExpectOperationDelete(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        exception=http_error.MakeHttpError(code=404, message='NOT_FOUND'))
    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'Some deletions did not succeed.'):
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
    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'Some deletions did not succeed.'):
      self.RunOperations('delete', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_OPERATION_UUID)


if __name__ == '__main__':
  test_case.main()
