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
"""Tests for 'gcloud category-manager taxonomies annotations list'."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib.surface.category_manager import base


class AnnotationsListIntTest(base.CategoryManagerUnitTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.taxonomy_id = '123'
    self.parent_annotation_id = '456'

    self.project_taxonomy_resource = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies',
        projectsId=self.Project(),
        taxonomiesId=self.taxonomy_id)

    self.annotations = [
        self.messages.Annotation(
            name=self.project_taxonomy_resource.RelativeName() +
            '/annotations/1',
            displayName='display name 1',
            description='description 1',
            taxonomyDisplayName='this annotation\'s taxonomy 1',
            childAnnotationIds=['4', '5'],
            parentAnnotationId=self.parent_annotation_id),
        self.messages.Annotation(
            name=self.project_taxonomy_resource.RelativeName() +
            '/annotations/2',
            displayName='display name 2',
            description='description 2',
            taxonomyDisplayName='this annotation\'s taxonomy 2',
            childAnnotationIds=['6', '7'],
            parentAnnotationId=self.parent_annotation_id),
        self.messages.Annotation(
            name=self.project_taxonomy_resource.RelativeName() +
            '/annotations/3',
            displayName='display name 3',
            description='description 3',
            taxonomyDisplayName='this annotation\'s taxonomy 3',
            childAnnotationIds=['8', '9'],
            parentAnnotationId=self.parent_annotation_id)
    ]

    self.expected_annotations_list = self.messages.ListAnnotationsResponse(
        annotations=self.annotations)
    self._ExpectAnnotationsList()

  def _ExpectAnnotationsList(self):
    m = self.messages
    self.mock_client.projects_taxonomies_annotations.List.Expect(
        m.CategorymanagerProjectsTaxonomiesAnnotationsListRequest(
            parent=self.project_taxonomy_resource.RelativeName()),
        self.expected_annotations_list)

  def testListingAnnotations(self):
    args = '--taxonomy {}'.format(self.taxonomy_id)
    self.Run('category-manager taxonomies annotations list ' + args)

    output = str(self.stdout.getvalue())
    for annotations in self.annotations:
      annotation_reference = resources.REGISTRY.Parse(
          annotations.name,
          collection='categorymanager.projects.taxonomies.annotations')
      self.assertIn(annotation_reference.Name(), output)
      self.assertIn(annotations.displayName, output)
      self.assertIn(annotations.description, output)
      self.assertIn(annotations.parentAnnotationId, output)
      for child_id in annotations.childAnnotationIds:
        self.assertIn(child_id, output)

  def testListingAnnotationFormat(self):
    args = '--taxonomy {}'.format(self.taxonomy_id)
    self.Run('category-manager taxonomies annotations list ' + args)
    # pylint: disable=line-too-long
    self.AssertOutputEquals(
        """\
        ID DISPLAY_NAME PARENT_ANNOTATION_ID CHILD_ANNOTATION_IDS DESCRIPTION
        1 display name 1 456 4,5 description 1
        2 display name 2 456 6,7 description 2
        3 display name 3 456 8,9 description 3
        """,
        normalize_space=True)


if __name__ == '__main__':
  sdk_test_base.main()
