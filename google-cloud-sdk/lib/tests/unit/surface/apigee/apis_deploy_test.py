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
"""Tests that exercise the 'gcloud apigee apis deploy' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.command_lib.apigee import errors
from tests.lib.surface.apigee import base


class APIsDeployTest(base.ApigeeSurfaceTest):

  def SetUp(self):
    self._canned_response = {
        "environment": "test",
        "apiProxy": "demo",
        "revision": "3",
        "deployStartTime": "1588262386845",
        "basePath": "/"
    }

    self._canned_describe_response = {
        "metaData": {
            "createdAt": "1582829537642",
            "lastModifiedAt": "1582829537642",
            "subType": "Proxy"
        },
        "name": "demo",
        "revision": ["1", "2", "3"]
    }

    self._canned_organization_response = {
        "organizations": [{
            "organization": "my-org",
            "projectIds": ["my-project"]
        }]
    }

  def _AddOrganizationListResponse(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations",
        status=200,
        body=json.dumps(self._canned_organization_response))

  def _AddDescribeResponse(self, organization, api):
    url = "https://apigee.googleapis.com/v1/organizations/%s/apis/%s" % (
        organization, api)
    response = self._canned_describe_response.copy()
    response["name"] = api
    self.AddHTTPResponse(url, status=200, body=json.dumps(response))

  def _AddDeployResponse(self, organization, override):
    url = ("https://apigee.googleapis.com/v1/organizations/%s/environments/%s"
           "/apis/%s/revisions/%s/deployments") % (
               organization, self._canned_response["environment"],
               self._canned_response["apiProxy"],
               self._canned_response["revision"])
    self.AddHTTPResponse(
        url,
        status=200,
        expected_params={"override": ["true"]} if override else None,
        body=json.dumps(self._canned_response))

  def testWithoutOrganization(self):
    with self.assertRaises(handlers.ParseError):
      self.RunApigee("apis deploy --api=demo --environment=test 2")
    self.AssertErrContains(
        "--organization",
        "Must prompt user for an organization name if organization and product "
        "are unknown.")

  def testWithoutAPI(self):
    with self.assertRaises(handlers.ParseError):
      self.RunApigee("apis deploy --organization=my-org --environment=test 2")
    self.AssertErrContains(
        "--api", "Must prompt user for a proxy name if none is provided.")

  def testWithExplicitRevision(self):
    self._canned_response["revision"] = 2
    self._AddDeployResponse("my-org", override=False)
    self.RunApigee("apis deploy --format=json 2 --organization=my-org "
                   "--environment=test --api=demo")
    self.AssertJsonOutputMatches(
        self._canned_response,
        "Must describe the successfully initiated deployment to the user.")

  def testWithOverride(self):
    self._canned_response["revision"] = 1
    self._AddDeployResponse("my-org", override=True)
    self.RunApigee("apis deploy --format=json 1 --organization=my-org "
                   "--environment=test --api=demo --override")
    self.AssertJsonOutputMatches(
        self._canned_response,
        "Must describe the successfully initiated deployment to the user.")

  def testWithLatestRevision(self):
    self._AddOrganizationListResponse()
    self._AddDescribeResponse("my-org", "demo")
    self._AddDeployResponse("my-org", override=False)
    self.RunApigee("apis deploy --format=json --project=my-project "
                   "--environment=test --api=demo")
    self.AssertJsonOutputMatches(
        self._canned_response,
        "Must describe the successfully initiated deployment to the user.")

  def testFailedDeployment(self):
    error_response = {
        "error": {
            "code": 400,
            "message": "revision organizations/my-org/apis/demo/revisions/2"
                       " is already deployed",
            "status": "FAILED_PRECONDITION"
        }
    }
    url = ("https://apigee.googleapis.com/v1/organizations/my-org/"
           "environments/test/apis/demo/revisions/2/deployments")
    self.AddHTTPResponse(url, status=400, body=json.dumps(error_response))
    with self.assertRaises(errors.RequestError):
      self.RunApigee("apis deploy --format=json 2 --organization=my-org "
                     "--environment=test --api=demo")
    self.AssertErrContains("Failed to deploy API proxy")
    self.AssertErrContains(error_response["error"]["message"],
                           "Must surface server's error message to the user.")

  def testFailedDeploymentWithComplexError(self):
    expected_error_message = "detailed description; show this one"
    expected_error_message2 = "also show this error message"
    error_response = {
        "error": {
            "code": 400,
            "message": "this error should not be shown as it's too generic",
            "details": [{
                "@type": "type.googleapis.com/google.rpc.DebugInfo",
                "detail": "Unrelated noise."
            }, {
                "@type":
                    "type.googleapis.com/google.rpc.PreconditionFailure",
                "violations": [{
                    "type": "SOMETHING",
                    "subject": "organizations/my-org/apis/demo/revisions/1",
                    "description": expected_error_message
                }, {
                    "type": "SOMETHING_ELSE",
                    "subject": "organizations/my-org/apis/demo",
                    "description": expected_error_message2
                }]
            }],
            "status": "FAILED_PRECONDITION"
        }
    }
    url = ("https://apigee.googleapis.com/v1/organizations/my-org/"
           "environments/test/apis/demo/revisions/2/deployments")
    self.AddHTTPResponse(url, status=400, body=json.dumps(error_response))
    with self.assertRaises(errors.RequestError):
      self.RunApigee("apis deploy --format=json 2 --organization=my-org "
                     "--environment=test --api=demo")
    self.AssertErrContains("Failed to deploy API proxy")
    self.AssertErrContains(expected_error_message,
                           "Must surface server's error message to the user.")
    self.AssertErrContains(expected_error_message2,
                           "Must surface server's error message to the user.")
    self.AssertErrNotContains(
        error_response["error"]["message"],
        "Must skip top level error message for precondition failures with "
        "detailed error messages.")

  def test404WithExplicitRevision(self):
    url = ("https://apigee.googleapis.com/v1/organizations/my-org/"
           "environments/test/apis/demo/revisions/2/deployments")
    self.AddHTTPResponse(url, status=404)
    with self.assertRaises(errors.EntityNotFoundError):
      self.RunApigee("apis deploy --format=json 2 --organization=my-org "
                     "--environment=test --api=demo")
    self.AssertErrContains("Requested API proxy does not exist")

  def test404WithLatestRevision(self):
    self._AddOrganizationListResponse()
    url = "https://apigee.googleapis.com/v1/organizations/my-org/apis/demo"
    self.AddHTTPResponse(url, status=404)
    with self.assertRaises(errors.EntityNotFoundError):
      self.RunApigee("apis deploy --format=json --project=my-project "
                     "--environment=test --api=demo")
    self.AssertErrContains("Requested api does not exist")
