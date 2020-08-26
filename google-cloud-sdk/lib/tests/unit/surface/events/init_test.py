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
from tests.lib.surface.events import base
import mock


class InitTestAlpha(base.EventsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.get_or_create_service_account = self.StartObjectPatch(
        iam_util,
        'GetOrCreateServiceAccountWithPrompt',
        side_effect=_MockGetOrCreateServiceAccount
    )
    self.operations.CreateOrReplaceServiceAccountSecret.side_effect = (
        self._MockCreateOrReplaceServiceAccountSecret)
    self.bind_missing_roles = self.StartObjectPatch(
        iam_util,
        'PrintOrBindMissingRolesWithPrompt',
    )
    self.mock_list_services = self.StartObjectPatch(
        serviceusage,
        'ListServices',
        return_value=[_MockService(name) for name
                      in init._CONTROL_PLANE_REQUIRED_SERVICES],
    )
    self.operations.IsClusterInitialized.return_value = False

  def _MockCreateOrReplaceServiceAccountSecret(self, secret_ref,
                                               service_account_ref):
    key_ref = self._registry.Parse(
        'somehexvalue',
        params={
            'projectsId': 'fake-project',
            'serviceAccountsId': service_account_ref,
        },
        collection='iam.projects.serviceAccounts.keys')
    return None, key_ref

  def runCommand(self, control_plane_sa=None, broker_sa=None, sources_sa=None):
    args = [
        '--platform=gke',
        '--cluster=cluster-1',
        '--cluster-location=us-central1-a',
    ]
    if control_plane_sa:
      args.append('--service-account={}'.format(control_plane_sa))
    if broker_sa:
      args.append('--broker-service-account={}'.format(broker_sa))
    if sources_sa:
      args.append('--sources-service-account={}'.format(sources_sa))
    self.Run('events init {}'.format(' '.join(args)))

  def assertCommandSucceeded(self, control_plane_sa=None, broker_sa=None,
                             sources_sa=None):
    # This method contains general assertions that should hold true for
    # all successful invocations.
    self.AssertErrContains(
        'Initialized cluster [cluster-1] for Cloud Run eventing')

    self.assertOnlyDefaultServiceAccountsCreated(
        control_plane_sa, broker_sa, sources_sa)
    self.assertOnlyDefaultServiceAccountsHadRolesBound(
        control_plane_sa, broker_sa, sources_sa)
    self.assertKeysAdded(
        control_plane_sa, broker_sa, sources_sa)
    self.operations.MarkClusterInitialized.assert_called_once_with()

  def assertOnlyDefaultServiceAccountsCreated(
      self, control_plane_sa=None, broker_sa=None, sources_sa=None):

    expected_creations = []
    if control_plane_sa is None:
      expected_creations.append(
          mock.call('cloud-run-events',
                    'Cloud Run Events',
                    'Cloud Run Events on-cluster Infrastructure')
      )

    if broker_sa is None:
      expected_creations.append(
          mock.call('cloud-run-events-broker',
                    'Cloud Run Events Broker',
                    'Cloud Run Events on-cluster Broker')
      )

    if sources_sa is None:
      expected_creations.append(
          mock.call('cloud-run-events-sources',
                    'Cloud Run Events Sources',
                    'Cloud Run Events on-cluster Sources')
      )

    self.get_or_create_service_account.assert_has_calls(expected_creations)
    self.assertEqual(self.get_or_create_service_account.call_count,
                     len(expected_creations))

  def assertOnlyDefaultServiceAccountsHadRolesBound(
      self, control_plane_sa=None, broker_sa=None, sources_sa=None):

    control_plane_ref = self._registry.Parse(
        control_plane_sa or _AccountToEmail('cloud-run-events'),
        params={'projectsId': '-'},
        collection=core_iam_util.SERVICE_ACCOUNTS_COLLECTION)
    broker_ref = self._registry.Parse(
        broker_sa or _AccountToEmail('cloud-run-events-broker'),
        params={'projectsId': '-'},
        collection=core_iam_util.SERVICE_ACCOUNTS_COLLECTION)
    sources_ref = self._registry.Parse(
        sources_sa or _AccountToEmail('cloud-run-events-sources'),
        params={'projectsId': '-'},
        collection=core_iam_util.SERVICE_ACCOUNTS_COLLECTION)

    # A binding call is always made, but when a default service account is
    # used, the last arg is True to indicate bind, otherwise False.
    expected_bindings = [
        mock.call(
            control_plane_ref,
            [
                'roles/cloudscheduler.admin',
                'roles/logging.configWriter',
                'roles/logging.privateLogViewer',
                'roles/pubsub.admin',
                'roles/storage.admin',
            ],
            control_plane_sa is None,
        ),
        mock.call(
            broker_ref,
            [
                'roles/pubsub.editor',
            ],
            broker_sa is None,
        ),
        mock.call(
            sources_ref,
            [
                'roles/pubsub.editor',
            ],
            sources_sa is None,
        ),
    ]
    self.bind_missing_roles.assert_has_calls(expected_bindings)
    self.assertEqual(self.bind_missing_roles.call_count, len(expected_bindings))

  def assertKeysAdded(
      self, control_plane_sa=None, broker_sa=None, sources_sa=None):
    self.AssertErrContains(
        'Added key [somehexvalue] to cluster for [{}]'.format(
            control_plane_sa or _AccountToEmail('cloud-run-events')))
    self.AssertErrContains(
        'Added key [somehexvalue] to cluster for [{}]'.format(
            broker_sa or _AccountToEmail('cloud-run-events-broker')))
    self.AssertErrContains(
        'Added key [somehexvalue] to cluster for [{}]'.format(
            sources_sa or _AccountToEmail('cloud-run-events-sources')))

  def testEventTypesFailFailNonGKE(self):
    """This command is only for initializing a cluster."""
    with self.assertRaises(exceptions.UnsupportedArgumentError):
      self.Run('events init --platform=managed --region=us-central1')
    self.AssertErrContains(
        'This command is only available with Cloud Run for Anthos.')

  def testInitWithPromptYes(self):
    """Tests successful init with success message on prompt confirmation."""
    self.WriteInput('y\n')
    self.runCommand()
    self.assertCommandSucceeded()

  def testInitWithPromptNoFails(self):
    """Tests failed init without prompt confirmation."""
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.runCommand()

  def testInitNoPrompt(self):
    """Tests successful init with success message on no prompting allowed."""
    self.is_interactive.return_value = False
    self.runCommand()
    self.assertCommandSucceeded()

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
    self.runCommand()
    self.assertCommandSucceeded()
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
    self.runCommand()
    self.assertCommandSucceeded()
    mock_batch_enable_api_call.assert_called_once_with(
        'fake-project', ['cloudresourcemanager.googleapis.com',
                         'cloudscheduler.googleapis.com'])
    mock_wait_operation.assert_called_once_with(
        mock_batch_enable_api_call.return_value.name, serviceusage.GetOperation)

  def testControlPlaneServiceAccountCanBeOverridden(self):
    service_account = 'existing-control-plane@gserviceaccount.com'
    self.runCommand(control_plane_sa=service_account)
    self.assertCommandSucceeded(control_plane_sa=service_account)
    self.AssertErrContains(service_account)

  def testBrokerServiceAccountCanBeOverridden(self):
    service_account = 'existing-broker@gserviceaccount.com'
    self.runCommand(broker_sa=service_account)
    self.assertCommandSucceeded(broker_sa=service_account)
    self.AssertErrContains(service_account)

  def testSourcesServiceAccountCanBeOverridden(self):
    service_account = 'existing-sources@gserviceaccount.com'
    self.runCommand(sources_sa=service_account)
    self.assertCommandSucceeded(sources_sa=service_account)
    self.AssertErrContains(service_account)

  def testUserPromptedIfAlreadyInitializedNoReinit(self):
    self.operations.IsClusterInitialized.return_value = True
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.runCommand()
    self.AssertErrContains('Would you like to re-run initialization?')

  def testUserPromptedIfAlreadyInitializedWithReinit(self):
    self.operations.IsClusterInitialized.return_value = True
    self.WriteInput('y\n')
    self.runCommand()
    self.AssertErrContains('Would you like to re-run initialization?')
    self.assertCommandSucceeded()

  def testInitializedMessage(self):
    message = init._InitializedMessage(self.track, 'my-cluster')
    self.assertEqual(
        message,
        ('Initialized cluster [my-cluster] for Cloud Run eventing. '
         'Next, initialize the namespace(s) you plan to use and create a '
         'broker via `gcloud alpha events namespaces init` and `gcloud alpha '
         'events brokers create`.'))


def _MockService(name):
  service = mock.Mock()
  service.config.name = name
  return service


def _MockGetOrCreateServiceAccount(name, display_name, description):
  del display_name
  del description
  return _AccountToEmail(name)


def _AccountToEmail(name):
  return '{}@fake-project.iam.gserviceaccount.com'.format(name)
