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
"""Tests for 'gcloud category-manager annotations describe'."""
from __future__ import absolute_import
from __future__ import unicode_literals
import copy
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.category_manager import base


class AnnotationsDescribeIntTest(base.CategoryManagerUnitTestBase):

  def SetUp(self):
    self.taxonomy_id = '111'
    self.taxonomy_store_id = '222'
    self.annotation_id = '333'

    self.taxonomy_store_annotation = resources.REGISTRY.Create(
        collection='categorymanager.taxonomyStores.taxonomies.annotations',
        taxonomyStoresId=self.taxonomy_store_id,
        taxonomiesId=self.taxonomy_id,
        annotationsId=self.annotation_id)
    self.project_annotation = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies.annotations',
        projectsId=self.Project(),
        taxonomiesId=self.taxonomy_id,
        annotationsId=self.annotation_id)

    self.expected_taxonomy_store_annotation = self.messages.Annotation(
        name=self.taxonomy_store_annotation.RelativeName(),
        displayName='taxonomy store taxonomy display name',
        description='taxonomy store taxonomy description',
        taxonomyDisplayName='this annotation\'s taxonomy',
        childAnnotationIds=['444', '555', '666'],
        parentAnnotationId='777')
    self.expected_project_annotation = self.messages.Annotation(
        name=self.project_annotation.RelativeName(),
        displayName='project annotation display name',
        description='project annotation description',
        taxonomyDisplayName='this annotation\'s taxonomy',
        childAnnotationIds=['444', '555', '666'],
        parentAnnotationId='777')

    self.track = calliope_base.ReleaseTrack.ALPHA

  def _ExpectGetTaxonomyStoreAnnotation(self, expected_annotation):
    m = self.messages
    self.mock_client.taxonomyStores_taxonomies_annotations.Get.Expect(
        m.CategorymanagerTaxonomyStoresTaxonomiesAnnotationsGetRequest(
            name=expected_annotation.name),
        copy.deepcopy(expected_annotation))

  def _ExpectGetProjectAnnotation(self, expected_annotation):
    m = self.messages
    self.mock_client.projects_taxonomies_annotations.Get.Expect(
        m.CategorymanagerProjectsTaxonomiesAnnotationsGetRequest(
            name=expected_annotation.name),
        copy.deepcopy(expected_annotation))

  def testDescribeProjectAnnotationUsingName(self):
    self._ExpectGetProjectAnnotation(self.expected_project_annotation)
    actual_annotation = self.Run(
        'category-manager taxonomies annotations describe ' +
        self.project_annotation.RelativeName())
    self.assertEqual(actual_annotation, self.expected_project_annotation)

  def testDescribeProjectAnnotationWithPositionalAndFlag(self):
    self._ExpectGetProjectAnnotation(self.expected_project_annotation)
    args = '{} --taxonomy {}'.format(self.annotation_id, self.taxonomy_id)
    actual_annotation = self.Run(
        'category-manager taxonomies annotations describe ' + args)
    self.assertEqual(actual_annotation, self.expected_project_annotation)

  @test_case.Filters.skip('Taxonomy store not yet supported.', 'b/74080347')
  def testDescribeTaxonomyStoreAnnotationUsingName(self):
    self._ExpectGetTaxonomyStoreAnnotation(
        self.expected_taxonomy_store_annotation)
    actual_annotation = self.Run(
        'category-manager taxonomies annotations describe ' +
        self.taxonomy_store_annotation.Name())
    self.assertEqual(actual_annotation,
                     self.expected_taxonomy_store_annotation)

  @test_case.Filters.skip('Taxonomy store not yet supported.', 'b/74080347')
  def testDescribeTaxonomyStoreAnnotationWithPositionalAndFlag(self):
    self._ExpectGetTaxonomyStoreAnnotation(
        self.expected_taxonomy_store_annotation)
    args = '{} --taxonomy {} --store {}'.format(
        self.annotation_id, self.taxonomy_id, self.taxonomy_store_id)
    actual_annotation = self.Run(
        'category-manager taxonomies annotations describe ' + args)
    self.assertEqual(actual_annotation,
                     self.expected_taxonomy_store_annotation)


if __name__ == '__main__':
  sdk_test_base.main()
