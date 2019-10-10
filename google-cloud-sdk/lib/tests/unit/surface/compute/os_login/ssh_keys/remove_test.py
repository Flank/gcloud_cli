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
"""Tests for the describe-profile subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.oslogin import client as oslogin_client
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.oslogin import test_base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA),
)
class RemoveTest(test_base.OsloginBaseTest):

  def _RunSetUp(self, track):
    self.track = track
    self.SetUpMockApis(self.track)
    self.profiles = self.GetProfiles(self.messages)

  def testSimpleCase(self, track):
    self._RunSetUp(track)
    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/user@google.com'),
        response=self.profiles['profile_with_keys'])

    self.mock_oslogin_client.users_sshPublicKeys.Delete.Expect(
        request=self.messages.OsloginUsersSshPublicKeysDeleteRequest(
            name='users/user@google.com/sshPublicKeys/qwertyuiop',
            ),
        response='')

    response = self.Run("""
        compute os-login ssh-keys remove --key 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ'
        """)

    self.assertEqual(response, None)

  def testWithKeyFile(self, track):
    self._RunSetUp(track)
    public_key_fname = os.path.join(self.CreateTempDir(), 'key.pub')
    with open(public_key_fname, 'w') as pub_key_file:
      pub_key_file.write('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ')

    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/user@google.com'),
        response=self.profiles['profile_with_keys'])

    self.mock_oslogin_client.users_sshPublicKeys.Delete.Expect(
        request=self.messages.OsloginUsersSshPublicKeysDeleteRequest(
            name='users/user@google.com/sshPublicKeys/qwertyuiop',
            ),
        response='')

    response = self.Run("""
        compute os-login ssh-keys remove --key-file {0}
        """.format(public_key_fname))

    self.assertEqual(response, None)

  def testWithFingerprint(self, track):
    self._RunSetUp(track)
    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/user@google.com'),
        response=self.profiles['profile_with_keys'])

    self.mock_oslogin_client.users_sshPublicKeys.Delete.Expect(
        request=self.messages.OsloginUsersSshPublicKeysDeleteRequest(
            name='users/user@google.com/sshPublicKeys/qwertyuiop',
            ),
        response='')

    response = self.Run("""
        compute os-login ssh-keys remove --key 'qwertyuiop'
        """)

    self.assertEqual(response, None)

  def testWithFingerprintInKeyFile(self, track):
    self._RunSetUp(track)
    public_key_fname = os.path.join(self.CreateTempDir(), 'key.pub')
    with open(public_key_fname, 'w') as pub_key_file:
      pub_key_file.write('qwertyuiop')

    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/user@google.com'),
        response=self.profiles['profile_with_keys'])

    self.mock_oslogin_client.users_sshPublicKeys.Delete.Expect(
        request=self.messages.OsloginUsersSshPublicKeysDeleteRequest(
            name='users/user@google.com/sshPublicKeys/qwertyuiop',
            ),
        response='')

    response = self.Run("""
        compute os-login ssh-keys remove --key-file {0}
        """.format(public_key_fname))

    self.assertEqual(response, None)

  def testWithInvalidKey(self, track):
    self._RunSetUp(track)
    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/user@google.com'),
        response=self.profiles['profile_with_keys'])

    with self.AssertRaisesExceptionRegexp(
        oslogin_client.OsloginKeyNotFoundError,
        'Cannot find requested SSH key.'):
      self.Run("""
          compute os-login ssh-keys remove --key 'ssh-rsa AAAAB3NINVALIDQABAAABAQ'
          """)

  def testWithInvalidFingerprint(self, track):
    self._RunSetUp(track)
    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/user@google.com'),
        response=self.profiles['profile_with_keys'])

    with self.AssertRaisesExceptionRegexp(
        oslogin_client.OsloginKeyNotFoundError,
        'Cannot find requested SSH key.'):

      self.Run("""
          compute os-login ssh-keys remove --key 'badprint'
          """)


if __name__ == '__main__':
  test_case.main()
