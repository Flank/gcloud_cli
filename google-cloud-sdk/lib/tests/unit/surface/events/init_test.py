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
"""Unit tests for the `events init` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.events import iam_util
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.iam import iam_util as core_iam_util
from googlecloudsdk.core.console import console_io
from surface.events import init
from tests.lib.surface.run import base
import mock


class InitTestAlpha(base.ServerlessSurfaceBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.service_account = 'svcacc@gserviceaccount.com'
    self.service_account_ref = self._registry.Parse(
        self.service_account,
        params={'projectsId': '-'},
        collection=core_iam_util.SERVICE_ACCOUNTS_COLLECTION)
    self.service_account_key_ref = self._registry.Parse(
        'somehexvalue',
        params={
            'projectsId': 'fake-project',
            'serviceAccountsId': self.service_account
        },
        collection='iam.projects.serviceAccounts.keys')
    self.operations.CreateOrReplaceServiceAccountSecret.return_value = (
        None, self.service_account_key_ref)
    # Provide the superpower roles/owner permission to get around the validation
    # logic by default
    self.StartObjectPatch(
        iam_util,
        'GetProjectRolesForServiceAccount',
        return_value=set(['roles/owner']))
    self.mock_list_services = self.StartObjectPatch(
        serviceusage,
        'ListServices',
        return_value=[_mock_service(name) for name
                      in init._CONTROL_PLANE_REQUIRED_SERVICES],
    )

  def runCommandAndAssertComplete(self):
    self.Run('events init --service-account=svcacc@gserviceaccount.com '
             '--platform=gke --cluster=cluster-1 '
             '--cluster-location=us-central1-a')
    self.AssertErrContains(
        'Initialized cluster [cluster-1] for Cloud Run eventing')
    self.AssertErrContains(self.service_account)
    self.AssertErrContains(self.service_account_key_ref.Name())

  def testEventTypesFailFailNonGKE(self):
    """This command is only for initializing a cluster."""
    with self.assertRaises(exceptions.UnsupportedArgumentError):
      self.Run('events init --service-account=svcacc@gserviceaccount.com '
               '--platform=managed --region=us-central1')
    self.AssertErrContains(
        'This command is only available with Cloud Run for Anthos.')

  def testInitWithPromptYes(self):
    """Tests successful init with success message on prompt confirmation."""
    self.WriteInput('y\n')
    self.runCommandAndAssertComplete()

  def testInitWithPromptNoFails(self):
    """Tests failed init without prompt confirmation."""
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('events init --service-account=svcacc@gserviceaccount.com '
               '--platform=gke --cluster=cluster-1 '
               '--cluster-location=us-central1-a')

  def testInitNoPrompt(self):
    """Tests successful init with success message on no prompting allowed."""
    self.is_interactive.return_value = False
    self.runCommandAndAssertComplete()

  def testServiceAccountHasAllRoles(self):
    self.StartObjectPatch(
        iam_util,
        'GetProjectRolesForServiceAccount',
        return_value=set([
            'roles/pubsub.editor', 'roles/storage.admin',
            'roles/cloudscheduler.admin', 'roles/pubsub.admin',
            'roles/logging.configWriter', 'roles/logging.privateLogViewer'
        ]))
    self.WriteInput('y\n')
    self.runCommandAndAssertComplete()

  def testMissingServiceAccountRolesAreBound(self):
    self.StartObjectPatch(
        iam_util,
        'GetProjectRolesForServiceAccount',
        return_value=set([
            'roles/pubsub.editor', 'roles/storage.admin',
            'roles/cloudscheduler.admin', 'roles/pubsub.admin',
        ]))
    bind_roles = self.StartObjectPatch(
        iam_util,
        'BindProjectRolesForServiceAccount')
    self.WriteInput('y\n')
    self.WriteInput('y\n')
    self.runCommandAndAssertComplete()
    bind_roles.assert_called_once_with(
        self.service_account_ref,
        {'roles/logging.configWriter', 'roles/logging.privateLogViewer'})
    self.AssertErrContains(
        'This will bind the following project roles to this service account:\\n'
        '- roles/logging.configWriter\\n'
        '- roles/logging.privateLogViewer', normalize_space=True)

  def testMissingServicesAreEnabledEnablesOneService(self):
    # ListServices has been mocked out to return all required services as
    # enaabled. Lets change that by removing one from the return value.
    self.mock_list_services.return_value.pop(0)

    mock_enable_api_call = self.StartObjectPatch(
        serviceusage,
        'EnableApiCall',
    )
    mock_enable_api_call.return_value.done = True
    self.WriteInput('y\n')
    self.WriteInput('y\n')
    self.runCommandAndAssertComplete()
    mock_enable_api_call.assert_called_once_with(
        'fake-project', 'cloudresourcemanager.googleapis.com')

  def testMissingServicesAreEnabledEnablesMultipleServices(self):
    # ListServices has been mocked out to return all required services as
    # enaabled. Lets change that by removing two from the return value.
    # Removing two exercises a different code path using BatchEnableApiCall.
    self.mock_list_services.return_value.pop(0)
    self.mock_list_services.return_value.pop(0)

    mock_batch_enable_api_call = self.StartObjectPatch(
        serviceusage,
        'BatchEnableApiCall',
    )
    mock_batch_enable_api_call.return_value.done = False
    mock_wait_operation = self.StartObjectPatch(
        services_util,
        'WaitOperation',
    )
    self.WriteInput('y\n')
    self.WriteInput('y\n')
    self.runCommandAndAssertComplete()
    mock_batch_enable_api_call.assert_called_once_with(
        'fake-project', ['cloudresourcemanager.googleapis.com',
                         'cloudscheduler.googleapis.com'])
    mock_wait_operation.assert_called_once_with(
        mock_batch_enable_api_call.return_value.name, serviceusage.GetOperation)


def _mock_service(name):
  service = mock.Mock()
  service.config.name = name
  return service
