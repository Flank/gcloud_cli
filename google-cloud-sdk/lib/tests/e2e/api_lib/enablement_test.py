# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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

"""e2e tests for automatica enablement of disabled APIs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.resource_manager import operations
from googlecloudsdk.api_lib.services import enable_api as services_enable_api
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


GOOGLE_ORG_ID = 'organizations/433637338589'


class EnablementTest(e2e_base.WithServiceAuth):
  """Tests for api enablement flow.

  Note that these tests can change the state of the project (for example,
  enabling an api), which is why it is necessary to have a new project per
  invocation. If this project was shared with another test, it'd be possible to
  have test invocations interfering with each other's projects, which would lead
  to weird failures.
  """

  def SetUp(self):
    self.name_generator = e2e_utils.GetResourceNameGenerator('sdk-e2e')
    project_name = next(self.name_generator)
    self.project_id = command_lib_util.IdFromName(project_name)
    self.project_ref = command_lib_util.ParseProject(self.project_id)
    create_op = projects_api.Create(
        self.project_ref,
        parent=projects_api.ParentNameToResourceId(GOOGLE_ORG_ID))
    log.CreatedResource(self.project_ref, is_async=True)
    operations.WaitForOperation(create_op)

    log.debug('Enabling cloudapis.googleapis.com')
    services_client = apis.GetClientInstance('servicemanagement', 'v1')
    enable_operation = services_enable_api.EnableServiceApiCall(
        self.project_ref.Name(), 'cloudapis.googleapis.com')
    enable_operation_ref = resources.REGISTRY.Parse(
        enable_operation.name, collection='servicemanagement.operations')
    services_util.WaitForOperation(enable_operation_ref, services_client)

    self.Run('services enable cloudbilling')
    self.Run(('alpha billing accounts projects link {project} '
              '--account-id={billing}').format(project=self.project_id,
                                               billing=self.BillingId()))
    self.Run('projects add-iam-policy-binding {project} '
             '--member="group:mdb.cloud-sdk-build@google.com" '
             '--role="roles/owner"'.format(project=self.project_id))

    properties.VALUES.core.disable_prompts.Set(True)
    # This is set to false by sdk_test_base.SdkBase.
    properties.VALUES.core.should_prompt_to_enable_api.Set(True)
    # The api enablement check will prompt, and this will inject a yes into that
    self.StartPatch('googlecloudsdk.core.console.console_io.PromptContinue',
                    return_value=True)

  def TearDown(self):
    projects_api.Delete(self.project_ref)
    log.DeletedResource(self.project_ref)

  def testBasicCommandWorks(self):
    # A sanity check that everything is ok
    self._Run('services list')

  def testComputeInstancesEnablement(self):
    service = 'compute.googleapis.com'
    self.assertFalse(services_enable_api.IsServiceEnabled(self.project_id,
                                                          service))
    instance_name = next(self.name_generator)
    self._Run(
        'compute instances create --zone=us-east1-d {}'.format(instance_name))
    self._Run('compute instances list')
    self.AssertOutputContains(instance_name)
    self.assertTrue(services_enable_api.IsServiceEnabled(self.project_id,
                                                         service))

  def _Run(self, command):
    return self.Run('--project={} {}'.format(self.project_id, command))


if __name__ == '__main__':
  test_case.main()
