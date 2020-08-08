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
"""Tests that exercise the 'gcloud apigee products delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from tests.lib.surface.apigee import base


class ProductsDeleteTest(base.ApigeeSurfaceTest):

  def testSimpleDescribe(self):
    canned_response = {
        "name": "gcloud-test3",
        "displayName": "gCloud Test #3",
        "approvalType": "auto",
        "attributes": [{
            "name": "access",
            "value": "public"
        }],
        "description": "Testing product deletion",
        "apiResources": ["/gcloud-test1c", "/gcloud-test1"],
        "environments": ["prod", "test"],
        "quota": "7",
        "quotaInterval": "1",
        "quotaTimeUnit": "minute",
        "createdAt": "1590528446060",
        "lastModifiedAt": "1590528446060"
    }

    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/"
        "test-org/apiproducts/gcloud-test3",
        status=200,
        body=json.dumps(canned_response))
    self.RunApigee("products delete gcloud-test3 "
                   "--organization=test-org --format=json")
    self.AssertJsonOutputMatches(canned_response)
