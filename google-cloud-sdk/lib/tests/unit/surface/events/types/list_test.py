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
"""Unit tests for the `events types list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.events import custom_resource_definition
from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.events import base


class TypesListTestAlpha(base.EventsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _MakeEventTypes(self, num_sources, num_event_types_per_source):
    """Creates source CRDs with event types and assigns them to ListSourceCRDs."""
    self.source_crds = [
        custom_resource_definition.SourceCustomResourceDefinition.New(
            self.mock_crd_client, 'fake-project')
        for _ in range(num_sources)]
    self.event_types = []
    for i, crd in enumerate(self.source_crds):
      crd.spec.names = self.crd_messages.CustomResourceDefinitionNames(
          kind='SourceKind{}'.format(i))
      event_types = []
      for j in range(num_event_types_per_source):
        event_types.append(
            custom_resource_definition.EventType(
                crd,
                type='google.source.{}.et.{}'.format(i, j),
                description='desc{}{}'.format(i, j)))
      crd.event_types = event_types
      self.event_types.extend(event_types)

    self.operations.ListSourceCustomResourceDefinitions.return_value = (
        self.source_crds)

  def testListManaged(self):
    """Event types are listable."""
    self._MakeEventTypes(num_sources=2, num_event_types_per_source=3)
    out = self.Run('events types list --platform=managed --region=us-central1')

    self.operations.ListSourceCustomResourceDefinitions.assert_called_once()
    self.assertEqual(out, self.event_types)
    self.AssertOutputEquals(
        """TYPE SOURCE DESCRIPTION
           google.source.0.et.0 SourceKind0 desc00
           google.source.0.et.1 SourceKind0 desc01
           google.source.0.et.2 SourceKind0 desc02
           google.source.1.et.0 SourceKind1 desc10
           google.source.1.et.1 SourceKind1 desc11
           google.source.1.et.2 SourceKind1 desc12
        """,
        normalize_space=True)

  def testListGke(self):
    """Event types are listable."""
    self._MakeEventTypes(num_sources=2, num_event_types_per_source=3)
    out = self.Run('events types list --platform=gke '
                   '--cluster=cluster-1 --cluster-location=us-central1-a')

    self.operations.ListSourceCustomResourceDefinitions.assert_called_once()
    self.assertEqual(out, self.event_types)
    self.AssertOutputEquals(
        """TYPE SOURCE DESCRIPTION
           google.source.0.et.0 SourceKind0 desc00
           google.source.0.et.1 SourceKind0 desc01
           google.source.0.et.2 SourceKind0 desc02
           google.source.1.et.0 SourceKind1 desc10
           google.source.1.et.1 SourceKind1 desc11
           google.source.1.et.2 SourceKind1 desc12
        """,
        normalize_space=True)

  def testListWithSource(self):
    """Event types are listable with source filtering."""
    self._MakeEventTypes(num_sources=3, num_event_types_per_source=3)
    self.Run('events types list --source=SourceKind0 --platform=gke '
             '--cluster=cluster-1 --cluster-location=us-central1-a')

    self.operations.ListSourceCustomResourceDefinitions.assert_called_once()
    self.AssertOutputEquals(
        """TYPE SOURCE DESCRIPTION
           google.source.0.et.0 SourceKind0 desc00
           google.source.0.et.1 SourceKind0 desc01
           google.source.0.et.2 SourceKind0 desc02
        """,
        normalize_space=True)
