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
"""Tests for the ssh-keys update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

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
class UpdateTest(test_base.OsloginBaseTest):

  def _RunSetUp(self, track):
    self.track = track
    self.SetUpMockApis(self.track)
    self.profiles = self.GetProfiles(self.messages)

  def testWithTtlSeconds(self, track):
    self._RunSetUp(track)
    self.time.return_value = 1500000000.000001

    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/user@google.com'),
        response=self.profiles['profile_with_keys'])

    self.mock_oslogin_client.users_sshPublicKeys.Patch.Expect(
        request=self.messages.OsloginUsersSshPublicKeysPatchRequest(
            name='users/user@google.com/sshPublicKeys/qwertyuiop',
            sshPublicKey=self.messages.SshPublicKey(
                expirationTimeUsec=1500000010000001,
                fingerprint=None,
                key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ',
            ),
            updateMask='expirationTimeUsec',
        ),
        response=self.profiles['profile_with_keys'])

    response = self.Run("""
        compute os-login ssh-keys update --key 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ'
            --ttl 10s
        """)

    self.assertEqual(response, self.profiles['profile_with_keys'])

  def testWithTtlMinutes(self, track):
    self._RunSetUp(track)
    self.time.return_value = 1500000000.000001

    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/user@google.com'),
        response=self.profiles['profile_with_keys'])

    self.mock_oslogin_client.users_sshPublicKeys.Patch.Expect(
        request=self.messages.OsloginUsersSshPublicKeysPatchRequest(
            name='users/user@google.com/sshPublicKeys/qwertyuiop',
            sshPublicKey=self.messages.SshPublicKey(
                expirationTimeUsec=1500000600000001,
                fingerprint=None,
                key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ',
            ),
            updateMask='expirationTimeUsec',
        ),
        response=self.profiles['profile_with_keys'])

    response = self.Run("""
        compute os-login ssh-keys update --key 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ'
            --ttl 10m
        """)

    self.assertEqual(response, self.profiles['profile_with_keys'])

  def testWithTtlHours(self, track):
    self._RunSetUp(track)
    self.time.return_value = 1500000000.000001

    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/user@google.com'),
        response=self.profiles['profile_with_keys'])

    self.mock_oslogin_client.users_sshPublicKeys.Patch.Expect(
        request=self.messages.OsloginUsersSshPublicKeysPatchRequest(
            name='users/user@google.com/sshPublicKeys/qwertyuiop',
            sshPublicKey=self.messages.SshPublicKey(
                expirationTimeUsec=1500036000000001,
                fingerprint=None,
                key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ',
            ),
            updateMask='expirationTimeUsec',
        ),
        response=self.profiles['profile_with_keys'])

    response = self.Run("""
        compute os-login ssh-keys update --key 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ'
            --ttl 10h
        """)

    self.assertEqual(response, self.profiles['profile_with_keys'])

  def testWithTtlDays(self, track):
    self._RunSetUp(track)
    self.time.return_value = 1500000000.000001

    self.mock_oslogin_client.users.GetLoginProfile.Expect(
        request=self.messages.OsloginUsersGetLoginProfileRequest(
            name='users/user@google.com'),
        response=self.profiles['profile_with_keys'])

    self.mock_oslogin_client.users_sshPublicKeys.Patch.Expect(
        request=self.messages.OsloginUsersSshPublicKeysPatchRequest(
            name='users/user@google.com/sshPublicKeys/qwertyuiop',
            sshPublicKey=self.messages.SshPublicKey(
                expirationTimeUsec=1500864000000001,
                fingerprint=None,
                key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ',
            ),
            updateMask='expirationTimeUsec',
        ),
        response=self.profiles['profile_with_keys'])

    response = self.Run("""
        compute os-login ssh-keys update --key 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ'
            --ttl 10d
        """)

    self.assertEqual(response, self.profiles['profile_with_keys'])

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
          compute os-login ssh-keys update --key 'ssh-rsa AAAAB3NINVALIDQABAAABAQ'
               --ttl 10s
          """)


if __name__ == '__main__':
  test_case.main()
