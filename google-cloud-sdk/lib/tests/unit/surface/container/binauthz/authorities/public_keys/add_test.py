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

"""Tests for surface.container.binauthz.authorities.public_keys.add."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import datetime
import textwrap

from googlecloudsdk.command_lib.container.binauthz import exceptions
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class AddTest(sdk_test_base.WithTempCWD,
              base.BinauthzMockedPolicyClientUnitTest):

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
    new_pub_key = self.messages.AttestationAuthorityPublicKey(
        asciiArmoredPgpPublicKey=ascii_armored_key,
        comment=None,
        id='0638AADD940361EA2D7F14C58C124F0E663DA097')
    aa = self.messages.AttestationAuthority(
        name='projects/{}/attestationAuthorities/{}'.format(proj, name),
        systemOwnedDrydockNote=None,
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='providers/{}/notes/{}'.format(proj, name),
            publicKeys=[],
        ))

    updated_aa = copy.deepcopy(aa)
    updated_aa.userOwnedDrydockNote.publicKeys.append(new_pub_key)
    updated_aa.updateTime = times.FormatDateTime(datetime.datetime.utcnow())

    req = self.messages.BinaryauthorizationProjectsAttestationAuthoritiesGetRequest(  # pylint: disable=line-too-long
        name=aa.name)

    self.client.projects_attestationAuthorities.Get.Expect(
        req, response=aa)
    self.client.projects_attestationAuthorities.Update.Expect(
        aa, response=updated_aa)

    response = self.RunBinauthz(
        'authorities public-keys add '
        '--authority={name} --public-key-file={fname}'.format(
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
    new_pub_key = self.messages.AttestationAuthorityPublicKey(
        asciiArmoredPgpPublicKey=ascii_armored_key,
        comment=None,
        id='0638AADD940361EA2D7F14C58C124F0E663DA097')
    aa = self.messages.AttestationAuthority(
        name='projects/{}/attestationAuthorities/{}'.format(proj, name),
        systemOwnedDrydockNote=None,
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='providers/{}/notes/{}'.format(proj, name),
            publicKeys=[new_pub_key],
        ))

    req = self.messages.BinaryauthorizationProjectsAttestationAuthoritiesGetRequest(  # pylint: disable=line-too-long
        name=aa.name)

    self.client.projects_attestationAuthorities.Get.Expect(
        req, response=aa)

    with self.assertRaises(exceptions.AlreadyExistsError):
      self.RunBinauthz(
          'authorities public-keys add '
          '--authority={name} --public-key-file={fname}'.format(
              name=name, fname=fname))

  def testUnknownFile(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunBinauthz(
          'authorities public-keys add '
          '--authority=any-old-name --public-key-file=not-a-real-file.pub')


if __name__ == '__main__':
  test_case.main()
