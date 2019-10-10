# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for Binary Authorization's containeranalysis client wrapper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import containeranalysis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base as binauthz_test_base


class ContaineranalysisClientTest(
    binauthz_test_base.WithMockBetaContaineranalysis,
    binauthz_test_base.BinauthzTestBase,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.ca_client = containeranalysis.Client()
    self.project_ref = resources.REGISTRY.Parse(
        self.Project(),
        collection='cloudresourcemanager.projects',
    )
    self.artifact_url = self.GenerateArtifactUrl()
    self.pgp_key_fingerprint = 'AAAABBBB'
    self.signature = 'fake-signature'
    self.note_id = 'my-aa-note'
    self.note_project = 'other-' + self.Project()
    self.note_relative_name = binauthz_test_base.GetNoteRelativeName(
        project_id=self.note_project,
        note_id=self.note_id,
    )
    self.note_ref = resources.REGISTRY.ParseRelativeName(
        relative_name=self.note_relative_name,
        collection='containeranalysis.projects.notes',
    )
    self.request_occurrence = self.CreateRequestOccurrence(
        artifact_url=self.artifact_url,
        project_ref=self.project_ref,
        note_ref=self.note_ref,
        pgp_key_fingerprint=self.pgp_key_fingerprint,
        signature=self.signature,
    )
    self.response_occurrence = self.CreateResponseOccurrence(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

  def testCreateAttestationOccurrence(self):
    self.ExpectProjectsOccurrencesCreate(
        request_occurrence=self.request_occurrence,
        project_ref=self.project_ref,
    )
    self.ca_client.CreatePgpAttestationOccurrence(
        note_ref=self.note_ref,
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        pgp_key_fingerprint=self.pgp_key_fingerprint,
        signature=self.signature,
    )

  def testYieldAttestations(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        expected_filter_content='resourceUrl="{}"'.format(self.artifact_url),
        occurrences_to_return=[self.response_occurrence],
    )
    # We need the list() to force-unroll the returned iterator, otherwise the
    # actual code isn't run.
    occurrences = list(
        self.ca_client.YieldAttestations(
            note_ref=self.note_ref, artifact_url=self.artifact_url))
    self.assertEqual([self.response_occurrence], occurrences)

  def testYieldAttestationsFilter(self):
    # Mock a returned occurrence with the wrong kind (but matching artifact URL)
    messages = self.ca_messages
    unmatched_kind_response_occurrence = self.CreateGenericResponseOccurrence(
        project_ref=self.project_ref,
        kind=messages.Occurrence.KindValueValuesEnum.BUILD,
        resource_url=self.artifact_url,
        note_name=self.note_ref.RelativeName(),
        build=messages.GrafeasV1beta1BuildDetails(),
    )

    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        expected_filter_content='resourceUrl="{}"'.format(self.artifact_url),
        occurrences_to_return=[
            self.response_occurrence,
            unmatched_kind_response_occurrence,
        ],
    )
    # We need the list() to force-unroll the returned iterator, otherwise the
    # actual code isn't run.
    occurrences = list(
        self.ca_client.YieldAttestations(
            note_ref=self.note_ref, artifact_url=self.artifact_url))
    self.assertEqual([self.response_occurrence], occurrences)


if __name__ == '__main__':
  test_case.main()
