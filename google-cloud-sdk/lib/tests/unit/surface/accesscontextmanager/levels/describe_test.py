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
"""Tests for `gcloud access-context-manager levels describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager
from six import text_type


class LevelsDescribeTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectGet(self, level, policy, level_format='AS_DEFINED'):
    level_name = 'accessPolicies/{}/accessLevels/{}'.format(policy, level.name)
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesAccessLevelsGetRequest
    level_format = request_type.AccessLevelFormatValueValuesEnum(level_format)
    self.client.accessPolicies_accessLevels.Get.Expect(
        request_type(name=level_name, accessLevelFormat=level_format), level)

  def testDescribe_MissingRequired(self):
    self.SetUpForTrack(self.track)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'must be specified'):
      self.Run('access-context-manager levels describe --policy 123')

  def testDescribe(self):
    self.SetUpForTrack(self.track)
    level = self._MakeBasicLevel(
        'my_level', title='My Level', combining_function='AND')
    self._ExpectGet(level, '123')

    result = self.Run(
        'access-context-manager levels describe my_level --policy 123')

    self.assertEqual(result, level)

  def testDescribe_PolicyFromProperty(self):
    self.SetUpForTrack(self.track)
    level = self._MakeBasicLevel(
        'my_level', title='My Level', combining_function='AND')
    policy = '456'
    properties.VALUES.access_context_manager.policy.Set(policy)
    self._ExpectGet(level, policy)

    result = self.Run('access-context-manager levels describe my_level')

    self.assertEqual(result, level)

  def testDescribe_InvalidPolicyArg(self):
    self.SetUpForTrack(self.track)
    with self.assertRaises(properties.InvalidValueError) as ex:
      # Common error is to specify --policy arg as 'accessPolicies/<num>'
      self.Run('access-context-manager levels describe my_level'
               ' --policy accessPolicy/123')
    self.assertIn('set to the policy number', text_type(ex.exception))


class LevelsDescribeTestBeta(LevelsDescribeTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class LevelsDescribeTestAlpha(LevelsDescribeTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
