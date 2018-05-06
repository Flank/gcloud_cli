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
"""Tests for 'category-manager assets apply-annotation' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib.surface.category_manager import base


class ApplyAnnotationsIntegrationTest(base.CategoryManagerUnitTestBase):
  """Tests for category-manager apply-annotation."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.asset = resources.REGISTRY.Create(
        'categorymanager.assets', assetId='company.com:project-12345/a/b/c')
    self.taxonomy_id = '123'
    self.annotation_id = '456'
    self.project_annotation = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies.annotations',
        projectsId=self.Project(),
        taxonomiesId=self.taxonomy_id,
        annotationsId=self.annotation_id)
    expected_annotation_tag = self.CreateAnnotationTag(
        self.asset.assetId, self.taxonomy_id, self.annotation_id, 'tax1',
        'anno1')
    self.ExpectApplyAnnotation(self.asset, self.project_annotation,
                               expected_annotation_tag)

  def testApplyAnnotation(self):
    args = ('{asset_name} --annotation {annotation_id} '
            '--taxonomy {taxonomy_id}').format(
                asset_name=('assets/' + self.asset.assetId),
                annotation_id=self.annotation_id,
                taxonomy_id=self.taxonomy_id)
    self.Run('category-manager assets apply-annotation ' + args)
    self._VerifyOutputFormat()

  def _VerifyOutputFormat(self):
    """"Test that the format of applying an annotation tag is correct."""
    self.AssertOutputEquals(
        """\
    annotation: projects/fake-project/taxonomies/123/annotations/456
    annotationDisplayName: anno1
    asset: assets/company.com%3Aproject-12345%2Fa%2Fb%2Fc
    taxonomyDisplayName: tax1\n""",
        normalize_space=True)


if __name__ == '__main__':
  sdk_test_base.main()
