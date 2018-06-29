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
"""Unit tests for metadata_utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import metadata_utils
from tests.lib import cli_test_base
from tests.lib import parameterized


class MetadataUtilsTest(cli_test_base.CliTestBase, parameterized.TestCase):

  @parameterized.parameters(
      ({
          'key': 'value'
      },),)
  def testValidateSshKeys_NoSshKeys(self, metadata_dict):
    metadata_utils._ValidateSshKeys(metadata_dict)

  @parameterized.parameters(
      ({
          'ssh-keys': ''
      },),
      ({
          'ssh-keys': 'first_user:ssh-rsa first_key first_user@example.com'
      },),
      ({
          'ssh-keys': 'first_user:ssh-rsa first_key google-ssh '
                      '{"userName":"first_user@example.com",'
                      '"expireOn":"2019-01-04T20:12:00+0000"}'
      },),
  )
  def testValidateSshKeys_ValidKey(self, metadata_dict):
    metadata_utils._ValidateSshKeys(metadata_dict)

  @parameterized.parameters(
      ({
          'ssh-keys': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCy6PKBE/xkf+I test'
      }, metadata_utils.InvalidSshKeyException,
       'The following key(s) are missing the <username> at the front\n'
       'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCy6PKBE/xkf+I test\n\n'
       'Format ssh keys following '
       'https://cloud.google.com/compute/docs/'
       'instances/adding-removing-ssh-keys'),
      ({
          'ssh-keys': '-----BEGIN RSA PRIVATE KEY-----\n'
                      'MIIEpAIBAAKCAQEAsujygRP8ZH/iHVz0'
                      'iXSqoProNu0m8aF7ZfogLiToZsvR5MaU\n'
                      '-----END RSA PRIVATE KEY-----'
      }, metadata_utils.InvalidSshKeyException,
       'Private key(s) are detected. Note that only public keys '
       'should be added.'),
      ({
          'ssh-keys': 'ssh-rsa first_key google-ssh '
                      '{"userName":"first_user@example.com",'
                      '"expireOn":"2019-01-04T20:12:00+0000"}'
      }, metadata_utils.InvalidSshKeyException,
       'The following key(s) are missing the <username> at the front\n'
       'ssh-rsa first_key google-ssh '
       '{"userName":"first_user@example.com",'
       '"expireOn":"2019-01-04T20:12:00+0000"}\n\n'
       'Format ssh keys following '
       'https://cloud.google.com/compute/docs/'
       'instances/adding-removing-ssh-keys'),
      ({
          'ssh-keys': 'ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzd test',
          'sshKeys': 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILpOfrGZez9B test'
      }, metadata_utils.InvalidSshKeyException,
       'The following key(s) are missing the <username> at the front\n'
       'ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzd test\n'
       'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILpOfrGZez9B test\n\n'
       'Format ssh keys following '
       'https://cloud.google.com/compute/docs/'
       'instances/adding-removing-ssh-keys'),
  )
  def testValidateSshKeys_InvalidKey(self, metadata_dict, expected_error,
                                     expected_message):
    with self.AssertRaisesExceptionMatches(expected_error, expected_message):
      metadata_utils._ValidateSshKeys(metadata_dict)

  @parameterized.parameters(
      ('ssh-rsa key-blob', True),
      ('ssh-dss key-blob', True),
      ('ecdsa-sha2-nistp256 key-blob', True),
      ('ssh-ed25519 key-blob', True),
      ('username:ssh-rsa key-blob', False),
      ('username:ecdsa-sha2-nistp256 key-blob', False),
  )
  def testSshKeyStartsWithKeyType(self, key, starts_with_key_type):
    self.assertEqual(
        metadata_utils._SshKeyStartsWithKeyType(key), starts_with_key_type)


if __name__ == '__main__':
  cli_test_base.main()
