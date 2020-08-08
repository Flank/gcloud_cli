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
"""Tests that exercise the 'gcloud apigee applications describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from tests.lib.surface.apigee import base


class ApplicationsDescribeTest(base.ApigeeSurfaceTest):

  def testSimpleDescribe(self):
    canned_response = {
        "appId": "c3b20cec-c3f8-42e9-8a89-83f55c24149c",
        "attributes": [{
            "name": "DisplayName",
            "value": "Hungry Bird 0.1"
        }, {
            "name": "Notes",
            "value": "Test app for gcloud commands..."
        }],
        "createdAt": "1591645866735",
        "credentials": [{
            "apiProducts": [{
                "apiproduct": "gcloud-test2",
                "status": "pending"
            }, {
                "apiproduct": "gcloud-test1",
                "status": "approved"
            }],
            "consumerKey": "vJ5hNFx8Tq3sSIBWKZnkT8y1LVz9BbSR",
            "consumerSecret": "UTJehpjnbiLIcrSL",
            "expiresAt": "-1",
            "issuedAt": "1591645866792",
            "status": "approved"
        }],
        "developerId": "659525a4-212b-4f46-ad6f-02d9d33ed69b",
        "lastModifiedAt": "1591645866735",
        "name": "hungrybird01",
        "status": "approved"
    }

    self.AddHTTPResponse(
        ("https://apigee.googleapis.com/v1/organizations/test-org/apps/"
         "c3b20cec-c3f8-42e9-8a89-83f55c24149c"),
        body=json.dumps(canned_response))
    self.RunApigee("applications describe --organization=test-org "
                   "c3b20cec-c3f8-42e9-8a89-83f55c24149c --format=json")
    self.AssertJsonOutputMatches(canned_response)
