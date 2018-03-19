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
"""Mocked unit tests for Binary Authorization client wrapper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from googlecloudsdk.command_lib.container.binauthz import binauthz_util as binauthz_command_util
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
        provider_id=self.note_project,
        note_id=self.note_id,
    )
    self.note_ref = resources.REGISTRY.ParseRelativeName(
        relative_name=self.note_relative_name,
        collection='containeranalysis.providers.notes',
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
    self.client.CreateAttestationOccurrence(
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
        self.client._YieldNoteOccurrences(
            note_ref=self.note_ref, artifact_url=self.artifact_url))
    self.assertItemsEqual([self.response_occurrence], occurrences)

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
        self.client._YieldNoteOccurrences(
            note_ref=self.note_ref, artifact_url=self.artifact_url))
    self.assertItemsEqual([self.response_occurrence], occurrences)

  def testYieldPgpKeyFingerprintsAndSignatures(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[self.response_occurrence],
    )
    # We need the list() to force-unroll the returned iterator, otherwise the
    # actual code isn't run.
    signatures = list(
        self.client.YieldPgpKeyFingerprintsAndSignatures(
            note_ref=self.note_ref, artifact_url=self.artifact_url))
    self.assertItemsEqual(
        [(self.pgp_key_fingerprint, self.signature)],
        signatures,
    )

  def testYieldUrlsWithOccurrences(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[self.response_occurrence],
    )
    resources_urls = list(
        self.client.YieldUrlsWithOccurrences(note_ref=self.note_ref))
    self.assertItemsEqual([self.artifact_url], resources_urls)

  def testYieldUrlsWithOccurrencesDeduplication(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[
            self.response_occurrence,
            self.response_occurrence,
        ],
    )
    resources_urls = list(
        self.client.YieldUrlsWithOccurrences(note_ref=self.note_ref))
    self.assertItemsEqual([self.artifact_url], resources_urls)


class BinauthzLegacyClientTest(
    binauthz_test_base.BinauthzMockedLegacyClientTestBase):

  def SetUp(self):
    self.project_ref = resources.REGISTRY.Parse(
        self.Project(),
        collection='cloudresourcemanager.projects',
    )
    self.provider_ref = resources.REGISTRY.Parse(
        self.Project(),
        collection='containeranalysis.providers',
    )
    self.public_key = 'fake-public-key'
    self.signature = 'fake-signature'
    self.note_id = binauthz_command_util.NoteId(
        artifact_url=self.artifact_url,
        public_key=self.public_key,
        signature=self.signature,
    )
    self.note_relative_name = binauthz_test_base.GetNoteRelativeName(
        provider_id=self.Project(),
        note_id=self.note_id,
    )
    self.request_note = self.CreateRequestNote(
        public_key=self.public_key,
        signature=self.signature,
    )
    self.response_note = self.CreateResponseNote(
        request_note=self.request_note,
        expected_note_relative_name=self.note_relative_name,
    )
    self.request_occurrence = self.CreateRequestOccurrence(
        artifact_url=self.artifact_url,
        project_ref=self.project_ref,
        public_key=self.public_key,
        signature=self.signature,
    )
    self.response_occurrence = self.CreateResponseOccurrence(
        request_occurrence=self.request_occurrence,
        project_ref=self.project_ref,
    )
    self.filter_content = 'resourceUrl="{}" AND kind="BUILD_DETAILS"'.format(
        self.artifact_url)

  def testPutSignature(self):
    provider_ref = binauthz_command_util.CreateProviderRefFromProjectRef(
        self.project_ref)
    provider_note_ref = binauthz_command_util.ParseProviderNote(
        note_id=self.note_id,
        provider_ref=self.provider_ref,
    )

    self.ExpectProvidersNotesCreate(
        provider_ref=provider_ref,
        request_note=self.request_note,
        note_id=self.note_id,
    )
    self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    self.client.PutSignature(
        occurrence_project_ref=self.project_ref,
        provider_ref=provider_ref,
        provider_note_ref=provider_note_ref,
        note_id=self.note_id,
        artifact_url=self.artifact_url,
        public_key=self.public_key,
        signature=self.signature)

  def testYieldOccurrences(self):
    self.ExpectProjectsOccurrencesList(
        project_ref=self.project_ref,
        expected_filter_content=self.filter_content,
        occurrences_to_return=[self.response_occurrence],
    )
    # We need the list() to force-unroll the returned iterator, otherwise the
    # actual code isn't run.
    occurrences = list(
        self.client._YieldOccurrences(
            project_ref=self.project_ref, artifact_url=self.artifact_url))
    self.assertItemsEqual(occurrences, [self.response_occurrence])

  def testYieldNotes(self):
    self.ExpectProjectsOccurrencesList(
        project_ref=self.project_ref,
        expected_filter_content=self.filter_content,
        occurrences_to_return=[self.response_occurrence],
    )
    self.ExpectProjectsOccurrencesGetNotes(
        occurrence_name=self.response_occurrence.name,
        expected_note=self.response_note,
    )
    # We need the list() to force-unroll the returned iterator, otherwise the
    # actual code isn't run.
    notes = list(
        self.client._YieldNotes(
            project_ref=self.project_ref, artifact_url=self.artifact_url))
    self.assertItemsEqual(notes, [self.response_note])

  def testYieldSignatures(self):
    self.ExpectProjectsOccurrencesList(
        project_ref=self.project_ref,
        expected_filter_content=self.filter_content,
        occurrences_to_return=[self.response_occurrence],
    )
    self.ExpectProjectsOccurrencesGetNotes(
        occurrence_name=self.response_occurrence.name,
        expected_note=self.response_note,
    )
    # We need the list() to force-unroll the returned iterator, otherwise the
    # actual code isn't run.
    signatures = list(
        self.client.YieldSignatures(
            project_ref=self.project_ref, artifact_url=self.artifact_url))
    self.assertItemsEqual(signatures, [(self.public_key, self.signature)])

  def testYieldUrlsWithOccurrences(self):
    self.ExpectProjectsOccurrencesList(
        project_ref=self.project_ref,
        occurrences_to_return=[self.response_occurrence],
    )
    resources_urls = list(
        self.client.YieldUrlsWithOccurrences(project_ref=self.project_ref))
    self.assertItemsEqual(resources_urls, [self.artifact_url])


if __name__ == '__main__':
  test_case.main()
