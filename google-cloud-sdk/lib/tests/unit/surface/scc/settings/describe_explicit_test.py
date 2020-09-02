# Lint as: python3
# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for google3.third_party.py.tests.unit.surface.scc.settings.describe-explicit."""

from tests.lib import test_case
from tests.lib.surface.scc import base


class DescribeExplicitTest(base.SecurityCenterSettingsUnitTestBase):

  def test_describe_explicit_organization(self):
    expected_request = self._BuildRequest('organizations/12345')
    expected_response = self._BuildResponse()
    self.mocked_client.organizations.GetSecurityCenterSettings.Expect(
        expected_request, expected_response)

    response = self.RunSccSettings('settings', 'describe-explicit',
                                   '--organization', '12345')
    self.assertEqual(response, expected_response)

  def _BuildRequest(self, resource_name):
    return self.messages.SecuritycenterOrganizationsGetSecurityCenterSettingsRequest(
        name='{}/securityCenterSettings'.format(resource_name))

  def _BuildResponse(self):
    return self.messages.SecurityCenterSettings()


if __name__ == '__main__':
  test_case.main()
