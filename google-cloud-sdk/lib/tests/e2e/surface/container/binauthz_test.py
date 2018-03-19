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
from __future__ import print_function

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container import binauthz_util as binauthz_api_util
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
      relative_name='providers/{}/notes/{}'.format(project_id, note_id),
      collection='containeranalysis.providers.notes',
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


class BinauthzLegacyTest(
    e2e_base.WithServiceAuth,
    sdk_test_base.WithTempCWD,
    cli_test_base.CliTestBase,
    binauthz_test_base.BinauthzUnitTestBase,
):

  def SetUp(self):
    # We don't get our track from the base binauthz test because `CliTestBase`
    # clobbers it in its SetUp.
    self.track = base.ReleaseTrack.ALPHA
    # CliTestBase sets this to True in its SetUp, but we only need to consume
    # the result of calling self.Run in their structured format.
    properties.VALUES.core.user_output_enabled.Set(False)
    self.containeranalysis_client = apis.GetClientInstance(
        'containeranalysis',
        binauthz_api_util.DEFAULT_CONTAINERANALYSIS_API_VERSION)
    self.client = binauthz_api_util.ContainerAnalysisClient(
        client=self.containeranalysis_client,
        messages=self.containeranalysis_messages)
    self.artifact_url = self.GenerateArtifactUrl()
    self.project_ref = resources.REGISTRY.Parse(
        self.Project(), collection='cloudresourcemanager.projects')
    self.provider_ref = resources.REGISTRY.Parse(
        self.project_ref.Name(), collection='containeranalysis.providers')

  def GetOccurrence(self, occurrence_name):
    return self.containeranalysis_client.projects_occurrences.Get(
        self.containeranalysis_messages.
        ContaineranalysisProjectsOccurrencesGetRequest(name=occurrence_name))

  def GetNote(self, note_name):
    return self.containeranalysis_client.projects_notes.Get(
        self.containeranalysis_messages.
        ContaineranalysisProjectsNotesGetRequest(name=note_name))

  def CleanUpAttestation(self, occurrence, note):
    self.containeranalysis_client.projects_occurrences.Delete(
        self.containeranalysis_messages.
        ContaineranalysisProjectsOccurrencesDeleteRequest(name=occurrence.name))
    self.containeranalysis_client.providers_notes.Delete(
        self.containeranalysis_messages.
        ContaineranalysisProvidersNotesDeleteRequest(name=note.name))

  def CreateAttestation(self, public_key, signature):
    public_key_path = self.Touch(directory=self.cwd_path, contents=public_key)
    signature_path = self.Touch(directory=self.cwd_path, contents=signature)
    occurrence, note = self.RunBinauthz([
        'attestations',
        'create',
        '--artifact-url',
        self.artifact_url,
        '--public-key-file',
        public_key_path,
        '--signature-file',
        signature_path,
    ])
    self.addCleanup(self.CleanUpAttestation, occurrence=occurrence, note=note)
    return occurrence, note

  def testAttestationsCreate(self):
    public_key = 'bogus_pk_contents'
    signature = 'bogus_sig_contents'
    result_occurrence, result_note = self.CreateAttestation(
        public_key=public_key, signature=signature)
    occurrence = self.GetOccurrence(result_occurrence.name)
    note = self.GetNote(result_note.name)
    self.assertEqual(note.buildType.signature.publicKey, public_key)
    self.assertEqual(note.buildType.signature.signature, signature)
    self.assertEqual(occurrence.noteName, note.name)

  @test_case.Filters.DoNotRunIf(
      condition=True,
      reason='This test is present only as a convenient way to demonstrate a '
      'perf issue with our e2e testing and Drydock queries.  Should not be run '
      'as part of periodic or presubmit tests. Only run by hand to test the '
      'perf issue documented in issue b/63458988.')
  def testListRuntime(self):
    occurrences_iter = list_pager.YieldFromList(
        self.containeranalysis_client.projects_occurrences,
        request=self.containeranalysis_messages.
        ContaineranalysisProjectsOccurrencesListRequest(
            parent=self.project_ref.RelativeName(),
            filter='kind="BUILD_DETAILS"'),
        field='occurrences',
        batch_size=100,
        batch_size_attribute='pageSize')

    # Since this iterator is streaming results and we're only interested
    # in the count, we can count up the elements without buffering the
    # entire result in memory.  Note that this consumes the iterator.
    # pylint: disable=unused-variable
    occurrence_count = sum(1 for _ in occurrences_iter)


class BinauthzTest(
    e2e_base.WithServiceAuth,
    sdk_test_base.WithTempCWD,
    cli_test_base.CliTestBase,
    binauthz_test_base.BinauthzUnitTestBase,
):

  def SetUp(self):
    # We don't get our track from the base binauthz test because `CliTestBase`
    # clobbers it in its SetUp.
    self.track = base.ReleaseTrack.ALPHA
    # CliTestBase sets this to True in its SetUp, but we only need to consume
    # the result of calling self.Run in their structured format.
    properties.VALUES.core.user_output_enabled.Set(False)
    self.containeranalysis_client = apis.GetClientInstance(
        'containeranalysis',
        binauthz_api_util.DEFAULT_CONTAINERANALYSIS_API_VERSION)
    self.client = binauthz_api_util.ContainerAnalysisClient(
        client=self.containeranalysis_client,
        messages=self.containeranalysis_messages)
    self.artifact_url = self.GenerateArtifactUrl()
    self.project_ref = resources.REGISTRY.Parse(
        self.Project(), collection='cloudresourcemanager.projects')
    self.provider_ref = resources.REGISTRY.Parse(
        self.project_ref.Name(), collection='containeranalysis.providers')
    self.note_id = self.note_id_generator.next()
    self.note_relative_name = 'providers/{}/notes/{}'.format(
        self.Project(), self.note_id)

  def RunAndUnwindWithRetry(self, cmd, result_predicate=bool):
    # TODO(b/63455376): Listing Notes/Occurrences immediately after creation
    # sometimes races, so retry a couple times with backoff.
    def RunAndUnwind():
      return list(self.Run(cmd))

    return _ReRunUntilResultPredicate(
        run_fn=RunAndUnwind, result_predicate=result_predicate)

  def CleanUpAttestationAuthority(self, note):
    self.containeranalysis_client.providers_notes.Delete(
        self.containeranalysis_messages.
        ContaineranalysisProvidersNotesDeleteRequest(name=note.name))

  def CleanUpAttestation(self, occurrence):
    self.containeranalysis_client.projects_occurrences.Delete(
        self.containeranalysis_messages.
        ContaineranalysisProjectsOccurrencesDeleteRequest(name=occurrence.name))

  def CreateAttestationAuthority(self, note_id):
    """There is no surface to do this, so we use the client directly."""

    request = self.ProvidersNotesCreateRequest(
        name=self.provider_ref.RelativeName(),
        noteId=note_id,
        note=self.Note(
            kind=self.Note.KindValueValuesEnum.ATTESTATION_AUTHORITY,
            shortDescription='Attestation Authority Note',
            attestationAuthority=self.AttestationAuthority(),
        ),
    )
    note = self.containeranalysis_client.providers_notes.Create(request)
    self.addCleanup(self.CleanUpAttestationAuthority, note=note)

  def GetOccurrence(self, occurrence_name):
    return self.containeranalysis_client.projects_occurrences.Get(
        self.containeranalysis_messages.
        ContaineranalysisProjectsOccurrencesGetRequest(name=occurrence_name))

  def CreateAttestation(
      self,
      note_ref,
      pgp_key_fingerprint,
      signature,
      artifact_url=None,
  ):
    signature_path = self.Touch(directory=self.cwd_path, contents=signature)
    occurrence = self.RunBinauthz([
        'attestations',
        'create',
        '--artifact-url',
        artifact_url or self.artifact_url,
        '--attestation-authority-note',
        note_ref,
        '--pgp-key-fingerprint',
        pgp_key_fingerprint,
        '--signature-file',
        signature_path,
    ])
    self.addCleanup(self.CleanUpAttestation, occurrence=occurrence)
    return occurrence

  def testAttestationsCreate(self):
    pgp_key_fingerprint = 'AAAABBBB'
    signature = 'bogus_sig_contents'
    self.CreateAttestationAuthority(note_id=self.note_id)

    create_result = self.CreateAttestation(
        note_ref=self.note_relative_name,
        pgp_key_fingerprint=pgp_key_fingerprint,
        signature=signature,
    )
    occurrence = self.GetOccurrence(create_result.name)

    self.assertEqual(occurrence.attestation.pgpSignedAttestation.pgpKeyId,
                     pgp_key_fingerprint)
    self.assertEqual(occurrence.attestation.pgpSignedAttestation.signature,
                     signature)

  def testAttestationsList(self):
    self.CreateAttestationAuthority(note_id=self.note_id)

    self.CreateAttestation(
        note_ref=self.note_relative_name,
        pgp_key_fingerprint='bogus_pk_id',
        signature='bogus_sig',
        artifact_url=self.artifact_url,
    )

    # Create an attestation with a different artifact URL.
    artifact_url2 = self.GenerateArtifactUrl()
    self.CreateAttestation(
        note_ref=self.note_relative_name,
        pgp_key_fingerprint='bogus_pk_id2',
        signature='bogus_sig2',
        artifact_url=artifact_url2,
    )

    def HasAtLeastTwoElements(result):
      return len(result) >= 2

    self.assertItemsEqual(
        self.RunAndUnwindWithRetry(
            [
                'container',
                'binauthz',
                'attestations',
                'list',
                '--attestation-authority-note',
                self.note_relative_name,
            ],
            result_predicate=HasAtLeastTwoElements),
        [self.artifact_url, artifact_url2],
    )
    self.assertItemsEqual(
        self.RunAndUnwindWithRetry([
            'container',
            'binauthz',
            'attestations',
            'list',
            '--attestation-authority-note',
            self.note_relative_name,
            '--artifact-url',
            self.artifact_url,
        ]),
        [('bogus_pk_id', 'bogus_sig')],
    )


if __name__ == '__main__':
  test_case.main()
