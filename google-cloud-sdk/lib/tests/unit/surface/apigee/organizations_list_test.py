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
"""Tests that exercise the 'gcloud apigee organizations list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
from tests.lib.surface.apigee import base


class OrganizationsListTest(base.ApigeeSurfaceTest):
  _canned_response = {
      "organizations": [
          {
              "organization": "my-project",
              "projectIds": ["my-project"]
          },
          {
              "organization": "old-organization",
              "projectIds": ["legacy-project"]
          },
      ]
  }

  def testDefaultFormatting(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations",
        status=200,
        body=json.dumps(self._canned_response))
    self.RunApigee("organizations list")
    self.AssertOutputContains(
        """\
NAME              PROJECT
my-project        my-project
old-organization  legacy-project
""",
        normalize_space=True)

  def testSortedResults(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations",
        status=200,
        body=json.dumps(self._canned_response))
    self.RunApigee("organizations list --format=json --sort-by=project")
    self.AssertJsonOutputMatches([{
        "name": "old-organization",
        "project": ["legacy-project"]
    }, {
        "name": "my-project",
        "project": ["my-project"]
    }], "Must return expected organizations in project order.")
