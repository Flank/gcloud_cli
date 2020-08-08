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
"""Unit tests for the `events triggers delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.events import custom_resource_definition
from googlecloudsdk.api_lib.events import source
from googlecloudsdk.api_lib.events import trigger
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.console import console_io
from tests.lib.surface.events import base


class TriggersDeleteTestAlpha(base.EventsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _MakeSourceCrd(self):
    """Creates a source CRD and assigns it as output to ListSourceCRD."""
    self.source_crd = (
        custom_resource_definition.SourceCustomResourceDefinition.New(
            self.mock_crd_client, 'fake-project'))
    self.source_crd.spec.names = (
        self.crd_messages.CustomResourceDefinitionNames(
            kind='CloudPubSubSource', plural='cloudpubsubsources'))
    self.operations.ListSourceCustomResourceDefinitions.return_value = [
        self.source_crd
    ]

  def _MakeSource(self):
    """Creates a source and assigns it as output to GetSource."""
    self.source = source.Source.New(self.mock_client, 'fake-project',
                                    'CloudPubSubSource',
                                    'sources.eventing.knative.dev')
    self.source.name = 'my-source'
    self.source.set_sink('my-broker', 'v1alpha1')
    self.source.spec.project = 'fake-project'
    self.source.spec.topic = 'my-topic'
    self.operations.GetSource.return_value = self.source

  def _MakeTrigger(self, source_obj):
    """Creates a trigger and assigns it as output to GetTrigger."""
    self.trigger = trigger.Trigger.New(self.mock_client, 'default')
    self.trigger.name = 'my-trigger'
    self.trigger.status.conditions = [
        self.messages.TriggerCondition(type='Ready', status='True')
    ]
    self.trigger.dependency = source_obj
    self.trigger.filter_attributes[
        trigger.EVENT_TYPE_FIELD] = 'com.google.event.type'
    self.trigger.subscriber = 'my-service'
    self.operations.GetTrigger.return_value = self.trigger

  def testDeleteManaged(self):
    """Tests the source is manually deleted for requests against managed."""
    self._MakeSourceCrd()
    self._MakeSource()
    self._MakeTrigger(self.source)
    self.WriteInput('Y\n')
    self.Run('events triggers delete my-trigger --region=us-central1')

    self.operations.DeleteSource.assert_called_once_with(
        self._SourceRef('my-source', 'cloudpubsubsources', 'fake-project'),
        self.source_crd)
    self.operations.DeleteTrigger.assert_called_once_with(
        self._TriggerRef('my-trigger', 'fake-project'))
    self.AssertErrContains('Deleted trigger [my-trigger].')

  def testDeleteGke(self):
    """Tests successful delete with default output format."""
    self.WriteInput('Y\n')
    self.Run('events triggers delete my-trigger --platform=gke '
             '--cluster=cluster-1 --cluster-location=us-central1-a')

    self.operations.DeleteTrigger.assert_called_once_with(
        self._TriggerRef('my-trigger', 'default'))
    self.AssertErrContains('Deleted trigger [my-trigger].')

  def testDeleteFailsIfUnattended(self):
    """Tests that delete fails if console is unattended."""
    self.is_interactive.return_value = False
    with self.assertRaises(console_io.UnattendedPromptError):
      self.Run('events triggers delete my-trigger --platform=gke '
               '--cluster=cluster-1 --cluster-location=us-central1-a')
    self.operations.DeleteTrigger.assert_not_called()
