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

"""Unit tests for type-providers list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base


class TypeProvidersListTest(unit_test_base.DmV2UnitTestBase):
  """Unit tests for type-providers list command."""

  def SetUp(self):
    self.TargetingV2BetaApi()
    self.TargetingBetaCommandTrack()

  def testList(self):
    insert_time_string = '2016-10-18T09:56:11.710-07:00'
    providers = [self.messages.TypeProvider(name='provider-1',
                                            insertTime=insert_time_string),
                 self.messages.TypeProvider(name='provider-2')]
    self.mocked_client.typeProviders.List.Expect(
        request=self.messages.DeploymentmanagerTypeProvidersListRequest(
            project=self.Project()
        ),
        response=self.messages.TypeProvidersListResponse(
            typeProviders=providers
        )
    )
    self.Run('deployment-manager type-providers list')
    expected_output = ('NAME        INSERT_DATE\n'
                       'provider-1  2016-10-18\n'
                       'provider-2\n')
    self.AssertOutputEquals(expected_output)

  def testEmptyList(self):
    self.mocked_client.typeProviders.List.Expect(
        request=self.messages.DeploymentmanagerTypeProvidersListRequest(
            project=self.Project()
        ),
        response=self.messages.TypeProvidersListResponse()
    )
    self.Run('deployment-manager type-providers list')
    self.AssertErrEquals('Listed 0 items.\n')
    self.AssertOutputEquals('')

if __name__ == '__main__':
  test_case.main()
