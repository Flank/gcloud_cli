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
"""Tests for `gcloud access-context-manager levels list`."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager
from six.moves import map
from six.moves import range


@parameterized.parameters((base.ReleaseTrack.ALPHA,))
class LevelsListTest(accesscontextmanager.Base):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakeBasicLevelNum(self, idx):
    combining_function = ['AND', 'OR'][idx % 2]
    return self._MakeBasicLevel(
        'level{}'.format(idx),
        combining_function=combining_function,
        description='My level #{} is very complicated.'.format(idx),
        title='My level #{}'.format(idx))

  def _MakeLevels(self, num=3):
    return list(map(self._MakeBasicLevelNum, list(range(num))))

  def _ExpectList(self, levels, policy):
    policy_name = 'accessPolicies/{}'.format(policy)
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesAccessLevelsListRequest
    self.client.accessPolicies_accessLevels.List.Expect(
        request_type(
            parent=policy_name,
        ),
        self.messages.ListAccessLevelsResponse(accessLevels=levels))

  def testList(self, track):
    self.SetUpForTrack(track)
    levels = self._MakeLevels()
    self._ExpectList(levels, 'my-policy')

    results = self.Run('access-context-manager levels list --policy my-policy')

    self.assertEqual(results, levels)

  def testList_PolicyFromProperty(self, track):
    self.SetUpForTrack(track)
    levels = self._MakeLevels()
    policy = 'my-acm-policy'
    properties.VALUES.access_context_manager.policy.Set(policy)
    self._ExpectList(levels, policy)

    results = self.Run('access-context-manager levels list')

    self.assertEqual(results, levels)

  def testList_Format(self, track):
    self.SetUpForTrack(track)
    properties.VALUES.core.user_output_enabled.Set(True)
    levels = self._MakeLevels()
    self._ExpectList(levels, 'my-policy')

    self.Run('access-context-manager levels list --policy my-policy')

    self.AssertOutputEquals("""\
        NAME    TITLE        LEVEL_TYPE
        level0  My level #0  Basic
        level1  My level #1  Basic
        level2  My level #2  Basic
        """, normalize_space=True)

if __name__ == '__main__':
  test_case.main()
