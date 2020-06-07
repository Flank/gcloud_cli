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
"""Tests that exercise the 'gcloud apigee environments list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
from tests.lib.surface.apigee import base


class EnvironmentsListTest(base.ApigeeSurfaceTest):
  _canned_response = ["test", "beta", "prod"]

  def testDefaultFormatting(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/environments",
        status=200,
        body=json.dumps(self._canned_response))
    self.RunApigee("environments list --organization=test-org")
    self.AssertOutputContains(
        """\
 - test
 - beta
 - prod""", normalize_space=True)

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
        "https://apigee.googleapis.com/v1/organizations/test-org/environments",
        status=200,
        body=json.dumps(self._canned_response))
    self.RunApigee("environments list --format=json --project=test-proj")
    self.AssertJsonOutputMatches(
        self._canned_response,
        "Must return expected environments in proper order.")
