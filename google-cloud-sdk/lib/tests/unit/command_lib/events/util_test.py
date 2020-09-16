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
"""Tests of the Eventflow API Client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import random

from googlecloudsdk.api_lib.events import custom_resource_definition
from googlecloudsdk.api_lib.events import source
from googlecloudsdk.api_lib.events import trigger
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.events import util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib.surface.events import base


class UtilTest(base.EventsBase):

  def _MakeSourceCrds(self, num_sources, num_event_types_per_source):
    """Creates source CRDs with event types."""
    source_crds = [
        custom_resource_definition.SourceCustomResourceDefinition.New(
            self.mock_crd_client, 'fake-project') for _ in range(num_sources)
    ]
    if hasattr(self, 'source_crds'):
      self.source_crds.extend(source_crds)
    else:
      self.source_crds = source_crds

    if not hasattr(self, 'event_types'):
      self.event_types = []
    for i, crd in enumerate(source_crds):
      crd.spec.group = 'events.api.group.{}'.format(i)
      # Keep i == 0 to a valid source kind (CloudPubSubSource), but all others
      # we'll append the index to keep the source kinds unique
      source_kind = 'CloudPubSubSource' if i == 0 else 'CloudPubSubSource{}'.format(
          i)
      crd.spec.names = (
          self.crd_messages.CustomResourceDefinitionNames(
              kind=source_kind, plural='cloudpubsubsources'))
      event_types = []
      for j in range(num_event_types_per_source):
        event_types.append(
            custom_resource_definition.EventType(
                crd,
                type='google.source.{}.event.type.{}'.format(i, j),
                description='desc{}{}'.format(i, j)))
      crd.event_types = event_types
      self.event_types.extend(event_types)

  def _MakeSource(self, source_crd):
    """Creates a source object of the type specified by source_crd."""
    self.source = source.Source.New(self.mock_client, 'source-namespace',
                                    source_crd.source_kind,
                                    source_crd.source_api_category)
    self.source.name = 'source-for-my-trigger'

  def _MakeTrigger(self, source_obj, event_type):
    """Creates a trigger object with the given source dependency and event type."""
    self.trigger = trigger.Trigger.New(self.mock_client, 'default')
    self.trigger.name = 'my-trigger'
    self.trigger.dependency = source_obj
    # TODO(b/141617597): Set to str(random.random()) without prepended string
    self.trigger.filter_attributes[trigger.SOURCE_TRIGGER_LINK_FIELD] = (
        'link{}'.format(random.random()))
    self.trigger.filter_attributes[trigger.EVENT_TYPE_FIELD] = event_type.type

  def testEventTypeFromTypeString(self):
    self._MakeSourceCrds(num_sources=2, num_event_types_per_source=2)
    self.assertEqual(
        self.event_types[2],
        util.EventTypeFromTypeString(self.source_crds,
                                     'google.source.1.event.type.0'))

  def testEventTypeFromTypeStringNotFound(self):
    self._MakeSourceCrds(num_sources=2, num_event_types_per_source=2)
    with self.assertRaises(exceptions.EventTypeNotFound):
      util.EventTypeFromTypeString(self.source_crds, 'nonexistent.event.type')

  def testEventTypeFromTypeStringNoEventTypes(self):
    self._MakeSourceCrds(num_sources=2, num_event_types_per_source=0)
    with self.assertRaises(exceptions.EventTypeNotFound):
      util.EventTypeFromTypeString(self.source_crds,
                                   'google.source.0.event.type.0')

  def testEventTypeFromTypeStringNoSources(self):
    self._MakeSourceCrds(num_sources=0, num_event_types_per_source=0)
    with self.assertRaises(exceptions.EventTypeNotFound):
      util.EventTypeFromTypeString(self.source_crds,
                                   'google.source.0.event.type.0')

  def testEventTypeFromTypeStringFilterSource(self):
    self._MakeSourceCrds(num_sources=2, num_event_types_per_source=2)
    self.assertEqual(
        self.event_types[2],
        util.EventTypeFromTypeString(self.source_crds,
                                     'google.source.1.event.type.0',
                                     'CloudPubSubSource1'))

  def testEventTypeFromTypeStringMultipleMatchesNoPrompt(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self._MakeSourceCrds(num_sources=1, num_event_types_per_source=2)
    self._MakeSourceCrds(num_sources=1, num_event_types_per_source=2)
    with self.assertRaises(exceptions.MultipleEventTypesFound):
      util.EventTypeFromTypeString(self.source_crds,
                                   'google.source.0.event.type.0')

  def testEventTypeFromTypeStringMultipleMatchesWithPrompt(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self._MakeSourceCrds(num_sources=1, num_event_types_per_source=2)
    self._MakeSourceCrds(num_sources=1, num_event_types_per_source=2)
    self.WriteInput('2')
    self.assertEqual(
        self.event_types[1],
        util.EventTypeFromTypeString(self.source_crds,
                                     'google.source.0.event.type.1'))

  def testGetSourceRefAndCrdForTrigger(self):
    self._MakeSourceCrds(num_sources=1, num_event_types_per_source=1)
    self._MakeSource(self.source_crds[0])
    self._MakeTrigger(self.source, self.event_types[0])

    expected = resources.REGISTRY.Parse(
        'source-for-my-trigger',
        params={'namespacesId': 'source-namespace'},
        collection='anthosevents.namespaces.cloudpubsubsources',
        api_version=self.api_version)
    self.assertEqual((expected, self.source_crds[0]),
                     util.GetSourceRefAndCrdForTrigger(self.trigger,
                                                       self.source_crds, True))

  def testValidateTriggerSucceeds(self):
    self._MakeSourceCrds(num_sources=1, num_event_types_per_source=1)
    self._MakeSource(self.source_crds[0])
    self._MakeTrigger(self.source, self.event_types[0])
    util.ValidateTrigger(self.trigger, self.source, self.event_types[0])

  def testValidateTriggerNoDependency(self):
    self._MakeSourceCrds(num_sources=1, num_event_types_per_source=1)
    self._MakeSource(self.source_crds[0])
    self._MakeTrigger(self.source, self.event_types[0])
    del self.trigger.annotations[trigger.DEPENDENCY_ANNOTATION_FIELD]
    with self.assertRaises(AssertionError):
      util.ValidateTrigger(self.trigger, self.source, self.event_types[0])

  def testValidateTriggerBadDependency(self):
    self._MakeSourceCrds(num_sources=1, num_event_types_per_source=1)
    self._MakeSource(self.source_crds[0])
    self._MakeTrigger(self.source, self.event_types[0])
    self.trigger.annotations[trigger.DEPENDENCY_ANNOTATION_FIELD] = (
        '{"name": "something else"}')
    with self.assertRaises(AssertionError):
      util.ValidateTrigger(self.trigger, self.source, self.event_types[0])

  def testValidateTriggerNoEventTypeField(self):
    self._MakeSourceCrds(num_sources=1, num_event_types_per_source=1)
    self._MakeSource(self.source_crds[0])
    self._MakeTrigger(self.source, self.event_types[0])
    del self.trigger.filter_attributes[trigger.EVENT_TYPE_FIELD]
    with self.assertRaises(AssertionError):
      util.ValidateTrigger(self.trigger, self.source, self.event_types[0])

  def testValidateTriggerBadEventTypeField(self):
    self._MakeSourceCrds(num_sources=1, num_event_types_per_source=1)
    self._MakeSource(self.source_crds[0])
    self._MakeTrigger(self.source, self.event_types[0])
    self.trigger.filter_attributes[trigger.EVENT_TYPE_FIELD] = 'bla'
    with self.assertRaises(AssertionError):
      util.ValidateTrigger(self.trigger, self.source, self.event_types[0])
