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


from googlecloudsdk.api_lib.events import custom_resource_definition
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.events import util
from tests.lib.surface.run import base


class UtilTest(base.ServerlessBase):

  def _MakeSourceCrds(self, num_sources, num_events_per_source):
    """Creates source CRDs with event types."""
    self.source_crds = [
        custom_resource_definition.SourceCustomResourceDefinition.New(
            self.mock_crd_client, 'fake-project')
        for _ in range(num_sources)]
    for i, crd in enumerate(self.source_crds):
      event_types = []
      for j in range(num_events_per_source):
        event_types.append(
            self._EventTypeAdditionalProperty(
                'e{}-{}'.format(i, j), 'desc{}{}'.format(i, j),
                'google.source.{}.event.type.{}'.format(i, j)))
      crd.spec.validation = self.crd_messages.CustomResourceValidation(
          openAPIV3Schema=self._SourceSchemaProperties('Source{}'.format(i),
                                                       event_types))
    # self.event_types is all event types across all sources ordered by
    # source then event type (e.g. [s.0.et.0, s.0.et.1, s.1.et.0, etc.])
    self.event_types = []
    for crd in self.source_crds:
      self.event_types.extend(crd.event_types)

  def testEventTypeFromPattern(self):
    self._MakeSourceCrds(num_sources=2, num_events_per_source=2)
    self.assertEqual(
        self.event_types[2],
        util.EventTypeFromPattern(self.source_crds,
                                  'google.source.1.event.type.0'))

  def testEventTypeFromPatternNotFound(self):
    self._MakeSourceCrds(num_sources=2, num_events_per_source=2)
    with self.assertRaises(exceptions.EventTypeNotFound):
      util.EventTypeFromPattern(self.source_crds, 'nonexistent.event.type')

  def testEventTypeFromPatternNoEventTypes(self):
    self._MakeSourceCrds(num_sources=2, num_events_per_source=0)
    with self.assertRaises(exceptions.EventTypeNotFound):
      util.EventTypeFromPattern(self.source_crds,
                                'google.source.0.event.type.0')

  def testEventTypeFromPatternNoSources(self):
    self._MakeSourceCrds(num_sources=0, num_events_per_source=0)
    with self.assertRaises(exceptions.EventTypeNotFound):
      util.EventTypeFromPattern(self.source_crds,
                                'google.source.0.event.type.0')
