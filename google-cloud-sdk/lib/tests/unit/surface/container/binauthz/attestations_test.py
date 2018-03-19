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
"""Tests for the `gcloud container binauthz attestations create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from googlecloudsdk.command_lib.container.binauthz import binauthz_util as binauthz_command_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base as binauthz_test_base


class BinauthzLegacyAttestationsSurfaceTest(
    sdk_test_base.WithTempCWD,
    binauthz_test_base.BinauthzMockedLegacyClientTestBase,
    cli_test_base.CliTestBase,
):

  def SetUp(self):
    self.project_ref = resources.REGISTRY.Parse(
        self.Project(),
        collection='cloudresourcemanager.projects',
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
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )
    self.filter_content = 'resourceUrl="{}" AND kind="BUILD_DETAILS"'.format(
        self.artifact_url)

  def testAttestationsCreate(self):
    provider_ref = binauthz_command_util.CreateProviderRefFromProjectRef(
        self.project_ref)
    self.ExpectProvidersNotesCreate(
        provider_ref=provider_ref,
        request_note=self.request_note,
        note_id=self.note_id,
    )
    self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    pk_path = self.Touch(directory=self.cwd_path, contents=self.public_key)
    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.RunBinauthz([
        'attestations',
        'create',
        '--artifact-url',
        self.artifact_url,
        '--public-key-file',
        pk_path,
        '--signature-file',
        sig_path,
    ])

  def testAttestationsListUrl(self):
    self.ExpectProjectsOccurrencesList(
        project_ref=self.project_ref,
        expected_filter_content=self.filter_content,
        occurrences_to_return=[self.response_occurrence],
    )
    self.ExpectProjectsOccurrencesGetNotes(
        occurrence_name=self.response_occurrence.name,
        expected_note=self.response_note)
    self.RunBinauthz([
        'attestations',
        'list',
        '--artifact-url',
        self.artifact_url,
    ])

  def testAttestationsListAllUrls(self):
    self.ExpectProjectsOccurrencesList(
        project_ref=self.project_ref,
        occurrences_to_return=[self.response_occurrence],
    )
    self.RunBinauthz(['attestations', 'list'])


class BinauthzAttestationsSurfaceTest(
    sdk_test_base.WithTempCWD,
    binauthz_test_base.BinauthzMockedClientTestBase,
    cli_test_base.CliTestBase,
):

  def SetUp(self):
    self.project_ref = resources.REGISTRY.Parse(
        self.Project(),
        collection='cloudresourcemanager.projects',
    )
    self.pgp_key_fingerprint = 'AAAABBBB'
    self.signature = 'fake-signature'
    self.note_id = 'my-aa-note'
    self.note_project = 'other-' + self.Project()
    self.note_relative_name = 'providers/{}/notes/{}'.format(
        self.note_project, self.note_id)
    self.request_occurrence = self.CreateRequestOccurrence(
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        note_ref=resources.REGISTRY.ParseRelativeName(
            relative_name=self.note_relative_name,
            collection='containeranalysis.providers.notes',
        ),
        pgp_key_fingerprint=self.pgp_key_fingerprint,
        signature=self.signature,
    )


class BinauthzAttestationsCreateSurfaceTest(BinauthzAttestationsSurfaceTest):

  def testCreateRelativeNoteName(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestation-authority-note',
            self.note_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--pgp-key-fingerprint',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
        ]),
    )

  def testCreateNoteIdWithProjectFlag(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestation-authority-note',
            self.note_id,
            '--attestation-authority-note-project',
            self.note_project,
            '--artifact-url',
            self.artifact_url,
            '--pgp-key-fingerprint',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
        ]),
    )

  def testCreateRelativeNoteNameWithProjectFlag(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestation-authority-note',
            self.note_relative_name,
            '--attestation-authority-note-project',
            self.note_project,
            '--artifact-url',
            self.artifact_url,
            '--pgp-key-fingerprint',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
        ]),
    )


class BinauthzAttestationsListSurfaceTest(BinauthzAttestationsSurfaceTest):

  def SetUp(self):
    # CliTestBase sets this to True in its SetUp, but we only need to consume
    # the results of calling self.Run in their structured format.
    properties.VALUES.core.user_output_enabled.Set(False)
    self.response_occurrence = self.CreateResponseOccurrence(
        request_occurrence=self.request_occurrence,
        project_ref=self.project_ref,
    )

  def testArtifactUrl(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[self.response_occurrence],
    )
    self.assertItemsEqual(
        [(self.pgp_key_fingerprint, self.signature)],
        list(
            self.RunBinauthz([
                'attestations',
                'list',
                '--attestation-authority-note',
                self.note_relative_name,
                '--artifact-url',
                self.artifact_url,
            ])),
    )

  def testAllUrls(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[self.response_occurrence],
    )
    self.assertItemsEqual(
        [self.artifact_url],
        self.RunBinauthz([
            'attestations',
            'list',
            '--attestation-authority-note',
            self.note_relative_name,
        ]),
    )

  def testAllUrlsDeduplication(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[
            self.response_occurrence,
            self.response_occurrence,
        ],
    )
    self.assertItemsEqual(
        [self.artifact_url],
        self.RunBinauthz([
            'attestations',
            'list',
            '--attestation-authority-note',
            self.note_relative_name,
        ]),
    )

  def testAllUrlsNoteIdWithProject(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[self.response_occurrence],
    )
    self.assertItemsEqual(
        [self.artifact_url],
        self.RunBinauthz([
            'attestations',
            'list',
            '--attestation-authority-note',
            self.note_id,
            '--attestation-authority-note-project',
            self.note_project,
        ]),
    )

  def testAllUrlsNoteRelativeNameWithProject(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[self.response_occurrence],
    )
    self.assertItemsEqual(
        [self.artifact_url],
        self.RunBinauthz([
            'attestations',
            'list',
            '--attestation-authority-note',
            self.note_relative_name,
            '--attestation-authority-note-project',
            self.note_project,
        ]),
    )


if __name__ == '__main__':
  test_case.main()
