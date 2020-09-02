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
"""Tests for google3.third_party.py.tests.unit.surface.scc.settings.services.modules_describe_explicit."""

from tests.lib import test_case
from tests.lib.surface.scc import base


class SettingsDescribeExplicitTest(base.SecurityCenterSettingsUnitTestBase):

  def testDescribeExplicit_org_succeeds(self):
    request_message = self._BuildShaRequest('organizations/12345')
    response_message = self._BuildShaResponse('OPEN_FIREWALL')
    self.mocked_client.organizations.GetSecurityHealthAnalyticsSettings.Expect(
        request_message, response=response_message)
    result = self.RunSccSettings('settings', 'services', 'modules',
                                 'describe-explicit', '--organization', '12345',
                                 '--service', 'SECURITY_HEALTH_ANALYTICS',
                                 '--module', 'OPEN_FIREWALL')

    self.assertEqual(
        result,
        self.messages.Config.ModuleEnablementStateValueValuesEnum.ENABLED)

  def testDescribeExplicit_folder_succeeds(self):
    request_message = self._BuildShaRequest('folders/12345')
    response_message = self._BuildShaResponse('OPEN_FIREWALL')
    self.mocked_client.folders.GetSecurityHealthAnalyticsSettings.Expect(
        request_message, response=response_message)
    result = self.RunSccSettings('settings', 'services', 'modules',
                                 'describe-explicit', '--folder', '12345',
                                 '--service', 'SECURITY_HEALTH_ANALYTICS',
                                 '--module', 'OPEN_FIREWALL')

    self.assertEqual(
        result,
        self.messages.Config.ModuleEnablementStateValueValuesEnum.ENABLED)

  def testDescribeExplicit_project_succeeds(self):
    request_message = self._BuildShaRequest('projects/12345')
    response_message = self._BuildShaResponse('OPEN_FIREWALL')
    self.mocked_client.projects.GetSecurityHealthAnalyticsSettings.Expect(
        request_message, response=response_message)
    result = self.RunSccSettings('settings', 'services', 'modules',
                                 'describe-explicit', '--project', '12345',
                                 '--service', 'SECURITY_HEALTH_ANALYTICS',
                                 '--module', 'OPEN_FIREWALL')

    self.assertEqual(
        result,
        self.messages.Config.ModuleEnablementStateValueValuesEnum.ENABLED)

  def testDescribeExplicit_org_moduleNotFound(self):
    request_message = self._BuildShaRequest('organizations/12345')
    response_message = self._BuildShaResponse('OPEN_FIREWALL')
    self.mocked_client.organizations.GetSecurityHealthAnalyticsSettings.Expect(
        request_message, response=response_message)

    result = self.RunSccSettings('settings', 'services', 'modules',
                                 'describe-explicit', '--organization', '12345',
                                 '--service', 'SECURITY_HEALTH_ANALYTICS',
                                 '--module', 'NON_EXISTENT_DETECTOR')

    self.assertEqual(result, None)
    self.AssertLogContains('No setting found')

  def _BuildShaRequest(self, resource_name):
    name = '{}/securityHealthAnalyticsSettings'.format(resource_name)
    if resource_name.startswith('organizations'):
      return self.messages.SecuritycenterOrganizationsGetSecurityHealthAnalyticsSettingsRequest(
          name=name)
    elif resource_name.startswith('folders'):
      return self.messages.SecuritycenterFoldersGetSecurityHealthAnalyticsSettingsRequest(
          name=name)
    elif resource_name.startswith('projects'):
      return self.messages.SecuritycenterProjectsGetSecurityHealthAnalyticsSettingsRequest(
          name=name)
    else:
      raise ValueError('Invalid resource name.')

  def _BuildShaResponse(self, module):
    return self.messages.SecurityHealthAnalyticsSettings(
        modules=self.messages.SecurityHealthAnalyticsSettings.ModulesValue(
            additionalProperties=[
                self.messages.SecurityHealthAnalyticsSettings.ModulesValue
                .AdditionalProperty(
                    key=module,
                    value=self.messages.Config(
                        moduleEnablementState=self.messages.Config
                        .ModuleEnablementStateValueValuesEnum.ENABLED))
            ]))


if __name__ == '__main__':
  test_case.main()
