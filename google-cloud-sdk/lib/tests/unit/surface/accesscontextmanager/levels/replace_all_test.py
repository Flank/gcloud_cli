# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud access-context-manager levels replace-all`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class LevelsReplaceAllTest(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectReplace(self, levels=None, policy=''):
    policy_name = 'accessPolicies/{}'.format(policy)
    m = self.messages
    req_type = m.AccesscontextmanagerAccessPoliciesAccessLevelsReplaceAllRequest
    replace_levels_req_type = m.ReplaceAccessLevelsRequest
    response_type = m.ReplaceAccessLevelsResponse(accessLevels=levels)
    response_value = encoding.DictToMessage(
        encoding.MessageToDict(response_type), m.Operation.ResponseValue)

    op = self.messages.Operation(
        name='operations/{}/replaceLevels/9876543210'.format(policy_name),
        response=response_value,
        done=True)
    self.client.accessPolicies_accessLevels.ReplaceAll.Expect(
        req_type(
            parent=policy_name,
            replaceAccessLevelsRequest=replace_levels_req_type(
                etag='12345ff', accessLevels=levels)), op)
    self._ExpectGetOperation(
        'operations/{}/replaceLevels/9876543210'.format(policy_name))
    list_req_type = m.AccesscontextmanagerAccessPoliciesAccessLevelsListRequest
    list_response_type = m.ListAccessLevelsResponse
    self.client.accessPolicies_accessLevels.List.Expect(
        list_req_type(parent=policy_name),
        list_response_type(accessLevels=levels))

  def testReplace_InvalidSourceFileArg(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(
        yaml.FileLoadError, 'Failed to load YAML from [not-found]'):
      self.Run('access-context-manager levels replace-all 1234 --source-file '
               'not-found')

  def testReplace_MissingSourceFile(self):
    self.SetUpForAPI(self.api_version)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Must be specified'):
      self.Run('access-context-manager levels replace-all 1234')

  def testReplace_MissingPolicy(self):
    self.SetUpForAPI(self.api_version)
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.ACCESS_LEVEL_SPECS_BASIC)
    with self.AssertRaisesExceptionMatches(
        handlers.ParseError, 'resource is not properly specified.'):
      self.Run(
          'access-context-manager levels replace-all --source-file {}'.format(
              level_spec_path))

  def testReplace(self):
    self.SetUpForAPI(self.api_version)
    level_name1 = 'accessPolicies/1234/accessLevels/myLevel1'
    level_name2 = 'accessPolicies/1234/accessLevels/myLevel2'
    levels = [
        self._MakeBasicLevel(
            name=level_name1,
            title='replacement level 1',
            description='level description 1',
            combining_function='AND'),
        self._MakeBasicLevel(
            name=level_name2,
            title='replacement level 2',
            description='level description 2',
            combining_function='AND')
    ]

    self._ExpectReplace(levels, '1234')
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.ACCESS_LEVEL_SPECS_BASIC)

    results = self.Run(
        'access-context-manager levels replace-all 1234 --etag=12345ff --source-file {}'
        .format(level_spec_path))
    self.assertEqual(results.accessLevels, levels)

  def testReplaceWithCustom(self):
    self.SetUpForAPI(self.api_version)
    level_name1 = 'accessPolicies/1234/accessLevels/myLevel1'
    level_name2 = 'accessPolicies/1234/accessLevels/myLevel2'
    levels = [
        self._MakeBasicLevel(
            name=level_name1,
            title='replacement level 1',
            description='level description 1',
            combining_function='AND'),
        self._MakeCustomLevel(
            name=level_name2,
            title='replacement level 2',
            description='level description 2',
            expression="inIpRange(origin.ip, ['127.0.0.1/24'])")
    ]

    self._ExpectReplace(levels, '1234')
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.ACCESS_LEVEL_SPECS_BASIC_CUSTOM)

    results = self.Run(
        'access-context-manager levels replace-all 1234 --etag=12345ff --source-file {}'
        .format(level_spec_path))
    self.assertEqual(results.accessLevels, levels)

  def testReplace_PolicyFromProperty(self):
    self.SetUpForAPI(self.api_version)
    policy = '1234'
    properties.VALUES.access_context_manager.policy.Set(policy)

    level_name1 = 'accessPolicies/1234/accessLevels/myLevel1'
    level_name2 = 'accessPolicies/1234/accessLevels/myLevel2'
    levels = [
        self._MakeBasicLevel(
            name=level_name1,
            title='replacement level 1',
            description='level description 1',
            combining_function='AND'),
        self._MakeBasicLevel(
            name=level_name2,
            title='replacement level 2',
            description='level description 2',
            combining_function='AND')
    ]

    self._ExpectReplace(levels, '1234')
    level_spec_path = self.Touch(
        self.temp_path, '', contents=self.ACCESS_LEVEL_SPECS_BASIC)

    results = self.Run(
        'access-context-manager levels replace-all --etag=12345ff --source-file {}'
        .format(level_spec_path))
    self.assertEqual(results.accessLevels, levels)


class LevelsReplaceAllTestAlpha(LevelsReplaceAllTest):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
