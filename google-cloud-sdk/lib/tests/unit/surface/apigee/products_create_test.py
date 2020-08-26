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
"""Tests that exercise the 'gcloud apigee products create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.apigee import errors
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib.surface.apigee import base


class ProductsCreateTest(base.ApigeeSurfaceTest, base.WithJSONBodyValidation):

  _dummy_response = {
      "this": 1,
      "content": "doesn't",
      "matter": ["the", "request", "body", "is", "what's", "important"]
  }

  def _CannedDeployment(self, proxy, revision):
    return {
        "environment": "test",
        "apiProxy": proxy,
        "revision": "%s" % revision,
        "deployStartTime": "1559105476161",
        "basePath": "/"
    }

  def _AddDummyOrganizationList(self, names):
    response = [{"organization": name, "projectIds": [name]} for name in names]
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations",
        body=json.dumps({"organizations": response} if names else {}))

  def _AddDummyResponse(self, name, access, fields=None, attributes=None):
    expected_payload = {
        "name": name,
        "displayName": name,
        "approvalType": "auto",
        "attributes": [{
            "name": "access",
            "value": access
        }]
    }
    if fields:
      expected_payload.update(fields)
    if attributes:

      def _AttributeDict(key, value):
        return {"name": key, "value": value}

      attribute_entries = [_AttributeDict(*item) for item in attributes.items()]
      expected_payload["attributes"] += attribute_entries

    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/apiproducts",
        expected_body=e2e_base.IGNORE,
        expected_json_body=expected_payload,
        body=json.dumps(self._dummy_response),
        request_headers={"Content-Type": "application/json"})

  def testMinimalCreate(self):
    self._AddDummyResponse("testprod", "public")
    self.RunApigee("products create testprod --public-access --format=json "
                   "--organization=test-org --all-environments --all-proxies")
    self.AssertJsonOutputMatches(self._dummy_response)

  def testComprehensiveCreate(self):
    fields = {
        "description": "some description text",
        "displayName": "some display name",
        "approvalType": "manual",
        "environments": ["staging", "prod"],
        "proxies": ["prox", "proy", "proz"],
        "apiResources": ["/foo", "/bar/**"],
        "quota": "77",
        "quotaInterval": "2",
        "quotaTimeUnit": "hour",
        "scopes": ["news:read", "breakfast:consume"]
    }
    attributes = {"nonsense": "abadede", "sense": "common"}
    self._AddDummyResponse("bigtest", "internal", fields, attributes)

    fields["environments"] = ",".join(fields["environments"])
    fields["proxies"] = ",".join(fields["proxies"])
    fields["scopes"] = "@".join(fields["scopes"])
    fields["apiResources"] = "#".join(fields["apiResources"])
    attributes = ",".join("%s=%s" % tuple(item) for item in attributes.items())

    command_line_args = (
        "bigtest --organization=test-org --internal-access --manual-approval "
        "--apis={proxies} --resources='{apiResources}' --quota={quota} "
        "--quota-interval={quotaInterval} --quota-unit={quotaTimeUnit} "
        "--display-name='{displayName}' --environments={environments} "
        "--description='{description}' --oauth-scopes=^@^{scopes}").format(
            **fields)
    command_line_args += " --attributes=" + attributes
    self.RunApigee("products create --format=json " + command_line_args)
    self.AssertJsonOutputMatches(self._dummy_response)

  def testMissingName(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunApigee("products create --public-access --format=json "
                     "--organization=test-org --all-environments --all-proxies")

  def testMissingAccess(self):
    with self.assertRaises(exceptions.OneOfArgumentsRequiredException):
      self.RunApigee("products create testprod --format=json "
                     "--organization=test-org --all-environments --all-proxies")

  def testMissingEnvironment(self):
    with self.assertRaises(exceptions.OneOfArgumentsRequiredException):
      self.RunApigee("products create testprod --public-access --format=json "
                     "--organization=test-org --all-proxies")

  def testMissingProxies(self):
    with self.assertRaises(exceptions.OneOfArgumentsRequiredException):
      self.RunApigee("products create testprod --public-access --format=json "
                     "--organization=test-org --all-environments")

  def testConflictingProxies(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunApigee("products create testprod --public-access --format=json "
                     "--organization=test-org --all-environments "
                     "--apis=api-name --all-proxies")
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunApigee("products create testprod --public-access --format=json "
                     "--organization=test-org --all-environments "
                     "--resources=/resource/path --all-proxies")

  def testPartialProxyInfoAPIsOnly(self):
    fields = {
        "proxies": ["prox", "proy", "proz"],
    }
    self._AddDummyResponse("ppi1", "public", fields)
    self.RunApigee(
        "products create ppi1 --public-access --format=json --all-environments "
        "--organization=test-org --all-environments --apis=prox,proy,proz")
    self.AssertJsonOutputMatches(self._dummy_response)

  def testPartialProxyInfoResourcesOnly(self):
    fields = {
        "apiResources": ["/foo", "/bar/**"],
    }
    self._AddDummyResponse("ppi2", "public", fields)

    self.RunApigee(
        "products create ppi2 --public-access --format=json --all-environments "
        "--organization=test-org --all-environments --resources='/foo#/bar/**'")
    self.AssertJsonOutputMatches(self._dummy_response)

  def testPartialQuotaInfo(self):
    with self.assertRaises(exceptions.RequiredArgumentException):
      self.RunApigee("products create testprod --public-access --format=json "
                     "--organization=test-org --all-environments --all-proxies "
                     "--quota=5")
    with self.assertRaises(exceptions.RequiredArgumentException):
      self.RunApigee("products create testprod --public-access --format=json "
                     "--organization=test-org --all-environments --all-proxies "
                     "--quota-interval=5")
    with self.assertRaises(exceptions.RequiredArgumentException):
      self.RunApigee("products create testprod --public-access --format=json "
                     "--organization=test-org --all-environments --all-proxies "
                     "--quota-unit=day")

  def testWeirdQuotaUnit(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunApigee("products create testprod --public-access --format=json "
                     "--organization=test-org --all-environments --all-proxies "
                     "--quota=5 --quota-interval=40 quota-unit=wink")

  def testBadProductName(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunApigee("products create test~prod --public-access --format=json "
                     "--organization=test-org --all-environments --all-proxies")

  def testTooManyAttributes(self):
    flotsam = ",".join(
        "%s=%sval" % (name, name) for name in "qwertyuiopasdfghjk")
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunApigee("products create testprod --public-access --format=json "
                     "--organization=test-org --all-environments --all-proxies "
                     "--attributes=%s" % flotsam)

  def testLazyInteractive(self):
    # Force prompting to turn on despite this test running in a test harness.
    self.StartPatch(
        "googlecloudsdk.core.console.console_io.CanPrompt", return_value=True)

    # Prompt for organizations.
    self._AddDummyOrganizationList(["test-org"])
    self.WriteInput("1")  # Take what's offered.

    self.WriteInput("blahblah")  # Product name.

    self.WriteInput("1")  # Take all environments.
    self.WriteInput("1")  # Take all proxies.
    self.WriteInput("1")  # Public

    self._AddDummyResponse("blahblah", "public")
    self.RunApigee("products create --format=json")
    self.AssertJsonOutputMatches(self._dummy_response)

  def testInteractiveEncounteringErrors(self):
    # Force prompting to turn on despite this test running in a test harness.
    self.StartPatch(
        "googlecloudsdk.core.console.console_io.CanPrompt", return_value=True)
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations",
        status=500)
    self.WriteInput("test-org")  # Skip straight to prompting the user.

    self.WriteInput("2")  # Select environments manually.
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/environments",
        body="[]")
    with self.assertRaises(errors.EntityNotFoundError):
      self.RunApigee("products create mycoolproduct --format=json")

  def testIndecisiveInteractive(self):
    # Force prompting to turn on despite this test running in a test harness.
    self.StartPatch(
        "googlecloudsdk.core.console.console_io.CanPrompt", return_value=True)

    self._AddDummyOrganizationList([])  # API is flaking again...
    self.WriteInput("test-org")  # Skip straight to prompting the user.

    self.WriteInput("2")  # Select API proxies manually.
    deployment_enum = enumerate(["cinnamon", "apple", "broccoli", "cinnamon"])
    deployments = [
        self._CannedDeployment(item, idx) for idx, item in deployment_enum
    ]
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/deployments",
        body=json.dumps({"deployments": deployments}))
    self.WriteInput("4")  # No specific proxies.
    self.WriteInput("2")  # Actually, nevermind, don't limit resources either.

    self._AddDummyResponse("testprod", "public")
    self.RunApigee("products create testprod --public-access --format=json "
                   "--all-environments")
    self.AssertJsonOutputMatches(self._dummy_response)

  def testPickyInteractive(self):
    # Force prompting to turn on despite this test running in a test harness.
    self.StartPatch(
        "googlecloudsdk.core.console.console_io.CanPrompt", return_value=True)

    # Prompt for organizations.
    self._AddDummyOrganizationList(["fake", "nope"])
    self.WriteInput("3")  # One past the end of the list - enter it custom.
    self.WriteInput("test-org")

    # Prompt for internal name.
    self.WriteInput("typed-product/")  # Typo. Will be rejected.
    self.WriteInput("interactive-product")

    # Prompt for environment.
    self.WriteInput("2")  # Select manually.
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/environments",
        body=json.dumps(["env1", "env2", "env3"]))
    self.WriteInput("3")  # Should add "env3"
    self.WriteInput("3")  # Should add "env2", since "env3" moves to the top
    self.WriteInput("1")  # Should remove "env3"
    self.WriteInput("4")  # Accept.

    # Prompt for API proxies.
    self.WriteInput("2")  # Select manually.

    deployment_enum = enumerate(["cinnamon", "apple", "broccoli", "cinnamon"])
    deployments = [
        self._CannedDeployment(item, idx) for idx, item in deployment_enum
    ]
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations/test-org/deployments",
        body=json.dumps({"deployments": deployments}))
    # Expect the options to be "apple, broccoli, cinnamon", as the proxy names
    # should have been deduplicated.
    self.WriteInput("2")  # Add "broccoli"
    self.WriteInput("2")  # Add "apple".
    self.WriteInput("4")  # Accept.

    self.WriteInput("1")  # Choose to manually specify proxy resources.
    self.WriteInput("/this-one/will-be/removed-later")
    self.WriteInput("2")  # Enter another.
    self.WriteInput("/this-one/will/survive/*")
    self.WriteInput("1")  # Delete the original one.
    self.WriteInput("3")  # Accept.

    self.WriteInput("2")  # Private access.

    expected_fields = {
        "apiResources": ["/this-one/will/survive/*"],
        "proxies": ["broccoli", "apple"],
        "environments": ["env2"]
    }
    self._AddDummyResponse("interactive-product", "private", expected_fields)
    self.RunApigee("products create --format=json")
    self.AssertJsonOutputMatches(self._dummy_response)
