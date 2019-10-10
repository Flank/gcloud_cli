# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Unit tests for the `events triggers describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.events import trigger
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.events import exceptions
from tests.lib.surface.run import base


class TriggersDescribeTestAlpha(base.ServerlessSurfaceBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _MakeTrigger(self):
    """Creates a trigger and assigns it as output to GetTrigger."""
    self.trigger = trigger.Trigger.New(
        self.mock_serverless_client, 'default')
    self.trigger.name = 'my-trigger'
    self.trigger.status.conditions = [
        self.serverless_messages.TriggerCondition(
            type='Ready',
            status='True')
    ]
    self.trigger.filter_attributes[
        trigger.EVENT_TYPE_FIELD] = 'com.google.event.type'
    self.trigger.subscriber = 'my-service'
    self.operations.GetTrigger.return_value = self.trigger

  def testTriggersFailNonGKE(self):
    """Triggers are not yet supported on managed Cloud Run."""
    with self.assertRaises(exceptions.UnsupportedArgumentError):
      self.Run('events triggers describe my-trigger --region=us-central1')
    self.AssertErrContains(
        'Events are only available with Cloud Run for Anthos.')

  def testTriggersDescribe(self):
    """Trigger and source spec are both described with the default output."""
    self._MakeTrigger()
    self.Run('events triggers describe my-trigger --platform=gke '
             '--cluster=cluster-1 --cluster-location=us-central1-a')
    self.operations.GetTrigger.assert_called_once_with(
        self._TriggerRef('my-trigger', 'default'))
    self.AssertOutputContains('name: my-trigger')
    self.AssertOutputContains(
        """filter:
             attributes:
               type: com.google.event.type""", normalize_space=True)
    self.AssertOutputContains(
        """subscriber:
            ref:
              apiVersion: serving.knative.dev/v1alpha1
              kind: Service
              name: my-service""", normalize_space=True)

  def testTriggersDescribeFailsIfMissing(self):
    """Error is raised when trigger is not found."""
    self.operations.GetTrigger.return_value = None
    with self.assertRaises(exceptions.TriggerNotFound):
      self.Run('events triggers describe my-trigger --platform=gke '
               '--cluster=cluster-1 --cluster-location=us-central1-a')
    self.AssertErrContains('Trigger [my-trigger] not found.')
