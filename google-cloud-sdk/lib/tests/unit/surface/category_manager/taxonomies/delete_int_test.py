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
"""Tests for 'gcloud category-manager taxonomies delete'."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from tests.lib.surface.category_manager import base


class TaxonomiesDeleteIntTest(base.CategoryManagerUnitTestBase):

  def SetUp(self):
    self.project_taxonomy_id = '999'
    self.project_taxonomy_ref = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies',
        projectsId=self.Project(),
        taxonomiesId=self.project_taxonomy_id)
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testDeleteProjectTaxonomyPromptingWithYes(self):
    self.ExpectDeleteProjectTaxonomy(self.project_taxonomy_ref.RelativeName())
    self.WriteInput('Y\n')
    self.Run('category-manager taxonomies delete ' +
             self.project_taxonomy_ref.Name())
    self.AssertErrContains('Deleted project_taxonomy [{}].'.format(
        self.project_taxonomy_id))

  def testDeleteProjectTaxonomyPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(
        console_io.OperationCancelledError,
        console_io.OperationCancelledError.DEFAULT_MESSAGE):
      self.Run('category-manager taxonomies delete ' +
               self.project_taxonomy_ref.Name())
