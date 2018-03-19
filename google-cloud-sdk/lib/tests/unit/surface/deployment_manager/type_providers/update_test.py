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


"""Unit tests for 'type-providers update' command."""

import re

from googlecloudsdk.api_lib.deployment_manager import exceptions
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base


TP_NAME = 'tp1'
DESCRIPTOR_URL = 'foobar.com'
DESCRIPTION = 'foo bar'


class TypeProvidersUpdateTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for 'type-providers update' command.

  We only test a few scenarios here, because most of the functionality is
  covered by the DeploymentManagerWriteCommand.
  """

  def SetUp(self):
    self.TargetingV2BetaApi()
    self.TargetingBetaCommandTrack()
    self.options_path = self.GetTestFilePath('no_collection_overrides.yaml')
    self.withExpectedGet()
    self.withExpectedUpdate()

  def FinalTestDataDir(self):
    return 'type_providers'

  def testUpdateOneTypeProviderSuccess(self):
    self.WithOperationPolling(operation_type='update')
    self.Run(self.updateCommand())
    self.AssertOutputEquals('')
    self.AssertErrContains('Waiting for update [op-123]')
    self.AssertErrContains('Updated type_provider [tp1].')

  def testAsync(self):
    self.Run(self.updateCommand() + ' --async')
    self.AssertOutputContains('Operation [op-123] running...')
    self.AssertErrEquals('Update in progress for type_provider [tp1].\n')

  def testOperationFailed(self):
    self.WithOperationPolling(poll_attempts=0,
                              error=self.OperationErrorFor('something bad'),
                              operation_type='update')
    with self.assertRaisesRegexp(exceptions.OperationError,
                                 re.compile(r'.*something bad.*')):
      self.Run(self.updateCommand())

  def updateCommand(self):
    return ('deployment-manager type-providers update {0}'
            ' --api-options-file {1} --descriptor-url {2} --description "{3}"'
            ' --update-labels {4} --remove-labels {5}'.format(TP_NAME,
                                                              self.options_path,
                                                              DESCRIPTOR_URL,
                                                              DESCRIPTION,
                                                              'foo=baz',
                                                              'baz'))

  def withExpectedGet(self):
    type_provider = self.messages.TypeProvider(
        name=TP_NAME,
        descriptorUrl=DESCRIPTOR_URL,
        description='',
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
        labels=[self.messages.TypeProviderLabelEntry(key='baz', value='quux'),
                self.messages.TypeProviderLabelEntry(key='foo', value='bar')],
        credential=self.messages.Credential(
            basicAuth=self.messages.BasicAuth(
                user='cool_user',
                password='cooler_password'))
    )
    self.mocked_client.typeProviders.Get.Expect(
        request=self.messages.DeploymentmanagerTypeProvidersGetRequest(
            project=self.Project(),
            typeProvider=TP_NAME),
        response=type_provider
    )

  def withExpectedUpdate(self):
    type_provider = self.messages.TypeProvider(
        name=TP_NAME,
        descriptorUrl=DESCRIPTOR_URL,
        description=DESCRIPTION,
        options=self.messages.Options(
            inputMappings=[
                self.messages.InputMapping(
                    fieldName='Authorization',
                    location='HEADER',
                    value='$.BasicAuth($.type.my_secrets, $.type.secrets)'),
            ],
        ),
        labels=[self.messages.TypeProviderLabelEntry(key='foo', value='baz')],
        credential=self.messages.Credential(
            basicAuth=self.messages.BasicAuth(
                user='cool_user',
                password='cooler_password'))
    )
    self.mocked_client.typeProviders.Update.Expect(
        request=self.messages.DeploymentmanagerTypeProvidersUpdateRequest(
            project=self.Project(),
            typeProvider=TP_NAME,
            typeProviderResource=type_provider),
        response=self.messages.Operation(
            name=self.OPERATION_NAME,
            operationType='update',
            status='PENDING',
        )
    )


if __name__ == '__main__':
  test_case.main()

