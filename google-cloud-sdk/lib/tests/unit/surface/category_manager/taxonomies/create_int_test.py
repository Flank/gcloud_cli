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
"""Tests for 'gcloud category-manager taxonomies create'."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib.surface.category_manager import base


class TaxonomiesCreateIntTest(base.CategoryManagerUnitTestBase):

  def SetUp(self):
    self.taxonomy_id = '111'
    self.taxonomy_display_name = 'animal taxonomy'
    self.taxonomy_description = self.taxonomy_display_name + ' description'

    self.project_taxonomy = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies',
        projectsId=self.Project(),
        taxonomiesId=self.taxonomy_id)
    self.expected_project_taxonomy = self.messages.Taxonomy(
        displayName=self.taxonomy_display_name,
        description=self.taxonomy_description)

    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreateProjectTaxonomyId(self):
    self.ExpectCreateProjectTaxonomy(self.project_taxonomy.Parent(),
                                     self.expected_project_taxonomy)
    args = '--display-name "{}" --description "{}"'.format(
        self.taxonomy_display_name, self.taxonomy_description)
    actual_taxonomy = self.Run('category-manager taxonomies create ' + args)
    self.assertEqual(actual_taxonomy, self.expected_project_taxonomy)
    self.AssertOutputContains(self.taxonomy_display_name)
    self.AssertOutputContains(self.taxonomy_description)


if __name__ == '__main__':
  sdk_test_base.main()
