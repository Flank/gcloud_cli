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
"""E2e tests for 'category-manager assets' command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
from googlecloudsdk.api_lib.category_manager import utils
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import retry
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.category_manager import e2e_base as base


class AssetE2eTest(base.CategoryManagerE2eBase):
  """E2e test for asset related commands."""
  _BQ_TABLE_ASSET_FMT = 'projects/{project}/datasets/{dataset}/entries/{entry}'

  _BQ_DATASET = 'DO_NOT_DELETE_CATEGORY_MANAGER_TEST_DATASET'
  _BQ_TABLE = 'test_table1'

  def SetUp(self):
    self._asset = self._BQ_TABLE_ASSET_FMT.format(
        project=self.Project(), dataset=self._BQ_DATASET, entry=self._BQ_TABLE)

  @contextlib.contextmanager
  def TagAsset(self, asset, annotation):
    """Tags an asset with an annotation."""
    try:
      annotation_tag = self.Run(
          'category-manager assets apply-annotation {} --annotation {} '.format(
              asset, annotation.name))
      yield annotation_tag
    finally:
      args = '{} --annotation {} --quiet'.format(asset, annotation.name)
      self.Run('category-manager assets delete-annotation ' + args)

  def testListAnnotationTagCommandOnBigQueryTableAsset(self):
    description = 'arbitrary-test-description'
    with self.CreateTaxonomyResource(description) as taxonomy, \
        self.CreateAnnotationResource(taxonomy, description) as annotation, \
        self.TagAsset(self._asset, annotation) as asset_tag:
      tag = self._ListAssetAnnotationTagsAndReturnMatch(self._asset,
                                                        annotation.displayName)
      self.assertEqual(tag, asset_tag)

  def testApplyAnnotationCommandOnBigQueryTableAsset(self):
    description = 'arbitrary-test-description'
    with self.CreateTaxonomyResource(description) as taxonomy, \
        self.CreateAnnotationResource(taxonomy, description) as annotation, \
        self.TagAsset(self._asset, annotation) as asset_tag:
      escaped_asset = ('assets/projects%2Fcatman-e2e-test%2Fdatasets%2F'
                       'DO_NOT_DELETE_CATEGORY_MANAGER_TEST_DATASET%2Fentries'
                       '%2Ftest_table1')
      expected_tag = utils.GetMessagesModule().AnnotationTag(
          annotation=annotation.name,
          annotationDisplayName=annotation.displayName,
          asset=escaped_asset,
          taxonomyDisplayName=taxonomy.displayName)
      self.assertEqual(asset_tag, expected_tag)

  def testDeleteAnnotationCommandOnBigQueryTableAsset(self):
    description = 'arbitrary-test-description'
    with self.CreateTaxonomyResource(description) as taxonomy, \
        self.CreateAnnotationResource(taxonomy, description) as annotation, \
        self.TagAsset(self._asset, annotation):
      tag = self._ListAssetAnnotationTagsAndReturnMatch(self._asset,
                                                        annotation.displayName)
      self.assertIsNotNone(tag)

      args = '{} --annotation {} --quiet'.format(self._asset, annotation.name)
      self.Run('category-manager assets delete-annotation ' + args)

      tag = self._ListAssetAnnotationTagsAndReturnMatch(self._asset,
                                                        annotation.displayName)
      self.assertIsNone(tag)

  def testSearchAssetsCommandOnBigQueryTableAsset(self):
    args = '"project_id:{}" --format=disable'.format(self.Project())
    assets = list(self.Run('category-manager assets search ' + args))
    table_asset = self._FindTableAsset(assets)
    self.assertIsNotNone(table_asset)

  def _FindTableAsset(self, assets):
    for asset in assets:
      if asset.subAsset is None and asset.name == self._asset:
        return asset

  @test_case.Filters.skip('Failing', 'b/116202444')
  def testAssetCommandGroupUserJourney(self):
    description = 'arbitrary-test-description'
    with self.CreateTaxonomyResource(description) as taxonomy:
      with self.CreateAnnotationResource(taxonomy, description) as annotation:
        taxonomy_resource = resources.REGISTRY.Parse(
            taxonomy.name, collection='categorymanager.projects.taxonomies')
        annotation_resource = resources.REGISTRY.Parse(
            annotation.name,
            collection='categorymanager.projects.taxonomies.annotations')

        # Search for BigQuery table asset.
        args = '"project_id:{}" --format=disable'.format(self.Project())
        assets = list(self.Run('category-manager assets search ' + args))
        table_asset = self._FindTableAsset(assets)
        self.assertIsNotNone(table_asset)

        # Tag asset with annotation.
        with self.TagAsset(table_asset.name, annotation) as asset_tag:
          listed_asset_tag = self._ListAssetAnnotationTagsAndReturnMatch(
              self._asset, annotation.displayName)
          self.assertEqual(asset_tag, listed_asset_tag)

          # Search for tagged asset based on annotation. We may have to retry
          # searching for the tagged asset a few times until Datahub's search
          # index updates which may take a few seconds.
          args = '--taxonomy {} --annotations {} --format=disable'.format(
              taxonomy_resource.taxonomiesId, annotation_resource.annotationsId)
          assets = retry.Retryer().RetryOnResult(
              lambda: list(self.Run('category-manager assets search ' + args)),
              should_retry_if=lambda result, _: not result,
              sleep_ms=[1000, 3000, 5000])
          self.assertEqual(len(assets), 1)
          tagged_table_asset = assets[0]
          self.assertEqual(table_asset, tagged_table_asset)


if __name__ == '__main__':
  sdk_test_base.main()
