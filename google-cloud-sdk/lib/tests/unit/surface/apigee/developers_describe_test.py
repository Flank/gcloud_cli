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
"""Tests that exercise the 'gcloud apigee apis describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from tests.lib.surface.apigee import base


class DevelopersDescribeTest(base.ApigeeSurfaceTest):

  def testSimpleDescribe(self):
    canned_response = {
        "email": "keith@example.com",
        "firstName": "Karen",
        "lastName": "Eith",
        "userName": "keith",
        "developerId": "f140c2db-d5d6-41ae-a10f-0c0cb6f583b8",
        "organizationName": "test-org",
        "status": "active",
        "createdAt": "1585846082012",
        "lastModifiedAt": "1585846082012"
    }
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/developers/keith%40example.com",
        status=200,
        body=json.dumps(canned_response))
    self.RunApigee("developers describe keith@example.com "
                   "--organization=test-org --format=json")
    self.AssertJsonOutputMatches(canned_response)
