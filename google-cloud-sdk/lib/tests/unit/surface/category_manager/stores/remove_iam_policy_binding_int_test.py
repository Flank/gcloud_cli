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
"""Tests for 'category-manager taxonomies remove-iam-policy-binding' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import sdk_test_base
from tests.lib.surface.category_manager import base


class RemoveIamPolicyBindingIntegrationTest(base.CategoryManagerUnitTestBase):
  """Tests for category-manager stores remove-iam-policy-binding."""

  def SetUp(self):
    self.old_policy = self.messages.Policy(bindings=[
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
    self.new_policy = self.messages.Policy(bindings=[
        self.messages.Binding(
            role='roles/categorymanager.admin',
            members=[
                'serviceAccount:account@test-project.googleservice.com',
            ]),
        self.messages.Binding(
            role='roles/categorymanager.reader',
            members=['user:user1@gmail.com', 'user:user2@gmail.com'])
    ])

  def testRemoveIamPolicyBindingWithOrganizationResource(self):
    self.ExpectGetTaxonomyStore(org_id='1', taxonomy_store_id='2')
    self.mock_client.taxonomyStores.GetIamPolicy.Expect(
        self.messages.CategorymanagerTaxonomyStoresGetIamPolicyRequest(
            resource='taxonomyStores/2',
            getIamPolicyRequest=self.messages.GetIamPolicyRequest()),
        self.old_policy)
    self.mock_client.taxonomyStores.SetIamPolicy.Expect(
        self.messages.CategorymanagerTaxonomyStoresSetIamPolicyRequest(
            resource='taxonomyStores/2',
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=self.new_policy)), self.new_policy)
    result = self.Run('alpha category-manager stores remove-iam-policy-binding '
                      'organizations/1 --role=roles/categorymanager.admin '
                      '--member=user:admin@gmail.com')
    self.assertEqual(self.new_policy, result)

  def testRemoveIamPolicyBindingWithOrganizationId(self):
    self.ExpectGetTaxonomyStore(org_id='1', taxonomy_store_id='2')
    self.mock_client.taxonomyStores.GetIamPolicy.Expect(
        self.messages.CategorymanagerTaxonomyStoresGetIamPolicyRequest(
            resource='taxonomyStores/2',
            getIamPolicyRequest=self.messages.GetIamPolicyRequest()),
        self.old_policy)
    self.mock_client.taxonomyStores.SetIamPolicy.Expect(
        self.messages.CategorymanagerTaxonomyStoresSetIamPolicyRequest(
            resource='taxonomyStores/2',
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=self.new_policy)), self.new_policy)
    result = self.Run('alpha category-manager stores remove-iam-policy-binding '
                      '1 --role=roles/categorymanager.admin '
                      '--member=user:admin@gmail.com')
    self.assertEqual(self.new_policy, result)


if __name__ == '__main__':
  sdk_test_base.main()
