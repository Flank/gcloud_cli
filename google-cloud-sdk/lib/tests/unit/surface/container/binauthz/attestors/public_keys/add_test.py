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

from googlecloudsdk.command_lib.container.binauthz import exceptions
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class AddTest(sdk_test_base.WithTempCWD,
              base.BinauthzMockedBetaPolicyClientUnitTest):

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

    self.client.projects_attestors.Get.Expect(
        req, response=attestor)
    self.client.projects_attestors.Update.Expect(
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

    self.client.projects_attestors.Get.Expect(
        req, response=attestor)

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


if __name__ == '__main__':
  test_case.main()
