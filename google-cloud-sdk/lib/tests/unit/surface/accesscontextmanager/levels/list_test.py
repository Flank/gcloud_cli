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
"""Tests for `gcloud access-context-manager levels list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager
from six import text_type
from six.moves import map
from six.moves import range


class LevelsListTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakeBasicLevelNum(self, idx):
    combining_function = ['AND', 'OR'][idx % 2]
    return self._MakeBasicLevel(
        'level{}'.format(idx),
        combining_function=combining_function,
        description='My level #{} is very complicated.'.format(idx),
        title='My level #{}'.format(idx))

  def _MakeCustomLevelNum(self, idx):
    return self._MakeCustomLevel(
        'customlevel{}'.format(idx),
        expression='1 < {}'.format(idx),
        description='My custom level #{} is very complicated.'.format(idx),
        title='My custom level #{}'.format(idx))

  def _MakeLevels(self, basic_num=3, custom_num=3):
    combined_list = list(map(self._MakeBasicLevelNum, list(range(basic_num))))
    combined_list.extend(
        list(map(self._MakeCustomLevelNum, list(range(custom_num)))))
    return combined_list

  def _MakeLevelsPerTrack(self):
    return self._MakeLevels(basic_num=3, custom_num=0)

  def _ExpectList(self, levels, policy):
    policy_name = 'accessPolicies/{}'.format(policy)
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesAccessLevelsListRequest
    self.client.accessPolicies_accessLevels.List.Expect(
        request_type(parent=policy_name,),
        self.messages.ListAccessLevelsResponse(accessLevels=levels))

  def testList(self):
    self.SetUpForAPI(self.api_version)
    levels = self._MakeLevelsPerTrack()
    self._ExpectList(levels, '123')

    results = self.Run('access-context-manager levels list --policy 123')

    self.assertEqual(results, levels)

  def testList_PolicyFromProperty(self):
    self.SetUpForAPI(self.api_version)
    levels = self._MakeLevelsPerTrack()
    policy = '456'
    properties.VALUES.access_context_manager.policy.Set(policy)
    self._ExpectList(levels, policy)

    results = self.Run('access-context-manager levels list')

    self.assertEqual(results, levels)

  def testList_Format(self):
    self.SetUpForAPI(self.api_version)
    properties.VALUES.core.user_output_enabled.Set(True)
    levels = self._MakeLevelsPerTrack()
    self._ExpectList(levels, '123')

    self.Run('access-context-manager levels list --policy 123')

    self.AssertOutputEquals(
        """\
        NAME    TITLE        LEVEL_TYPE
        level0  My level #0  Basic
        level1  My level #1  Basic
        level2  My level #2  Basic
        """,
        normalize_space=True)

  def testList_InvalidPolicyArg(self):
    self.SetUpForAPI(self.api_version)
    with self.assertRaises(properties.InvalidValueError) as ex:
      # Common error is to specify --policy arg as 'accessPolicies/<num>'
      self.Run('access-context-manager levels list'
               ' --policy accessPolicy/123')
    self.assertIn('set to the policy number', text_type(ex.exception))


class LevelsListTestBeta(LevelsListTestGA):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA

  def _MakeLevelsPerTrack(self):
    return self._MakeLevels(basic_num=3, custom_num=3)

  def testList_Format(self):
    self.SetUpForAPI(self.api_version)
    properties.VALUES.core.user_output_enabled.Set(True)
    levels = self._MakeLevelsPerTrack()
    self._ExpectList(levels, '123')

    self.Run('access-context-manager levels list --policy 123')

    self.AssertOutputEquals(
        """\
        NAME    TITLE        LEVEL_TYPE
        level0  My level #0  Basic
        level1  My level #1  Basic
        level2  My level #2  Basic
        customlevel0  My custom level #0  Custom
        customlevel1  My custom level #1  Custom
        customlevel2  My custom level #2  Custom
        """,
        normalize_space=True)


class LevelsListTestAlpha(LevelsListTestGA):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _MakeLevelsPerTrack(self):
    return self._MakeLevels(basic_num=3, custom_num=3)

  def testList_Format(self):
    self.SetUpForAPI(self.api_version)
    properties.VALUES.core.user_output_enabled.Set(True)
    levels = self._MakeLevelsPerTrack()
    self._ExpectList(levels, '123')

    self.Run('access-context-manager levels list --policy 123')

    self.AssertOutputEquals(
        """\
        NAME    TITLE        LEVEL_TYPE
        level0  My level #0  Basic
        level1  My level #1  Basic
        level2  My level #2  Basic
        customlevel0  My custom level #0  Custom
        customlevel1  My custom level #1  Custom
        customlevel2  My custom level #2  Custom
        """,
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
