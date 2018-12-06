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
"""Tests for 'gcloud category-manager taxonomies annotations delete'."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib.surface.category_manager import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,])
class AnnotationsDeleteIntTest(base.CategoryManagerUnitTestBase):

  def SetUp(self):
    self.project_taxonomy_id = '1111'
    self.annotation_id = '2222'
    self.annotation_ref = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies.annotations',
        projectsId=self.Project(),
        taxonomiesId=self.project_taxonomy_id,
        annotationsId=self.annotation_id)

  def testDeleteAnnotationPromptingWithYes(self, track):
    self.track = track
    self.ExpectProjectAnnotationDelete(self.annotation_ref.RelativeName())
    self.WriteInput('Y\n')
    args = '{} --taxonomy {}'.format(self.annotation_ref.annotationsId,
                                     self.annotation_ref.taxonomiesId)
    self.Run('category-manager taxonomies annotations delete ' + args)
    self.AssertErrContains('Deleted project_annotation [{}].'.format(
        self.annotation_ref.annotationsId))

  def testDeleteAnnotationPromptingWithNo(self, track):
    self.track = track
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(
        console_io.OperationCancelledError,
        console_io.OperationCancelledError.DEFAULT_MESSAGE):
      self.Run('category-manager taxonomies annotations delete ' +
               self.annotation_ref.RelativeName())
