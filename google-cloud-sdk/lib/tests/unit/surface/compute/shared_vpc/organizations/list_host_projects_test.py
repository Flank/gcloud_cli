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
"""Tests for `gcloud compute shared-vpc list-associated-resources`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import xpn_test_base


@parameterized.parameters(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class ListHostProjectsTest(xpn_test_base.XpnTestBase):

  def testListHostProjects_ProjectUnset(self, track):
    self._SetUp(track)
    properties.PersistProperty(properties.VALUES.core.project, None)
    with self.assertRaises(properties.RequiredPropertyError):
      self.Run('compute shared-vpc organizations list-host-projects 12345')

  def testListHostProjects_OrganizationId(self, track):
    self._SetUp(track)
    self._testListHostProjects_OrganizationId('shared-vpc')

  def testListHostProjects_OrganizationId_xpn(self, track):
    self._SetUp(track)
    self._testListHostProjects_OrganizationId('xpn')

  def _testListHostProjects_OrganizationId(self, module_name):
    properties.VALUES.core.project.Set('myproject')
    self.xpn_client.ListOrganizationHostProjects.return_value = (
        iter([
            self._MakeProject()
        ]))

    self.Run(
        'compute {} organizations list-host-projects 12345'.format(module_name))

    self.AssertOutputEquals("""\
        NAME      CREATION_TIMESTAMP             XPN_PROJECT_STATUS
        xpn-host  2013-09-06T17:54:10.636-07:00  HOST
        """, normalize_space=True)
    self.xpn_client.ListOrganizationHostProjects.assert_called_once_with(
        'myproject', organization_id='12345')
    self.get_xpn_client_mock.assert_called_once_with(self.track)


if __name__ == '__main__':
  test_case.main()
