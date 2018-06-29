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
"""Unit tests for the taxonomy API."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.api_lib.category_manager import store as store_api
from googlecloudsdk.api_lib.category_manager import taxonomies
from googlecloudsdk.api_lib.category_manager import utils
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.category_manager import base


class TaxonomiesTest(base.CategoryManagerUnitTestBase):
  """Taxonomy api lib tests."""

  def SetUp(self):
    self.taxonomy1 = self.messages.Taxonomy(
        name='taxonomy 1',
        displayName='display name 1',
        description='description 1')
    self.taxonomy2 = self.messages.Taxonomy(
        name='taxonomy 2',
        displayName='display name 2',
        description='description 2')
    self.taxonomy3 = self.messages.Taxonomy(
        name='taxonomy 3',
        displayName='display name 3',
        description='description 3')
    self.taxonomies = [self.taxonomy1, self.taxonomy2, self.taxonomy3]

  def testListTaxonomies(self):
    self.ExpectProjectTaxonomyList(self.Project(), self.taxonomies)
    actual_taxonomies = taxonomies.ListTaxonomies(utils.GetProjectResource())
    self.assertEqual(actual_taxonomies, self.taxonomies)

  def testCreateTaxonomy(self):
    expected_taxonomy = self.messages.Taxonomy(
        displayName='test display name', description='test description')
    self.ExpectCreateProjectTaxonomy(utils.GetProjectResource(),
                                     expected_taxonomy)
    created_taxonomy = taxonomies.CreateTaxonomy(utils.GetProjectResource(),
                                                 expected_taxonomy.displayName,
                                                 expected_taxonomy.description)
    self.assertEqual(created_taxonomy, expected_taxonomy)

  def testDeleteTaxonomy(self):
    taxonomy_resource = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies',
        projectsId=self.Project(),
        taxonomiesId='12345')
    self.ExpectDeleteProjectTaxonomy(taxonomy_resource.RelativeName())
    taxonomies.DeleteTaxonomy(taxonomy_resource)

  def testGetCommon(self):
    expected_store_name = 'taxonomyStores/expected-store-name'
    self.mock_client.taxonomyStores.GetCommon.Expect(
        self.messages.CategorymanagerTaxonomyStoresGetCommonRequest(),
        self.messages.TaxonomyStore(name=expected_store_name))
    actual_store = store_api.GetCommonStore()
    self.assertEqual(
        actual_store, self.messages.TaxonomyStore(name=expected_store_name))


if __name__ == '__main__':
  test_case.main()
