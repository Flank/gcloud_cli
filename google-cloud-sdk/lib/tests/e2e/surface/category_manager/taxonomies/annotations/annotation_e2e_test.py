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
"""E2e test for 'category-manager taxonomies annotations' command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.category_manager import utils
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.category_manager import e2e_base as base


class AnnotationE2eTest(base.CategoryManagerE2eBase):
  """E2e test for annotation commands."""

  def _UpdateAnnotation(self, annotation, new_description):
    args = '{} --description "{}"'.format(annotation.name, new_description)
    updated_annotation = self.Run('category-manager taxonomies annotations '
                                  'update ' + args)
    return updated_annotation

  def _DescribeAnnotation(self, annotation):
    return self.Run('category-manager taxonomies annotations describe ' +
                    annotation.name)

  @test_case.Filters.skip('Failing', 'b/115917883')
  def testUpdateAnnotation(self):
    description = 'old description'
    new_description = 'new description'
    with self.CreateTaxonomyResource('taxonomy description') as taxonomy:
      with self.CreateAnnotationResource(taxonomy, description) as annotation:
        updated_annotation = self._UpdateAnnotation(annotation, new_description)
        self.assertEqual(updated_annotation.description, new_description)

  @test_case.Filters.skip('Failing', 'b/121190998')
  def testDescribeAnnotation(self):
    description = 'test description'
    with self.CreateTaxonomyResource('taxonomy description') as taxonomy:
      with self.CreateAnnotationResource(taxonomy, description) as annotation:
        described_annotation = self._DescribeAnnotation(annotation)
        self.assertEqual(described_annotation.description, description)

  @test_case.Filters.skip('Failing', 'b/121190998')
  def testListAnnotation(self):
    description = 'test description'
    with self.CreateTaxonomyResource('taxonomy description') as taxonomy:
      with self.CreateAnnotationResource(taxonomy, description) as annotation:
        listed_annotation = self._ListAnnotationsAndReturnMatch(
            taxonomy, annotation.displayName)
        self.assertEqual(listed_annotation.description, description)

  @test_case.Filters.skip('Failing', 'b/115762046')
  def testAllAnnotationCommandsAsUserJourney(self):
    taxonomy_description = 'test taxonomy description'
    annotation_description = 'test annotation description'
    new_annotation_description = 'new test annotation description'
    with self.CreateTaxonomyResource(taxonomy_description) as taxonomy:
      with self.CreateAnnotationResource(taxonomy,
                                         annotation_description) as annotation:
        expected_annotation = utils.GetMessagesModule().Annotation(
            name=annotation.name,
            description=annotation_description,
            displayName=annotation.displayName,
            taxonomyDisplayName=taxonomy.displayName)
        self.assertEqual(annotation, expected_annotation)

        updated_annotation = self._UpdateAnnotation(annotation,
                                                    new_annotation_description)
        expected_annotation.description = new_annotation_description
        self.assertEqual(updated_annotation, expected_annotation)

        described_annotation = self._DescribeAnnotation(annotation)
        self.assertEqual(described_annotation, expected_annotation)

        found_annotation = self._ListAnnotationsAndReturnMatch(
            taxonomy, annotation.displayName)
        self.assertEqual(found_annotation, expected_annotation)


if __name__ == '__main__':
  sdk_test_base.main()
