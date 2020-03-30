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
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib.surface.run import base


class InitTestAlpha(base.ServerlessSurfaceBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.service_account = 'svcacc@gserviceaccount.com'
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
    self.Run('events init --service-account=svcacc@gserviceaccount.com '
             '--platform=gke --cluster=cluster-1 '
             '--cluster-location=us-central1-a')
    self.AssertErrContains(
        'Initialized cluster [cluster-1] for Cloud Run eventing')
    self.AssertErrContains(self.service_account)
    self.AssertErrContains(self.service_account_key_ref.Name())

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
    self.Run('events init --service-account=svcacc@gserviceaccount.com '
             '--platform=gke --cluster=cluster-1 '
             '--cluster-location=us-central1-a')
    self.AssertErrContains(
        'Initialized cluster [cluster-1] for Cloud Run eventing')
    self.AssertErrContains(self.service_account)
    self.AssertErrContains(self.service_account_key_ref.Name())

  def testMinRequiredMissingFails(self):
    self.StartObjectPatch(
        iam_util,
        'GetProjectRolesForServiceAccount',
        return_value=set())
    with self.assertRaises(exceptions.ServiceAccountMissingRequiredPermissions):
      self.Run('events init --service-account=svcacc@gserviceaccount.com '
               '--platform=gke --cluster=cluster-1 '
               '--cluster-location=us-central1-a')

  def testMinRequiredRolesShowsMessage(self):
    self.StartObjectPatch(
        iam_util,
        'GetProjectRolesForServiceAccount',
        return_value=set(['roles/pubsub.editor']))
    self.WriteInput('y\n')
    self.Run('events init --service-account=svcacc@gserviceaccount.com '
             '--platform=gke --cluster=cluster-1 '
             '--cluster-location=us-central1-a')
    self.AssertErrContains(
        'The service account has the minimum necessary project permissions')
    self.AssertErrContains(
        'Initialized cluster [cluster-1] for Cloud Run eventing')
    self.AssertErrContains(self.service_account)
    self.AssertErrContains(self.service_account_key_ref.Name())

  def testMinRequiredAndAllOptionalNoMessage(self):
    self.StartObjectPatch(
        iam_util,
        'GetProjectRolesForServiceAccount',
        return_value=set([
            'roles/pubsub.editor', 'roles/storage.admin',
            'roles/cloudscheduler.admin', 'roles/pubsub.admin',
            'roles/logging.configWriter', 'roles/logging.privateLogViewer'
        ]))
    self.WriteInput('y\n')
    self.Run('events init --service-account=svcacc@gserviceaccount.com '
             '--platform=gke --cluster=cluster-1 '
             '--cluster-location=us-central1-a')
    self.AssertErrNotContains(
        'The service account has the minimum necessary project permissions')
    self.AssertErrContains(
        'Initialized cluster [cluster-1] for Cloud Run eventing')
    self.AssertErrContains(self.service_account)
    self.AssertErrContains(self.service_account_key_ref.Name())
