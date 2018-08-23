# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Tests for DM base commands command_lib."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.deployment_manager import dm_write
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.deployment_manager import unit_test_base


OPERATION_NAME = 'op-123'


def LogResource(request, is_async):
  log.CreatedResource(request.deployment, kind='deployment', is_async=is_async)


def CallDmApiSuccess(request):  # pylint: disable=unused-argument
  return apis.GetMessagesModule('deploymentmanager', 'v2').Operation(
      name=OPERATION_NAME, status='PENDING')


def CallDmApiError(request):  # pylint: disable=unused-argument
  raise http_error.MakeHttpError(404, message='unsuccessful', url='op.com')


class DmWriteTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for write command functionality."""

  def SetUp(self):
    self.request = self.messages.DeploymentmanagerDeploymentsStopRequest(
        project=self.Project(),
        deployment='foo',
    )
    self.client = apis.GetClientInstance('deploymentmanager', 'v2')
    self.messages = apis.GetMessagesModule('deploymentmanager', 'v2')
    self.resources = resources.REGISTRY

  def testCallSuccess(self):
    self.WithOperationPolling(operation_type='op')
    dm_write.Execute(self.client, self.messages, self.resources, self.request,
                     False, CallDmApiSuccess, LogResource)
    self.AssertErrContains('Waiting for [op-123]')
    self.AssertErrContains('Created deployment [foo].')

  def testCallAsync(self):
    operation = dm_write.Execute(self.client, self.messages, self.resources,
                                 self.request, True, CallDmApiSuccess,
                                 LogResource)
    self.AssertErrContains('Create in progress for deployment [foo].')
    self.AssertOutputContains('Operation [op-123] running')
    self.assertEqual(CallDmApiSuccess('foo'), operation)

  def testCallFailed(self):
    # HttpError => HttpException happens later in the CLI.
    with self.assertRaisesRegex(apitools_exceptions.HttpError,
                                'unsuccessful'):
      dm_write.Execute(self.client, self.messages, self.resources, self.request,
                       False, CallDmApiError, LogResource)
    self.AssertErrNotContains('Created endpoint [foo].')

  def testOperationFailed(self):
    self.WithOperationPolling(operation_type='op',
                              error=self.OperationErrorFor('fail'))
    with self.assertRaisesRegex(exceptions.OperationError,
                                re.compile(r'.*fail.*')):
      dm_write.Execute(self.client, self.messages, self.resources, self.request,
                       False, CallDmApiSuccess, LogResource)
    self.AssertErrContains('Waiting for [op-123]')
    self.AssertErrNotContains('Created endpoint [foo].')

  def testOperationTookTooLong(self):
    # only one poll because we don't poll every second
    self.WithOperationPolling(operation_type='op',
                              poll_attempts=3,
                              require_final_poll=False)
    with self.assertRaisesRegex(
        exceptions.Error,
        re.compile(r'.*'+OPERATION_NAME+'.*exceeded timeout.*')):
      dm_write.WaitForOperation(self.client, self.messages, OPERATION_NAME,
                                project=self.Project(), timeout=3)
    self.AssertErrContains('Waiting for [op-123]')
    self.AssertErrNotContains('Created endpoint [foo].')


if __name__ == '__main__':
  test_case.main()

