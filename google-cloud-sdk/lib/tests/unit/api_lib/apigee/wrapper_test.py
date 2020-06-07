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
"""Tests for googlecloudsdk.api_lib.apigee."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib import apigee
from tests.lib.surface.apigee import base


class BrokenClient(apigee.base.BaseClient):
  pass


class WrapperTest(base.ApigeeIsolatedTest):

  def testClientWithoutEntityPath(self):
    with self.assertRaises(NotImplementedError):
      BrokenClient.List({"organizationsId": "some-org"})
    with self.assertRaises(NotImplementedError):
      BrokenClient.Describe({"organizationsId": "some-org"})

  def testDeploymentListIgnoresDanglingRevisionIdentifier(self):
    fake_response = [
        {
            "environment": "test",
            "apiProxy": "someproxy",
            "revision": "1",
            "deployStartTime": "1559105475891",
            "basePath": "/"
        },
        {
            "environment": "test",
            "apiProxy": "Another_Proxy",
            "revision": "2",
            "deployStartTime": "1559105476161",
            "basePath": "/"
        },
    ]
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/deployments",
        status=200,
        body=json.dumps({"deployments": fake_response}))

    list_output = apigee.DeploymentsClient.List({
        "organizationsId": "test-org",
        "revisionsId": "3"
    })

    self.assertEqual(fake_response, list_output)
