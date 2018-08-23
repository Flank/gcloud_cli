# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


@parameterized.parameters((base.ReleaseTrack.ALPHA,))
class LevelsDescribeTest(accesscontextmanager.Base):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectGet(self, level, policy, level_format='AS_DEFINED'):
    level_name = 'accessPolicies/{}/accessLevels/{}'.format(policy, level.name)
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesAccessLevelsGetRequest
    level_format = request_type.AccessLevelFormatValueValuesEnum(level_format)
    self.client.accessPolicies_accessLevels.Get.Expect(
        request_type(
            name=level_name,
            accessLevelFormat=level_format
        ),
        level)

  def testDescribe_MissingRequired(self, track):
    self.SetUpForTrack(track)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'must be specified'):
      self.Run('access-context-manager levels describe --policy my_policy')

  def testDescribe(self, track):
    self.SetUpForTrack(track)
    level = self._MakeBasicLevel('my_level', title='My Level',
                                 combining_function='AND')
    self._ExpectGet(level, 'my_policy')

    result = self.Run(
        'access-context-manager levels describe my_level --policy my_policy')

    self.assertEqual(result, level)

  def testDelete_PolicyFromProperty(self, track):
    self.SetUpForTrack(track)
    level = self._MakeBasicLevel('my_level', title='My Level',
                                 combining_function='AND')
    policy = 'my_acm_policy'
    properties.VALUES.access_context_manager.policy.Set(policy)
    self._ExpectGet(level, policy)

    result = self.Run(
        'access-context-manager levels describe my_level')

    self.assertEqual(result, level)

if __name__ == '__main__':
  test_case.main()
