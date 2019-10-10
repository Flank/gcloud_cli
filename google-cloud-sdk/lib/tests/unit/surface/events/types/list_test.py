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
from googlecloudsdk.command_lib.events import exceptions
from tests.lib.surface.run import base


class TypesListTestAlpha(base.ServerlessSurfaceBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _MakeEventTypes(self, num_sources, num_event_types_per_source):
    """Creates source CRDs with event types and assigns them to ListSourceCRDs."""
    self.source_crds = [
        custom_resource_definition.SourceCustomResourceDefinition.New(
            self.mock_crd_client, 'fake-project')
        for _ in range(num_sources)]
    for i, crd in enumerate(self.source_crds):
      event_types = []
      for j in range(num_event_types_per_source):
        event_types.append(
            self._EventTypeAdditionalProperty(
                'et{}-{}'.format(i, j), 'desc{}{}'.format(i, j),
                'google.source.{}.et.{}'.format(i, j)))
      crd.spec.validation = self.crd_messages.CustomResourceValidation(
          openAPIV3Schema=self._SourceSchemaProperties('Source{}'.format(i),
                                                       event_types))
    self.event_types = []
    for crd in self.source_crds:
      self.event_types.extend(crd.event_types)
    (self.operations.ListSourceCustomResourceDefinitions
     .return_value) = self.source_crds

  def testListFailsNonGKE(self):
    """Event Types are not yet supported on managed Cloud Run."""
    with self.assertRaises(exceptions.UnsupportedArgumentError):
      self.Run('events types list --platform=managed --region=us-central1')
    self.AssertErrContains(
        'Events are only available with Cloud Run for Anthos.')

  def testList(self):
    """Two event types are listable."""
    self._MakeEventTypes(num_sources=2, num_event_types_per_source=3)
    out = self.Run('events types list --platform=gke '
                   '--cluster=cluster-1 --cluster-location=us-central1-a')

    self.operations.ListSourceCustomResourceDefinitions.assert_called_once()
    self.assertEqual(out, self.event_types)
    self.AssertOutputEquals(
        """TYPE CATEGORY DESCRIPTION
           google.source.0.et.0 Source0 desc00
           google.source.0.et.1 Source0 desc01
           google.source.0.et.2 Source0 desc02
           google.source.1.et.0 Source1 desc10
           google.source.1.et.1 Source1 desc11
           google.source.1.et.2 Source1 desc12
        """,
        normalize_space=True)

  def testListWithCategory(self):
    """Two event types are listable."""
    self._MakeEventTypes(num_sources=3, num_event_types_per_source=3)
    self.Run('events types list --category=Source0 --platform=gke '
             '--cluster=cluster-1 --cluster-location=us-central1-a')

    self.operations.ListSourceCustomResourceDefinitions.assert_called_once()
    self.AssertOutputEquals(
        """TYPE CATEGORY DESCRIPTION
           google.source.0.et.0 Source0 desc00
           google.source.0.et.1 Source0 desc01
           google.source.0.et.2 Source0 desc02
        """,
        normalize_space=True)
