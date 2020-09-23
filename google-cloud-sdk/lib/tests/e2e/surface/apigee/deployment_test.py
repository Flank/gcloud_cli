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
"""Critical user journey test for deploying a new version of an API proxy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.command_lib.apigee import errors
from tests.lib import e2e_utils
from tests.lib.surface.apigee import base
from tests.lib.surface.apigee import temp_resources


class DeploymentTest(base.ApigeeServiceAccountTest):

  @contextlib.contextmanager
  def DeployCommand(self, identifying_string, deploy_params=None):
    """Runs an `apis deploy` with the given identifiers as a context manager.

    Automatically attempts to undeploy its deployment upon exiting the context.

    Args:
      identifying_string: string with arguments to add to the deploy and
        undeploy commands that identify the deployment.
      deploy_params: string with arguments to add only to the deploy command.

    Yields:
      without a value, to invoke the with: statement's body.
    """
    deploy_command = "apis deploy %s --format=json" % identifying_string
    if deploy_params:
      deploy_command += " " + deploy_params
    self.RunApigee(deploy_command)
    try:
      yield
    finally:
      try:
        self.RunApigee("apis undeploy %s --format=disable" % identifying_string)
      except errors.EntityNotFoundError:
        # If the API is already undeployed, nothing needs to be done.
        pass

  def SetUp(self):
    super(DeploymentTest, self).SetUp()

    # If some problem with a previous test run caused resources to remain
    # undeleted, clean them up before beginning this test run.
    temp_resources.CleanUpOldResources("cloud-sdk-integration-testing")

  def testProxyRevisionDeployment(self):
    # The project-to-organization lookup is slightly flaky until some
    # server-side fixes launch. To avoid this causing test flakes, provide an
    # explicit --organization in all gcloud apigee commands.
    # TODO(b/133315199): use `config set project` and implicit lookup instead
    organization = "cloud-sdk-integration-testing"

    environment = "do-not-delete-environment"
    with temp_resources.APIProxy(organization, "helloapi", "R1", "A") as api, \
        temp_resources.Revision(organization, api, 2, "R2", "B"), \
        temp_resources.Revision(organization, api, 3, "R2", "B"):
      self.RunApigee("environments list --format=json --organization=" +
                     organization)
      self.assertIn(environment, self.GetJsonOutput())

      self.RunApigee("apis list --format=json --organization=" + organization)
      self.assertIn(api, self.GetJsonOutput())

      api_and_environment_flags = (
          " --organization=%s --api=%s --environment=%s" %
          (organization, api, environment))

      with self.DeployCommand(api_and_environment_flags):
        deploy_output = self.GetJsonOutput()
        self.assertIn("deployStartTime", deploy_output)
        del deploy_output["deployStartTime"]
        # TODO(b/168247570) The basepath field is deprecated and hidden from
        # the public API. It's safe to ignore until b/168247570 maybe repurposes
        # the field.
        del deploy_output["basePath"]
        self.assertEqual(
            deploy_output, {
                "environment": environment,
                "apiProxy": api,
                "revision": "3",
            })

        self.RunApigee("deployments describe --format=json %s 3" %
                       api_and_environment_flags)
        describe_output = self.GetJsonOutput()
        self.assertIn("apiProxy", describe_output)
        self.assertEqual(describe_output["apiProxy"], api)

        # Must not allow a conflicting deployment.
        with self.assertRaises(errors.RequestError):
          self.RunApigee("apis deploy 2" + api_and_environment_flags)

        # Must allow a conflicting deployment to override the old.
        with self.DeployCommand("2" + api_and_environment_flags, "--override"):
          new_deploy_output = self.GetJsonOutput()
          self.assertEqual(new_deploy_output["revision"], "2")

          self.RunApigee("deployments list --format=json" +
                         api_and_environment_flags)
          list_output = self.GetJsonOutput()
          self.assertEqual(
              len(list_output), 1, "Exactly one revision must be deployed.")
          self.assertEqual(list_output[0]["revision"], "2",
                           "Deployed revision must be the most recent one.")

          product_name = next(e2e_utils.GetResourceNameGenerator("product"))
          try:
            self.RunApigee(("products create %s --all-environments --apis=%s "
                            "--description='Created by E2E test' --format=json "
                            "--organization=%s --public-access") %
                           (product_name, api, organization))
            prod_create_output = self.GetJsonOutput()
            self.assertEqual(prod_create_output["name"], product_name)
            self.assertNotIn("environments", prod_create_output)
            self.assertNotIn("apiResources", prod_create_output)
            self.assertEqual(prod_create_output["proxies"], [api])
            self.RunApigee("products list --organization=%s --format=json" %
                           organization)
            prod_list = self.GetJsonOutput()
            self.assertIn({"name": product_name}, prod_list)

          finally:
            try:
              self.RunApigee(
                  "products delete %s --organization=%s --format=disable" %
                  (product_name, organization))

              self.RunApigee("products list --organization=%s --format=json" %
                             organization)
              prod_list = self.GetJsonOutput()
              self.assertNotIn({"name": product_name}, prod_list)
            except errors.EntityNotFoundError:
              # If the product doesn't exist, there's nothing to be done.
              pass

      self.RunApigee("deployments list --format=json" +
                     api_and_environment_flags)
      self.AssertJsonOutputMatches([])
