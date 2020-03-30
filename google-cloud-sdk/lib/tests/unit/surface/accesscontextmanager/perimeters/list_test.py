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
"""Tests for `gcloud access-context-manager perimeters list`."""

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


class PerimetersListTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakePerimeterNum(self, idx):
    return self._MakePerimeter('MY_PERIMETER{}'.format(idx))

  def _MakePerimeters(self, num=3):
    return list(map(self._MakePerimeterNum, list(range(num))))

  def _ExpectList(self, perimeters, policy):
    policy_name = 'accessPolicies/{}'.format(policy)
    m = self.messages
    request_type = (
        m.AccesscontextmanagerAccessPoliciesServicePerimetersListRequest)
    self.client.accessPolicies_servicePerimeters.List.Expect(
        request_type(parent=policy_name,),
        m.ListServicePerimetersResponse(servicePerimeters=perimeters))

  def testList(self):
    self.SetUpForAPI(self.api_version)
    perimeters = self._MakePerimeters()
    self._ExpectList(perimeters, '123')

    results = self.Run('access-context-manager perimeters list --policy 123')

    self.assertEqual(results, perimeters)

  def testList_PolicyFromProperty(self):
    self.SetUpForAPI(self.api_version)
    perimeters = self._MakePerimeters()
    policy = '456'
    properties.VALUES.access_context_manager.policy.Set(policy)
    self._ExpectList(perimeters, policy)

    results = self.Run('access-context-manager perimeters list')

    self.assertEqual(results, perimeters)

  def testList_Format(self):
    self.SetUpForAPI(self.api_version)
    properties.VALUES.core.user_output_enabled.Set(True)
    perimeters = self._MakePerimeters()
    self._ExpectList(perimeters, '123')

    self.Run('access-context-manager perimeters list --policy 123')

    self.AssertOutputEquals(
        """\
        NAME      TITLE
        MY_PERIMETER0  My Perimeter
        MY_PERIMETER1  My Perimeter
        MY_PERIMETER2  My Perimeter
        """,
        normalize_space=True)

  def testList_InvalidPolicyArg(self):
    with self.assertRaises(properties.InvalidValueError) as ex:
      # Common error is to specify --policy arg as 'accessPolicies/<num>'
      self.Run('access-context-manager perimeters list'
               '    --policy accessPolicies/123')
    self.assertIn('set to the policy number', text_type(ex.exception))


class PerimetersListTestBeta(PerimetersListTestGA):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA


class PerimetersListTestAlpha(PerimetersListTestGA):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
