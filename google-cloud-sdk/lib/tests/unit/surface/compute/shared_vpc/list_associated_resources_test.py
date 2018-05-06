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
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.compute import xpn_test_base


class ListAssociatedResourcesTest(xpn_test_base.XpnTestBase):

  def testListAssociatedResources_NoProject(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument PROJECT_ID: Must be specified.'):
      self.Run('compute shared-vpc list-associated-resources')
    self.xpn_client.ListEnabledResources.assert_not_called()

  def testListAssociatedResources(self):
    self._testListAssociatedResources('shared-vpc')

  def testListAssociatedResources_xpn(self):
    self._testListAssociatedResources('xpn')

  def _testListAssociatedResources(self, module_name):
    xpn_types = self.messages.XpnResourceId.TypeValueValuesEnum

    self.xpn_client.ListEnabledResources.return_value = iter([
        self.messages.XpnResourceId(
            id='associated-project-1', type=xpn_types.PROJECT),
        self.messages.XpnResourceId(
            id='associated-resource-2',
            type=xpn_types.XPN_RESOURCE_TYPE_UNSPECIFIED),
    ])

    self.Run('compute {} list-associated-resources foo'.format(module_name))

    self.AssertOutputEquals("""\
        RESOURCE_ID            RESOURCE_TYPE
        associated-project-1   PROJECT
        associated-resource-2  XPN_RESOURCE_TYPE_UNSPECIFIED
        """, normalize_space=True)
    self.xpn_client.ListEnabledResources.assert_called_once_with('foo')


if __name__ == '__main__':
  test_case.main()
