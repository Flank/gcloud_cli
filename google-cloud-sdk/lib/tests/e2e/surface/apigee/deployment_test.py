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
from tests.lib.surface.apigee import base
from tests.lib.surface.apigee import temp_resources


class DeploymentTest(base.ApigeeServiceAccountTest):

  @contextlib.contextmanager
  def DeployCommand(self, identifying_string):
    """Runs an `apis deploy` with the given identifiers as a context manager.

    Automatically attempts to undeploy its deployment upon exiting the context.

    Args:
      identifying_string: string with arguments to add to the deploy and
        undeploy commands that identify the deployment.

    Yields:
      without a value, to invoke the with: statement's body.
    """
    self.RunApigee("apis deploy %s --format=json" % identifying_string)
    try:
      yield
    finally:
      self.RunApigee("apis undeploy %s --format=disable" % identifying_string)

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

    with temp_resources.Environment(organization, "testenv") as environment, \
        temp_resources.APIProxy(organization, "helloapi", "R1", "A") as api, \
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
        self.assertEqual(
            deploy_output, {
                "environment": environment,
                "apiProxy": api,
                "revision": "3",
                "basePath": "/"
            })

        self.RunApigee("deployments describe --format=json %s 3" %
                       api_and_environment_flags)
        describe_output = self.GetJsonOutput()
        self.assertIn("apiProxy", describe_output)
        self.assertEqual(describe_output["apiProxy"], api)

        # Must not allow a conflicting deployment.
        with self.assertRaises(errors.RequestError):
          self.RunApigee("apis deploy 2" + api_and_environment_flags)

        # Must allow a nonconflicting deployment.
        with self.DeployCommand("1" + api_and_environment_flags):
          new_deploy_output = self.GetJsonOutput()
          self.assertEqual(new_deploy_output["revision"], "1")

          self.RunApigee("apis deployments list --format=json" +
                         api_and_environment_flags)
          list_output = self.GetJsonOutput()
          self.assertEqual(
              len(list_output), 2, "Both revisions must be deployed.")

      self.RunApigee("apis deployments list --format=json" +
                     api_and_environment_flags)
      self.AssertJsonOutputMatches([])
