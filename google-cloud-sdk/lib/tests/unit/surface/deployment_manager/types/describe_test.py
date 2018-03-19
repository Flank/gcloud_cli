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

"""Unit tests for 'types describe' command."""

from googlecloudsdk.calliope import exceptions
from tests.lib.apitools import http_error
from tests.lib.surface.deployment_manager import unit_test_base


TYPE_INFO_DESCRIPTION = 'Frodo'
COMPOSITE_DESCRIPTION = 'Baggins'


class TypesDescribeTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for 'types describe' command."""

  def SetUp(self):
    self.TargetingV2BetaApi()
    self.TargetingBetaCommandTrack()

  def testDescribeSuccess_JustDefaultTypeInfo(self):
    self.withType()
    self.Run('deployment-manager types describe foo --provider=bar')
    self.AssertOutputContains(TYPE_INFO_DESCRIPTION)
    self.AssertOutputContains('foo')
    self.AssertErrContains(self.Project() + '/bar:foo')
    self.AssertOutputContains('input:')
    self.AssertOutputContains('foobar:')
    self.AssertOutputContains('- baz')

  def testDescribeSuccess_CompositeType(self):
    self.withCompositeType()
    self.Run('deployment-manager types describe foo --provider=composite '
             '--format=json')
    self.AssertOutputContains('foo')
    self.AssertOutputContains(TYPE_INFO_DESCRIPTION)
    self.AssertOutputContains(COMPOSITE_DESCRIPTION)
    self.AssertOutputContains('{')
    self.AssertOutputContains('}')
    self.AssertErrContains(self.Project() + '/composite:foo')

  def testDescribeFormat_JustTypeInfo(self):
    self.withType()
    self.Run('deployment-manager types describe foo --provider=bar '
             '--format=json')
    self.AssertOutputContains('foo')
    self.AssertOutputContains(TYPE_INFO_DESCRIPTION)
    self.AssertOutputContains('This is not a composite type.')
    self.AssertOutputContains('{')
    self.AssertOutputContains('}')
    self.AssertErrContains(self.Project() + '/bar:foo')

  def testDescribeNotFound(self):
    self.withExceptionalType()
    with self.assertRaises(exceptions.HttpException):
      self.Run('deployment-manager types describe foo --provider=bar')

  def withType(self, provider='bar'):
    self.mocked_client.typeProviders.GetType.Expect(
        request=self.messages.DeploymentmanagerTypeProvidersGetTypeRequest(
            project=self.Project(),
            type='foo',
            typeProvider=provider
        ),
        response=self.messages.TypeInfo(name='foo',
                                        description=TYPE_INFO_DESCRIPTION,
                                        schema=self.messages.TypeInfoSchemaInfo(
                                            input='{"foobar":["baz"]}'))
    )

  def withCompositeType(self):
    self.withType(provider='composite')
    self.mocked_client.compositeTypes.Get.Expect(
        request=self.messages.DeploymentmanagerCompositeTypesGetRequest(
            project=self.Project(),
            compositeType='foo'
        ),
        response=self.messages.CompositeType(name='foo',
                                             description=COMPOSITE_DESCRIPTION)
    )

  def withExceptionalType(self):
    http_err = http_error.MakeHttpError(code=404)
    self.mocked_client.typeProviders.GetType.Expect(
        request=self.messages.DeploymentmanagerTypeProvidersGetTypeRequest(
            project=self.Project(),
            type='foo',
            typeProvider='bar'
        ),
        exception=http_err
    )
