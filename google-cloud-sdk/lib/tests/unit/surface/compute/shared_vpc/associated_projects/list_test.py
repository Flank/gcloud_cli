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
"""Tests for `gcloud compute shared-vpc associated-projects list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import xpn_test_base


@parameterized.parameters(
    (base.ReleaseTrack.ALPHA, 'alpha'),
    (base.ReleaseTrack.BETA, 'beta'),
    (base.ReleaseTrack.GA, 'v1'))
class ListTest(xpn_test_base.XpnApitoolsTestBase):

  def testList_NoProject(self, track, api_version):
    self._SetUp(track, api_version)
    with self.AssertRaisesArgumentErrorMatches(
        'argument PROJECT_ID: Must be specified.'):
      self.Run('compute shared-vpc associated-projects list')

  def testList(self, track, api_version):
    self._SetUp(track, api_version)
    self._testList('shared-vpc')

  def testList_xpn(self, track, api_version):
    self._SetUp(track, api_version)
    self._testList('xpn')

  def _testList(self, module_name):
    xpn_types = self.messages.XpnResourceId.TypeValueValuesEnum
    self.apitools_client.projects.GetXpnResources.Expect(
        self.messages.ComputeProjectsGetXpnResourcesRequest(project='foo'),
        self.messages.ProjectsGetXpnResources(
            kind='compute#projectsGetXpnResources',
            resources=[
                self.messages.XpnResourceId(
                    id='associated-project-1',
                    type=xpn_types.PROJECT),
                self.messages.XpnResourceId(
                    id='associated-resource-2',
                    type=xpn_types.XPN_RESOURCE_TYPE_UNSPECIFIED),
            ]))

    self.Run('compute {} associated-projects list foo'.format(module_name))

    self.AssertOutputEquals("""\
        RESOURCE_ID            RESOURCE_TYPE
        associated-project-1   PROJECT
        """, normalize_space=True)


if __name__ == '__main__':
  test_case.main()
