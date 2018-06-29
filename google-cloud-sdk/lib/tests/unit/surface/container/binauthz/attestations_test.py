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
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base as binauthz_test_base


class BinauthzAttestationsSurfaceTest(
    sdk_test_base.WithTempCWD,
    binauthz_test_base.BinauthzMockedClientTestBase,
    binauthz_test_base.BinauthzMockedPolicyClientUnitTest,
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
    self.note_relative_name = 'projects/{}/notes/{}'.format(
        self.note_project, self.note_id)
    self.aa_id = 'my-aa'
    self.aa_project = self.Project()
    self.aa_relative_name = 'projects/{}/attestationAuthorities/{}'.format(
        self.aa_project, self.aa_id)
    self.aa = self.messages.AttestationAuthority(
        name=self.aa_relative_name,
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference=self.note_relative_name,
            publicKeys=[],
        ))
    self.request_occurrence = self.CreateRequestOccurrence(
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        note_ref=resources.REGISTRY.ParseRelativeName(
            relative_name=self.note_relative_name,
            collection='containeranalysis.projects.notes',
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

  def testCreateWithAttestationAuthority(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestationAuthoritiesGetRequest(  # pylint: disable=line-too-long
        name=self.aa_relative_name,
    )
    self.client.projects_attestationAuthorities.Get.Expect(
        req, response=self.aa)

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestation-authority',
            self.aa_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--pgp-key-fingerprint',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
        ]),
    )

  def testCreateWithAttestationAuthorityUsingAAProjectFlag(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestationAuthoritiesGetRequest(  # pylint: disable=line-too-long
        name=self.aa_relative_name,
    )
    self.client.projects_attestationAuthorities.Get.Expect(
        req, response=self.aa)

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestation-authority',
            self.aa_id,
            '--attestation-authority-project',
            self.aa_project,
            '--artifact-url',
            self.artifact_url,
            '--pgp-key-fingerprint',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
        ]),
    )

  def testCreateCannotProvideBothAttestationAuthorityAndNote(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      unused_result = self.RunBinauthz([
          'attestations',
          'create',
          '--attestation-authority',
          'projects/{}/attestationAuthorities/{}'.format(self.Project(), 'foo'),
          '--attestation-authority-note',
          self.note_relative_name,
          '--artifact-url',
          self.artifact_url,
          '--pgp-key-fingerprint',
          self.pgp_key_fingerprint,
          '--signature-file',
          'any/path',
      ]),


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
    self.assertEqual(
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

  def testArtifactUrl_AA(self):
    req = self.messages.BinaryauthorizationProjectsAttestationAuthoritiesGetRequest(  # pylint: disable=line-too-long
        name=self.aa_relative_name,
    )
    self.client.projects_attestationAuthorities.Get.Expect(
        req, response=self.aa)
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[self.response_occurrence],
    )
    self.assertEqual(
        [(self.pgp_key_fingerprint, self.signature)],
        list(
            self.RunBinauthz([
                'attestations',
                'list',
                '--attestation-authority',
                self.aa_relative_name,
                '--artifact-url',
                self.artifact_url,
            ])),
    )

  def testArtifactUrl_AAWithProject(self):
    req = self.messages.BinaryauthorizationProjectsAttestationAuthoritiesGetRequest(  # pylint: disable=line-too-long
        name=self.aa_relative_name,
    )
    self.client.projects_attestationAuthorities.Get.Expect(
        req, response=self.aa)
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[self.response_occurrence],
    )
    self.assertEqual(
        [(self.pgp_key_fingerprint, self.signature)],
        list(
            self.RunBinauthz([
                'attestations',
                'list',
                '--attestation-authority',
                self.aa_id,
                '--attestation-authority-project',
                self.aa_project,
                '--artifact-url',
                self.artifact_url,
            ])),
    )

  def testAllUrls(self):
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[self.response_occurrence],
    )
    self.assertEqual(
        [self.artifact_url],
        self.RunBinauthz([
            'attestations',
            'list',
            '--attestation-authority-note',
            self.note_relative_name,
        ]),
    )

  def testAllUrls_AA(self):
    req = self.messages.BinaryauthorizationProjectsAttestationAuthoritiesGetRequest(  # pylint: disable=line-too-long
        name=self.aa_relative_name,
    )
    self.client.projects_attestationAuthorities.Get.Expect(
        req, response=self.aa)
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        occurrences_to_return=[self.response_occurrence],
    )
    self.assertEqual(
        [self.artifact_url],
        self.RunBinauthz([
            'attestations',
            'list',
            '--attestation-authority',
            self.aa_relative_name,
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
    self.assertEqual(
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
    self.assertEqual(
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
    self.assertEqual(
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

  def testAllUrls_FailIfBothNoteAndAA(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      unused_result = self.RunBinauthz([
          'attestations',
          'list',
          '--attestation-authority',
          self.aa_relative_name,
          '--attestation-authority-note',
          self.note_relative_name,
      ])


if __name__ == '__main__':
  test_case.main()
