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

"""Tests for DM type_providers command_lib."""

from googlecloudsdk.command_lib.deployment_manager import type_providers
from googlecloudsdk.core import yaml
from tests.lib.surface.deployment_manager import unit_test_base


class TypeProvidersCommandTest(unit_test_base.DmV2UnitTestBase):

  def FinalTestDataDir(self):
    return 'type_providers'

  def SetUp(self):
    self.TargetingV2BetaApi()
    self.full_type_provider = self.messages.TypeProvider(
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
                        self.messages.InputMapping(
                            fieldName='bob',
                            location='PATH',
                            methodMatch='^(get|update|delete)',
                            value='$.resource.properties.metadata.name')
                    ],
                    validationOptions=self.messages.ValidationOptions(
                        schemaValidation='IGNORE',
                        undeclaredProperties='INCLUDE_WITH_WARNINGS'))),
            self.messages.CollectionOverride(
                collection='/api/v1/namespaces/{namespace}/foos',
                options=self.messages.Options(
                    virtualProperties='baz',
                    validationOptions=self.messages.ValidationOptions(
                        schemaValidation='IGNORE',
                        undeclaredProperties='INCLUDE_WITH_WARNINGS')))
        ],
        labels=[],
        options=self.messages.Options(
            inputMappings=[self.messages.InputMapping(
                fieldName='Authorization',
                location='HEADER',
                value='$.BasicAuth($.type.my_secrets, $.type.secrets)')]),
        credential=self.messages.Credential(
            basicAuth=self.messages.BasicAuth(
                user='cool_user',
                password='cooler_password')))

  def testBadYaml(self):
    api_options = self.GetTestFilePath('bad_yaml.yaml')
    with self.assertRaises(yaml.Error):
      type_providers.AddOptions(
          self.messages, api_options, self.messages.TypeProvider())

  def testFullTypeProviderTranslation(self):
    api_options = self.GetTestFilePath('full_config.yaml')
    type_provider = type_providers.AddOptions(
        self.messages, api_options, self.messages.TypeProvider())
    self.assertEqual(type_provider, self.full_type_provider)

  def testEmpty(self):
    api_options = self.GetTestFilePath('empty_config.yaml')
    type_provider = type_providers.AddOptions(
        self.messages, api_options, self.messages.TypeProvider())
    empty_provider = self.messages.TypeProvider()
    self.assertEqual(type_provider, empty_provider)

  def testNoTopLevelOptions(self):
    api_options = self.GetTestFilePath('no_top_level_options.yaml')
    type_provider = type_providers.AddOptions(
        self.messages, api_options, self.messages.TypeProvider())
    optionless_provider = self.full_type_provider
    optionless_provider.options = None
    self.assertEqual(type_provider, optionless_provider)

  def testNoCollectionOverrides(self):
    api_options = self.GetTestFilePath('no_collection_overrides.yaml')
    type_provider = type_providers.AddOptions(
        self.messages, api_options, self.messages.TypeProvider())
    collectionless_provider = self.full_type_provider
    collectionless_provider.collectionOverrides = []
    self.assertEqual(type_provider, collectionless_provider)

  def testEmptyOptions(self):
    self.assertEqual(type_providers._OptionsFrom(self.messages, {}),
                     self.messages.Options())

  def testEmptyValidationOptions(self):
    self.assertEqual(type_providers._OptionsFrom(
        self.messages, {'validationOptions': {}}),
                     self.messages.Options(
                         validationOptions=self.messages.ValidationOptions()))

  def testEmptyInputMapping(self):
    self.assertEqual(type_providers._InputMappingFrom(self.messages, {}),
                     self.messages.InputMapping())

  def testNoOptionsFile(self):
    # Using a string as input ensures the type provider isn't touched
    self.assertEqual('baz', type_providers.AddOptions(self.messages, '', 'baz'))
    self.assertEqual('baz', type_providers.AddOptions(
        self.messages, None, 'baz'))

  def testNoCredential(self):
    api_options = self.GetTestFilePath('no_credential.yaml')
    type_provider = type_providers.AddOptions(
        self.messages, api_options, self.messages.TypeProvider())
    credentialless_provider = self.full_type_provider
    credentialless_provider.credential = None
    self.assertEqual(type_provider, credentialless_provider)
