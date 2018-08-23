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
"""Tests for 'category-manager assets search' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.category_manager import assets
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from surface.category_manager.assets import search
from tests.lib import sdk_test_base
from tests.lib.surface.category_manager import base


class SearchAnnotationsIntegrationTest(base.CategoryManagerUnitTestBase):
  """Tests for category-manager asset search command."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.expected_json_response = b"""\
    {
      "assets": [
        {
          "name": "projects/company.com:project/datasets/tables/entries/entry1",
          "type": "BIGQUERY_TABLE",
          "projectId": "company.com:project",
          "createTime": "2018-02-01T21:05:42.187Z",
          "updateTime": "2018-02-01T21:05:42.187Z",
          "annotatable": true
        },
        {
          "name": "projects/company.com:project/datasets/tables/entries/entry1",
          "type": "BIGQUERY_TABLE_COLUMN",
          "subAsset": "col1",
          "projectId": "company.com:project",
          "createTime": "2018-02-01T21:05:42.187Z",
          "updateTime": "2018-02-01T21:05:42.187Z",
          "annotatable": true
        }
      ]
    }"""

  def testSearchAssetsWithAllFlags(self):
    self.MockHttpRequest(self.expected_json_response)
    args = ('"name:asset_name" --taxonomy 222 --annotations 111 '
            '--show-only-annotatable --match-child-annotations')
    self.Run('category-manager assets search ' + args)
    self._VerifyOutput()

  def testSearchAssetsWithQueryPositional(self):
    self.MockHttpRequest(self.expected_json_response)
    self.Run('category-manager assets search name:asset_name')
    self._VerifyOutput()

  def testSearchAssetsWithoutQueryPositional(self):
    self.MockHttpRequest(self.expected_json_response)
    self.Run('category-manager assets search')
    self._VerifyOutput()

  def testSearchAssetsWithSingleAnnotation(self):
    self.MockHttpRequest(self.expected_json_response)
    args = '--taxonomy 123 --annotations 111'
    self.Run('category-manager assets search ' + args)
    self._VerifyOutput()

  def testSearchAssetsWithMultipleAnnotations(self):
    self.MockHttpRequest(self.expected_json_response)
    args = '--taxonomy 123 --annotations 111,222,333,444'
    self.Run('category-manager assets search ' + args)
    self._VerifyOutput()

  def _VerifyOutput(self):
    """Tests that the format of searching assets is correct."""
    self.AssertOutputEquals(
        """\
        ---
        annotatable: true
        createTime: '2018-02-01T21:05:42.187Z'
        name: projects/company.com:project/datasets/tables/entries/entry1
        projectId: company.com:project
        type: BIGQUERY_TABLE
        updateTime: '2018-02-01T21:05:42.187Z'
        ---
        annotatable: true
        createTime: '2018-02-01T21:05:42.187Z'
        name: projects/company.com:project/datasets/tables/entries/entry1
        projectId: company.com:project
        subAsset: col1
        type: BIGQUERY_TABLE_COLUMN
        updateTime: '2018-02-01T21:05:42.187Z'\n""",
        normalize_space=True)

  def testInvalidServerResponse(self):
    invalid_json_response = '{'
    self.MockHttpRequest(invalid_json_response)
    with self.assertRaises(assets.MessageDecodeError):
      self.Run('category-manager assets search')

  def testInvalidStatusCodeResponse(self):
    status_code = '500'
    valid_json_response = '{"assets" : []}'
    self.MockHttpRequest(valid_json_response, status_code)
    with self.assertRaises(exceptions.HttpException) as e:
      self.Run('category-manager assets search')
    err_msg = str(e.exception)
    expected_msg = assets.GetHttpErrorFormat().format(status_code,
                                                      valid_json_response)
    self.assertEqual(err_msg, expected_msg)

  def testPaginationWithPageSizeTooLarge(self):
    page_size = str(search.GetMaxPageSize() + 1)
    with self.assertRaises(ValueError) as e:
      self.Run('category-manager assets search --page-size ' + page_size)
    err_msg = str(e.exception)
    expected_err_msg = search.PAGE_SIZE_ERR_FORMAT.format(
        search.GetMaxPageSize(), page_size)
    self.assertEqual(err_msg, expected_err_msg)


if __name__ == '__main__':
  sdk_test_base.main()
