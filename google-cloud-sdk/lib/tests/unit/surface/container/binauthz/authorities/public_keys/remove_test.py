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

"""Tests for surface.container.binauthz.authorities.public_keys.remove."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import datetime
import textwrap

from googlecloudsdk.command_lib.container.binauthz import exceptions
from googlecloudsdk.core.util import times
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class RemoveTest(sdk_test_base.WithTempCWD,
                 base.BinauthzMockedPolicyClientUnitTest):

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
    self.aa = self.messages.AttestationAuthority(
        name='projects/{}/attestationAuthorities/{}'.format(proj, self.name),
        systemOwnedDrydockNote=None,
        updateTime=times.FormatDateTime(datetime.datetime.utcnow()),
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='providers/{}/notes/{}'.format(proj, self.name),
            publicKeys=[
                self.messages.AttestationAuthorityPublicKey(
                    asciiArmoredPgpPublicKey=self.ascii_armored_key,
                    comment=None,
                    id=self.fingerprint),
            ],
        ))

    self.updated_aa = copy.deepcopy(self.aa)
    self.updated_aa.userOwnedDrydockNote.publicKeys = []
    self.updated_aa.updateTime = (
        times.FormatDateTime(datetime.datetime.utcnow()))

    self.req = self.messages.BinaryauthorizationProjectsAttestationAuthoritiesGetRequest(  # pylint: disable=line-too-long
        name=self.aa.name)

  def testSuccess_KeyId(self):
    self.client.projects_attestationAuthorities.Get.Expect(
        self.req, response=self.aa)
    self.client.projects_attestationAuthorities.Update.Expect(
        self.aa, response=self.updated_aa)

    response = self.RunBinauthz(
        'authorities public-keys remove {fingerprint} '
        '--authority={name}'.format(
            fingerprint=self.fingerprint, name=self.name))

    self.assertIsNone(response)

  def testSuccess_MultipleMatches(self):
    self.aa.userOwnedDrydockNote.publicKeys.append(
        self.messages.AttestationAuthorityPublicKey(
            asciiArmoredPgpPublicKey=self.ascii_armored_key,
            comment=None,
            id='other_key'))

    self.client.projects_attestationAuthorities.Get.Expect(
        self.req, response=self.aa)
    self.client.projects_attestationAuthorities.Update.Expect(
        self.aa, response=self.updated_aa)

    response = self.RunBinauthz(
        'authorities public-keys remove {fingerprint} '
        '--authority={name}'.format(
            fingerprint=self.fingerprint, name=self.name))

    self.assertIsNone(response)

  def testUnknownKeyId(self):
    self.client.projects_attestationAuthorities.Get.Expect(
        self.req, response=self.aa)

    with self.assertRaises(exceptions.NotFoundError):
      self.RunBinauthz(
          'authorities public-keys remove {fingerprint} '
          '--authority={name}'.format(
              fingerprint='not_a_real_id', name=self.name))

  def testUnknownPubKey(self):
    self.aa.userOwnedDrydockNote.publicKeys[0].asciiArmoredPgpPublicKey = 'foo'
    self.client.projects_attestationAuthorities.Get.Expect(
        self.req, response=self.aa)

    with self.assertRaises(exceptions.NotFoundError):
      self.RunBinauthz(
          'authorities public-keys remove {fingerprint} '
          '--authority={name}'.format(
              fingerprint='not_a_real_id', name=self.name))

  def testEmptyPubKeyField(self):
    self.client.projects_attestationAuthorities.Get.Expect(
        self.req, response=self.updated_aa)

    with self.assertRaises(exceptions.NotFoundError):
      self.RunBinauthz(
          'authorities public-keys remove {fingerprint} '
          '--authority={name}'.format(
              fingerprint='not_a_real_id', name=self.name))


if __name__ == '__main__':
  test_case.main()
