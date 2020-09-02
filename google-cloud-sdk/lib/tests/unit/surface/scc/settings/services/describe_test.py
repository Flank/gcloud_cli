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
"""Tests for google3.third_party.py.tests.unit.surface.scc.settings.services.describe."""

from tests.lib import test_case
from tests.lib.surface.scc import base
from tests.lib import cli_test_base


class DescribeTest(base.SecurityCenterSettingsUnitTestBase):

  def test_describe_organization_web_security_scanner(self):
    expected_request = self._BuildWSSRequest('organizations/12345')
    expected_response = self._BuildWSSResponse()
    self.mocked_client.organizations_webSecurityScannerSettings.Calculate.Expect(
        expected_request, expected_response)

    response = self.RunSccSettings('settings', 'services', 'describe',
                                   '--organization', '12345', '--service',
                                   'WEB_SECURITY_SCANNER')
    self.assertEqual(response, expected_response)

  def test_describe_folders_web_security_scanner(self):
    expected_request = self._BuildWSSRequest('folders/12345')
    expected_response = self._BuildWSSResponse()
    self.mocked_client.folders_webSecurityScannerSettings.Calculate.Expect(
        expected_request, expected_response)

    response = self.RunSccSettings('settings', 'services', 'describe',
                                   '--folder', '12345', '--service',
                                   'WEB_SECURITY_SCANNER')
    self.assertEqual(response, expected_response)

  def test_describe_projects_web_security_scanner(self):
    expected_request = self._BuildWSSRequest('projects/12345')
    expected_response = self._BuildWSSResponse()
    self.mocked_client.projects_webSecurityScannerSettings.Calculate.Expect(
        expected_request, expected_response)

    response = self.RunSccSettings('settings', 'services', 'describe',
                                   '--project', '12345', '--service',
                                   'WEB_SECURITY_SCANNER')
    self.assertEqual(response, expected_response)

  def test_describe_invalid_service(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError, 'argument --service: Invalid choice'):
      self.RunSccSettings('settings', 'services', 'describe', '--organization',
                          '12345', '--service', 'NOT_A_COMPONENT')

  def _BuildWSSRequest(self, resource_name):
    name = '{}/webSecurityScannerSettings'.format(resource_name)
    if resource_name.startswith('organizations'):
      return self.messages.SecuritycenterOrganizationsWebSecurityScannerSettingsCalculateRequest(
          name=name)
    elif resource_name.startswith('folders'):
      return self.messages.SecuritycenterFoldersWebSecurityScannerSettingsCalculateRequest(
          name=name)
    elif resource_name.startswith('projects'):
      return self.messages.SecuritycenterProjectsWebSecurityScannerSettingsCalculateRequest(
          name=name)

  def _BuildWSSResponse(self):
    return self.messages.WebSecurityScannerSettings()


if __name__ == '__main__':
  test_case.main()
