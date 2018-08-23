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


"""Unit tests for 'types delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.deployment_manager import exceptions
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base


CT_NAME = 'ct1'


class TypesDeleteTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for 'types delete' command.

  We only test a few scenarios here, because most of the functionality is
  covered by the DeploymentManagerWriteCommand.
  """

  def SetUp(self):
    self.TargetingV2BetaApi()
    self.TargetingBetaCommandTrack()

  def testNoDelete(self):
    self.WriteInput('n\n')
    with self.assertRaisesRegex(exceptions.OperationError,
                                'Deletion aborted by user.'):
      self.Run(self.deleteCommand(additional_args=''))
    self.AssertErrContains(CT_NAME)

  def testYesDelete(self):
    self.withExpectedDelete()
    self.WithOperationPolling(operation_type='create')
    self.WriteInput('y\n')
    self.Run(self.deleteCommand(additional_args=''))
    self.AssertErrContains('Waiting for delete [op-123]')
    self.AssertErrContains('Deleted composite_type [ct1].')

  def testDeleteOneCompositeTypeSuccess(self):
    self.withExpectedDelete()
    self.WithOperationPolling(operation_type='create')
    self.Run(self.deleteCommand())
    self.AssertOutputEquals('')
    self.AssertErrContains('Waiting for delete [op-123]')
    self.AssertErrContains('Deleted composite_type [ct1].')

  def testAsync(self):
    self.withExpectedDelete()
    self.Run(self.deleteCommand() + ' --async')
    self.AssertOutputEquals('Operation [op-123] running....\n')
    self.AssertErrContains('Delete in progress for composite_type [ct1].\n')

  def testOperationFailed(self):
    self.withExpectedDelete()
    self.WithOperationPolling(poll_attempts=0,
                              error=self.OperationErrorFor('something bad'),
                              operation_type='create')
    with self.assertRaisesRegex(exceptions.Error,
                                re.compile(r'.*something bad.*')):
      self.Run(self.deleteCommand())

  def deleteCommand(self, additional_args='--quiet'):
    return 'deployment-manager types delete {0} {1}'.format(CT_NAME,
                                                            additional_args)

  def withExpectedDelete(self):
    self.mocked_client.compositeTypes.Delete.Expect(
        request=self.messages.DeploymentmanagerCompositeTypesDeleteRequest(
            project=self.Project(),
            compositeType=CT_NAME),
        response=self.messages.Operation(
            name=self.OPERATION_NAME,
            operationType='delete',
            status='PENDING',
        )
    )


if __name__ == '__main__':
  test_case.main()


