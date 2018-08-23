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

"""Tests for surface.container.binauthz.attestors.public_keys.update."""

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


class UpdateTest(sdk_test_base.WithTempCWD,
                 base.BinauthzMockedBetaPolicyClientUnitTest):

  def SetUp(self):
    self.ascii_armored_key = textwrap.dedent("""
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        Key1
        Key1
        Key1
        -----END PGP PUBLIC KEY BLOCK-----
    """)
    self.name = 'bar'
    proj = self.Project()
    self.fingerprint = '0638AttestorDD940361EA2D7F14C58C124F0E663DA097'
    self.existing_pub_key = self.messages.AttestorPublicKey(
        asciiArmoredPgpPublicKey=self.ascii_armored_key,
        comment=None,
        id=self.fingerprint)
    self.attestor = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, self.name),
        updateTime=times.FormatDateTime(datetime.datetime.utcnow()),
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='projects/{}/notes/{}'.format(proj, self.name),
            publicKeys=[self.existing_pub_key],
        ))

    self.updated_pub_key = copy.deepcopy(self.existing_pub_key)
    self.updated_ascii_armored_key = (
        self.ascii_armored_key.replace('Key1', 'Key2'))
    self.updated_pub_key.asciiArmoredPgpPublicKey = (
        self.updated_ascii_armored_key)
    self.updated_attestor = copy.deepcopy(self.attestor)
    self.updated_attestor.userOwnedDrydockNote.publicKeys = [
        self.updated_pub_key]

    self.fname = self.Touch(
        directory=self.cwd_path, contents=self.updated_ascii_armored_key)

    self.req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(  # pylint: disable=line-too-long
        name=self.attestor.name)

  def testSuccess(self):
    self.client.projects_attestors.Get.Expect(
        self.req, response=self.attestor)
    self.client.projects_attestors.Update.Expect(
        self.updated_attestor, response=self.updated_attestor)

    response = self.RunBinauthz(
        'attestors public-keys update {fingerprint} '
        '--attestor={name} --public-key-file={fname}'.format(
            fingerprint=self.existing_pub_key.id, name=self.name,
            fname=self.fname))

    self.assertEqual(response, self.updated_pub_key)

  def testSuccess_AddComment(self):
    self.updated_pub_key.comment = 'foo'

    self.client.projects_attestors.Get.Expect(
        self.req, response=self.attestor)
    self.client.projects_attestors.Update.Expect(
        self.updated_attestor, response=self.updated_attestor)

    response = self.RunBinauthz(
        'attestors public-keys update {fingerprint} '
        '--attestor={name} --public-key-file={fname} --comment="foo"'.format(
            fingerprint=self.existing_pub_key.id, name=self.name,
            fname=self.fname))

    self.assertEqual(response, self.updated_pub_key)

  def testSuccess_RemoveComment(self):
    self.existing_pub_key.comment = 'A comment'
    self.updated_pub_key.comment = ''

    self.client.projects_attestors.Get.Expect(
        self.req, response=self.attestor)
    self.client.projects_attestors.Update.Expect(
        self.updated_attestor, response=self.updated_attestor)

    response = self.RunBinauthz(
        'attestors public-keys update {fingerprint} '
        '--attestor={name} --public-key-file={fname} --comment='.format(
            fingerprint=self.existing_pub_key.id, name=self.name,
            fname=self.fname))

    self.assertEqual(response, self.updated_pub_key)

  def testSuccess_EmptyUpdate(self):
    self.client.projects_attestors.Get.Expect(
        self.req, response=self.attestor)
    self.client.projects_attestors.Update.Expect(
        self.attestor, response=self.attestor)

    response = self.RunBinauthz(
        'attestors public-keys update {fingerprint} '
        '--attestor={name}'.format(
            fingerprint=self.existing_pub_key.id, name=self.name))

    self.assertEqual(response, self.existing_pub_key)

  def testUnknownKeyId(self):
    self.client.projects_attestors.Get.Expect(
        self.req, response=self.attestor)

    with self.assertRaises(exceptions.NotFoundError):
      self.RunBinauthz(
          'attestors public-keys update {fingerprint} '
          '--attestor={name} --public-key-file={fname}'.format(
              fingerprint='not_a_real_id', name=self.name, fname=self.fname))

  def testUnknownFile(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunBinauthz(
          'attestors public-keys update '
          '--attestor=any-old-name --public-key-file=not-a-real-file.pub')


if __name__ == '__main__':
  test_case.main()
