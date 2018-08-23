# -*- coding: utf-8 -*- #
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
"""e2e tests for Binary Authorization command surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import containeranalysis
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import retry
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base as binauthz_test_base


def GetNoteRef(project_id, note_id):
  return resources.REGISTRY.ParseRelativeName(
      relative_name='projects/{}/notes/{}'.format(project_id, note_id),
      collection='containeranalysis.projects.notes',
  )


def _ReRunUntilResultPredicate(
    run_fn,
    args=(),
    result_predicate=bool,
    max_retrials=5,
    sleep_ms=1000,
    max_wait_ms=15000,
    exponential_sleep_multiplier=1.5,
):
  """A generalization of ReRunUntilOutputContains for result predicates."""

  def ShouldRetryIf(result, unused_state):
    return not result_predicate(result)

  retryer = retry.Retryer(
      max_retrials=max_retrials,
      max_wait_ms=max_wait_ms,
      exponential_sleep_multiplier=exponential_sleep_multiplier,
  )
  return retryer.RetryOnResult(
      func=run_fn,
      args=args,
      should_retry_if=ShouldRetryIf,
      sleep_ms=sleep_ms,
  )


class BinauthzTest(
    e2e_base.WithServiceAuth,
    sdk_test_base.WithTempCWD,
    cli_test_base.CliTestBase,
    binauthz_test_base.WithEarlyCleanup,
    binauthz_test_base.BinauthzUnitTestBase,
):

  def SetUp(self):
    # We don't get our track from the base binauthz test because `CliTestBase`
    # clobbers it in its SetUp.
    self.track = base.ReleaseTrack.BETA
    # CliTestBase sets this to True in its SetUp, but we only need to consume
    # the result of calling self.Run in their structured format.
    properties.VALUES.core.user_output_enabled.Set(False)
    self.containeranalysis_client = apis.GetClientInstance(
        containeranalysis.API_NAME,
        containeranalysis.DEFAULT_VERSION)
    self.client = containeranalysis.Client()
    self.artifact_url = self.GenerateArtifactUrl()
    self.project_ref = resources.REGISTRY.Parse(
        self.Project(), collection='cloudresourcemanager.projects')
    self.note_id = next(self.note_id_generator)
    self.note_relative_name = 'projects/{}/notes/{}'.format(
        self.Project(), self.note_id)
    self.attestor_id = self.note_id
    self.attestor_relative_name = 'projects/{}/attestors/{}'.format(
        self.Project(), self.attestor_id)

  def RunAndUnwindWithRetry(self, cmd, result_predicate=bool):
    # TODO(b/63455376): Listing Notes/Occurrences immediately after creation
    # sometimes races, so retry a couple times with backoff.
    def RunAndUnwind():
      return list(self.Run(cmd))

    return _ReRunUntilResultPredicate(
        run_fn=RunAndUnwind, result_predicate=result_predicate)

  def CleanUpAttestor(self, note_name, attestor_id):
    self.containeranalysis_client.projects_notes.Delete(
        self.containeranalysis_messages.
        ContaineranalysisProjectsNotesDeleteRequest(name=note_name))

    self.RunBinauthz([
        'attestors',
        'delete',
        attestor_id,
    ])

  def CleanUpAttestation(self, occurrence_name):
    self.containeranalysis_client.projects_occurrences.Delete(
        self.containeranalysis_messages.
        ContaineranalysisProjectsOccurrencesDeleteRequest(name=occurrence_name))

  def CreateAttestor(self, note_id, attestor_id):
    # There is no surface to create the note so we use the client directly.
    request = self.ProjectsNotesCreateRequest(
        parent=self.project_ref.RelativeName(),
        noteId=note_id,
        note=self.Note(
            kind=self.Note.KindValueValuesEnum.ATTESTATION_AUTHORITY,
            shortDescription='Attestation Authority Note',
            attestationAuthority=self.AttestationAuthority(),
        ),
    )
    note = self.containeranalysis_client.projects_notes.Create(request)

    self.RunBinauthz([
        'attestors',
        'create',
        '--attestation-authority-note',
        note_id,
        '--attestation-authority-note-project',
        self.Project(),
        attestor_id,
    ])

    self.AddEarlyCleanup(self.CleanUpAttestor,
                         note_name=note.name,
                         attestor_id=attestor_id)

  def GetOccurrence(self, occurrence_name):
    return self.containeranalysis_client.projects_occurrences.Get(
        self.containeranalysis_messages.
        ContaineranalysisProjectsOccurrencesGetRequest(name=occurrence_name))

  def CreateAttestation(
      self,
      attestor_ref,
      pgp_key_fingerprint,
      signature,
      artifact_url,
  ):
    signature_path = self.Touch(directory=self.cwd_path, contents=signature)
    occurrence = self.RunBinauthz([
        'attestations',
        'create',
        '--artifact-url',
        artifact_url,
        '--attestor',
        attestor_ref,
        '--pgp-key-fingerprint',
        pgp_key_fingerprint,
        '--signature-file',
        signature_path,
    ])
    self.AddEarlyCleanup(self.CleanUpAttestation,
                         occurrence_name=occurrence.name)
    return occurrence

  # TODO(b/112087150): Split into several tests when quota is more forgiving.
  def testAttestations(self):
    self.CreateAttestor(self.note_id, self.attestor_id)

    attestation = self.CreateAttestation(
        attestor_ref=self.attestor_relative_name,
        pgp_key_fingerprint='bogus_pk_id',
        signature='bogus_sig',
        artifact_url=self.artifact_url,
    )

    # Verify the generated Occurrence.
    occurrence = self.GetOccurrence(attestation.name)
    self.assertEqual(occurrence.attestation.pgpSignedAttestation.pgpKeyId,
                     'bogus_pk_id')
    self.assertEqual(occurrence.attestation.pgpSignedAttestation.signature,
                     'bogus_sig')

    # Create an attestation with a different artifact URL.
    artifact_url2 = self.GenerateArtifactUrl()
    self.CreateAttestation(
        attestor_ref=self.attestor_relative_name,
        pgp_key_fingerprint='bogus_pk_id2',
        signature='bogus_sig2',
        artifact_url=artifact_url2,
    )

    def HasAtLeastTwoElements(result):
      return len(result) >= 2

    # Verify that the bare listing gets attestations for both the artifacts.
    occurrences = self.RunAndUnwindWithRetry(
        [
            'container',
            'binauthz',
            'attestations',
            'list',
            '--attestor',
            self.attestor_id,
        ],
        result_predicate=HasAtLeastTwoElements)
    self.assertEqual(
        set(occ.resourceUrl for occ in occurrences),
        set([self.artifact_url, artifact_url2]),
    )

    # Verify that artifact-based filtering works.
    occurrences = list(self.RunAndUnwindWithRetry(
        [
            'container',
            'binauthz',
            'attestations',
            'list',
            '--attestor',
            self.attestor_id,
            '--artifact-url',
            self.artifact_url,
        ]))
    self.assertEqual(1, len(occurrences))
    self.assertEqual(occurrences[0].attestation.pgpSignedAttestation.pgpKeyId,
                     'bogus_pk_id')
    self.assertEqual(occurrences[0].attestation.pgpSignedAttestation.signature,
                     'bogus_sig')


if __name__ == '__main__':
  test_case.main()
