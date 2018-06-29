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
"""Tests for 'category-manager taxonomies get-iam-policy' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import sdk_test_base
from tests.lib.surface.category_manager import base


class GetIamPolicyIntegrationTest(base.CategoryManagerUnitTestBase):
  """Tests for category-manager stores get-iam-policy."""

  def SetUp(self):
    self.policy = self.messages.Policy(bindings=[
        self.messages.Binding(
            role='roles/categorymanager.admin',
            members=[
                'user:admin@gmail.com',
                'serviceAccount:account@test-project.googleservice.com'
            ]),
        self.messages.Binding(
            role='roles/categorymanager.reader',
            members=['user:user1@gmail.com', 'user:user2@gmail.com'])
    ])

  def testAddIamPolicyBindingWithOrganizationResource(self):
    self.ExpectGetTaxonomyStore(org_id='1', taxonomy_store_id='2')
    self.mock_client.taxonomyStores.GetIamPolicy.Expect(
        self.messages.CategorymanagerTaxonomyStoresGetIamPolicyRequest(
            resource='taxonomyStores/2',
            getIamPolicyRequest=self.messages.GetIamPolicyRequest()),
        self.policy)
    result = self.Run('alpha category-manager stores get-iam-policy '
                      '--organization organizations/1')
    self.assertEqual(self.policy, result)

  def testAddIamPolicyBindingWithOrganizationId(self):
    self.ExpectGetTaxonomyStore(org_id='3', taxonomy_store_id='4')
    self.mock_client.taxonomyStores.GetIamPolicy.Expect(
        self.messages.CategorymanagerTaxonomyStoresGetIamPolicyRequest(
            resource='taxonomyStores/4',
            getIamPolicyRequest=self.messages.GetIamPolicyRequest()),
        self.policy)

    result = self.Run('alpha category-manager stores get-iam-policy '
                      '--organization=3')
    self.assertEqual(self.policy, result)


if __name__ == '__main__':
  sdk_test_base.main()
