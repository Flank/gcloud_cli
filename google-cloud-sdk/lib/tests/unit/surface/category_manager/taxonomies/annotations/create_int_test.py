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
"""Tests for 'gcloud category-manager taxonomies annotations create'."""
from __future__ import absolute_import
from __future__ import unicode_literals
import copy
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib.surface.category_manager import base


class AnnotationsCreateIntTest(base.CategoryManagerUnitTestBase):

  def SetUp(self):
    self.taxonomy_id = '111'
    self.annotation_id = '555'
    self.annotation_display_name = 'xyz annotation'
    self.annotation_description = self.annotation_display_name + ' description'

    self.project_annotation = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies.annotations',
        projectsId=self.Project(),
        taxonomiesId=self.taxonomy_id,
        annotationsId=self.annotation_id)
    self.expected_project_annotation = self.messages.Annotation(
        displayName=self.annotation_display_name,
        description=self.annotation_description)

    self.track = calliope_base.ReleaseTrack.ALPHA

  def _SetupCreateExpectation(self, parent_resource, expected_annotation):
    # Mock backend call to create a project annotation and return the expected
    # created annotation result.

    # Make expected value copy to ensure that field mutations don't occur.
    created_annotation = copy.deepcopy(expected_annotation)
    self.mock_client.projects_taxonomies_annotations.Create.Expect(
        self.messages.CategorymanagerProjectsTaxonomiesAnnotationsCreateRequest(
            parent=parent_resource.RelativeName(),
            annotation=expected_annotation),
        created_annotation)

  def testDescribeProjectTaxonomyId(self):
    self._SetupCreateExpectation(self.project_annotation.Parent(),
                                 self.expected_project_annotation)
    args = '--taxonomy {} --display-name "{}" --description "{}"'.format(
        self.taxonomy_id, self.annotation_display_name,
        self.annotation_description)
    actual_annotation = self.Run(
        'category-manager taxonomies annotations create ' + args)
    self.assertEqual(actual_annotation, self.expected_project_annotation)
    # TODO(b/74408080): check that err contains created project annotation.
    # self.AssertErrContains('Created projectAnnotation [{}]'.format(
    #    self.annotation_id))


if __name__ == '__main__':
  sdk_test_base.main()
