# -*- coding: utf-8 -*- #
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
"""Unit tests for the annotations API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.category_manager import annotations
from googlecloudsdk.core import resources
from tests.lib.surface.category_manager import base


class AnnotationsTest(base.CategoryManagerUnitTestBase):
  """Annotations api lib tests."""

  def SetUp(self):
    self.taxonomy_id = '111'
    self.annotation_id = '222'
    self.annotation_display_name = 'xyz annotation'
    self.annotation_description = self.annotation_display_name + ' description'

    self.project_annotation = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies.annotations',
        projectsId=self.Project(),
        taxonomiesId=self.taxonomy_id,
        annotationsId=self.annotation_id)
    self.taxonomy_resource = self.project_annotation.Parent()
    self.expected_project_annotation = self.messages.Annotation(
        displayName=self.annotation_display_name,
        description=self.annotation_description)

  def testApiLibCreateAnnotation(self):
    self.ExpectProjectAnnotationCreate(self.taxonomy_resource,
                                       self.expected_project_annotation)
    created_annotation = annotations.CreateAnnotation(
        taxonomy_resource=self.project_annotation.Parent(),
        display_name=self.annotation_display_name,
        description=self.annotation_description)
    self.assertEqual(created_annotation, self.expected_project_annotation)
