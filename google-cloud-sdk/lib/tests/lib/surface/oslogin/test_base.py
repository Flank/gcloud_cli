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
"""Module for oslogin test base classes."""

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
import mock


class OsloginBaseTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):
  """Base class for gcloud oslogin tests."""

  VERSION_MAP = {base.ReleaseTrack.ALPHA: 'v1alpha',
                 base.ReleaseTrack.BETA: 'v1beta',
                 base.ReleaseTrack.GA: 'v1'}

  def SetUpMockApis(self, release_track):
    self.api = self.VERSION_MAP[release_track]
    self.messages = core_apis.GetMessagesModule('oslogin', self.api)
    self.mock_oslogin_client = api_mock.Client(
        core_apis.GetClientClass('oslogin', self.api),
        real_client=core_apis.GetClientInstance('oslogin', self.api,
                                                no_http=True))
    self.mock_oslogin_client.Mock()
    self.addCleanup(self.mock_oslogin_client.Unmock)

    properties.VALUES.core.account.Set('user@google.com')

    time_patcher = mock.patch('time.time', autospec=True)
    self.addCleanup(time_patcher.stop)
    self.time = time_patcher.start()

  def GetProfiles(self, messages):
    profiles = {
        'profile_with_keys':
        messages.LoginProfile(
            name='user@google.com',
            posixAccounts=[
                messages.PosixAccount(
                    gid=123456,
                    uid=123456,
                    shell='/bin/bash',
                    primary=True,
                    username='test_user',
                    homeDirectory='/home/test_user'),
                messages.PosixAccount(
                    gid=234567,
                    uid=234567,
                    shell='/bin/bash',
                    primary=False,
                    username='test_user2',
                    homeDirectory='/home/test_user2'),
            ],
            sshPublicKeys=messages.LoginProfile.SshPublicKeysValue(
                additionalProperties=[
                    messages.LoginProfile.SshPublicKeysValue.AdditionalProperty(
                        key='qwertyuiop',
                        value=messages.SshPublicKey(
                            fingerprint='qwertyuiop',
                            key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ')),
                    messages.LoginProfile.SshPublicKeysValue.AdditionalProperty(
                        key='asdfghjkl',
                        value=messages.SshPublicKey(
                            expirationTimeUsec=1501694210974295,
                            fingerprint='asdfghjkl',
                            key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABQDFC1y')),
                ]),
        ),
        'profile_without_keys':
        messages.LoginProfile(
            name='user@google.com',
            posixAccounts=[
                messages.PosixAccount(
                    gid=123456,
                    uid=123456,
                    shell='/bin/bash',
                    primary=True,
                    username='test_user',
                    homeDirectory='/home/test_user'),
                messages.PosixAccount(
                    gid=234567,
                    uid=234567,
                    shell='/bin/bash',
                    primary=False,
                    username='test_user2',
                    homeDirectory='/home/test_user2'),
            ],
        ),
        'profile_with_account_id':
        messages.LoginProfile(
            name='user@google.com',
            posixAccounts=[
                messages.PosixAccount(
                    accountId='fake-project',
                    gid=123456,
                    uid=123456,
                    shell='/bin/bash',
                    primary=True,
                    username='test_user',
                    homeDirectory='/home/test_user'),
                messages.PosixAccount(
                    gid=234567,
                    uid=234567,
                    shell='/bin/bash',
                    primary=False,
                    username='test_user2',
                    homeDirectory='/home/test_user2'),
            ],
        ),
        'profile_without_account_id':
        messages.LoginProfile(
            name='user@google.com',
            posixAccounts=[
                messages.PosixAccount(
                    gid=123456,
                    uid=123456,
                    shell='/bin/bash',
                    primary=True,
                    username='test_user',
                    homeDirectory='/home/test_user'),
                messages.PosixAccount(
                    gid=234567,
                    uid=234567,
                    shell='/bin/bash',
                    primary=False,
                    username='test_user2',
                    homeDirectory='/home/test_user2'),
            ],
        ),
        }
    return profiles


