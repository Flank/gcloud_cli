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
"""Tests for 'category-manager assets delete-annotation' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.surface.category_manager import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,])
class DeleteAnnotationIntegrationTest(base.CategoryManagerUnitTestBase):
  """Tests for category-manager delete-annotation."""

  def SetUp(self):
    self.asset = resources.REGISTRY.Create(
        'categorymanager.assets', assetId='company.com:project-12345/a/b/c')
    self.taxonomy_id = '123'
    self.annotation_id = '456'
    self.project_annotation = resources.REGISTRY.Create(
        collection='categorymanager.projects.taxonomies.annotations',
        projectsId=self.Project(),
        taxonomiesId=self.taxonomy_id,
        annotationsId=self.annotation_id)
    self.sub_asset = 'column1'

  def testDeleteAssetAnnotation_promptingYes(self, track):
    self.track = track
    self.ExpectDeleteAnnotation(self.asset, self.project_annotation,
                                self.sub_asset)
    args = ('{asset_name} --annotation {annotation_id} '
            '--taxonomy {taxonomy_id} --sub-asset {sub_asset}').format(
                asset_name=('assets/' + self.asset.assetId),
                annotation_id=self.annotation_id,
                taxonomy_id=self.taxonomy_id,
                sub_asset=self.sub_asset)
    self.WriteInput('Y\n')
    self.Run('category-manager assets delete-annotation ' + args)
    self.AssertErrContains('Deleted annotation tag [{}].'.format(
        self.project_annotation.RelativeName()))

  def testDeleteAssetAnnotation_promptingNo(self, track):
    self.track = track
    args = ('{asset_name} --annotation {annotation_id} '
            '--taxonomy {taxonomy_id} --sub-asset {sub_asset}').format(
                asset_name=('assets/' + self.asset.assetId),
                annotation_id=self.annotation_id,
                taxonomy_id=self.taxonomy_id,
                sub_asset=self.sub_asset)
    self.WriteInput('n\n')
    with self.AssertRaisesExceptionMatches(
        console_io.OperationCancelledError,
        console_io.OperationCancelledError.DEFAULT_MESSAGE):
      self.Run('category-manager assets delete-annotation ' + args)


if __name__ == '__main__':
  sdk_test_base.main()
