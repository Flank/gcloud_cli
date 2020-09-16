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
"""Tests that exercise the 'gcloud apigee operations list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
from tests.lib.surface.apigee import base


class OperationsListTest(base.ApigeeSurfaceTest):
  _canned_response = {
      "operations": [{
          "name":
              "organizations/test-org/operations/9cc99855-bb7e-0000-9ee5-efd96edafe7e",
          "metadata": {
              "@type":
                  "type.googleapis.com/google.cloud.apigee.v1.OperationMetadata",
              "operationType":
                  "INSERT",
              "targetResourceName":
                  "organizations/test-org",
              "state":
                  "IN_PROGRESS"
          }
      }, {
          "name":
              "organizations/test-org/operations/5a726aaa-d7c3-0000-a641-b37cfd6f4a77",
          "metadata": {
              "@type":
                  "type.googleapis.com/google.cloud.apigee.v1.OperationMetadata",
              "operationType":
                  "INSERT",
              "targetResourceName":
                  "organizations/test-org/environment/test",
              "state":
                  "IN_PROGRESS"
          }
      }]
  }

  def testDefaultFormatting(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/operations",
        status=200,
        body=json.dumps(self._canned_response))
    self.RunApigee("operations list --organization=test-org")
    self.AssertOutputContains(
        """\
UUID                                  ORGANIZATION  STATE
9cc99855-bb7e-0000-9ee5-efd96edafe7e  test-org      IN_PROGRESS
5a726aaa-d7c3-0000-a641-b37cfd6f4a77  test-org      IN_PROGRESS""",
        normalize_space=True)

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
        "https://apigee.googleapis.com/v1/organizations/test-org/operations",
        status=200,
        body=json.dumps(self._canned_response))
    self.RunApigee("operations list --format=json --project=test-proj")
    expected_output = []
    for item in self._canned_response["operations"]:
      item = item.copy()
      item["uuid"] = item["name"].split("/")[-1]
      item["organization"] = "test-org"
      expected_output.append(item)
    self.AssertJsonOutputMatches(
        expected_output, "Must return expected environments in proper order.")
