# -*- coding: utf-8 -*- #
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

"""Unit tests for network diagnostics."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.diagnostics import check_base
from googlecloudsdk.core.diagnostics import property_diagnostics
from tests.lib import test_case
from tests.lib.core.diagnostics import diagnostics_test_base


def CheckFailResult(props):
  message = 'Hidden Property Check failed.\n'
  message += 'The following hidden properties have been set:\n'
  def CreateFailure(prop):
    msg = '[{0}]'.format(prop)
    return check_base.Failure(message=msg)
  failures = [CreateFailure(prop) for prop in props]
  for failure in failures:
    message += '    {0}\n'.format(failure.message)
  message += ('Properties files\n'
              '    User: {}\n'
              '    Installation: {}\n'.format(
                  named_configs.ConfigurationStore.ActiveConfig().file_path,
                  config.Paths().installation_properties_path)
             )
  return check_base.Result(passed=False, message=message, failures=failures)


class HiddenPropertiesCheckerTests(diagnostics_test_base.DiagnosticTestBase):

  def SetUp(self):
    # Unset the following environment variables, which are set in
    # sdk_test_base.py for all tests.
    self.StartEnvPatch({'CLOUDSDK_APP_RUNTIME_ROOT': None,
                        'CLOUDSDK_CORE_INTERACTIVE_UX_STYLE': None,
                        'CLOUDSDK_CORE_CHECK_GCE_METADATA': None,
                        'CLOUDSDK_CORE_SHOULD_PROMPT_TO_ENABLE_API': None})

  def testIgnoreWhitelistedProperty(self):
    self.StartEnvPatch({'CLOUDSDK_CORE_ENABLE_GRI': 'MOCK'})
    self.StartPropertyPatch(property_diagnostics.HiddenPropertiesChecker,
                            '_WHITELIST',
                            return_value={'core/enable_gri'})
    hidden_prop_checker = property_diagnostics.HiddenPropertiesChecker(False)

    expected_result = check_base.Result(passed=True,
                                        message='Hidden Property Check passed.')
    actual_result, actual_fixer = hidden_prop_checker.Check()
    self.AssertResultEqual(expected_result, actual_result)
    self.assertIsNone(actual_fixer)

  def testIgnoreUserWhitelistedProperty(self):
    self.StartEnvPatch({'CLOUDSDK_CORE_ENABLE_GRI': 'MOCK',
                        'CLOUDSDK_DIAGNOSTICS_HIDDEN_PROPERTY_WHITELIST':
                            'core/enable_gri'})
    hidden_prop_checker = property_diagnostics.HiddenPropertiesChecker(False)

    expected_result = check_base.Result(passed=True,
                                        message='Hidden Property Check passed.')
    actual_result, actual_fixer = hidden_prop_checker.Check()
    self.AssertResultEqual(expected_result, actual_result)
    self.assertIsNone(actual_fixer)

  def testIgnoreWhitelist(self):
    self.StartEnvPatch({'CLOUDSDK_CORE_ENABLE_GRI': 'MOCK',
                        'CLOUDSDK_DIAGNOSTICS_HIDDEN_PROPERTY_WHITELIST':
                            'core/enable_gri'})
    hidden_prop_checker = property_diagnostics.HiddenPropertiesChecker(True)

    expected_result = CheckFailResult(['core/enable_gri'])
    actual_result, actual_fixer = hidden_prop_checker.Check()
    self.AssertResultEqual(expected_result, actual_result)
    self.assertIsNone(actual_fixer)

  def testIgnoreWhitelistAlwaysIgnore_WHITELIST(self):
    self.StartEnvPatch({'CLOUDSDK_CORE_ENABLE_GRI': 'MOCK',
                        'CLOUDSDK_DIAGNOSTICS_HIDDEN_PROPERTY_WHITELIST':
                        'core/enable_gri'})
    self.StartPropertyPatch(property_diagnostics.HiddenPropertiesChecker,
                            '_WHITELIST',
                            return_value={'core/enable_gri'})
    hidden_prop_checker = property_diagnostics.HiddenPropertiesChecker(True)

    expected_result = check_base.Result(passed=True,
                                        message='Hidden Property Check passed.')
    actual_result, actual_fixer = hidden_prop_checker.Check()
    self.AssertResultEqual(expected_result, actual_result)
    self.assertIsNone(actual_fixer)

  def testIgnoreInternalProperty(self):
    self.StartEnvPatch({'CLOUDSDK_METRICS_COMMAND_NAME': 'MOCK'})
    hidden_prop_checker = property_diagnostics.HiddenPropertiesChecker(False)

    expected_result = check_base.Result(passed=True,
                                        message='Hidden Property Check passed.')
    actual_result, actual_fixer = hidden_prop_checker.Check()
    self.AssertResultEqual(expected_result, actual_result)
    self.assertIsNone(actual_fixer)

  def testWarnEnvironmentProperty(self):
    self.StartEnvPatch({'CLOUDSDK_CORE_ENABLE_GRI': 'True'})
    hidden_prop_checker = property_diagnostics.HiddenPropertiesChecker(False)

    expected_result = CheckFailResult(['core/enable_gri'])
    actual_result, actual_fixer = hidden_prop_checker.Check()
    self.AssertResultEqual(expected_result, actual_result)
    self.assertIsNone(actual_fixer)

  def testWarnActiveConfigurationProperty(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root',
                            return_value=self.temp_path)
    prop = properties.VALUES.core.enable_gri
    properties.PersistProperty(prop, 'True', properties.Scope.USER)
    hidden_prop_checker = property_diagnostics.HiddenPropertiesChecker(False)

    expected_result = CheckFailResult(['core/enable_gri'])
    actual_result, actual_fixer = hidden_prop_checker.Check()
    self.AssertResultEqual(expected_result, actual_result)
    self.assertIsNone(actual_fixer)

  def testWarnInstallationConfigurationProperty(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root',
                            return_value=self.temp_path)
    prop = properties.VALUES.core.enable_gri
    properties.PersistProperty(prop, 'True', properties.Scope.INSTALLATION)
    hidden_prop_checker = property_diagnostics.HiddenPropertiesChecker(False)

    expected_result = CheckFailResult(['core/enable_gri'])
    actual_result, actual_fixer = hidden_prop_checker.Check()
    self.AssertResultEqual(expected_result, actual_result)
    self.assertIsNone(actual_fixer)


if __name__ == '__main__':
  test_case.main()
