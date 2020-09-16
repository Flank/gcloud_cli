# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests that exercise the 'gcloud apigee products list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
from tests.lib.surface.apigee import base


class ProductsListTest(base.ApigeeSurfaceTest):
  _canned_response = {
      "apiProduct": [{
          "name": "gcloud-test3"
      }, {
          "name": "gcloud-test2"
      }, {
          "name": "gcloud-test1"
      }]
  }

  def testDefaultFormatting(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/apiproducts",
        status=200,
        expected_params={"count": "1000"},
        body=json.dumps(self._canned_response))
    self.RunApigee("products list --organization=test-org")
    self.AssertOutputContains(
        """\
 - gcloud-test3
 - gcloud-test2
 - gcloud-test1""",
        normalize_space=True)

  def testEmptyResponse(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/apiproducts",
        status=200,
        expected_params={"count": "1000"},
        body=json.dumps({}))
    self.RunApigee("products list --format=json --organization=test-org")
    self.AssertJsonOutputMatches([], "Must properly handle empty response.")

  def testLongResponse(self):
    names = ["gcloud-test%d" % idx for idx in range(1, 1234)]
    product_structures = [{"name": name} for name in names]
    first_response = {"apiProduct": product_structures[:1000]}
    second_response = {"apiProduct": product_structures[999:]}

    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/apiproducts",
        status=200,
        expected_params={"count": "1000"},
        body=json.dumps(first_response))
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/apiproducts",
        status=200,
        expected_params={
            "count": "1000",
            "startKey": "gcloud-test1000"
        },
        body=json.dumps(second_response))
    self.RunApigee("products list --organization=test-org --format=json")
    self.AssertJsonOutputMatches(
        product_structures, "Must correctly splice a multi-part API response.")

  def testProjectFallback(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations",
        status=200,
        body=json.dumps({
            "organizations": [{
                "organization": "test-org",
                "projectIds": ["test-proj"]
            }]
        }))
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/apiproducts",
        status=200,
        expected_params={"count": "1000"},
        body=json.dumps(self._canned_response))
    self.RunApigee("products list --format=json --project=test-proj")
    self.AssertJsonOutputMatches(
        self._canned_response["apiProduct"],
        "Must return expected products in proper order.")
