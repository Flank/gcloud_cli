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
"""Tests that exercise the 'gcloud apigee developers list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
from tests.lib.surface.apigee import base


class DevelopersListTest(base.ApigeeSurfaceTest):
  _canned_response = {
      "developer": [{
          "email": "bigboy@example.com"
      }, {
          "email": "littleman@example.com"
      }]
  }

  def testDefaultFormatting(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/developers",
        status=200,
        expected_params={"count": "1000"},
        body=json.dumps(self._canned_response))
    self.RunApigee("developers list --organization=test-org")
    self.AssertOutputContains(
        """\
 - bigboy@example.com
 - littleman@example.com""",
        normalize_space=True)

  def testLongResponse(self):
    emails = ["robot%d@example.com" % idx for idx in range(1, 1234)]
    developer_structures = [{"email": email} for email in emails]
    first_response = {"developer": developer_structures[:1000]}
    second_response = {"developer": developer_structures[999:]}

    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/developers",
        status=200,
        expected_params={"count": "1000"},
        body=json.dumps(first_response))
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/developers",
        status=200,
        expected_params={
            "count": "1000",
            "startKey": "robot1000@example.com"
        },
        body=json.dumps(second_response))
    self.RunApigee("developers list --organization=test-org --format=json")
    self.AssertJsonOutputMatches(
        emails, "Must correctly splice a multi-part API response.")

  def testEmptyResponse(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/developers",
        status=200,
        expected_params={"count": "1000"},
        body=json.dumps({}))
    self.RunApigee("developers list --format=json --organization=test-org")
    self.AssertJsonOutputMatches([], "Must properly handle empty response.")

  def testMismatchWithResponseFormat(self):
    wrong_type_response = [{"email": "keith@example.com"}]
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/developers",
        status=200,
        expected_params={"count": "1000"},
        body=json.dumps(wrong_type_response))
    with self.assertRaises(AssertionError):
      self.RunApigee("developers list --format=json --organization=test-org")

    wrong_wrapper_response = {"devs": [{"email": "keith@example.com"}]}
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/developers",
        status=200,
        expected_params={"count": "1000"},
        body=json.dumps(wrong_wrapper_response))
    with self.assertRaises(AssertionError):
      self.RunApigee("developers list --format=json --organization=test-org")

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
        "https://apigee.googleapis.com/v1/organizations/test-org/developers",
        status=200,
        expected_params={"count": "1000"},
        body=json.dumps(self._canned_response))
    self.RunApigee("developers list --format=json --project=test-proj")
    self.AssertJsonOutputMatches(
        ["bigboy@example.com", "littleman@example.com"],
        "Must return expected developers in proper order.")
