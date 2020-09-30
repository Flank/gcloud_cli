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
"""Tests for the `gcloud container binauthz attestations create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.container.binauthz import apis as binauthz_apis
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.binauthz import util as binauthz_command_util
from googlecloudsdk.command_lib.kms import get_digest
from googlecloudsdk.core import resources
from googlecloudsdk.core.console.console_io import OperationCancelledError
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base as binauthz_test_base

import six


class BaseAttestationsTest(
    sdk_test_base.WithTempCWD,
    binauthz_test_base.BinauthzTestBase,
):

  def SetUp(self):
    self.project_ref = resources.REGISTRY.Parse(
        self.Project(),
        collection='cloudresourcemanager.projects',
    )
    self.artifact_url = self.GenerateArtifactUrl()
    self.pgp_key_fingerprint = 'AAAABBBB'
    self.signature = binauthz_command_util.MakeSignaturePayload(
        self.artifact_url)
    self.note_id = 'my-aa-note'
    self.note_project = 'other-' + self.Project()
    self.note_relative_name = 'projects/{}/notes/{}'.format(
        self.note_project, self.note_id)
    self.attestor_id = 'my-attestor'
    self.attestor_project = self.Project()
    self.attestor_relative_name = 'projects/{}/attestors/{}'.format(
        self.attestor_project, self.attestor_id)
    try:
      self.attestor = self.messages.Attestor(
          name=self.attestor_relative_name,
          updateTime=None,
          userOwnedGrafeasNote=self.messages.UserOwnedGrafeasNote(
              noteReference=self.note_relative_name,
              publicKeys=[],
          ))
    except AttributeError:
      self.attestor = self.messages.Attestor(
          name=self.attestor_relative_name,
          updateTime=None,
          userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
              noteReference=self.note_relative_name,
              publicKeys=[],
          ))

    self.request_occurrence = self.CreateRequestAttestationOccurrence(
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        note_ref=resources.REGISTRY.ParseRelativeName(
            relative_name=self.note_relative_name,
            collection='containeranalysis.projects.notes',
        ),
        plaintext=self.signature,
        signatures=[(self.pgp_key_fingerprint, self.signature)],
    )


class CreateTest(
    binauthz_test_base.WithMockV1Containeranalysis,
    binauthz_test_base.WithMockGaBinauthz,
    BaseAttestationsTest,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

    # Save the V1 client under a different name so CreateAlphaTest can still
    # use it after replacing self.mock_client with a V1Alpha2 version. (The
    # apitools mock library modifies the class being mocked in a way that
    # breaks any additional mocks. This is the least ugly workaround.)
    # TODO(b/159263189): Delete after removing ValidationHelperV1Alpha2 service.
    self.v1_mock_client = self.mock_client

  def testCreateWithAttestor(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--public-key-id',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
        ]),
    )

  def testCreateWithAttestorUsingProjectFlag(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestor',
            self.attestor_id,
            '--attestor-project',
            self.attestor_project,
            '--artifact-url',
            self.artifact_url,
            '--public-key-id',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
        ]),
    )

  def testCreateWithExplicitPayloadFlag(self):
    # Construct payload without a trailing newline.
    fake_payload = binauthz_command_util.MakeSignaturePayload(
        self.artifact_url)[:-1]
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.CreateRequestAttestationOccurrence(
            project_ref=self.project_ref,
            artifact_url=self.artifact_url,
            note_ref=resources.REGISTRY.ParseRelativeName(
                relative_name=self.note_relative_name,
                collection='containeranalysis.projects.notes',
            ),
            plaintext=fake_payload,
            signatures=[(self.pgp_key_fingerprint, self.signature)],
        ))

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    payload_path = self.Touch(directory=self.cwd_path, contents=fake_payload)
    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--public-key-id',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
            '--payload-file',
            payload_path,
        ]),
    )

  def testCreateWithSuccessfulValidation(self):
    request_occurrence = self.CreateRequestAttestationOccurrence(
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        note_ref=resources.REGISTRY.ParseRelativeName(
            relative_name=self.note_relative_name,
            collection='containeranalysis.projects.notes',
        ),
        plaintext=self.signature,
        signatures=[(self.pgp_key_fingerprint, self.signature)],
    )
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=request_occurrence,
    )

    attestor_req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(
        attestor_req, response=self.attestor)

    validate_attestation_request = self.messages.ValidateAttestationOccurrenceRequest(
        attestation=encoding.JsonToMessage(
            self.messages.AttestationOccurrence,
            encoding.MessageToJson(request_occurrence.attestation)),
        occurrenceNote=request_occurrence.noteName,
        occurrenceResourceUri=request_occurrence.resourceUri,
    )
    validate_req = self.messages.BinaryauthorizationProjectsAttestorsValidateAttestationOccurrenceRequest(
        attestor=self.attestor_relative_name,
        validateAttestationOccurrenceRequest=validate_attestation_request)
    validate_attestation_response = self.messages.ValidateAttestationOccurrenceResponse(
        result=self.messages.ValidateAttestationOccurrenceResponse
        .ResultValueValuesEnum.VERIFIED)
    self.mock_client.projects_attestors.ValidateAttestationOccurrence.Expect(
        validate_req, response=validate_attestation_response)

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--public-key-id',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
            '--validate',
        ]),
    )

  def testCreateWithUnsuccessfulValidationWithOverride(self):
    request_occurrence = self.CreateRequestAttestationOccurrence(
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        note_ref=resources.REGISTRY.ParseRelativeName(
            relative_name=self.note_relative_name,
            collection='containeranalysis.projects.notes',
        ),
        plaintext=self.signature,
        signatures=[(self.pgp_key_fingerprint, self.signature)],
    )
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=request_occurrence,
    )

    attestor_req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(
        attestor_req, response=self.attestor)

    validate_attestation_request = self.messages.ValidateAttestationOccurrenceRequest(
        attestation=encoding.JsonToMessage(
            self.messages.AttestationOccurrence,
            encoding.MessageToJson(request_occurrence.attestation)),
        occurrenceNote=request_occurrence.noteName,
        occurrenceResourceUri=request_occurrence.resourceUri,
    )
    validate_req = self.messages.BinaryauthorizationProjectsAttestorsValidateAttestationOccurrenceRequest(
        attestor=self.attestor_relative_name,
        validateAttestationOccurrenceRequest=validate_attestation_request)
    validate_attestation_response = self.messages.ValidateAttestationOccurrenceResponse(
        result=self.messages.ValidateAttestationOccurrenceResponse
        .ResultValueValuesEnum.ATTESTATION_NOT_VERIFIABLE,
        denialReason='You failed!')
    self.mock_client.projects_attestors.ValidateAttestationOccurrence.Expect(
        validate_req, response=validate_attestation_response)

    self.WriteInput('y\n')

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--public-key-id',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
            '--validate',
        ]),
    )

  def testCreateWithUnsuccessfulValidationWithoutOverride(self):
    request_occurrence = self.CreateRequestAttestationOccurrence(
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        note_ref=resources.REGISTRY.ParseRelativeName(
            relative_name=self.note_relative_name,
            collection='containeranalysis.projects.notes',
        ),
        plaintext=self.signature,
        signatures=[(self.pgp_key_fingerprint, self.signature)],
    )

    attestor_req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(
        attestor_req, response=self.attestor)

    validate_attestation_request = self.messages.ValidateAttestationOccurrenceRequest(
        attestation=encoding.JsonToMessage(
            self.messages.AttestationOccurrence,
            encoding.MessageToJson(request_occurrence.attestation)),
        occurrenceNote=request_occurrence.noteName,
        occurrenceResourceUri=request_occurrence.resourceUri,
    )
    validate_req = self.messages.BinaryauthorizationProjectsAttestorsValidateAttestationOccurrenceRequest(
        attestor=self.attestor_relative_name,
        validateAttestationOccurrenceRequest=validate_attestation_request)
    validate_attestation_response = self.messages.ValidateAttestationOccurrenceResponse(
        result=self.messages.ValidateAttestationOccurrenceResponse
        .ResultValueValuesEnum.ATTESTATION_NOT_VERIFIABLE,
        denialReason='You failed!')
    self.mock_client.projects_attestors.ValidateAttestationOccurrence.Expect(
        validate_req, response=validate_attestation_response)

    self.WriteInput('n\n')

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)

    with self.assertRaises(OperationCancelledError):
      self.RunBinauthz([
          'attestations',
          'create',
          '--attestor',
          self.attestor_relative_name,
          '--artifact-url',
          self.artifact_url,
          '--public-key-id',
          self.pgp_key_fingerprint,
          '--signature-file',
          sig_path,
          '--validate',
      ])


class CreateBetaTest(
    binauthz_test_base.WithMockKms,
    binauthz_test_base.WithMockBetaBinauthz,
    CreateTest,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CreateAlphaTest(
    binauthz_test_base.WithMockKms,
    binauthz_test_base.WithMockAlphaBinauthz,
    CreateTest,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

    # TODO(b/159263189): Delete after removing ValidationHelperV1Alpha2 service.
    self.v1_messages = apis.GetMessagesModule('binaryauthorization',
                                              binauthz_apis.V1)

  def testCreateWithAttestor(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--public-key-id',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
        ]),
    )

  def testCreateWithAttestorUsingProjectFlag(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestor',
            self.attestor_id,
            '--attestor-project',
            self.attestor_project,
            '--artifact-url',
            self.artifact_url,
            '--public-key-id',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
        ]),
    )

  def testCreateWithExplicitPayloadFlag(self):
    # Construct payload without a trailing newline.
    fake_payload = binauthz_command_util.MakeSignaturePayload(
        self.artifact_url)[:-1]
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.CreateRequestAttestationOccurrence(
            project_ref=self.project_ref,
            artifact_url=self.artifact_url,
            note_ref=resources.REGISTRY.ParseRelativeName(
                relative_name=self.note_relative_name,
                collection='containeranalysis.projects.notes',
            ),
            plaintext=fake_payload,
            signatures=[(self.pgp_key_fingerprint, self.signature)],
        ))

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    payload_path = self.Touch(directory=self.cwd_path, contents=fake_payload)
    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--public-key-id',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
            '--payload-file',
            payload_path,
        ]),
    )

  # TODO(b/159263189): Delete after removing ValidationHelperV1Alpha2 service.
  def testCreateWithSuccessfulValidation(self):
    request_occurrence = self.CreateRequestAttestationOccurrence(
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        note_ref=resources.REGISTRY.ParseRelativeName(
            relative_name=self.note_relative_name,
            collection='containeranalysis.projects.notes',
        ),
        plaintext=self.signature,
        signatures=[(self.pgp_key_fingerprint, self.signature)],
    )
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=request_occurrence,
    )

    attestor_req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(
        attestor_req, response=self.attestor)

    validate_attestation_request = self.v1_messages.ValidateAttestationOccurrenceRequest(
        attestation=encoding.JsonToMessage(
            self.v1_messages.AttestationOccurrence,
            encoding.MessageToJson(request_occurrence.attestation)),
        occurrenceNote=request_occurrence.noteName,
        occurrenceResourceUri=request_occurrence.resourceUri,
    )
    validate_req = self.v1_messages.BinaryauthorizationProjectsAttestorsValidateAttestationOccurrenceRequest(
        attestor=self.attestor_relative_name,
        validateAttestationOccurrenceRequest=validate_attestation_request)
    validate_attestation_response = self.v1_messages.ValidateAttestationOccurrenceResponse(
        result=self.v1_messages.ValidateAttestationOccurrenceResponse
        .ResultValueValuesEnum.VERIFIED)
    self.v1_mock_client.projects_attestors.ValidateAttestationOccurrence.Expect(
        validate_req, response=validate_attestation_response)

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--public-key-id',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
            '--validate',
        ]),
    )

  # TODO(b/159263189): Delete after removing ValidationHelperV1Alpha2 service.
  def testCreateWithUnsuccessfulValidationWithOverride(self):
    request_occurrence = self.CreateRequestAttestationOccurrence(
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        note_ref=resources.REGISTRY.ParseRelativeName(
            relative_name=self.note_relative_name,
            collection='containeranalysis.projects.notes',
        ),
        plaintext=self.signature,
        signatures=[(self.pgp_key_fingerprint, self.signature)],
    )
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=request_occurrence,
    )

    attestor_req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(
        attestor_req, response=self.attestor)

    validate_attestation_request = self.v1_messages.ValidateAttestationOccurrenceRequest(
        attestation=encoding.JsonToMessage(
            self.v1_messages.AttestationOccurrence,
            encoding.MessageToJson(request_occurrence.attestation)),
        occurrenceNote=request_occurrence.noteName,
        occurrenceResourceUri=request_occurrence.resourceUri,
    )
    validate_req = self.v1_messages.BinaryauthorizationProjectsAttestorsValidateAttestationOccurrenceRequest(
        attestor=self.attestor_relative_name,
        validateAttestationOccurrenceRequest=validate_attestation_request)
    validate_attestation_response = self.v1_messages.ValidateAttestationOccurrenceResponse(
        result=self.v1_messages.ValidateAttestationOccurrenceResponse
        .ResultValueValuesEnum.ATTESTATION_NOT_VERIFIABLE,
        denialReason='You failed!')
    self.v1_mock_client.projects_attestors.ValidateAttestationOccurrence.Expect(
        validate_req, response=validate_attestation_response)

    self.WriteInput('y\n')

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--public-key-id',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
            '--validate',
        ]),
    )

  # TODO(b/159263189): Delete after removing ValidationHelperV1Alpha2 service.
  def testCreateWithUnsuccessfulValidationWithoutOverride(self):
    request_occurrence = self.CreateRequestAttestationOccurrence(
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        note_ref=resources.REGISTRY.ParseRelativeName(
            relative_name=self.note_relative_name,
            collection='containeranalysis.projects.notes',
        ),
        plaintext=self.signature,
        signatures=[(self.pgp_key_fingerprint, self.signature)],
    )

    attestor_req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(
        attestor_req, response=self.attestor)

    validate_attestation_request = self.v1_messages.ValidateAttestationOccurrenceRequest(
        attestation=encoding.JsonToMessage(
            self.v1_messages.AttestationOccurrence,
            encoding.MessageToJson(request_occurrence.attestation)),
        occurrenceNote=request_occurrence.noteName,
        occurrenceResourceUri=request_occurrence.resourceUri,
    )
    validate_req = self.v1_messages.BinaryauthorizationProjectsAttestorsValidateAttestationOccurrenceRequest(
        attestor=self.attestor_relative_name,
        validateAttestationOccurrenceRequest=validate_attestation_request)
    validate_attestation_response = self.v1_messages.ValidateAttestationOccurrenceResponse(
        result=self.v1_messages.ValidateAttestationOccurrenceResponse
        .ResultValueValuesEnum.ATTESTATION_NOT_VERIFIABLE,
        denialReason='You failed!')
    self.v1_mock_client.projects_attestors.ValidateAttestationOccurrence.Expect(
        validate_req, response=validate_attestation_response)

    self.WriteInput('n\n')

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)

    with self.assertRaises(OperationCancelledError):
      self.RunBinauthz([
          'attestations',
          'create',
          '--attestor',
          self.attestor_relative_name,
          '--artifact-url',
          self.artifact_url,
          '--public-key-id',
          self.pgp_key_fingerprint,
          '--signature-file',
          sig_path,
          '--validate',
      ])


class SignAndCreateTestBeta(
    binauthz_test_base.WithMockKms,
    binauthz_test_base.WithMockBetaBinauthz,
    binauthz_test_base.WithMockV1Containeranalysis,
    BaseAttestationsTest,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.keyversion_project = self.Project()
    self.keyversion_location = 'global'
    self.keyversion_keyring = 'testKeyRing'
    self.keyversion_key = 'testCryptoKey'
    self.keyversion_keyversion = '1'
    self.keyversion = 'projects/{}/locations/{}/keyRings/{}/cryptoKeys/{}/cryptoKeyVersions/{}'.format(
        self.keyversion_project, self.keyversion_location,
        self.keyversion_keyring, self.keyversion_key,
        self.keyversion_keyversion)

    self.kms_key_id = '//cloudkms.googleapis.com/v1/{}'.format(self.keyversion)
    self.request_occurrence = self.CreateRequestAttestationOccurrence(
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        note_ref=resources.REGISTRY.ParseRelativeName(
            relative_name=self.note_relative_name,
            collection='containeranalysis.projects.notes',
        ),
        plaintext=self.signature,
        signatures=[(self.kms_key_id, self.signature)],
    )

    self.digest = get_digest.GetDigestOfFile('sha256',
                                             six.BytesIO(self.signature))
    self.kms_sign_request = self.kms_messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsAsymmetricSignRequest(
        name=self.keyversion,
        asymmetricSignRequest=self.kms_messages.AsymmetricSignRequest(
            digest=self.digest))
    self.kms_sign_response = self.kms_messages.AsymmetricSignResponse(
        signature=self.signature,
    )
    self.kms_key_request = self.kms_messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetPublicKeyRequest(
        name=self.keyversion)
    self.kms_key_response = self.kms_messages.PublicKey(
        algorithm=self.kms_messages.PublicKey.AlgorithmValueValuesEnum
        .EC_SIGN_P256_SHA256,
        pem='public_key',
    )
    self.attestor = self.messages.Attestor(
        name=self.attestor_relative_name,
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference=self.note_relative_name,
            publicKeys=[
                self.messages.AttestorPublicKey(
                    id=self.kms_key_id,
                    pkixPublicKey=self.messages.PkixPublicKey(
                        publicKeyPem='pkix_public_key',
                        signatureAlgorithm=self.messages.PkixPublicKey
                        .SignatureAlgorithmValueValuesEnum.ECDSA_P256_SHA256,
                    ),
                )
            ],
        ))

  def testSignAndCreateWithAttestorAndKeyversion(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey.Expect(
        self.kms_key_request, self.kms_key_response)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.AsymmetricSign.Expect(
        self.kms_sign_request, self.kms_sign_response)

    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'sign-and-create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--keyversion',
            self.keyversion,
        ]),
    )

  def testSignAndCreateWithAttestorUsingProjectFlagAndKeyversion(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey.Expect(
        self.kms_key_request, self.kms_key_response)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.AsymmetricSign.Expect(
        self.kms_sign_request, self.kms_sign_response)

    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'sign-and-create',
            '--attestor',
            self.attestor_id,
            '--attestor-project',
            self.attestor_project,
            '--artifact-url',
            self.artifact_url,
            '--keyversion',
            self.keyversion,
        ]),
    )

  def testSignAndCreateWithAttestorAndKeyversionUsingKeyversionFlags(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey.Expect(
        self.kms_key_request, self.kms_key_response)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.AsymmetricSign.Expect(
        self.kms_sign_request, self.kms_sign_response)

    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'sign-and-create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--keyversion-project',
            self.keyversion_project,
            '--keyversion-location',
            self.keyversion_location,
            '--keyversion-keyring',
            self.keyversion_keyring,
            '--keyversion-key',
            self.keyversion_key,
            '--keyversion',
            self.keyversion_keyversion,
        ]),
    )

  def testSignAndCreateWithAttestorAndKeyversionWithPublicKeyIdOverride(self):
    override_id = 'overridden_id'
    id_override_attestor = self.messages.Attestor(
        name=self.attestor_relative_name,
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference=self.note_relative_name,
            publicKeys=[
                self.messages.AttestorPublicKey(
                    id=override_id,
                    pkixPublicKey=self.messages.PkixPublicKey(
                        publicKeyPem='pkix_public_key',
                        signatureAlgorithm=self.messages.PkixPublicKey
                        .SignatureAlgorithmValueValuesEnum.ECDSA_P256_SHA256,
                    ),
                )
            ],
        ))

    id_override_request_occurrence = self.CreateRequestAttestationOccurrence(
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        note_ref=resources.REGISTRY.ParseRelativeName(
            relative_name=self.note_relative_name,
            collection='containeranalysis.projects.notes',
        ),
        plaintext=self.signature,
        signatures=[(override_id, self.signature)],
    )

    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=id_override_request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(
        req, response=id_override_attestor)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey.Expect(
        self.kms_key_request, self.kms_key_response)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.AsymmetricSign.Expect(
        self.kms_sign_request, self.kms_sign_response)

    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'sign-and-create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--keyversion',
            self.keyversion,
            '--public-key-id-override',
            override_id,
        ]),
    )

  def testSignAndCreateWithSuccessfulValidation(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey.Expect(
        self.kms_key_request, self.kms_key_response)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.AsymmetricSign.Expect(
        self.kms_sign_request, self.kms_sign_response)

    validate_attestation_request = self.messages.ValidateAttestationOccurrenceRequest(
        attestation=encoding.JsonToMessage(
            self.messages.AttestationOccurrence,
            encoding.MessageToJson(self.request_occurrence.attestation)),
        occurrenceNote=self.request_occurrence.noteName,
        occurrenceResourceUri=self.request_occurrence.resourceUri,
    )
    validate_req = self.messages.BinaryauthorizationProjectsAttestorsValidateAttestationOccurrenceRequest(
        attestor=self.attestor_relative_name,
        validateAttestationOccurrenceRequest=validate_attestation_request)
    validate_attestation_response = self.messages.ValidateAttestationOccurrenceResponse(
        result=self.messages.ValidateAttestationOccurrenceResponse
        .ResultValueValuesEnum.VERIFIED)
    self.mock_client.projects_attestors.ValidateAttestationOccurrence.Expect(
        validate_req, response=validate_attestation_response)

    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'sign-and-create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--keyversion',
            self.keyversion,
            '--validate',
        ]),
    )

  def testSignAndCreateWithUnsuccessfulValidationWithOverride(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey.Expect(
        self.kms_key_request, self.kms_key_response)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.AsymmetricSign.Expect(
        self.kms_sign_request, self.kms_sign_response)

    validate_attestation_request = self.messages.ValidateAttestationOccurrenceRequest(
        attestation=encoding.JsonToMessage(
            self.messages.AttestationOccurrence,
            encoding.MessageToJson(self.request_occurrence.attestation)),
        occurrenceNote=self.request_occurrence.noteName,
        occurrenceResourceUri=self.request_occurrence.resourceUri,
    )
    validate_req = self.messages.BinaryauthorizationProjectsAttestorsValidateAttestationOccurrenceRequest(
        attestor=self.attestor_relative_name,
        validateAttestationOccurrenceRequest=validate_attestation_request)
    validate_attestation_response = self.messages.ValidateAttestationOccurrenceResponse(
        result=self.messages.ValidateAttestationOccurrenceResponse
        .ResultValueValuesEnum.ATTESTATION_NOT_VERIFIABLE,
        denialReason='You failed!')
    self.mock_client.projects_attestors.ValidateAttestationOccurrence.Expect(
        validate_req, response=validate_attestation_response)

    self.WriteInput('y\n')

    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'sign-and-create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--keyversion',
            self.keyversion,
            '--validate',
        ]),
    )

  def testSignAndCreateWithUnsuccessfulValidationWithoutOverride(self):
    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey.Expect(
        self.kms_key_request, self.kms_key_response)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.AsymmetricSign.Expect(
        self.kms_sign_request, self.kms_sign_response)

    validate_attestation_request = self.messages.ValidateAttestationOccurrenceRequest(
        attestation=encoding.JsonToMessage(
            self.messages.AttestationOccurrence,
            encoding.MessageToJson(self.request_occurrence.attestation)),
        occurrenceNote=self.request_occurrence.noteName,
        occurrenceResourceUri=self.request_occurrence.resourceUri,
    )
    validate_req = self.messages.BinaryauthorizationProjectsAttestorsValidateAttestationOccurrenceRequest(
        attestor=self.attestor_relative_name,
        validateAttestationOccurrenceRequest=validate_attestation_request)
    validate_attestation_response = self.messages.ValidateAttestationOccurrenceResponse(
        result=self.messages.ValidateAttestationOccurrenceResponse
        .ResultValueValuesEnum.ATTESTATION_NOT_VERIFIABLE,
        denialReason='You failed!')
    self.mock_client.projects_attestors.ValidateAttestationOccurrence.Expect(
        validate_req, response=validate_attestation_response)

    self.WriteInput('n\n')

    with self.assertRaises(OperationCancelledError):
      self.RunBinauthz([
          'attestations',
          'sign-and-create',
          '--attestor',
          self.attestor_relative_name,
          '--artifact-url',
          self.artifact_url,
          '--keyversion',
          self.keyversion,
          '--validate',
      ])


class SignAndCreateTestAlpha(
    binauthz_test_base.WithMockAlphaBinauthz,
    SignAndCreateTestBeta,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

    # The alpha track calls the V1 API for validation.
    # TODO(b/159263189): Delete after removing ValidationHelperV1Alpha2 service.
    self.v1_mock_client = self.CreateMockClient('binaryauthorization',
                                                binauthz_apis.V1)
    self.v1_messages = apis.GetMessagesModule('binaryauthorization',
                                              binauthz_apis.V1)

  def testSignAndCreateWithSuccessfulValidation(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey.Expect(
        self.kms_key_request, self.kms_key_response)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.AsymmetricSign.Expect(
        self.kms_sign_request, self.kms_sign_response)

    validate_attestation_request = self.v1_messages.ValidateAttestationOccurrenceRequest(
        attestation=encoding.JsonToMessage(
            self.v1_messages.AttestationOccurrence,
            encoding.MessageToJson(self.request_occurrence.attestation)),
        occurrenceNote=self.request_occurrence.noteName,
        occurrenceResourceUri=self.request_occurrence.resourceUri,
    )
    validate_req = self.v1_messages.BinaryauthorizationProjectsAttestorsValidateAttestationOccurrenceRequest(
        attestor=self.attestor_relative_name,
        validateAttestationOccurrenceRequest=validate_attestation_request)
    validate_attestation_response = self.v1_messages.ValidateAttestationOccurrenceResponse(
        result=self.v1_messages.ValidateAttestationOccurrenceResponse
        .ResultValueValuesEnum.VERIFIED)
    self.v1_mock_client.projects_attestors.ValidateAttestationOccurrence.Expect(
        validate_req, response=validate_attestation_response)

    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'sign-and-create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--keyversion',
            self.keyversion,
            '--validate',
        ]),
    )

  def testSignAndCreateWithUnsuccessfulValidationWithOverride(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey.Expect(
        self.kms_key_request, self.kms_key_response)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.AsymmetricSign.Expect(
        self.kms_sign_request, self.kms_sign_response)

    validate_attestation_request = self.v1_messages.ValidateAttestationOccurrenceRequest(
        attestation=encoding.JsonToMessage(
            self.v1_messages.AttestationOccurrence,
            encoding.MessageToJson(self.request_occurrence.attestation)),
        occurrenceNote=self.request_occurrence.noteName,
        occurrenceResourceUri=self.request_occurrence.resourceUri,
    )
    validate_req = self.v1_messages.BinaryauthorizationProjectsAttestorsValidateAttestationOccurrenceRequest(
        attestor=self.attestor_relative_name,
        validateAttestationOccurrenceRequest=validate_attestation_request)
    validate_attestation_response = self.v1_messages.ValidateAttestationOccurrenceResponse(
        result=self.v1_messages.ValidateAttestationOccurrenceResponse
        .ResultValueValuesEnum.ATTESTATION_NOT_VERIFIABLE,
        denialReason='You failed!')
    self.v1_mock_client.projects_attestors.ValidateAttestationOccurrence.Expect(
        validate_req, response=validate_attestation_response)

    self.WriteInput('y\n')

    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'sign-and-create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--keyversion',
            self.keyversion,
            '--validate',
        ]),
    )

  def testSignAndCreateWithUnsuccessfulValidationWithoutOverride(self):
    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,)
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey.Expect(
        self.kms_key_request, self.kms_key_response)

    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.AsymmetricSign.Expect(
        self.kms_sign_request, self.kms_sign_response)

    validate_attestation_request = self.v1_messages.ValidateAttestationOccurrenceRequest(
        attestation=encoding.JsonToMessage(
            self.v1_messages.AttestationOccurrence,
            encoding.MessageToJson(self.request_occurrence.attestation)),
        occurrenceNote=self.request_occurrence.noteName,
        occurrenceResourceUri=self.request_occurrence.resourceUri,
    )
    validate_req = self.v1_messages.BinaryauthorizationProjectsAttestorsValidateAttestationOccurrenceRequest(
        attestor=self.attestor_relative_name,
        validateAttestationOccurrenceRequest=validate_attestation_request)
    validate_attestation_response = self.v1_messages.ValidateAttestationOccurrenceResponse(
        result=self.v1_messages.ValidateAttestationOccurrenceResponse
        .ResultValueValuesEnum.ATTESTATION_NOT_VERIFIABLE,
        denialReason='You failed!')
    self.v1_mock_client.projects_attestors.ValidateAttestationOccurrence.Expect(
        validate_req, response=validate_attestation_response)

    self.WriteInput('n\n')

    with self.assertRaises(OperationCancelledError):
      self.RunBinauthz([
          'attestations',
          'sign-and-create',
          '--attestor',
          self.attestor_relative_name,
          '--artifact-url',
          self.artifact_url,
          '--keyversion',
          self.keyversion,
          '--validate',
      ])


class ListTest(
    binauthz_test_base.WithMockV1Containeranalysis,
    binauthz_test_base.WithMockGaBinauthz,
    BaseAttestationsTest,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.response_occurrence = self.CreateResponseOccurrence(
        request_occurrence=self.request_occurrence,
        project_ref=self.project_ref,
    )

  def testAllAttestations(self):
    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,
    )
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        expected_filter_content='',
        occurrences_to_return=[self.response_occurrence],
    )

    self.RunBinauthz([
        'attestations',
        'list',
        '--attestor',
        self.attestor_relative_name,
    ])

    self.AssertOutputContains(self.pgp_key_fingerprint)
    self.AssertOutputContains(self.artifact_url)

  def testArtifactUrl(self):
    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,
    )
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        expected_filter_content='resourceUrl="{}"'.format(self.artifact_url),
        occurrences_to_return=[self.response_occurrence],
    )
    self.RunBinauthz([
        'attestations',
        'list',
        '--attestor',
        self.attestor_relative_name,
        '--artifact-url',
        self.artifact_url,
    ])

    self.AssertOutputContains(self.pgp_key_fingerprint)
    self.AssertOutputContains(self.artifact_url)

  def testArtifactUrl_AttestorWithProject(self):
    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,
    )
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        expected_filter_content='resourceUrl="{}"'.format(self.artifact_url),
        occurrences_to_return=[self.response_occurrence],
    )

    self.RunBinauthz([
        'attestations',
        'list',
        '--attestor',
        self.attestor_id,
        '--attestor-project',
        self.attestor_project,
        '--artifact-url',
        self.artifact_url,
    ])

    self.AssertOutputContains(self.pgp_key_fingerprint)
    self.AssertOutputContains(self.artifact_url)


class ListBetaTest(
    binauthz_test_base.WithMockBetaBinauthz,
    ListTest,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ListAlphaTest(
    binauthz_test_base.WithMockAlphaBinauthz,
    ListBetaTest,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
