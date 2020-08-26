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

from googlecloudsdk.api_lib.events import custom_resource_definition
from googlecloudsdk.api_lib.events import source
from googlecloudsdk.api_lib.events import trigger
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.events import exceptions
from tests.lib.surface.events import base


class TriggersDescribeTestAlpha(base.EventsBase):

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
    self.source = source.Source.New(self.mock_client, 'default',
                                    'CloudPubSubSource',
                                    'sources.eventing.knative.dev')
    self.source.name = 'my-source'
    self.source.set_sink('my-broker', self.api_version)
    self.source.spec.project = 'fake-project'
    self.source.spec.topic = 'my-topic'
    self.operations.GetSource.return_value = self.source

  def _MakeTrigger(self, source_obj):
    """Creates a trigger and assigns it as output to GetTrigger."""
    self.trigger = trigger.Trigger.New(self.mock_client, 'default')
    self.trigger.name = 'my-trigger'
    if self.api_name == 'anthosevents':
      self.trigger.status.conditions = [
          self.messages.Condition(type='Ready', status='True')
      ]
    else:
      self.trigger.status.conditions = [
          self.messages.TriggerCondition(type='Ready', status='True')
      ]
    self.trigger.dependency = source_obj
    self.trigger.filter_attributes[
        trigger.EVENT_TYPE_FIELD] = 'com.google.event.type'
    self.trigger.subscriber = 'my-service'
    self.operations.GetTrigger.return_value = self.trigger

  def testDescribeManaged(self):
    """Trigger and source spec are both described with the default output."""
    self._MakeSourceCrd()
    self._MakeSource()
    self._MakeTrigger(self.source)
    self.Run('events triggers describe my-trigger --region=us-central1')

    self.operations.GetTrigger.assert_called_once_with(
        self._TriggerRef('my-trigger', 'fake-project'))
    self.operations.GetSource.assert_called_once_with(
        self._SourceRef('my-source', 'cloudpubsubsources', 'default'),
        self.source_crd)
    self.AssertOutputContains('name: my-trigger')
    self.AssertOutputContains(
        """filter:
             attributes:
               type: com.google.event.type""",
        normalize_space=True)
    self.AssertOutputContains(
        """subscriber:
            ref:
              apiVersion: serving.knative.dev/v1alpha1
              kind: Service
              name: my-service""",
        normalize_space=True)
    self.AssertOutputContains(
        """sink:
            ref:
              apiVersion: eventing.knative.dev/v1alpha1
              kind: Broker
              name: my-broker""",
        normalize_space=True)
    self.AssertOutputContains('topic: my-topic')

  def testDescribeGke(self):
    """Trigger and source spec are both described with the default output."""
    self._MakeSourceCrd()
    self._MakeSource()
    self._MakeTrigger(self.source)
    self.Run('events triggers describe my-trigger --platform=gke '
             '--cluster=cluster-1 --cluster-location=us-central1-a')

    self.operations.GetTrigger.assert_called_once_with(
        self._TriggerRef('my-trigger', 'default'))
    self.operations.GetSource.assert_called_once_with(
        self._SourceRef('my-source', 'cloudpubsubsources', 'default'),
        self.source_crd)
    self.AssertOutputContains('name: my-trigger')
    self.AssertOutputContains(
        """filter:
             attributes:
               type: com.google.event.type""",
        normalize_space=True)
    self.AssertOutputContains(
        """subscriber:
            ref:
              apiVersion: serving.knative.dev/v1alpha1
              kind: Service
              name: my-service""",
        normalize_space=True)
    self.AssertOutputContains(
        """sink:
            ref:
              apiVersion: eventing.knative.dev/{}
              kind: Broker
              name: my-broker""".format(self.api_version),
        normalize_space=True)
    self.AssertOutputContains('topic: my-topic')

  def testDescribeFailsIfMissing(self):
    """Error is raised when trigger is not found."""
    self.operations.GetTrigger.return_value = None
    with self.assertRaises(exceptions.TriggerNotFound):
      self.Run('events triggers describe my-trigger --platform=gke '
               '--cluster=cluster-1 --cluster-location=us-central1-a')
    self.AssertErrContains('Trigger [my-trigger] not found.')

  def testDescribeWarnsIfNoSource(self):
    """Warning is shown when a source is not found."""
    self._MakeSourceCrd()
    self._MakeSource()
    self.operations.GetSource.return_value = None
    self._MakeTrigger(self.source)
    self.Run('events triggers describe my-trigger --platform=gke '
             '--cluster=cluster-1 --cluster-location=us-central1-a')
    self.AssertErrContains('No matching event source')


class TriggersDescribeTestAlphaAnthos(TriggersDescribeTestAlpha):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_name = 'anthosevents'
    self.api_version = 'v1beta1'

  def testDescribeManaged(self):
    pass
