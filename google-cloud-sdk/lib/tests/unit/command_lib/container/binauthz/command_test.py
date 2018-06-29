# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Mocked unit tests for Binary Authorization ca_client wrapper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base as binauthz_test_base


class BinauthzClientTest(binauthz_test_base.BinauthzMockedClientTestBase):

  def SetUp(self):
    self.project_ref = resources.REGISTRY.Parse(
        self.Project(),
        collection='cloudresourcemanager.projects',
    )
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
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )
    self.ca_client.CreateAttestationOccurrence(
        note_ref=self.note_ref,
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        pgp_key_fingerprint=self.pgp_key_fingerprint,
        signature=self.signature,
    )

  def testYieldNoteOccurrences(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[self.response_occurrence],
    )
    # We need the list() to force-unroll the returned iterator, otherwise the
    # actual code isn't run.
    occurrences = list(
        self.ca_client._YieldNoteOccurrences(
            note_ref=self.note_ref, artifact_url=self.artifact_url))
    self.assertEqual([self.response_occurrence], occurrences)

  def testYieldNoteOccurrencesFilter(self):
    # Mock a returned occurrence with the wrong kind (but matching artifact URL)
    messages = self.containeranalysis_messages
    unmatched_kind_response_occurrence = self.CreateGenericResponseOccurrence(
        project_ref=self.project_ref,
        kind=messages.Occurrence.KindValueValuesEnum.BUILD_DETAILS,
        resource_url=self.artifact_url,
        note_name=self.note_ref.RelativeName(),
        buildDetails=messages.BuildDetails(),
    )

    # Mock a returned occurrence with the wrong artifact URL.
    unmatched_artifact_response_occurrence = self.CreateResponseOccurrence(
        project_ref=self.project_ref,
        request_occurrence=self.CreateRequestOccurrence(
            project_ref=self.project_ref,
            artifact_url=self.GenerateArtifactUrl(),
            note_ref=self.note_ref,
            pgp_key_fingerprint=self.pgp_key_fingerprint,
            signature=self.signature,
        ),
    )

    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[
            self.response_occurrence,
            unmatched_artifact_response_occurrence,
            unmatched_kind_response_occurrence,
        ],
    )
    # We need the list() to force-unroll the returned iterator, otherwise the
    # actual code isn't run.
    occurrences = list(
        self.ca_client._YieldNoteOccurrences(
            note_ref=self.note_ref, artifact_url=self.artifact_url))
    self.assertEqual([self.response_occurrence], occurrences)

  def testYieldPgpKeyFingerprintsAndSignatures(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[self.response_occurrence],
    )
    # We need the list() to force-unroll the returned iterator, otherwise the
    # actual code isn't run.
    signatures = list(
        self.ca_client.YieldPgpKeyFingerprintsAndSignatures(
            note_ref=self.note_ref, artifact_url=self.artifact_url))
    self.assertEqual(
        [(self.pgp_key_fingerprint, self.signature)],
        signatures,
    )

  def testYieldUrlsWithOccurrences(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[self.response_occurrence],
    )
    resources_urls = list(
        self.ca_client.YieldUrlsWithOccurrences(note_ref=self.note_ref))
    self.assertEqual([self.artifact_url], resources_urls)

  def testYieldUrlsWithOccurrencesDeduplication(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[
            self.response_occurrence,
            self.response_occurrence,
        ],
    )
    resources_urls = list(
        self.ca_client.YieldUrlsWithOccurrences(note_ref=self.note_ref))
    self.assertEqual([self.artifact_url], resources_urls)


if __name__ == '__main__':
  test_case.main()
