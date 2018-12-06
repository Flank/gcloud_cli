# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for 'gcloud category-manager taxonomies describe'."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.category_manager import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,])
class TaxonomiesDescribeIntTest(base.CategoryManagerUnitTestBase):

  def SetUp(self):
    self.taxonomy_id = '111'
    self.taxonomy_store_id = '222'

    self.project_taxonomy = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies',
        projectsId=self.Project(),
        taxonomiesId=self.taxonomy_id)
    self.taxonomy_store_taxonomy = resources.REGISTRY.Create(
        collection='categorymanager.taxonomyStores.taxonomies',
        taxonomyStoresId=self.taxonomy_store_id,
        taxonomiesId=self.taxonomy_id)

    self.expected_project_taxonomy = self.messages.Taxonomy(
        name=self.project_taxonomy.RelativeName(),
        displayName='project taxonomy display name',
        description='project taxonomy description')
    self.expected_store_taxonomy = self.messages.Taxonomy(
        name=self.taxonomy_store_taxonomy.RelativeName(),
        displayName='store taxonomy display name',
        description='store taxonomy description')

  def _ExpectGetTaxonomyStoreTaxonomy(self, expected_taxonomy):
    self.mock_client.taxonomyStores_taxonomies.Get.Expect(
        self.messages.CategorymanagerTaxonomyStoresTaxonomiesGetRequest(
            name=expected_taxonomy.name),
        copy.deepcopy(expected_taxonomy))

  def _ExpectGetProjectTaxonomy(self, expected_taxonomy):
    self.mock_client.projects_taxonomies.Get.Expect(
        self.messages.CategorymanagerProjectsTaxonomiesGetRequest(
            name=expected_taxonomy.name),
        copy.deepcopy(expected_taxonomy))

  def testDescribeProjectTaxonomyId(self, track):
    self.track = track
    self._ExpectGetProjectTaxonomy(self.expected_project_taxonomy)
    actual_taxonomy = self.Run(
        'category-manager taxonomies describe ' + self.taxonomy_id)
    self.assertEqual(actual_taxonomy, self.expected_project_taxonomy)

  @test_case.Filters.skip('Taxonomy store not yet supported.', 'b/74080347')
  def testDescribeWithTaxonomyStoreTaxonomyName(self, track):
    self.track = track
    self._ExpectGetTaxonomyStoreTaxonomy(self.expected_store_taxonomy)
    actual_taxonomy = self.Run('category-manager taxonomies describe ' +
                               self.taxonomy_store_taxonomy.RelativeName())
    self.assertEqual(actual_taxonomy,
                     self.taxonomy_store_taxonomy.RelativeName())

  @test_case.Filters.skip('Taxonomy store not yet supported.', 'b/74080347')
  def testDescribeWithTaxonomyStoreTaxonomyPositionalAndFlag(self, track):
    self.track = track
    self._ExpectGetTaxonomyStoreTaxonomy(self.expected_store_taxonomy)
    actual_taxonomy = self.Run(
        'category-manager taxonomies describe ' + self.taxonomy_id +
        ' --store ' + self.taxonomy_store_id)
    self.assertEqual(actual_taxonomy,
                     self.taxonomy_store_taxonomy.RelativeName())


if __name__ == '__main__':
  sdk_test_base.main()
