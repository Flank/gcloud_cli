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
"""Unit tests for the `events triggers create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import random

from googlecloudsdk.api_lib.events import custom_resource_definition
from googlecloudsdk.api_lib.events import source
from googlecloudsdk.api_lib.events import trigger
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.events import flags
from googlecloudsdk.command_lib.events import util
from tests.lib.surface.run import base

import mock


class TriggersCreateTestAlpha(base.ServerlessSurfaceBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    def _GetParameters(args, unused_event_type):
      parameters = {}
      parameters.update(args.parameters)
      parameters.update(args.parameters_from_file)
      parameters.update(flags._ParseSecretParameters(args))
      return parameters

    self.validate_params = self.StartObjectPatch(
        flags,
        'GetAndValidateParameters',
        side_effect=_GetParameters)
    self.operations.GetTrigger.return_value = None
    self.operations.GetSource.return_value = None

  def _MakeEventType(self):
    """Creates a source CRD with event type and returns it on ListSourceCRDs."""
    self.source_crd = (
        custom_resource_definition.SourceCustomResourceDefinition.New(
            self.mock_crd_client, 'fake-project'))
    self.source_crd.spec.group = 'events.api.group'
    self.source_crd.spec.names = (
        self.crd_messages.CustomResourceDefinitionNames(
            kind='PubSub', plural='pubsubs'))
    self.event_type = custom_resource_definition.EventType(
        self.source_crd,
        type='google.source.my.type',
        description='desc')
    self.source_crd.event_types = [self.event_type]
    self.operations.ListSourceCustomResourceDefinitions.return_value = [
        self.source_crd
    ]

  def _MakeSource(self, source_crd):
    """Creates a source object of the type specified by source_crd."""
    self.source = source.Source.New(self.mock_serverless_client,
                                    'default',
                                    source_crd.source_kind,
                                    source_crd.source_api_category)
    self.source.name = 'source-for-my-trigger'

  def _MakeTrigger(self, source_obj, event_type):
    """Creates a trigger object with the given source dependency and event type."""
    self.trigger = trigger.Trigger.New(self.mock_serverless_client, 'default')
    self.trigger.name = 'my-trigger'
    self.trigger.dependency = source_obj
    # TODO(b/141617597): Set to str(random.random()) without prepended string
    self.trigger.filter_attributes[trigger.SOURCE_TRIGGER_LINK_FIELD] = (
        'link{}'.format(random.random()))
    self.trigger.filter_attributes[trigger.EVENT_TYPE_FIELD] = event_type.type

  def testTriggersFailNonGKE(self):
    """Triggers are not yet supported on managed Cloud Run."""
    with self.assertRaises(exceptions.UnsupportedArgumentError):
      self.Run('events triggers create my-trigger --region=us-central1 '
               '--target-service=my-service --type=com.google.event.type')
    self.AssertErrContains(
        'Events are only available with Cloud Run for Anthos.')

  def testTriggersCreate(self):
    """Tests successful create with default output format."""
    self._MakeEventType()
    self._MakeSource(self.source_crd)
    self._MakeTrigger(self.source, self.event_type)
    self.operations.CreateTrigger.return_value = self.trigger
    self.Run('events triggers create my-trigger --platform=gke '
             '--cluster=cluster-1 --cluster-location=us-central1-a '
             '--target-service=my-service --type=google.source.my.type')

    self.validate_params.assert_called_once_with(mock.ANY, self.event_type)
    self.source.name = 'source-for-my-trigger'
    self.operations.CreateTriggerAndSource.assert_called_once_with(
        None,
        self._TriggerRef('my-trigger', 'default'),
        self._NamespaceRef(project='default'),
        self.source,
        self.event_type,
        {},
        'default',
        'my-service',
        mock.ANY,
    )
    self.AssertErrContains('Initializing trigger...')
    self.AssertErrContains('"status": "SUCCESS"')

  def testTriggersCreateWithParameters(self):
    """Tests successful create with default output format."""
    self._MakeEventType()
    self._MakeSource(self.source_crd)
    self._MakeTrigger(self.source, self.event_type)
    self.Run('events triggers create my-trigger --platform=gke '
             '--cluster=cluster-1 --cluster-location=us-central1-a '
             '--target-service=my-service --type=google.source.my.type '
             '--parameters="someParam=value,otherParam=other value" '
             '--secrets=someSecret=name:key ')

    self.validate_params.assert_called_once_with(mock.ANY, self.event_type)
    self.source.name = 'source-for-my-trigger'
    self.operations.CreateTriggerAndSource.assert_called_once_with(
        None,
        self._TriggerRef('my-trigger', 'default'),
        self._NamespaceRef(project='default'),
        self.source,
        self.event_type,
        {
            'someParam': 'value',
            'otherParam': 'other value',
            'someSecret': {
                'name': 'name',
                'key': 'key'
            }
        },
        'default',
        'my-service',
        mock.ANY,
    )
    self.AssertErrContains('Initializing trigger...')
    self.AssertErrContains('"status": "SUCCESS"')

  def testTriggersCreateExistingTrigger(self):
    """Tests successful create with default output format."""
    self._MakeEventType()
    self._MakeSource(self.source_crd)
    self._MakeTrigger(self.source, self.event_type)
    self.operations.GetTrigger.return_value = self.trigger
    self.Run('events triggers create my-trigger --platform=gke '
             '--cluster=cluster-1 --cluster-location=us-central1-a '
             '--target-service=my-service --type=google.source.my.type')

    self.validate_params.assert_called_once_with(mock.ANY, self.event_type)
    self.source.name = 'source-for-my-trigger'
    self.operations.CreateTriggerAndSource.assert_called_once_with(
        self.trigger,
        self._TriggerRef('my-trigger', 'default'),
        self._NamespaceRef(project='default'),
        self.source,
        self.event_type,
        {},
        'default',
        'my-service',
        mock.ANY,
    )
    self.AssertErrContains('Initializing trigger...')
    self.AssertErrContains('"status": "SUCCESS"')

  def testTriggersCreateExistingTriggerFailsValidation(self):
    """Tests successful create with default output format."""
    self._MakeEventType()
    self._MakeSource(self.source_crd)
    self._MakeTrigger(self.source, self.event_type)
    self.operations.GetTrigger.return_value = self.trigger
    self.StartObjectPatch(util, 'ValidateTrigger', side_effect=AssertionError)
    with self.assertRaises(exceptions.TriggerCreationError):
      self.Run('events triggers create my-trigger --platform=gke '
               '--cluster=cluster-1 --cluster-location=us-central1-a '
               '--target-service=my-service --type=google.source.my.type')
    self.AssertErrContains('Trigger [my-trigger] already exists')

  def testTriggersCreateFailsIfExistingTriggerAndSource(self):
    """Tests failed create if both trigger and source already exist."""
    self._MakeEventType()
    self._MakeSource(self.source_crd)
    self._MakeTrigger(self.source, self.event_type)
    self.operations.GetTrigger.return_value = self.trigger
    self.operations.GetSource.return_value = self.source

    with self.assertRaises(exceptions.TriggerCreationError):
      self.Run('events triggers create my-trigger --platform=gke '
               '--cluster=cluster-1 --cluster-location=us-central1-a '
               '--target-service=my-service --type=google.source.my.type')
    self.AssertErrContains('Trigger [my-trigger] already exists')
