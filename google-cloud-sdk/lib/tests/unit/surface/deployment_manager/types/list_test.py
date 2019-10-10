# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Unit tests for types list command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from surface.deployment_manager.types import list as types_list
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.deployment_manager import unit_test_base
from six.moves import range  # pylint: disable=redefined-builtin


class TypesListTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for types list command."""

  def testTypesList(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    types = [self.messages.Type(name='type-' + str(i)) for i in range(20)]
    self.mocked_client.types.List.Expect(
        request=self.messages.DeploymentmanagerTypesListRequest(
            project=self.Project()
        ),
        response=self.messages.TypesListResponse(
            types=types
        )
    )
    self.Run('deployment-manager types list')
    names_list = '\n'.join([type_item.name for type_item in types])
    expected_output = 'NAME\n' + names_list + '\n'
    self.AssertOutputEquals(expected_output)

  def testTypesList_EmptyList(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    self.mocked_client.types.List.Expect(
        request=self.messages.DeploymentmanagerTypesListRequest(
            project=self.Project()
        ),
        response=self.messages.TypesListResponse()
    )
    self.Run('deployment-manager types list')
    self.AssertErrEquals('No types were found for your project!\n')


class TypesListBetaTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for types list alpha command."""

  def SetUp(self):
    self.TargetingV2BetaApi()
    self.TargetingBetaCommandTrack()

  def _MockTypeProviderListRequest(self, project, providers):
    self.mocked_client.typeProviders.List.Expect(
        request=self.messages.DeploymentmanagerTypeProvidersListRequest(
            project=project
        ),
        response=self.messages.TypeProvidersListResponse(
            typeProviders=providers
        )
    )

  def _MockTypesListRequest(self, project, provider, types):
    self.mocked_client.typeProviders.ListTypes.Expect(
        request=self.messages.DeploymentmanagerTypeProvidersListTypesRequest(
            project=project,
            typeProvider=provider
        ),
        response=self.messages.TypeProvidersListTypesResponse(
            types=types
        )
    )

  def testSingleProviderList(self):
    types = [self.messages.TypeInfo(name='type-1',
                                    description='baz'),
             self.messages.TypeInfo(name='type-2')]
    self._MockTypesListRequest(self.Project(), 'foo', types)
    self._MockTypesListRequest(types_list.GCP_TYPES_PROJECT, 'foo', types)
    self.Run('deployment-manager types list --provider=foo')
    expected_output = ('---\n'
                       'provider: {0}/foo\n'
                       'types:\n'
                       '- type-1\n'
                       '- type-2\n'
                       '---\n'
                       'provider: {1}/foo\n'
                       'types:\n'
                       '- type-1\n'
                       '- type-2\n').format(
                           self.Project(), types_list.GCP_TYPES_PROJECT)
    self.AssertOutputEquals(expected_output)

  def testSingleProjectList(self):
    providers = [self.messages.TypeProvider(name='provider-1')]
    self._MockTypeProviderListRequest('more-fake-project', providers)
    types = [self.messages.TypeInfo(name='type-1',
                                    description='baz'),
             self.messages.TypeInfo(name='type-2')]
    self._MockTypesListRequest('more-fake-project', 'provider-1', types)
    self.Run('deployment-manager types list '
             '--provider-project=more-fake-project')
    expected_output = ('---\n'
                       'provider: {0}/provider-1\n'
                       'types:\n'
                       '- type-1\n'
                       '- type-2\n').format('more-fake-project')
    self.AssertOutputEquals(expected_output)

  def testAllProvidersList(self):
    insert_time_string = '2016-10-18T09:56:11.710-07:00'
    providers_1 = [self.messages.TypeProvider(name='provider-1',
                                              insertTime=insert_time_string)]
    providers_2 = [self.messages.TypeProvider(name='provider-2')]
    self._MockTypeProviderListRequest(self.Project(), providers_1)
    self._MockTypeProviderListRequest(types_list.GCP_TYPES_PROJECT, providers_2)

    types_1 = [self.messages.TypeInfo(name='type-1', description='baz')]
    types_2 = [self.messages.TypeInfo(name='type-2', description='baz')]
    self._MockTypesListRequest(self.Project(), 'provider-1', types_1)
    self._MockTypesListRequest(
        types_list.GCP_TYPES_PROJECT, 'provider-2', types_2)

    self.Run('deployment-manager types list')
    expected_output = ('---\n'
                       'provider: {0}/provider-1\n'
                       'types:\n'
                       '- type-1\n'
                       '---\n'
                       'provider: {1}/provider-2\n'
                       'types:\n'
                       '- type-2\n').format(self.Project(),
                                            types_list.GCP_TYPES_PROJECT)
    self.AssertOutputEquals(expected_output)

  def testEmptySingleProviderList(self):
    self._MockTypesListRequest(self.Project(), 'foo', [])
    self._MockTypesListRequest(types_list.GCP_TYPES_PROJECT, 'foo', [])
    self.Run('deployment-manager types list --provider=foo')
    self.AssertOutputEquals('')
    self.AssertErrEquals('Listed 0 items.\n')

  def testNoTypeProvidersList(self):
    self._MockTypeProviderListRequest(self.Project(), [])
    self._MockTypeProviderListRequest(types_list.GCP_TYPES_PROJECT, [])
    self.Run('deployment-manager types list')
    self.AssertErrEquals('Listed 0 items.\n')

  def testMixedSuccessTypesList(self):
    insert_time_string = '2016-10-18T09:56:11.710-07:00'
    providers = [self.messages.TypeProvider(name='provider-1',
                                            insertTime=insert_time_string),
                 self.messages.TypeProvider(name='provider-2')]
    self._MockTypeProviderListRequest(self.Project(), providers)
    self._MockTypeProviderListRequest(types_list.GCP_TYPES_PROJECT, [])

    types_2 = [self.messages.TypeInfo(name='type-3', description='baz'),
               self.messages.TypeInfo(name='type-4')]
    self.mocked_client.typeProviders.ListTypes.Expect(
        request=self.messages.DeploymentmanagerTypeProvidersListTypesRequest(
            project=self.Project(),
            typeProvider='provider-1'
        ),
        exception=http_error.MakeHttpError(500,
                                           'Bob read the message',
                                           url='http://quux')
    )
    self._MockTypesListRequest(self.Project(), 'provider-2', types_2)

    try:
      self.cli.Execute(
          [self.track.prefix, 'deployment-manager', 'types', 'list'])
    except exceptions.ExitCodeNoError as e:
      self.assertEqual(e.exit_code, 1)

    expected_output = ('---\n'
                       "error: 'ResponseError: code=500, "
                       "message=Bob read the message'\n"
                       'provider: {0}/provider-1\n'
                       'types: []\n'
                       '---\n'
                       'provider: {0}/provider-2\n'
                       'types:\n'
                       '- type-3\n'
                       '- type-4\n').format(self.Project())
    self.AssertOutputEquals(expected_output)


if __name__ == '__main__':
  test_case.main()
