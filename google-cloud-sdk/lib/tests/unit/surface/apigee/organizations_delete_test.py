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
"""Tests that exercise the 'gcloud apigee organizations delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from tests.lib.surface.apigee import base


class OrganizationsDeleteTest(base.ApigeeSurfaceTest):

  def testDelete(self):
    canned_response = {
        "metadata": {
            "@type":
                "type.googleapis.com/google.cloud.apigee.v1.OperationMetadata",
            "operationType":
                "DELETE",
            "state":
                "IN_PROGRESS",
            "targetResourceName":
                "organizations/test-org"
        },
        "name":
            "organizations/test-org/operations/6d3aa49b-fec2-0000-988b-35c617cca401"
    }

    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org",
        status=200,
        body=json.dumps(canned_response))
    self.RunApigee("organizations delete test-org --format=json")
    self.AssertJsonOutputMatches(canned_response)
