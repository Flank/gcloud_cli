# Lint as: python3
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
"""Tests for google3.third_party.py.googlecloudsdk.command_lib.privateca.operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.privateca import operations
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock


class OperationsTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.messages = privateca_base.GetMessagesModule()

  def testOperationsInitialFailure(self):
    operation = self.messages.Operation()
    operation.done = True
    operation.error = self.messages.Status(message='failure')
    with self.AssertRaisesExceptionMatches(operations.OperationError,
                                           'failure'):
      operations.Await(operation, 'testing')

  @mock.patch.object(
      waiter.CloudOperationPollerNoResources, 'Poll', autospec=True)
  def testOperationDelayedFailure(self, cloud_op_poll_mock):
    operation = self.messages.Operation(
        done=False, name='projects/test/locations/test/operations/test')
    cloud_op_poll_mock.return_value = self.messages.Operation(
        done=True,
        name='projects/test/locations/test/operations/test',
        error=self.messages.Status(message='failure'))
    with self.AssertRaisesExceptionMatches(waiter.OperationError, 'failure'):
      operations.Await(operation, 'testing')

  @mock.patch.object(waiter, 'WaitFor', autospec=True)
  def testOperationTimeoutFailure(self, waiter_waitfor_mock):
    operation = self.messages.Operation(
        done=False, name='projects/test/locations/test/operations/test')
    waiter_waitfor_mock.side_effect = waiter.TimeoutError('timeout')
    with self.AssertRaisesExceptionMatches(operations.OperationTimeoutError,
                                           'action timed out'):
      operations.Await(operation, 'testing')


if __name__ == '__main__':
  test_case.main()
