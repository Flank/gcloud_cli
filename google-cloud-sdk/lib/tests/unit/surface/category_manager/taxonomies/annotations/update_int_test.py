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
"""Tests for 'gcloud category-manager taxonomies annotations update'."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.surface.category_manager import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,])
class AnnotationsUpdateIntTest(base.CategoryManagerUnitTestBase):

  def SetUp(self):
    self.taxonomy_id = '12345'
    self.annotation_id = '67890'
    self.annotation_description = 'annotation description'

    self.project_taxonomy = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies',
        projectsId=self.Project(),
        taxonomiesId=self.taxonomy_id)
    self.project_annotation = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies.annotations',
        projectsId=self.Project(),
        taxonomiesId=self.taxonomy_id,
        annotationsId=self.annotation_id)
    self.expected_project_annotation = self.messages.Annotation(
        description=self.annotation_description)

  def testUpdateProjectAnnotationDescription(self, track):
    self.track = track
    self.ExpectProjectAnnotationUpdate(self.project_annotation,
                                       self.expected_project_annotation)
    args = ('{annotation_id} --taxonomy {taxonomy_id} '
            '--description "{description}"').format(
                annotation_id=self.annotation_id,
                taxonomy_id=self.taxonomy_id,
                description=self.annotation_description)
    actual_annotation = self.Run(
        'category-manager taxonomies annotations update ' + args)
    self.assertEqual(actual_annotation, self.expected_project_annotation)


if __name__ == '__main__':
  sdk_test_base.main()
