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
"""Unit tests for the assets API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import copy
from apitools.base.py import encoding
from googlecloudsdk.api_lib.category_manager import assets
from googlecloudsdk.api_lib.category_manager import utils
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.category_manager import base


class AssetsTest(base.CategoryManagerUnitTestBase):

  def SetUp(self):
    self.asset_id = 'company.com:project-12345/a/b/c'
    self.taxonomy_id = '222'
    self.annotation_id = '333'
    self.asset_ref = resources.REGISTRY.Create(
        'categorymanager.assets', assetId=self.asset_id)
    self.annotation_ref = resources.REGISTRY.Create(
        'categorymanager.projects.taxonomies.annotations',
        projectsId=self.Project(),
        taxonomiesId=self.taxonomy_id,
        annotationsId=self.annotation_id)
    self.expected_annotation_tag = self.CreateAnnotationTag(
        self.asset_id, self.taxonomy_id, self.annotation_id, 'tax1', 'anno1')
    self.default_search_assets_args = {
        'annotations': self.annotation_ref.RelativeName(),
        'show_only_annotatable': 'false',
        'match_child_annotations': 'false',
        'query_filter': None,
        'page_size': None,
        'limit': None
    }
    # Set the base url for tests since the endpoint doesn't get set.
    self.StartObjectPatch(
        resources,
        'GetApiBaseUrl',
        return_value=utils.GetClientInstance().BASE_URL)

  def testApplyAnnotationTag(self):
    self.ExpectApplyAnnotation(self.asset_ref, self.annotation_ref,
                               self.expected_annotation_tag)
    actual_annotation_tag = assets.ApplyAnnotationTag(self.asset_ref,
                                                      self.annotation_ref)
    self.assertEqual(actual_annotation_tag, self.expected_annotation_tag)

  def testListAnnotationTags(self):
    expected_annotation_tags = self.messages.ListAnnotationTagsResponse(
        tags=[self.expected_annotation_tag])
    self.ExpectListAnnotationTags(self.asset_ref, expected_annotation_tags)
    actual_annotation_tags = assets.ListAssetAnnotationTags(self.asset_ref)
    self.assertEqual(actual_annotation_tags, expected_annotation_tags)

  def testSearchRequestReturnsValidJsonResponse(self):
    expected_json_response = self._CreateEmptySearchAssetsResponseOfSize(0)
    self.MockHttpRequest(expected_json_response)
    assets_response = assets.SearchAssets(**self.default_search_assets_args)
    self.assertEqual(list(assets_response), [])

  def testSearchRequestRaisesErrorOnInvalidJsonResponse(self):
    invalid_json_response = '{'
    self.MockHttpRequest(invalid_json_response)
    with self.assertRaises(assets.MessageDecodeError):
      next(assets.SearchAssets(**self.default_search_assets_args))

  def testSearchRequestInvalidStatusCode(self):
    status_code = '1'
    valid_json_response = self._CreateEmptySearchAssetsResponseOfSize(0)
    self.MockHttpRequest(valid_json_response, status_code)
    with self.assertRaises(exceptions.HttpException):
      e = next(assets.SearchAssets(**self.default_search_assets_args))
      err_msg = e.exception.message
      expected_msg = assets.GetHttpErrorFormat().format(status_code,
                                                        valid_json_response)
      self.assertEqual(err_msg, expected_msg)

  def testUrlConstructionWithNoAnnotations(self):
    valid_json_response = self._CreateEmptySearchAssetsResponseOfSize(1)
    http_mock = self.MockHttpRequest(valid_json_response, '200')

    kwargs = copy.deepcopy(self.default_search_assets_args)
    kwargs['annotations'] = []
    asset_generator = assets.SearchAssets(**kwargs)
    next(asset_generator)

    expected_url = ('https://categorymanager.googleapis.com/assets:search?'
                    'query.annotatable_only=false&'
                    'query.include_annotated_by_group=false')

    http_mock.request.assert_called_once_with(
        headers=assets.GetHeaders(), uri=expected_url)

  def testUrlConstructionWithAllParameters(self):
    valid_json_response = self._CreateEmptySearchAssetsResponseOfSize(1)
    http_mock = self.MockHttpRequest(valid_json_response, '200')

    search_assets_args = {
        'annotations': [
            'projects/p/taxonomies/123/annotations/456',
            'projects/p2/taxonomies/789/annotations/0'
        ],
        'show_only_annotatable':
            'false',
        'match_child_annotations':
            'true',
        'query_filter':
            'my_search_query',
        'page_size':
            55,
        'limit':
            200
    }

    asset_generator = assets.SearchAssets(**search_assets_args)
    next(asset_generator)

    expected_url = (
        'https://categorymanager.googleapis.com/assets:search?'
        'query.filter=my_search_query&'
        'query.annotatable_only=false&'
        'query.include_annotated_by_group=true&'
        'pageSize=55&'
        'query.annotations=projects%2Fp%2Ftaxonomies%2F123%2Fannotations%2F456&'
        'query.annotations=projects%2Fp2%2Ftaxonomies%2F789%2Fannotations%2F0')

    http_mock.request.assert_called_once_with(
        headers=assets.GetHeaders(), uri=expected_url)

  def testPaginationWithMultipleBatches(self):
    page_size = 5
    kwargs = copy.deepcopy(self.default_search_assets_args)
    kwargs['page_size'] = page_size

    asset_generator = assets.SearchAssets(**kwargs)

    assets_search_response = self._CreateEmptySearchAssetsResponseOfSize(
        page_size, next_token='next_page_token1')
    self.MockHttpRequest(assets_search_response)
    for _ in range(page_size):
      self.assertEqual(next(asset_generator), self.messages.Asset())

    assets_search_response = self._CreateEmptySearchAssetsResponseOfSize(
        page_size, next_token='next_page_token2')
    self.MockHttpRequest(assets_search_response)
    for _ in range(page_size):
      self.assertEqual(next(asset_generator), self.messages.Asset())

    assets_search_response = self._CreateEmptySearchAssetsResponseOfSize(
        page_size, next_token=None)
    self.MockHttpRequest(assets_search_response)
    for _ in range(page_size):
      self.assertEqual(next(asset_generator), self.messages.Asset())

    with self.assertRaises(StopIteration):
      next(asset_generator)

  def testPaginationWithLessItemsThanPageSize(self):
    assets_returned = 3
    kwargs = copy.deepcopy(self.default_search_assets_args)
    kwargs['page_size'] = 5

    asset_generator = assets.SearchAssets(**kwargs)

    assets_search_response = self._CreateEmptySearchAssetsResponseOfSize(
        assets_returned)
    self.MockHttpRequest(assets_search_response)
    for _ in range(assets_returned):
      self.assertEqual(next(asset_generator), self.messages.Asset())

    with self.assertRaises(StopIteration):
      next(asset_generator)

  def testAssetLimitWithPageSizeSmallerThanLimit(self):
    kwargs = copy.deepcopy(self.default_search_assets_args)
    kwargs['page_size'] = 1
    kwargs['limit'] = 3

    asset_generator = assets.SearchAssets(**kwargs)
    assets_search_response = self._CreateEmptySearchAssetsResponseOfSize(
        2, next_token='next_token1')
    self.MockHttpRequest(assets_search_response)
    for _ in range(2):
      self.assertEqual(next(asset_generator), self.messages.Asset())

    # Set a next token to indicate more assets are still available even though
    # the asset limit should be reached.
    assets_search_response = self._CreateEmptySearchAssetsResponseOfSize(
        2, next_token='next_token2')
    self.MockHttpRequest(assets_search_response)
    for _ in range(2):
      self.assertEqual(next(asset_generator), self.messages.Asset())

    with self.assertRaises(StopIteration):
      next(asset_generator)

  def testAssetLimitWithPageSizeLargerThanLimit(self):
    limit = 5
    kwargs = copy.deepcopy(self.default_search_assets_args)
    kwargs['page_size'] = 10
    kwargs['limit'] = limit

    # Set a next token to indicate more assets are still available even though
    # the asset limit should be reached.
    asset_generator = assets.SearchAssets(**kwargs)
    assets_search_response = self._CreateEmptySearchAssetsResponseOfSize(
        limit, next_token='next_token1')
    self.MockHttpRequest(assets_search_response)
    for _ in range(limit):
      self.assertEqual(next(asset_generator), self.messages.Asset())

    with self.assertRaises(StopIteration):
      next(asset_generator)

  def _CreateEmptySearchAssetsResponseOfSize(self, n, next_token=None):
    messages = utils.GetMessagesModule()
    empty_assets = [messages.Asset() for _ in range(n)]
    response = messages.SearchAssetsResponse(
        assets=empty_assets, nextPageToken=next_token)
    return encoding.MessageToJson(response)


if __name__ == '__main__':
  test_case.main()
