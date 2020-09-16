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
"""Tests that exercise the 'gcloud apigee operations describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from tests.lib.surface.apigee import base


class OperationsDescribeTest(base.ApigeeSurfaceTest):

  def testSimpleDescribe(self):
    canned_response = {
        "metadata": {
            "@type":
                "type.googleapis.com/google.cloud.apigee.v1.OperationMetadata",
            "operationType":
                "INSERT",
            "state":
                "IN_PROGRESS",
            "targetResourceName":
                "organizations/cwajh-test-project"
        },
        "name":
            "organizations/test-org/operations/20b4ba00-0806-0000-997a-522a4adf027f"
    }
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/operations/20b4ba00-0806-0000-997a-522a4adf027f",
        status=200,
        body=json.dumps(canned_response))
    self.RunApigee("operations describe 20b4ba00-0806-0000-997a-522a4adf027f "
                   "--organization=test-org --format=json")
    canned_response["uuid"] = "20b4ba00-0806-0000-997a-522a4adf027f"
    canned_response["organization"] = "test-org"
    self.AssertJsonOutputMatches(canned_response)
