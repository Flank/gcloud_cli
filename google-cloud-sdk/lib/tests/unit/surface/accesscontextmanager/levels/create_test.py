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
"""Tests for `gcloud access-context-manager levels create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager
from six import text_type


class LevelsCreateTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectCreate(self, level, policy):
    policy_name = 'accessPolicies/{}'.format(policy)
    m = self.messages
    req_type = m.AccesscontextmanagerAccessPoliciesAccessLevelsCreateRequest
    self.client.accessPolicies_accessLevels.Create.Expect(
        req_type(parent=policy_name, accessLevel=level),
        self.messages.Operation(name='operations/my-op', done=False))
    self._ExpectGetOperation('operations/my-op')
    get_req_type = m.AccesscontextmanagerAccessPoliciesAccessLevelsGetRequest
    self.client.accessPolicies_accessLevels.Get.Expect(
        get_req_type(name=level.name), level)

  def testCreateBasic_InvalidSpec(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(
        yaml.FileLoadError, r'Failed to load YAML from [not-found]'):
      self.Run('access-context-manager levels create my_level --policy 123 '
               '     --title "My Level" --basic-level-spec not-found')

  def testCreate_MissingRequired(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Must be specified'):
      self.Run('access-context-manager levels create my_level --policy 123 '
               '     --title "My Level"')

  def testCreateBasic(self):
    self.SetUpForAPI(self.api_version)
    level_name = 'accessPolicies/123/accessLevels/my_level'
    level = self._MakeBasicLevel(
        level_name, title='My Level', combining_function='AND')
    self._ExpectCreate(level, '123')
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.BASIC_LEVEL_SPEC)

    results = self.Run(
        'access-context-manager levels create my_level --policy 123 '
        '     --title "My Level"'
        '     --basic-level-spec {}'.format(level_spec_path))

    self.assertEqual(results, level)

  def testCreateBasic_AllParams(self):
    self.SetUpForAPI(self.api_version)
    level_name = 'accessPolicies/123/accessLevels/my_level'
    level = self._MakeBasicLevel(
        level_name,
        title='My Level',
        combining_function='OR',
        description='Very long description of my level')
    self._ExpectCreate(level, '123')
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.BASIC_LEVEL_SPEC)

    results = self.Run(
        'access-context-manager levels create my_level --policy 123 '
        '     --title "My Level"'
        '     --combine-function or '
        '     --description "Very long description of my level" '
        '     --basic-level-spec {}'.format(level_spec_path))

    self.assertEqual(results, level)

  def testCreateBasic_PolicyFromProperty(self):
    self.SetUpForAPI(self.api_version)
    policy = '456'
    level_name = 'accessPolicies/456/accessLevels/my_level'
    properties.VALUES.access_context_manager.policy.Set(policy)
    level = self._MakeBasicLevel(
        level_name, title='My Level', combining_function='AND')
    self._ExpectCreate(level, policy)
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.BASIC_LEVEL_SPEC)

    results = self.Run('access-context-manager levels create my_level '
                       '     --title "My Level"'
                       '     --basic-level-spec {}'.format(level_spec_path))

    self.assertEqual(results, level)

  def testCreate_InvalidPolicyArg(self):
    self.SetUpForAPI(self.api_version)
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.BASIC_LEVEL_SPEC)

    with self.assertRaises(properties.InvalidValueError) as ex:
      # Common error is to specify --policy arg as 'accessPolicies/<num>'
      self.Run(
          'access-context-manager levels create my_level --policy accessPolicies/123 '
          '     --title "My Level"'
          '     --combine-function or '
          '     --description "Very long description of my level" '
          '     --basic-level-spec {}'.format(level_spec_path))
    self.assertIn('set to the policy number', text_type(ex.exception))


class LevelsCreateTestBeta(LevelsCreateTestGA):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA

  def testCreateCustom_InvalidSpec(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(
        yaml.FileLoadError, r'Failed to load YAML from [not-found]'):
      self.Run('access-context-manager levels create my_level --policy 123 '
               '     --title "My Level" --custom-level-spec not-found')

  def testCreateCustom(self):
    self.SetUpForAPI(self.api_version)
    level_name = 'accessPolicies/123/accessLevels/my_level'
    level = self._MakeCustomLevel(
        level_name,
        title='My Level',
        expression="inIpRange(origin.ip, ['127.0.0.1/24']")
    self._ExpectCreate(level, '123')
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.CUSTOM_LEVEL_SPEC)

    results = self.Run(
        'access-context-manager levels create my_level --policy 123 '
        '     --title "My Level"'
        '     --custom-level-spec {}'.format(level_spec_path))

    self.assertEqual(results, level)

  def testCreateBasicCustom_bothProvided(self):
    self.SetUpForAPI(self.api_version)
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.CUSTOM_LEVEL_SPEC)

    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           r'Exactly one of'):
      self.Run('access-context-manager levels create my_level --policy 123 '
               '     --title "My Level"'
               '     --basic-level-spec {}'
               '     --custom-level-spec {}'.format(level_spec_path,
                                                    level_spec_path))

  def testCreate_MissingRequired(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Exactly one of'):
      self.Run('access-context-manager levels create my_level --policy 123 '
               '     --title "My Level"')


class LevelsCreateTestAlpha(LevelsCreateTestGA):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreateCustom_InvalidSpec(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(
        yaml.FileLoadError, r'Failed to load YAML from [not-found]'):
      self.Run('access-context-manager levels create my_level --policy 123 '
               '     --title "My Level" --custom-level-spec not-found')

  def testCreateCustom(self):
    self.SetUpForAPI(self.api_version)
    level_name = 'accessPolicies/123/accessLevels/my_level'
    level = self._MakeCustomLevel(
        level_name,
        title='My Level',
        expression="inIpRange(origin.ip, ['127.0.0.1/24']")
    self._ExpectCreate(level, '123')
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.CUSTOM_LEVEL_SPEC)

    results = self.Run(
        'access-context-manager levels create my_level --policy 123 '
        '     --title "My Level"'
        '     --custom-level-spec {}'.format(level_spec_path))

    self.assertEqual(results, level)

  def testCreateBasicCustom_bothProvided(self):
    self.SetUpForAPI(self.api_version)
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.CUSTOM_LEVEL_SPEC)

    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           r'Exactly one of'):
      self.Run('access-context-manager levels create my_level --policy 123 '
               '     --title "My Level"'
               '     --basic-level-spec {}'
               '     --custom-level-spec {}'.format(level_spec_path,
                                                    level_spec_path))

  def testCreate_MissingRequired(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Exactly one of'):
      self.Run('access-context-manager levels create my_level --policy 123 '
               '     --title "My Level"')


if __name__ == '__main__':
  test_case.main()
