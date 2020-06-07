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
"""Tests that exercise the 'gcloud apigee deployments list' commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
from googlecloudsdk.calliope.concepts import handlers
from tests.lib.surface.apigee import base


def _CannedListResponse(environment, name, revision):
  return {
      "environment": environment,
      "apiProxy": name,
      "revision": revision,
      "deployStartTime": "1568398344297",
      "basePath": "/"
  }


class DeploymentsListTest(base.ApigeeSurfaceTest):

  def _AddListResponse(self, organization, env=None, api=None, revision=None):
    envs = [env, env] if env else ["test", "staging"]
    apis = [api, api] if api else ["demo", "example"]
    revisions = [revision, revision] if revision else ["1", "2"]
    url = "https://apigee.googleapis.com/v1/organizations/" + organization
    if env:
      url += "/environments/" + env
    if api:
      url += "/apis/" + api
    if revision:
      url += "/revisions/" + revision
    url += "/deployments"

    if env and api and revision:
      # Server will send something that looks more like a "describe".
      response = _CannedListResponse(envs[0], apis[0], revisions[0])
      output = [response]
    else:
      output = [
          _CannedListResponse(envs[0], apis[0], revisions[0]),
          _CannedListResponse(envs[1], apis[1], revisions[1])
      ]
      response = {"deployments": output}
    self.AddHTTPResponse(url, status=200, body=json.dumps(response))
    return output

  def testWithoutOrganization(self):
    with self.assertRaises(handlers.ParseError):
      self.RunApigee("organizations deployments list --format=json")
    self.AssertErrContains(
        "ORGANIZATION", "Must prompt user for an organization name if "
        "organization and product are unknown.")

  def testOrganizationOnly(self):
    expected_output = self._AddListResponse("test-org")
    self.RunApigee("organizations deployments list test-org --format=json")
    self.AssertJsonOutputMatches(expected_output,
                                 "Must return a complete list of deployments.")

  def testEnvironmentsWithoutOrganization(self):
    with self.assertRaises(handlers.ParseError):
      self.RunApigee("environments deployments list prod --format=json")
    self.AssertErrContains(
        "--organization", "Must prompt user for an organization name if "
        "organization and product are unknown.")

  def testWithoutEnvironment(self):
    # Test harness may raise an error here for mismatch with surface spec.
    with self.assertRaises(Exception):
      self.RunApigee("environments deployments list --organization=test-org")
    self.AssertErrContains(
        "ENVIRONMENT",
        "Must prompt user for an environment name if none was provided.")

  def testEnvironments(self):
    expected_output = self._AddListResponse("test-org", "staging")
    self.RunApigee("environments deployments list staging "
                   "--organization=test-org --format=json")
    self.AssertJsonOutputMatches(expected_output,
                                 "Must return a complete list of deployments.")

  def testWithoutAPI(self):
    with self.assertRaises(handlers.ParseError):
      self.RunApigee("apis deployments list --organization=test-org "
                     "--environment=test --revision=1")
    self.AssertErrContains(
        "--api", "Must prompt user for an API proxy if none was provided.")

  def testAllRevision(self):
    expected = self._AddListResponse("test-org", env="test", api="demo")
    self.RunApigee("apis deployments list --organization=test-org "
                   "--environment=test --api=demo --format=json")
    self.AssertJsonOutputMatches(expected, "Must return multiple revisions.")

  def testAllEnvironment(self):
    expected = self._AddListResponse("test-org", api="demo", revision="2")
    self.RunApigee("apis deployments list --organization=test-org --api=demo "
                   "--revision=2 --format=json")
    self.AssertJsonOutputMatches(expected, "Must return multiple environments.")

  def testAPIOnly(self):
    expected_output = self._AddListResponse("test-org", api="demo")
    self.RunApigee("apis deployments list --organization=test-org --api=demo "
                   "--format=json")
    self.AssertJsonOutputMatches(
        expected_output, "Must return multiple environments and revisions.")

  def testFullIdentifier(self):
    expected = self._AddListResponse("test-org", "staging", "demo", "2")
    self.RunApigee("apis deployments list --organization=test-org --api=demo "
                   "--revision=2 --environment=staging --format=json")
    self.AssertJsonOutputMatches(expected,
                                 "Must return just the matching deployment.")

  def testConsistentEmptyOutputFromJSONArray(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/"
        "organizations/test-org/environments/test/deployments",
        status=200,
        body=json.dumps([]))
    self.RunApigee("environments deployments list test "
                   "--organization=test-org --format=json")
    self.AssertJsonOutputMatches(
        [], "Must return an empty array when there's no deployments to list.")

  def testConsistentEmptyOutputFromJSONObject(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/"
        "organizations/test-org/apis/demo/deployments",
        status=200,
        body=json.dumps({}))

    self.RunApigee("apis deployments list --api=demo "
                   "--organization=test-org --format=json")
    self.AssertJsonOutputMatches(
        [], "Must return an empty array when there's no deployments to list.")

  def testConsistentEmptyOutputFrom404(self):
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/"
        "environments/test/apis/demo/revisions/2/deployments",
        status=404)

    self.RunApigee("apis deployments list --environment=test --api=demo "
                   "--organization=test-org --revision=2 --format=json")
    self.AssertJsonOutputMatches(
        [], "Must return an empty array when there's no deployments to list.")
