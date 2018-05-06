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
"""Tests for 'gcloud category-manager taxonomies list'."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.category_manager import base


class TaxonomiesListIntTest(base.CategoryManagerUnitTestBase):

  def SetUp(self):
    self.taxonomy_store_id = '123456789'
    self.taxonomies = [
        self.messages.Taxonomy(
            name='taxonomy 1',
            displayName='display name 1',
            description='description 1'),
        self.messages.Taxonomy(
            name='taxonomy 2',
            displayName='display name 2',
            description='description 2'),
        self.messages.Taxonomy(
            name='taxonomy 3',
            displayName='display name 3',
            description='description 3')
    ]
    self.expected_taxonomy_list = self.messages.ListTaxonomiesResponse(
        taxonomies=self.taxonomies)

  def _ExpectTaxonomyStoreTaxonomyList(self, taxonomy_store,
                                       expected_taxonomy_list):
    taxonomy_store_resource = resources.REGISTRY.Create(
        collection='categorymanager.taxonomyStores',
        taxonomyStores=taxonomy_store)
    self.mock_client.taxonomyStores_taxonomies.List.Expect(
        self.messages.CategorymanagerTaxonomyStoresTaxonomiesListRequest(
            parent=taxonomy_store_resource.RelativeName()),
        expected_taxonomy_list)

  def _ExpectProjectTaxonomyList(self, project_id, expected_taxonomy_list):
    project_resource = resources.REGISTRY.Create(
        collection='categorymanager.projects', projectsId=project_id)
    self.mock_client.projects_taxonomies.List.Expect(
        self.messages.CategorymanagerProjectsTaxonomiesListRequest(
            parent=project_resource.RelativeName()),
        expected_taxonomy_list)

  def testListingTaxonomiesUsingProject(self):
    """Test that listing taxonomies emits the anticipated taxonomy fields."""
    self._ExpectProjectTaxonomyList(self.Project(), self.expected_taxonomy_list)
    self.Run('alpha category-manager taxonomies list')
    self._VerifyCorrectOutput()

  def testListingOutputFormatUsingProject(self):
    """Test that the format of listing taxonomies is correct."""
    self._ExpectProjectTaxonomyList(self.Project(), self.expected_taxonomy_list)
    self.Run('alpha category-manager taxonomies list')
    self._VerifyListingFormat()

  @test_case.Filters.skip('Taxonomy store not yet supported.', 'b/74080347')
  def testListingTaxonomiesUsingTaxonomyStore(self):
    """Test that listing taxonomies emits the anticipated taxonomy fields."""
    self._ExpectTaxonomyStoreTaxonomyList(self.taxonomy_store_id,
                                          self.expected_taxonomy_list)
    self.Run('alpha category-manager taxonomies list --store ' +
             self.taxonomy_store_id)
    self._VerifyCorrectOutput()

  @test_case.Filters.skip('Taxonomy store not yet supported.', 'b/74080347')
  def testListingOutputFormatUsingTaxonomyStore(self):
    """Test that the format of listing taxonomies is correct."""
    self._ExpectTaxonomyStoreTaxonomyList(self.taxonomy_store_id,
                                          self.expected_taxonomy_list)
    self.Run('alpha category-manager taxonomies list --store ' +
             self.taxonomy_store_id)
    self._VerifyListingFormat()

  def _VerifyCorrectOutput(self):
    """Test that listing taxonomies emits the anticipated taxonomy fields."""
    output = str(self.stdout.getvalue())
    for taxonomy in self.taxonomies:
      self.assertIn(taxonomy.name, output)
      self.assertIn(taxonomy.displayName, output)
      self.assertIn(taxonomy.description, output)

  def _VerifyListingFormat(self):
    """"Test that the format of listing taxonomies is correct."""
    self.AssertOutputEquals("""\
    DISPLAY_NAME    NAME        DESCRIPTION
    display name 1  taxonomy 1  description 1
    display name 2  taxonomy 2  description 2
    display name 3  taxonomy 3  description 3
    """, normalize_space=True)

if __name__ == '__main__':
  sdk_test_base.main()
