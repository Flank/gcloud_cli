# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Tests for surface.container.binauthz.attestors.public_keys.add."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import datetime
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.binauthz import exceptions
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class AddTest(
    sdk_test_base.WithTempCWD,
    base.WithMockBetaBinauthz,
    base.BinauthzTestBase,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testSuccess(self):
    ascii_armored_key = textwrap.dedent("""
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        aBcDeFg
        aBcDeFg
        aBcDeFg
        -----END PGP PUBLIC KEY BLOCK-----
    """)
    fname = self.Touch(directory=self.cwd_path, contents=ascii_armored_key)

    name = 'bar'
    proj = self.Project()
    new_pub_key = self.messages.AttestorPublicKey(
        asciiArmoredPgpPublicKey=ascii_armored_key,
        comment=None,
        id='0638AttestorDD940361EA2D7F14C58C124F0E663DA097')
    attestor = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, name),
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='projects/{}/notes/{}'.format(proj, name),
            publicKeys=[],
        ))

    updated_attestor = copy.deepcopy(attestor)
    updated_attestor.userOwnedDrydockNote.publicKeys.append(new_pub_key)
    updated_attestor.updateTime = times.FormatDateTime(
        datetime.datetime.utcnow())

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(  # pylint: disable=line-too-long
        name=attestor.name)

    self.mock_client.projects_attestors.Get.Expect(req, response=attestor)
    self.mock_client.projects_attestors.Update.Expect(
        attestor, response=updated_attestor)

    response = self.RunBinauthz(
        'attestors public-keys add '
        '--attestor={name} --public-key-file={fname}'.format(
            name=name, fname=fname))

    self.assertEqual(response, new_pub_key)

  def testAlreadyExists(self):
    ascii_armored_key = textwrap.dedent("""
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        aBcDeFg
        aBcDeFg
        aBcDeFg
        -----END PGP PUBLIC KEY BLOCK-----
    """)
    fname = self.Touch(directory=self.cwd_path, contents=ascii_armored_key)

    name = 'bar'
    proj = self.Project()
    new_pub_key = self.messages.AttestorPublicKey(
        asciiArmoredPgpPublicKey=ascii_armored_key,
        comment=None,
        id='0638AttestorDD940361EA2D7F14C58C124F0E663DA097')
    attestor = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, name),
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='projects/{}/notes/{}'.format(proj, name),
            publicKeys=[new_pub_key],
        ))

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(  # pylint: disable=line-too-long
        name=attestor.name)

    self.mock_client.projects_attestors.Get.Expect(req, response=attestor)

    with self.assertRaises(exceptions.AlreadyExistsError):
      self.RunBinauthz(
          'attestors public-keys add '
          '--attestor={name} --public-key-file={fname}'.format(
              name=name, fname=fname))

  def testUnknownFile(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunBinauthz(
          'attestors public-keys add '
          '--attestor=any-old-name --public-key-file=not-a-real-file.pub')


class AddAlphaTest(
    sdk_test_base.WithTempCWD,
    base.WithMockKms,
    base.WithMockAlphaBinauthz,
    base.BinauthzTestBase,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testSuccessPgp(self):
    ascii_armored_key = textwrap.dedent("""
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        aBcDeFg
        aBcDeFg
        aBcDeFg
        -----END PGP PUBLIC KEY BLOCK-----
    """)
    fname = self.Touch(directory=self.cwd_path, contents=ascii_armored_key)

    name = 'bar'
    proj = self.Project()
    expected_output_pub_key = self.messages.AttestorPublicKey(
        asciiArmoredPgpPublicKey=ascii_armored_key,
        comment=None,
        id='0638AttestorDD940361EA2D7F14C58C124F0E663DA097')
    expected_input_pub_key = self.messages.AttestorPublicKey(
        asciiArmoredPgpPublicKey=ascii_armored_key,
        comment=None,
        id=None)
    attestor = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, name),
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='projects/{}/notes/{}'.format(proj, name),
            publicKeys=[],
        ))

    input_attestor = copy.deepcopy(attestor)
    input_attestor.userOwnedDrydockNote.publicKeys.append(
        expected_input_pub_key)

    output_attestor = copy.deepcopy(attestor)
    output_attestor.userOwnedDrydockNote.publicKeys.append(
        expected_output_pub_key)
    output_attestor.updateTime = times.FormatDateTime(
        datetime.datetime.utcnow())

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=attestor.name)

    self.mock_client.projects_attestors.Get.Expect(
        req, response=copy.deepcopy(attestor))
    self.mock_client.projects_attestors.Update.Expect(
        input_attestor, response=output_attestor)

    response = self.RunBinauthz(
        'attestors public-keys add '
        '--attestor={name} --pgp-public-key-file={fname}'.format(
            name=name, fname=fname))

    self.assertEqual(response, expected_output_pub_key)

  def testSuccessKms(self):
    pem = textwrap.dedent("""
        -----BEGIN PUBLIC KEY-----
        aBcDeFg
        aBcDeFg
        aBcDeFg
        -----END PUBLIC KEY-----
    """)
    name = 'bar'
    proj = self.Project()
    key_resource = (
        'projects/{}/locations/us-west1-a/keyRings/foo/cryptoKeys/baz/cryptoKeyVersions/qux'
        .format(proj))
    expected_output_pub_key = self.messages.AttestorPublicKey(
        pkixPublicKey=self.messages.PkixPublicKey(
            publicKeyPem=pem,
            signatureAlgorithm=(
                self.messages.PkixPublicKey.
                SignatureAlgorithmValueValuesEnum.ECDSA_P256_SHA256),
        ),
        comment=None,
        id='//cloudkms.googleapis.com/v1/' + key_resource)
    expected_input_pub_key = expected_output_pub_key
    attestor = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, name),
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='projects/{}/notes/{}'.format(proj, name),
            publicKeys=[],
        ))

    input_attestor = copy.deepcopy(attestor)
    input_attestor.userOwnedDrydockNote.publicKeys.append(
        expected_input_pub_key)

    output_attestor = copy.deepcopy(attestor)
    output_attestor.userOwnedDrydockNote.publicKeys.append(
        expected_output_pub_key)
    output_attestor.updateTime = times.FormatDateTime(
        datetime.datetime.utcnow())

    # Set up KMS call.
    req = self.kms_messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetPublicKeyRequest(
        name=key_resource)
    resp = self.kms_messages.PublicKey(
        pem=pem,
        algorithm=(self.kms_messages.PublicKey.AlgorithmValueValuesEnum.
                   EC_SIGN_P256_SHA256))
    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey.Expect(
        req, response=resp)

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=attestor.name)
    self.mock_client.projects_attestors.Get.Expect(
        req, response=copy.deepcopy(attestor))
    self.mock_client.projects_attestors.Update.Expect(
        input_attestor, response=output_attestor)

    response = self.RunBinauthz(
        'attestors public-keys add '
        '--attestor={name} --keyversion={key_resource}'.format(
            name=name, key_resource=key_resource))

    self.assertEqual(response, expected_output_pub_key)

  def testSuccessPkix(self):
    pem = textwrap.dedent("""
        -----BEGIN PUBLIC KEY-----
        aBcDeFg
        aBcDeFg
        aBcDeFg
        -----END PUBLIC KEY-----
    """)
    fname = self.Touch(directory=self.cwd_path, contents=pem)

    name = 'bar'
    proj = self.Project()
    expected_output_pub_key = self.messages.AttestorPublicKey(
        pkixPublicKey=self.messages.PkixPublicKey(
            publicKeyPem=pem,
            signatureAlgorithm=(
                self.messages.PkixPublicKey.
                SignatureAlgorithmValueValuesEnum.ECDSA_P256_SHA256),
        ),
        comment=None,
        id='ni://sha256;0638attestordd940361ea2d7f14c58c124f0e663da097')
    expected_input_pub_key = self.messages.AttestorPublicKey(
        pkixPublicKey=self.messages.PkixPublicKey(
            publicKeyPem=pem,
            signatureAlgorithm=(
                self.messages.PkixPublicKey.
                SignatureAlgorithmValueValuesEnum.ECDSA_P256_SHA256),
        ),
        comment=None,
        id=None)
    attestor = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, name),
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='projects/{}/notes/{}'.format(proj, name),
            publicKeys=[],
        ))

    input_attestor = copy.deepcopy(attestor)
    input_attestor.userOwnedDrydockNote.publicKeys.append(
        expected_input_pub_key)

    output_attestor = copy.deepcopy(attestor)
    output_attestor.userOwnedDrydockNote.publicKeys.append(
        expected_output_pub_key)
    output_attestor.updateTime = times.FormatDateTime(
        datetime.datetime.utcnow())

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=attestor.name)
    self.mock_client.projects_attestors.Get.Expect(
        req, response=copy.deepcopy(attestor))
    self.mock_client.projects_attestors.Update.Expect(
        input_attestor, response=output_attestor)

    response = self.RunBinauthz(
        'attestors public-keys add '
        '--pkix-public-key-algorithm=ecdsa-p256-sha256 '
        '--attestor={name} --pkix-public-key-file={fname}'.format(
            name=name, fname=fname))

    self.assertEqual(response, expected_output_pub_key)

  def testSuccessWithPublicKeyOverride(self):
    pem = textwrap.dedent("""
        -----BEGIN PUBLIC KEY-----
        aBcDeFg
        aBcDeFg
        aBcDeFg
        -----END PUBLIC KEY-----
    """)
    name = 'bar'
    proj = self.Project()
    key_resource = (
        'projects/{}/locations/us-west1-a/keyRings/foo/cryptoKeys/baz/cryptoKeyVersions/qux'
        .format(proj))
    id_override = 'http://google.com/'
    expected_output_pub_key = self.messages.AttestorPublicKey(
        pkixPublicKey=self.messages.PkixPublicKey(
            publicKeyPem=pem,
            signatureAlgorithm=(
                self.messages.PkixPublicKey.
                SignatureAlgorithmValueValuesEnum.ECDSA_P256_SHA256),
        ),
        comment=None,
        id=id_override)
    expected_input_pub_key = expected_output_pub_key
    attestor = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, name),
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='projects/{}/notes/{}'.format(proj, name),
            publicKeys=[],
        ))

    input_attestor = copy.deepcopy(attestor)
    input_attestor.userOwnedDrydockNote.publicKeys.append(
        expected_input_pub_key)

    output_attestor = copy.deepcopy(attestor)
    output_attestor.userOwnedDrydockNote.publicKeys.append(
        expected_output_pub_key)
    output_attestor.updateTime = times.FormatDateTime(
        datetime.datetime.utcnow())

    # Set up KMS call.
    req = self.kms_messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetPublicKeyRequest(
        name=key_resource)
    resp = self.kms_messages.PublicKey(
        pem=pem,
        algorithm=(self.kms_messages.PublicKey.AlgorithmValueValuesEnum.
                   EC_SIGN_P256_SHA256))
    self.mock_kms_client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey.Expect(
        req, response=resp)

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=attestor.name)
    self.mock_client.projects_attestors.Get.Expect(
        req, response=copy.deepcopy(attestor))
    self.mock_client.projects_attestors.Update.Expect(
        input_attestor, response=output_attestor)

    response = self.RunBinauthz(
        'attestors public-keys add '
        '--attestor={name} --keyversion={key_resource} '
        '--public-key-id-override={id_override}'.format(
            name=name, key_resource=key_resource, id_override=id_override))

    self.assertEqual(response, expected_output_pub_key)

  def testAlreadyExistsPgp(self):
    ascii_armored_key = textwrap.dedent("""
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        aBcDeFg
        aBcDeFg
        aBcDeFg
        -----END PGP PUBLIC KEY BLOCK-----
    """)
    fname = self.Touch(directory=self.cwd_path, contents=ascii_armored_key)

    name = 'bar'
    proj = self.Project()
    new_pub_key = self.messages.AttestorPublicKey(
        asciiArmoredPgpPublicKey=ascii_armored_key,
        comment=None,
        id='0638AttestorDD940361EA2D7F14C58C124F0E663DA097')
    attestor = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, name),
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='projects/{}/notes/{}'.format(proj, name),
            publicKeys=[new_pub_key],
        ))

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=attestor.name)

    self.mock_client.projects_attestors.Get.Expect(req, response=attestor)

    with self.assertRaises(exceptions.AlreadyExistsError):
      self.RunBinauthz(
          'attestors public-keys add '
          '--attestor={name} --pgp-public-key-file={fname}'.format(
              name=name, fname=fname))

  def testAlreadyExistsPkix(self):
    pem = textwrap.dedent("""
        -----BEGIN PUBLIC KEY-----
        aBcDeFg
        aBcDeFg
        aBcDeFg
        -----END PUBLIC KEY-----
    """)
    fname = self.Touch(directory=self.cwd_path, contents=pem)

    name = 'bar'
    proj = self.Project()
    new_pub_key = self.messages.AttestorPublicKey(
        pkixPublicKey=self.messages.PkixPublicKey(
            publicKeyPem=pem,
            signatureAlgorithm=(
                self.messages.PkixPublicKey.
                SignatureAlgorithmValueValuesEnum.ECDSA_P256_SHA256),
        ),
        comment=None,
        id='ni://sha256;0638attestordd940361ea2d7f14c58c124f0e663da097')
    attestor = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, name),
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='projects/{}/notes/{}'.format(proj, name),
            publicKeys=[new_pub_key],
        ))

    updated_attestor = copy.deepcopy(attestor)
    updated_attestor.userOwnedDrydockNote.publicKeys.append(new_pub_key)
    updated_attestor.updateTime = times.FormatDateTime(
        datetime.datetime.utcnow())

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=attestor.name)
    self.mock_client.projects_attestors.Get.Expect(req, response=attestor)

    with self.assertRaises(exceptions.AlreadyExistsError):
      self.RunBinauthz(
          'attestors public-keys add '
          '--pkix-public-key-algorithm=ecdsa-p256-sha256 '
          '--public-key-id-override={id_override} '
          '--attestor={name} --pkix-public-key-file={fname}'.format(
              name=name, fname=fname, id_override=new_pub_key.id))

  def testOverridingPgpId(self):
    ascii_armored_key = textwrap.dedent("""
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        aBcDeFg
        aBcDeFg
        aBcDeFg
        -----END PGP PUBLIC KEY BLOCK-----
    """)
    fname = self.Touch(directory=self.cwd_path, contents=ascii_armored_key)
    name = 'bar'
    with self.assertRaises(exceptions.InvalidArgumentError):
      self.RunBinauthz(
          'attestors public-keys add '
          '--public-key-id-override=foo '
          '--attestor={name} --pgp-public-key-file={fname}'.format(
              name=name, fname=fname))

  def testUnknownFile(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunBinauthz(
          'attestors public-keys add '
          '--attestor=any-old-name --pgp-public-key-file=not-a-real-file.pub')

if __name__ == '__main__':
  test_case.main()
