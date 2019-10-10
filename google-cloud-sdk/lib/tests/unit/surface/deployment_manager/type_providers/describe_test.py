# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Unit tests for 'type-providers describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from tests.lib.apitools import http_error
from tests.lib.surface.deployment_manager import unit_test_base


class TypeProvidersDescribeTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for 'type-providers describe' command."""

  def SetUp(self):
    self.TargetingV2BetaApi()
    self.TargetingBetaCommandTrack()

  def withTypeProvider(self):
    self.mocked_client.typeProviders.Get.Expect(
        request=self.messages.DeploymentmanagerTypeProvidersGetRequest(
            project=self.Project(),
            typeProvider='foo'
        ),
        response=self.messages.TypeProvider(name='foo',
                                            descriptorUrl='EXPERIMENTAL')
    )

  def withExceptionalTypeProvider(self):
    http_err = http_error.MakeHttpError(code=404)
    self.mocked_client.typeProviders.Get.Expect(
        request=self.messages.DeploymentmanagerTypeProvidersGetRequest(
            project=self.Project(),
            typeProvider='foo'
        ),
        exception=http_err
    )

  def testDescribeSuccess(self):
    self.withTypeProvider()
    result = self.Run('deployment-manager type-providers describe foo')
    self.assertEqual('foo', result.name)
    self.assertEqual('EXPERIMENTAL', result.descriptorUrl)

  def testDescribeWithUri(self):
    self.withTypeProvider()
    result = self.Run(
        'deployment-manager type-providers describe '
        'https://www.googleapis.com/deploymentmanager/v2beta/projects/{0}'
        '/global/typeProviders/foo'.format(self.Project()))
    self.assertEqual('foo', result.name)
    self.assertEqual('EXPERIMENTAL', result.descriptorUrl)

  def testDescribeNotFound(self):
    self.withExceptionalTypeProvider()
    with self.assertRaises(exceptions.HttpException):
      self.Run('deployment-manager type-providers describe foo')
