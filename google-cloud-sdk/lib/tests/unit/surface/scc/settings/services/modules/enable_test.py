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
"""Tests for google3.third_party.py.tests.unit.surface.scc.settings.services.modules.enable."""

from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.scc import base


class ModulesEnableTest(base.SecurityCenterSettingsUnitTestBase):

  def testEnable_org_succeeds(self):
    expected_request = self._BuildShaRequest('organizations/12345',
                                             'OPEN_FIREWALL')
    expected_response = self._BuildResponse()
    self.mocked_client.organizations.UpdateSecurityHealthAnalyticsSettings.Expect(
        expected_request, expected_response)

    response = self.RunSccSettings('settings', 'services', 'modules', 'enable',
                                   '--organization', '12345', '--service',
                                   'SECURITY_HEALTH_ANALYTICS', '--module',
                                   'OPEN_FIREWALL')
    self.assertEqual(response, expected_response)

  def testEnable_folder_succeeds(self):
    expected_request = self._BuildShaRequest('folders/12345', 'OPEN_FIREWALL')
    expected_response = self._BuildResponse()
    self.mocked_client.folders.UpdateSecurityHealthAnalyticsSettings.Expect(
        expected_request, expected_response)

    response = self.RunSccSettings('settings', 'services', 'modules', 'enable',
                                   '--folder', '12345', '--service',
                                   'SECURITY_HEALTH_ANALYTICS', '--module',
                                   'OPEN_FIREWALL')
    self.assertEqual(response, expected_response)

  def testEnable_project_succeeds(self):
    expected_request = self._BuildShaRequest('projects/12345', 'OPEN_FIREWALL')
    expected_response = self._BuildResponse()
    self.mocked_client.projects.UpdateSecurityHealthAnalyticsSettings.Expect(
        expected_request, expected_response)

    response = self.RunSccSettings('settings', 'services', 'modules', 'enable',
                                   '--project', '12345', '--service',
                                   'SECURITY_HEALTH_ANALYTICS', '--module',
                                   'OPEN_FIREWALL')
    self.assertEqual(response, expected_response)

  def testEnable_invalidService_fails(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError, 'argument --service: Invalid choice'):
      self.RunSccSettings('settings', 'services', 'modules', 'enable',
                          '--organization', '12345', '--service',
                          'NOT_A_COMPONENT', '--module', 'OPEN_FIREWALL')

  def _BuildResponse(self):
    return self.messages.SecurityHealthAnalyticsSettings()

  def _BuildShaRequest(self, resource_name, module):
    name = '{}/securityHealthAnalyticsSettings'.format(resource_name)
    update_mask = 'modules'
    service_settings = self.messages.SecurityHealthAnalyticsSettings(
        modules=self.messages.SecurityHealthAnalyticsSettings.ModulesValue(
            additionalProperties=[
                self.messages.SecurityHealthAnalyticsSettings.ModulesValue
                .AdditionalProperty(
                    key=module,
                    value=self.messages.Config(
                        moduleEnablementState=self.messages.Config
                        .ModuleEnablementStateValueValuesEnum.ENABLED))
            ]))
    if resource_name.startswith('organizations'):
      return self.messages.SecuritycenterOrganizationsUpdateSecurityHealthAnalyticsSettingsRequest(
          name=name,
          updateMask=update_mask,
          securityHealthAnalyticsSettings=service_settings)
    elif resource_name.startswith('folders'):
      return self.messages.SecuritycenterFoldersUpdateSecurityHealthAnalyticsSettingsRequest(
          name=name,
          updateMask=update_mask,
          securityHealthAnalyticsSettings=service_settings)
    elif resource_name.startswith('projects'):
      return self.messages.SecuritycenterProjectsUpdateSecurityHealthAnalyticsSettingsRequest(
          name=name,
          updateMask=update_mask,
          securityHealthAnalyticsSettings=service_settings)
    else:
      raise ValueError('Invalid resource name.')


if __name__ == '__main__':
  test_case.main()
