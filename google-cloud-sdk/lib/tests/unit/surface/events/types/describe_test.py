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
"""Unit tests for the `events types describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.events import custom_resource_definition
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.events import exceptions
from tests.lib.surface.run import base


class TypesDescribeTestAlpha(base.ServerlessSurfaceBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _MakeSourceCrds(self, num_sources, num_event_types_per_source,
                      num_properties_per_source):
    """Creates source CRDs and assigns them as the output to ListSourceCRD."""
    self.source_crds = [
        custom_resource_definition.SourceCustomResourceDefinition.New(
            self.mock_crd_client, 'fake-project') for _ in range(num_sources)
    ]
    for i, crd in enumerate(self.source_crds):
      event_types = []
      for j in range(num_event_types_per_source):
        event_types.append(
            self._EventTypeAdditionalProperty(
                'e{}-{}'.format(i, j), 'desc{}{}'.format(i, j),
                'google.source.{}.et.{}'.format(i, j)))
      spec_properties = [
          self._SpecParameterAdditionalProperty('p{}-{}'.format(i, j), 'string',
                                                'pdesc{}{}'.format(i, j))
          for j in range(num_properties_per_source)
      ]
      spec_properties.append(
          self._SpecParameterAdditionalProperty('pSecret', 'object',
                                                'pSecretdesc'))
      required_properties = [
          'p{}-{}'.format(i, j) for j in range(1, num_properties_per_source, 3)
      ]
      crd.spec.validation = self.crd_messages.CustomResourceValidation(
          openAPIV3Schema=self._SourceSchemaProperties(
              'Source{}'.format(i),
              event_types,
              spec_properties,
              required_properties,
          ))
    # self.event_types is all event types across all sources ordered by
    # source then event type (e.g. [s.0.et.0, s.0.et.1, s.1.et.0, etc.])
    self.event_types = []
    for crd in self.source_crds:
      self.event_types.extend(crd.event_types)
    self.operations.ListSourceCustomResourceDefinitions.return_value = (
        self.source_crds)

  def testEventTypesFailFailNonGKE(self):
    """Event Types are not yet supported on managed Cloud Run."""
    with self.assertRaises(exceptions.UnsupportedArgumentError):
      self.Run('events types describe google.source.0.et.0 '
               '--platform=managed --region=us-central1')
    self.AssertErrContains(
        'Events are only available with Cloud Run for Anthos.')

  def testDescribe(self):
    """Tests successful describe with default output format."""
    self._MakeSourceCrds(
        num_sources=2,
        num_event_types_per_source=3,
        num_properties_per_source=3)
    self.Run('events types describe google.source.0.et.0 --platform=gke '
             '--cluster=cluster-1 --cluster-location=us-central1-a')
    self.AssertOutputEquals(
        """category: Source0
        description: desc00
        schema: https://somewhere.over.the.rainbow.json
        type: google.source.0.et.0

        Parameter(s) to create a trigger for this event type:
        REQUIRED PARAMETER DESCRIPTION
        Yes p0-1 pdesc01
            p0-0 pdesc00
            p0-2 pdesc02

        Secret parameter(s) to create a trigger for this event type:
        REQUIRED PARAMETER DESCRIPTION
         pSecret pSecretdesc
        """,
        normalize_space=True)

  def testDescribeFailsUnknownEventType(self):
    """Tests describe fails when the event type is not found."""
    self._MakeSourceCrds(
        num_sources=2,
        num_event_types_per_source=3,
        num_properties_per_source=3)
    self.operations.GetService.return_value = None
    with self.assertRaises(exceptions.EventTypeNotFound):
      self.Run('events types describe bad.event.type --platform=gke '
               '--cluster=cluster-1 --cluster-location=us-central1-a')
    self.AssertErrContains('Unknown event type: bad.event.type.')
