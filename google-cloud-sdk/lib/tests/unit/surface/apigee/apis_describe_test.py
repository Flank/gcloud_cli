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
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.command_lib.apigee import errors
from tests.lib.surface.apigee import base


class APIsDescribeTest(base.ApigeeSurfaceTest):

  def SetUp(self):
    self._canned_response = {
        "metaData": {
            "createdAt": "1582829537642",
            "lastModifiedAt": "1582829537642",
            "subType": "Proxy"
        },
        "name": "demo",
        "revision": ["1"]
    }

    self._canned_organization_response = {
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

  def _CannedRevisionResponse(self, revision_id):
    return {
        "basepaths": ["/%spath" % self._canned_response["name"]],
        "configurationVersion": {
            "majorVersion": 4
        },
        "createdAt": "1582829537642",
        "entityMetaDataAsProperties": {
            "bundle_type": "zip",
            "createdAt": "1582836800188",
            "lastModifiedAt": "1582829537642",
            "subType": "Proxy"
        },
        "lastModifiedAt": "1582836800188",
        "name": self._canned_response["name"],
        "revision": revision_id,
        "policies": ["XML-to-JSON-" + revision_id],
        "proxies": ["default"],
        "proxyEndpoints": ["default"],
        "resourceFiles": {},
        "targetEndpoints": ["default"],
        "targets": ["default"],
        "type": "Application"
    }

  def _AddOrganizationListResponse(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations",
        status=200,
        body=json.dumps(self._canned_organization_response))

  def _AddRevisionResponse(self, revision, organization):
    url = ("https://apigee.googleapis.com/v1/organizations/%s/"
           "apis/%s/revisions/%s") % (organization, revision["name"],
                                      revision["revision"])
    self.AddHTTPResponse(url, status=200, body=json.dumps(revision))

  def _AddDescribeResponse(self, organization):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/%s/apis/%s" %
        (organization, self._canned_response["name"]),
        status=200,
        body=json.dumps(self._canned_response))

  def testWithoutOrganization(self):
    with self.assertRaises(handlers.ParseError):
      self.RunApigee("apis describe demo --format=json")
    self.AssertErrContains(
        "--organization",
        "Must prompt user for an organization name if organization and product "
        "are unknown.")

  def testWithProjectFallback(self):
    self._AddOrganizationListResponse()
    self._AddDescribeResponse("my-project")
    self.RunApigee("apis describe demo --format=json --project=my-project")
    self.AssertJsonOutputMatches(
        self._canned_response,
        "First request must retrieve & use live project-organization mapping.")

    self._canned_response["revision"] = ["2"]
    self._AddDescribeResponse("old-organization")
    self.RunApigee("apis describe demo --format=json --project=legacy-project")
    self.AssertJsonOutputMatches(
        self._canned_response,
        "Subsequent requests with recognized project names must used cached mapping."
    )

    self._canned_organization_response = {
        "organizations": [
            {
                "organization": "my-project",
                "projectIds": ["my-project"]
            },
            {
                "organization": "new-project",
                "projectIds": ["new-project"]
            },
        ]
    }
    self._AddOrganizationListResponse()
    self._canned_response["revision"] = ["3"]
    self._AddDescribeResponse("new-project")
    self.RunApigee("apis describe demo --format=json --project=new-project")
    self.AssertJsonOutputMatches(
        self._canned_response,
        "Subsequent requests with unrecognized project names must use an updated mapping."
    )

    self._AddDescribeResponse("old-organization")
    self.RunApigee("apis describe demo --project=legacy-project  --format=json")
    self.AssertJsonOutputMatches(
        self._canned_response,
        "Subsequent requests with recognized project names must use cached mapping."
    )

    self._AddOrganizationListResponse()
    with self.assertRaises(handlers.ParseError):
      self.RunApigee("apis describe demo --project=fake-project --format=json")
    self.AssertErrMatches(
        "fake-project.*--organization",
        "Must mention absence of nonexistant GCP project and require an Apigee organization."
    )

  def testWithOrganization(self):
    self._AddDescribeResponse("some-org")
    self.RunApigee("apis describe demo --organization=some-org --format=json")
    self.AssertJsonOutputMatches(
        self._canned_response,
        "Must retrieve API proxy without using a project mapping if the user "
        "specifies a GCP organization.")

  def testAPINotFound(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/some-org/apis/demo",
        status=404)
    with self.assertRaises(errors.EntityNotFoundError):
      self.RunApigee("apis describe demo --organization=some-org --format=json")
    self.AssertErrContains("Requested api does not exist")
    self.AssertErrContains("demo",
                           "404 error must identify the missing resource.")
    self.AssertErrContains("some-org",
                           "404 error must identify the missing resource.")

  def testAPINotAccessible(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/some-org/apis/demo",
        status=403)
    with self.assertRaises(errors.UnauthorizedRequestError):
      self.RunApigee("apis describe demo --organization=some-org --format=json")
    self.AssertErrContains("Insufficient privileges to GET the requested api")
    self.AssertErrContains("demo",
                           "404 error must identify the missing resource.")
    self.AssertErrContains("some-org",
                           "404 error must identify the missing resource.")

  def testVerbose(self):
    revision_ids = ["1", "2", "3"]

    self._canned_response["revision"] = revision_ids
    self._AddDescribeResponse("some-org")
    expected_output = self._canned_response.copy()
    expected_output["revisions"] = []

    for revision_id in revision_ids:
      canned_revision = self._CannedRevisionResponse(revision_id)
      self._AddRevisionResponse(canned_revision, "some-org")
      # Verbose describe output drops the "name" field of revisions since it's
      # redundant with the API proxy's own "name" field.
      del canned_revision["name"]
      expected_output["revisions"].append(canned_revision)

    # Verbose describe output drops the list of revision IDs since it has a
    # list of full revision objects instead.
    del expected_output["revision"]

    self.RunApigee(
        "apis describe demo --organization=some-org --format=json --verbose")
    self.AssertJsonOutputMatches(expected_output,
                                 "Must retrieve API proxy and its revisions.")
