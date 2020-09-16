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
"""Tests that exercise the 'gcloud apigee organizations provision' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.command_lib.apigee import errors
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib.surface.apigee import base


class OrganizationsProvisionTest(base.ApigeeSurfaceTest,
                                 base.WithJSONBodyValidation):
  """Tests the `apigee organizations provision` command."""

  def CannedResponse(self):
    return {
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

  def CannedOutput(self):
    operation = self.CannedResponse()
    _, org_name, _, operation_uuid = operation["name"].split("/", 3)
    operation["uuid"] = operation_uuid
    operation["organization"] = org_name
    return operation

  def testNetworkMissing(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunApigee("organizations provision --project=test-org --format=json")

  def testProjectMissing(self):
    with self.assertRaises(errors.MissingIdentifierError):
      self.RunApigee(
          "organizations provision --format=json --authorized-network=coolnet")

  def testWithAnalyticsRegion(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/projects/test-org:provisionOrganization",
        status=200,
        request_headers={"Content-Type": "application/json"},
        expected_body=e2e_base.IGNORE,
        expected_json_body={
            "authorizedNetwork": "coolnet",
            "analyticsRegion": "us-beith1",
        },
        body=json.dumps(self.CannedResponse()))
    self.RunApigee(
        "organizations provision --project=test-org --format=json --async "
        "--authorized-network=coolnet --analytics-region=us-beith1")
    self.AssertJsonOutputMatches(self.CannedOutput())

  def testWithRuntimeLocation(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/projects/test-org:provisionOrganization",
        status=200,
        request_headers={"Content-Type": "application/json"},
        expected_body=e2e_base.IGNORE,
        expected_json_body={
            "authorizedNetwork": "coolnet",
            "runtimeLocation": "us-beith1-a",
        },
        body=json.dumps(self.CannedResponse()))
    self.RunApigee(
        "organizations provision --project=test-org --format=json --async "
        "--authorized-network=coolnet --runtime-location=us-beith1-a")
    self.AssertJsonOutputMatches(self.CannedOutput())

  def testProvisioningDefaults(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/projects/test-org:provisionOrganization",
        status=200,
        request_headers={"Content-Type": "application/json"},
        expected_body=e2e_base.IGNORE,
        expected_json_body={"authorizedNetwork": "coolnet"},
        body=json.dumps(self.CannedResponse()))
    self.RunApigee("organizations provision --project=test-org --async "
                   "--format=json --authorized-network=coolnet")
    self.AssertJsonOutputMatches(self.CannedOutput())

  def testSyncSuccess(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/projects/test-org:provisionOrganization",
        status=200,
        request_headers={"Content-Type": "application/json"},
        expected_body=e2e_base.IGNORE,
        expected_json_body={"authorizedNetwork": "coolnet"},
        body=json.dumps(self.CannedResponse()))

    complete_response = self.CannedResponse()
    complete_response["metadata"]["state"] = "FINISHED"

    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/operations/20b4ba00-0806-0000-997a-522a4adf027f",
        status=200,
        body=json.dumps(complete_response))

    self.RunApigee("organizations provision --project=test-org "
                   "--authorized-network=coolnet")
    self.AssertOutputEquals("")

  def testSyncSuccessWithPayload(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/projects/test-org:provisionOrganization",
        status=200,
        request_headers={"Content-Type": "application/json"},
        expected_body=e2e_base.IGNORE,
        expected_json_body={"authorizedNetwork": "coolnet"},
        body=json.dumps(self.CannedResponse()))

    complete_response = self.CannedResponse()
    complete_response["metadata"]["state"] = "FINISHED"
    complete_response["response"] = {"test": "object"}

    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/operations/20b4ba00-0806-0000-997a-522a4adf027f",
        status=200,
        body=json.dumps(complete_response))

    self.RunApigee("organizations provision --project=test-org --format=json "
                   "--authorized-network=coolnet")
    self.AssertJsonOutputMatches({"test": "object"},
                                 "Must return LRO response to user")

  def testSyncError(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/projects/test-org:provisionOrganization",
        status=200,
        request_headers={"Content-Type": "application/json"},
        expected_body=e2e_base.IGNORE,
        expected_json_body={"authorizedNetwork": "coolnet"},
        body=json.dumps(self.CannedResponse()))

    complete_response = self.CannedResponse()
    complete_response["metadata"]["state"] = "FINISHED"
    complete_response["error"] = {"code": 10, "message": "Injected error"}

    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/operations/20b4ba00-0806-0000-997a-522a4adf027f",
        status=200,
        body=json.dumps(complete_response))

    with self.assertRaises(errors.RequestError):
      self.RunApigee("organizations provision --project=test-org "
                     "--authorized-network=coolnet")
