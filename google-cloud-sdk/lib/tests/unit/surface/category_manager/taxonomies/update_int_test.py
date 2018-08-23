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
"""Tests for 'gcloud category-manager taxonomies update'."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.surface.category_manager import base


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,])
class TaxonomiesUpdateIntTest(base.CategoryManagerUnitTestBase):

  def SetUp(self):
    self.taxonomy_id = '12345'
    self.taxonomy_description = 'taxonomy description'

    self.project_taxonomy = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies',
        projectsId=self.Project(),
        taxonomiesId=self.taxonomy_id)
    self.expected_project_taxonomy = self.messages.Taxonomy(
        description=self.taxonomy_description)

  def _ExpectUpdateProjectTaxonomy(self, project_taxonomy, expected_taxonomy):
    """Mocks backend call thats updates a taxonomy's description."""

    # Make expected value copy to ensure that field mutations don't occur.
    created_taxonomy = copy.deepcopy(expected_taxonomy)
    self.mock_client.projects_taxonomies.Patch.Expect(
        self.messages.CategorymanagerProjectsTaxonomiesPatchRequest(
            name=project_taxonomy.RelativeName(), taxonomy=expected_taxonomy),
        created_taxonomy)

  def testUpdateProjectTaxonomyDescription(self, track):
    self.track = track
    self._ExpectUpdateProjectTaxonomy(self.project_taxonomy,
                                      self.expected_project_taxonomy)
    args = '{} --description "{}"'.format(self.taxonomy_id,
                                          self.taxonomy_description)
    actual_taxonomy = self.Run('category-manager taxonomies update ' + args)
    self.assertEqual(actual_taxonomy, self.expected_project_taxonomy)


if __name__ == '__main__':
  sdk_test_base.main()
