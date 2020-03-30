# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud access-context-manager levels update`."""

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


class LevelsUpdateTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectPatch(self, level_id, level, policy, update_mask):
    level_name = 'accessPolicies/{}/accessLevels/{}'.format(policy, level_id)
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesAccessLevelsPatchRequest
    self.client.accessPolicies_accessLevels.Patch.Expect(
        request_type(
            name=level_name, accessLevel=level, updateMask=update_mask),
        self.messages.Operation(done=False, name='operations/my-op'))
    self._ExpectGetOperation('operations/my-op')
    get_req_type = m.AccesscontextmanagerAccessPoliciesAccessLevelsGetRequest
    self.client.accessPolicies_accessLevels.Get.Expect(
        get_req_type(
            name='accessPolicies/{}/accessLevels/{}'.format(policy, level_id)),
        level)

  def testUpdateBasic_InvalidSpec(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(
        yaml.FileLoadError, r'Failed to load YAML from [not-found]'):
      self.Run('access-context-manager levels update my_level --policy 123 '
               '    --basic-level-spec not-found')

  def testUpdate_MissingRequired(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'must be specified'):
      self.Run('access-context-manager levels update --policy 123')

  def testUpdate(self):
    self.SetUpForAPI(self.api_version)
    level = self.messages.AccessLevel(title='My Level')
    self._ExpectPatch('my_level', level, '123', 'title')

    results = self.Run(
        'access-context-manager levels update my_level --policy 123 '
        '     --title "My Level"')

    self.assertEqual(results, level)

  def testUpdate_AllParams(self):
    self.SetUpForAPI(self.api_version)
    level = self._MakeBasicLevel(
        None,
        title='My Level',
        combining_function='OR',
        description='Very long description of my level')
    self._ExpectPatch(
        'my_level', level, '123',
        'basic.combiningFunction,basic.conditions,description,title')
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.BASIC_LEVEL_SPEC)

    results = self.Run(
        'access-context-manager levels update my_level --policy 123 '
        '     --title "My Level"'
        '     --combine-function or '
        '     --description "Very long description of my level" '
        '     --basic-level-spec {}'.format(level_spec_path))

    self.assertEqual(results, level)

  def testUpdate_PolicyFromProperty(self):
    self.SetUpForAPI(self.api_version)
    policy = '456'
    properties.VALUES.access_context_manager.policy.Set(policy)
    level = self.messages.AccessLevel(title='My Level')
    self._ExpectPatch('my_level', level, policy, 'title')

    results = self.Run(
        'access-context-manager levels update my_level --title "My Level"')

    self.assertEqual(results, level)

  def testUpdate_InvalidPolicyArg(self):
    self.SetUpForAPI(self.api_version)
    with self.assertRaises(properties.InvalidValueError) as ex:
      # Common error is to specify --policy arg as 'accessPolicies/<num>'
      self.Run(
          'access-context-manager levels update my_level --title "My Level"'
          ' --policy accessPolicy/123')
    self.assertIn('set to the policy number', text_type(ex.exception))


class LevelsUpdateTestBeta(LevelsUpdateTestGA):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA

  def testUpdateCustom_InvalidSpec(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(
        yaml.FileLoadError, r'Failed to load YAML from [not-found]'):
      self.Run('access-context-manager levels update my_level --policy 123 '
               '    --custom-level-spec not-found')

  def testUpdateCustom_BasicSpecSpecified(self):
    self.SetUpForAPI(self.api_version)
    basic_level_spec_path = self.Touch(
        self.temp_path, 'basic.yaml', contents=self.BASIC_LEVEL_SPEC)
    custom_level_spec_path = self.Touch(
        self.temp_path, 'custom.yaml', contents=self.CUSTOM_LEVEL_SPEC)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           r'At most one of'):
      self.Run('access-context-manager levels update my_level --policy 123 '
               '     --title "My Level"'
               '     --description "Very long description of my level" '
               '     --basic-level-spec {}'
               '     --custom-level-spec {}'.format(basic_level_spec_path,
                                                    custom_level_spec_path))

  def testUpdateCustom_AllParams(self):
    self.SetUpForAPI(self.api_version)
    level = self._MakeCustomLevel(
        None,
        title='My Level',
        description='Very long description of my level',
        expression="inIpRange(origin.ip, ['127.0.0.1/24']")
    self._ExpectPatch('my_level', level, '123', 'custom,description,title')
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.CUSTOM_LEVEL_SPEC)

    results = self.Run(
        'access-context-manager levels update my_level --policy 123 '
        '     --title "My Level"'
        '     --description "Very long description of my level" '
        '     --custom-level-spec {}'.format(level_spec_path))

    self.assertEqual(results, level)


class LevelsUpdateTestAlpha(LevelsUpdateTestGA):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testUpdateCustom_InvalidSpec(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(
        yaml.FileLoadError, r'Failed to load YAML from [not-found]'):
      self.Run('access-context-manager levels update my_level --policy 123 '
               '    --custom-level-spec not-found')

  def testUpdateCustom_BasicSpecSpecified(self):
    self.SetUpForAPI(self.api_version)
    basic_level_spec_path = self.Touch(
        self.temp_path, 'basic.yaml', contents=self.BASIC_LEVEL_SPEC)
    custom_level_spec_path = self.Touch(
        self.temp_path, 'custom.yaml', contents=self.CUSTOM_LEVEL_SPEC)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           r'At most one of'):
      self.Run('access-context-manager levels update my_level --policy 123 '
               '     --title "My Level"'
               '     --description "Very long description of my level" '
               '     --basic-level-spec {}'
               '     --custom-level-spec {}'.format(basic_level_spec_path,
                                                    custom_level_spec_path))

  def testUpdateCustom_AllParams(self):
    self.SetUpForAPI(self.api_version)
    level = self._MakeCustomLevel(
        None,
        title='My Level',
        description='Very long description of my level',
        expression="inIpRange(origin.ip, ['127.0.0.1/24']")
    self._ExpectPatch('my_level', level, '123', 'custom,description,title')
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.CUSTOM_LEVEL_SPEC)

    results = self.Run(
        'access-context-manager levels update my_level --policy 123 '
        '     --title "My Level"'
        '     --description "Very long description of my level" '
        '     --custom-level-spec {}'.format(level_spec_path))

    self.assertEqual(results, level)


if __name__ == '__main__':
  test_case.main()
