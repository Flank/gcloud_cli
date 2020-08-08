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
"""Tests that exercise the 'gcloud apigee applications list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
from tests.lib.surface.apigee import base

from six.moves import urllib


class ApplicationsListTest(base.ApigeeSurfaceTest):
  _canned_response = {
      "app": [{
          "appId": "95acc76a-1c5f-442c-9bb8-96196327543b",
          "name": "camille lion",
      }, {
          "appId": "76ee3b7d-12fa-42c0-adcb-19ba75082447",
          "name": "pricklypear",
      }]
  }

  def _AddCannedResponse(self, response, developer=None, page=None):
    developer_fragment = ""
    if developer:
      developer_fragment = "developers/%s/" % urllib.parse.quote(developer)
    url = ("https://apigee.googleapis.com/v1/organizations/test-org/" +
           developer_fragment + "apps")
    params = {
        "count" if developer else "rows": "1000",
        "shallowExpand" if developer else "expand": "true"
    }
    if page:
      params["startKey"] = page
    self.AddHTTPResponse(url, expected_params=params, body=json.dumps(response))

  def _BulkCannedResponses(self, count, start=1):
    for idx in range(start, start + count):
      yield {
          "appId": "95acc76a-1c5f-942c-9bb8-%012d" % idx,
          "name": "App #%d" % idx,
      }

  def testDefaultFormatting(self):
    self._AddCannedResponse(self._canned_response)
    self.RunApigee("applications list --organization=test-org")
    self.AssertOutputContains(
        """\
APP_ID                                NAME
95acc76a-1c5f-442c-9bb8-96196327543b  camille lion
76ee3b7d-12fa-42c0-adcb-19ba75082447  pricklypear
""",
        normalize_space=True)

  def testEmptyResponse(self):
    self._AddCannedResponse({})
    self.RunApigee("applications list --organization=test-org --format=json")
    self.AssertJsonOutputMatches([], "Must properly handle empty response.")

  def testDeveloperBasedSearch(self):
    self._AddCannedResponse(self._canned_response, developer="leaf@example.com")
    self.RunApigee("applications list --organization=test-org --format=json "
                   "--developer=leaf@example.com")
    self.AssertJsonOutputMatches(self._canned_response["app"])

  def testLongResponse(self):
    first_response = {"app": list(self._BulkCannedResponses(1000))}
    second_response = {"app": list(self._BulkCannedResponses(235, start=1000))}
    self._AddCannedResponse(first_response)
    self._AddCannedResponse(
        second_response, page=first_response["app"][-1]["appId"])

    self.RunApigee("applications list --organization=test-org --format=json")
    self.AssertJsonOutputMatches(
        list(self._BulkCannedResponses(1234)),
        "Must correctly splice a multi-part API response.")

  def testLongDeveloperBasedResponse(self):
    first_response = {"app": list(self._BulkCannedResponses(1000))}
    second_response = {"app": list(self._BulkCannedResponses(235, start=1000))}
    self._AddCannedResponse(first_response, developer="bob@example.com")
    self._AddCannedResponse(
        second_response,
        developer="bob@example.com",
        page=first_response["app"][-1]["name"])

    self.RunApigee("applications list --organization=test-org --format=json "
                   "--developer=bob@example.com")
    self.AssertJsonOutputMatches(
        list(self._BulkCannedResponses(1234)),
        "Must correctly splice a multi-part API response.")
