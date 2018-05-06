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


"""Unit tests for 'type-providers create' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import re

from googlecloudsdk.api_lib.deployment_manager import exceptions
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base


TP_NAME = 'tp1'
DESCRIPTOR_URL = 'foobar.com'
DESCRIPTION = 'foo bar'
LABELS = 'baz=quux'


class TypeProvidersCreateTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for 'type-providers create' command.

  We only test a few scenarios here, because most of the functionality is
  covered by the DeploymentManagerWriteCommand.
  """

  def SetUp(self):
    self.TargetingV2BetaApi()
    self.TargetingBetaCommandTrack()
    self.options_path = self.GetTestFilePath('bare_bones.yaml')

  def FinalTestDataDir(self):
    return 'type_providers'

  def testCreateOneTypeProviderSuccess(self):
    self.WithExpectedInsert()
    self.WithOperationPolling(operation_type='create')
    self.Run(self.createCommand())
    self.AssertOutputEquals('')
    self.AssertErrContains('Waiting for create [op-123]')
    self.AssertErrContains('Created type_provider [tp1].')

  def testAsync(self):
    self.WithExpectedInsert()
    self.Run(self.createCommand() + ' --async')
    self.AssertOutputEquals('Operation [op-123] running....\n')
    self.AssertErrContains('Create in progress for type_provider [tp1].\n')

  def testOperationFailed(self):
    self.WithExpectedInsert()
    self.WithOperationPolling(poll_attempts=0,
                              error=self.OperationErrorFor('something bad'),
                              operation_type='create')
    with self.assertRaisesRegex(exceptions.Error,
                                re.compile(r'.*something bad.*')):
      self.Run(self.createCommand())

  def createCommand(self):
    return ('deployment-manager type-providers create {0}'
            ' --api-options-file {1} --descriptor-url {2}'
            ' --description "{3}" --labels {4}'.format(
                TP_NAME,
                self.options_path,
                DESCRIPTOR_URL,
                DESCRIPTION,
                LABELS))

  def WithExpectedInsert(self):
    type_provider = self.messages.TypeProvider(
        name=TP_NAME,
        descriptorUrl=DESCRIPTOR_URL,
        description=DESCRIPTION,
        collectionOverrides=[
            self.messages.CollectionOverride(
                collection='/api/v1/namespaces/{namespace}/pods',
                options=self.messages.Options(
                    virtualProperties='quux',
                    inputMappings=[
                        self.messages.InputMapping(
                            fieldName='id',
                            location='PATH',
                            methodMatch='^(get|update|delete)',
                            value='$.resource.properties.metadata.name'),
                    ],
                    validationOptions=self.messages.ValidationOptions(
                        schemaValidation='IGNORE',
                        undeclaredProperties='INCLUDE_WITH_WARNINGS'))),
        ],
        labels=[self.messages.TypeProviderLabelEntry(key='baz', value='quux')]
    )
    self.mocked_client.typeProviders.Insert.Expect(
        request=self.messages.DeploymentmanagerTypeProvidersInsertRequest(
            project=self.Project(),
            typeProvider=type_provider),
        response=self.messages.Operation(
            name=self.OPERATION_NAME,
            operationType='create',
            status='PENDING',
        )
    )


if __name__ == '__main__':
  test_case.main()

