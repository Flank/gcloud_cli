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
"""Tests for 'category-manager assets list-annotations' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib.surface.category_manager import base


class ListAnnotationsIntegrationTest(base.CategoryManagerUnitTestBase):
  """Tests for category-manager list annotations."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.asset = resources.REGISTRY.Create(
        'categorymanager.assets', assetId='company.com:project-12345/a/b/c')
    expected_annotation_tags = self.messages.ListAnnotationTagsResponse(
        tags=[
            self.CreateAnnotationTag(self.asset.assetId, '222', '333', 'tax1',
                                     'anno1'),
            self.CreateAnnotationTag(self.asset.assetId, '555', '666', 'tax2',
                                     'anno2'),
            self.CreateAnnotationTag(self.asset.assetId, '888', '999', 'tax3',
                                     'anno3')
        ])
    self.ExpectListAnnotationTags(self.asset, expected_annotation_tags)

  def testListingOutputFormatUsingProject(self):
    args = self.asset.RelativeName()
    self.Run('category-manager assets list-annotations ' + args)
    self._VerifyListingFormat()

  def _VerifyListingFormat(self):
    """"Tests that the format of listing annotation tags is correct."""
    self.AssertOutputEquals(
        """\
    tags:
    - annotation: projects/fake-project/taxonomies/222/annotations/333
      annotationDisplayName: anno1
      asset: assets/company.com%3Aproject-12345%2Fa%2Fb%2Fc
      taxonomyDisplayName: tax1
    - annotation: projects/fake-project/taxonomies/555/annotations/666
      annotationDisplayName: anno2
      asset: assets/company.com%3Aproject-12345%2Fa%2Fb%2Fc
      taxonomyDisplayName: tax2
    - annotation: projects/fake-project/taxonomies/888/annotations/999
      annotationDisplayName: anno3
      asset: assets/company.com%3Aproject-12345%2Fa%2Fb%2Fc
      taxonomyDisplayName: tax3\n""",
        normalize_space=True)


if __name__ == '__main__':
  sdk_test_base.main()
