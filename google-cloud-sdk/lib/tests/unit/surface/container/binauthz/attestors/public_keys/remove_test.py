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

"""Tests for surface.container.binauthz.attestors.public_keys.remove."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import datetime
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.binauthz import exceptions
from googlecloudsdk.core.util import times
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class RemoveTest(
    sdk_test_base.WithTempCWD,
    base.WithMockBetaBinauthz,
    base.BinauthzTestBase,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.ascii_armored_key = textwrap.dedent("""
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        aBcDeFg
        aBcDeFg
        aBcDeFg
        -----END PGP PUBLIC KEY BLOCK-----
    """)

    self.name = 'bar'
    proj = self.Project()
    self.fingerprint = 'new_key'
    self.attestor = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, self.name),
        updateTime=times.FormatDateTime(datetime.datetime.utcnow()),
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='projects/{}/notes/{}'.format(proj, self.name),
            publicKeys=[
                self.messages.AttestorPublicKey(
                    asciiArmoredPgpPublicKey=self.ascii_armored_key,
                    comment=None,
                    id=self.fingerprint),
            ],
        ))

    self.updated_attestor = copy.deepcopy(self.attestor)
    self.updated_attestor.userOwnedDrydockNote.publicKeys = []
    self.updated_attestor.updateTime = (
        times.FormatDateTime(datetime.datetime.utcnow()))

    self.req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(  # pylint: disable=line-too-long
        name=self.attestor.name)

  def testSuccess_KeyId(self):
    self.mock_client.projects_attestors.Get.Expect(
        self.req, response=self.attestor)
    self.mock_client.projects_attestors.Update.Expect(
        self.attestor, response=self.updated_attestor)

    response = self.RunBinauthz(
        'attestors public-keys remove {fingerprint} '
        '--attestor={name}'.format(
            fingerprint=self.fingerprint, name=self.name))

    self.assertIsNone(response)

  def testSuccess_MultipleMatches(self):
    self.attestor.userOwnedDrydockNote.publicKeys.append(
        self.messages.AttestorPublicKey(
            asciiArmoredPgpPublicKey=self.ascii_armored_key,
            comment=None,
            id='other_key'))

    self.mock_client.projects_attestors.Get.Expect(
        self.req, response=self.attestor)
    self.mock_client.projects_attestors.Update.Expect(
        self.attestor, response=self.updated_attestor)

    response = self.RunBinauthz(
        'attestors public-keys remove {fingerprint} '
        '--attestor={name}'.format(
            fingerprint=self.fingerprint, name=self.name))

    self.assertIsNone(response)

  def testUnknownKeyId(self):
    self.mock_client.projects_attestors.Get.Expect(
        self.req, response=self.attestor)

    with self.assertRaises(exceptions.NotFoundError):
      self.RunBinauthz(
          'attestors public-keys remove {fingerprint} '
          '--attestor={name}'.format(
              fingerprint='not_a_real_id', name=self.name))

  def testUnknownPubKey(self):
    pub_key = self.attestor.userOwnedDrydockNote.publicKeys[0]
    pub_key.asciiArmoredPgpPublicKey = 'foo'
    self.mock_client.projects_attestors.Get.Expect(
        self.req, response=self.attestor)

    with self.assertRaises(exceptions.NotFoundError):
      self.RunBinauthz(
          'attestors public-keys remove {fingerprint} '
          '--attestor={name}'.format(
              fingerprint='not_a_real_id', name=self.name))

  def testEmptyPubKeyField(self):
    self.mock_client.projects_attestors.Get.Expect(
        self.req, response=self.updated_attestor)

    with self.assertRaises(exceptions.NotFoundError):
      self.RunBinauthz(
          'attestors public-keys remove {fingerprint} '
          '--attestor={name}'.format(
              fingerprint='not_a_real_id', name=self.name))


class RemoveAlphaTest(
    sdk_test_base.WithTempCWD,
    base.WithMockAlphaBinauthz,
    base.BinauthzTestBase,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.ascii_armored_key = textwrap.dedent("""
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        aBcDeFg
        aBcDeFg
        aBcDeFg
        -----END PGP PUBLIC KEY BLOCK-----
    """)

    self.name = 'bar'
    proj = self.Project()
    self.fingerprint = 'new_key'
    self.attestor = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, self.name),
        updateTime=times.FormatDateTime(datetime.datetime.utcnow()),
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='projects/{}/notes/{}'.format(proj, self.name),
            publicKeys=[
                self.messages.AttestorPublicKey(
                    asciiArmoredPgpPublicKey=self.ascii_armored_key,
                    comment=None,
                    id=self.fingerprint),
            ],
        ))

    self.updated_attestor = copy.deepcopy(self.attestor)
    self.updated_attestor.userOwnedDrydockNote.publicKeys = []

    self.req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor.name)

  def testSuccess_KeyId(self):
    self.mock_client.projects_attestors.Get.Expect(
        self.req, response=copy.deepcopy(self.attestor))
    self.mock_client.projects_attestors.Update.Expect(
        self.updated_attestor, response=self.updated_attestor)

    response = self.RunBinauthz(
        'attestors public-keys remove {fingerprint} '
        '--attestor={name}'.format(
            fingerprint=self.fingerprint, name=self.name))

    self.assertIsNone(response)

  def testSuccess_MultipleMatches(self):
    other_key = self.messages.AttestorPublicKey(
        asciiArmoredPgpPublicKey=self.ascii_armored_key,
        comment=None,
        id='other_key')
    self.updated_attestor.userOwnedDrydockNote.publicKeys.append(
        other_key)
    self.attestor.userOwnedDrydockNote.publicKeys.append(
        other_key)

    self.mock_client.projects_attestors.Get.Expect(
        self.req, response=copy.deepcopy(self.attestor))
    self.mock_client.projects_attestors.Update.Expect(
        self.updated_attestor, response=self.updated_attestor)

    response = self.RunBinauthz(
        'attestors public-keys remove {fingerprint} '
        '--attestor={name}'.format(
            fingerprint=self.fingerprint, name=self.name))

    self.assertIsNone(response)

  def testUnknownKeyId(self):
    self.mock_client.projects_attestors.Get.Expect(
        self.req, response=copy.deepcopy(self.attestor))

    with self.assertRaises(exceptions.NotFoundError):
      self.RunBinauthz(
          'attestors public-keys remove {fingerprint} '
          '--attestor={name}'.format(
              fingerprint='not_a_real_id', name=self.name))

  def testUnknownPubKey(self):
    pub_key = self.attestor.userOwnedDrydockNote.publicKeys[0]
    pub_key.asciiArmoredPgpPublicKey = 'foo'
    self.mock_client.projects_attestors.Get.Expect(
        self.req, response=copy.deepcopy(self.attestor))

    with self.assertRaises(exceptions.NotFoundError):
      self.RunBinauthz(
          'attestors public-keys remove {fingerprint} '
          '--attestor={name}'.format(
              fingerprint='not_a_real_id', name=self.name))

  def testEmptyPubKeyField(self):
    self.mock_client.projects_attestors.Get.Expect(
        self.req, response=copy.deepcopy(self.attestor))

    with self.assertRaises(exceptions.NotFoundError):
      self.RunBinauthz(
          'attestors public-keys remove {fingerprint} '
          '--attestor={name}'.format(
              fingerprint='not_a_real_id', name=self.name))


if __name__ == '__main__':
  test_case.main()
