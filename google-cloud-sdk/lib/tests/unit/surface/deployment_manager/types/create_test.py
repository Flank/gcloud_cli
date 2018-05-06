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


"""Unit tests for 'types create' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import re

from googlecloudsdk.api_lib.deployment_manager import exceptions
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base


CT_NAME = 'ct1'
STATUS = 'EXPERIMENTAL'
DESCRIPTION = 'foo bar'
LABELS = 'baz=quux'


class TypesCreateTest(unit_test_base.CompositeTypesUnitTestBase):
  """Unit tests for 'types create' command.

  We only test a few scenarios here, because most of the functionality is
  covered by the DeploymentManagerWriteCommand.
  """

  def SetUp(self):
    self.TargetingV2BetaApi()
    self.TargetingBetaCommandTrack()
    self.template = self.GetTestFilePath('simple.jinja')

  def FinalTestDataDir(self):
    return 'simple_configs'

  def testCreateOneCompositeTypeSuccess(self):
    self.withExpectedInsert()
    self.WithOperationPolling(operation_type='create')
    self.Run(self.createCommand())
    self.AssertOutputEquals('')
    self.AssertErrContains('Waiting for create [op-123]')
    self.AssertErrContains('Created composite_type [ct1].')

  def testAsync(self):
    self.withExpectedInsert()
    self.Run(self.createCommand() + ' --async')
    self.AssertOutputEquals('Operation [op-123] running....\n')
    self.AssertErrContains('Create in progress for composite_type [ct1].\n')

  def testOperationFailed(self):
    self.withExpectedInsert()
    self.WithOperationPolling(poll_attempts=0,
                              error=self.OperationErrorFor('something bad'),
                              operation_type='create')
    with self.assertRaisesRegex(exceptions.Error,
                                re.compile(r'.*something bad.*')):
      self.Run(self.createCommand())

  def createCommand(self):
    return ('deployment-manager types create {0} --template {1} --status {2}'
            ' --description "{3}" --labels {4}'.format(CT_NAME,
                                                       self.template,
                                                       STATUS,
                                                       DESCRIPTION,
                                                       LABELS))

  def withExpectedInsert(self):
    composite_type = self.messages.CompositeType(
        name=CT_NAME,
        description=DESCRIPTION,
        status=STATUS,
        templateContents=self.GetExpectedSimpleTemplate(),
        labels=[self.messages.CompositeTypeLabelEntry(key='baz', value='quux')])
    self.mocked_client.compositeTypes.Insert.Expect(
        request=self.messages.DeploymentmanagerCompositeTypesInsertRequest(
            project=self.Project(),
            compositeType=composite_type),
        response=self.messages.Operation(
            name=self.OPERATION_NAME,
            operationType='create',
            status='PENDING',
        )
    )


if __name__ == '__main__':
  test_case.main()

