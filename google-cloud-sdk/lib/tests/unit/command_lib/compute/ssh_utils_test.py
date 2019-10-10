# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Unit tests for the compute ssh utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.util.ssh import ssh
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock


class GetExternalIPAddressTests(sdk_test_base.SdkBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'v1')
    self.external_ip_address = '10.0.0.0'
    self.access_config = self.messages.AccessConfig(
        natIP=self.external_ip_address)
    self.external_nic = self.messages.NetworkInterface(
        accessConfigs=[self.access_config])
    self.internal_ip_address = '10.0.0.1'
    self.internal_nic = self.messages.NetworkInterface(
        networkIP=self.internal_ip_address)

  def testSingleExternalNic(self):
    instance = self.messages.Instance(
        name='instance-1', zone='zone-1', networkInterfaces=[self.external_nic])
    ip_result = ssh_utils.GetExternalIPAddress(instance)
    self.assertEqual(self.external_ip_address, ip_result)
    self.assertIs(ssh_utils.GetExternalInterface(instance), self.external_nic)

  def testSingleInternalNic(self):
    instance = self.messages.Instance(
        name='instance-1', zone='zone-1', networkInterfaces=[self.internal_nic])
    ip_result = ssh_utils.GetInternalIPAddress(instance)
    self.assertEqual(self.internal_ip_address, ip_result)
    self.assertIs(ssh_utils.GetInternalInterface(instance), self.internal_nic)

  def testMultipleNics(self):
    instance = self.messages.Instance(
        name='instance-1',
        zone='zone-1',
        networkInterfaces=[self.internal_nic, self.external_nic])
    self.assertEqual(ssh_utils.GetExternalIPAddress(instance),
                     self.external_ip_address)
    self.assertIs(ssh_utils.GetExternalInterface(instance), self.external_nic)
    self.assertEqual(ssh_utils.GetInternalIPAddress(instance),
                     self.internal_ip_address)
    self.assertIs(ssh_utils.GetInternalInterface(instance), self.internal_nic)

  def testMissingIPAddress(self):
    instance_no_ip = self.messages.Instance(
        name='Test', zone='Zone-test', networkInterfaces=[self.internal_nic])
    self.assertRaises(ssh_utils.MissingExternalIPAddressError,
                      ssh_utils.GetExternalIPAddress, instance_no_ip)

  def testMissingInterface(self):
    instance_no_internal = self.messages.Instance(name='Test', zone='Zone-test')
    self.assertRaises(exceptions.ToolException, ssh_utils.GetInternalInterface,
                      instance_no_internal)

  def testUnallocatedIPAddress(self):
    access_config_no_ip = self.messages.AccessConfig()
    nic_no_ip = self.messages.NetworkInterface(
        accessConfigs=[access_config_no_ip])
    instance_no_ip = self.messages.Instance(
        name='Test', zone='Zone-test', networkInterfaces=[nic_no_ip])
    self.assertRaises(ssh_utils.UnallocatedIPAddressError,
                      ssh_utils.GetExternalIPAddress, instance_no_ip)


class HostKeysTestsAlpha(sdk_test_base.SdkBase):

  def testWriteHostKeyToKnownHosts(self):
    known_hosts = mock.Mock()
    known_hosts.file_path = '/tmp/foo'
    known_hosts.known_hosts = [
        'compute.1234 ssh-rsa asdfasdf'
    ]
    known_hosts.Write.return_value = None
    known_hosts.AddMultiple.return_value = True

    host_keys = {'ssh-rsa': 'jkljkljkl',
                 'ecdsa': 'jkljkljkl'}

    ssh_helper = ssh_utils.BaseSSHHelper()

    ssh_helper.WriteHostKeysToKnownHosts(known_hosts, host_keys, 'compute.3456')

    known_hosts.AddMultiple.assert_called_with('compute.3456',
                                               [
                                                   'ecdsa jkljkljkl',
                                                   'ssh-rsa jkljkljkl',
                                               ],
                                               overwrite=False)


class AddSSHKeyToMetadataMessageTests(parameterized.TestCase,
                                      test_case.TestCase):

  def RunAddSSHKeyToMetadataMessage(
      self, user, public_key, expiration, legacy, existing_ssh_keys):
    unused_mock_get_keys = self.StartObjectPatch(
        ssh_utils, '_GetSSHKeysFromMetadata', autospec=True,
        return_value=(existing_ssh_keys, []))
    mock_construct = self.StartObjectPatch(metadata_utils,
                                           'ConstructMetadataMessage')
    ssh_utils._AddSSHKeyToMetadataMessage(None, user, public_key, None,
                                          expiration, legacy)
    if mock_construct.called:
      return mock_construct.mock_calls[0][2]['metadata']
    return {}

  @parameterized.named_parameters(
      ('legacy', True, 'sshKeys'),
      ('non-legacy', False, 'ssh-keys'))
  def testAddKey_CorrectMetadataKey(self, legacy, expected_key):
    user = 'user'
    public_key = ssh.Keys.PublicKey('type', 'data', 'comment')
    ssh_keys = []
    expected = {expected_key: 'user:type data comment'}

    metadata_update = self.RunAddSSHKeyToMetadataMessage(
        user, public_key, None, legacy, ssh_keys)
    self.assertEqual(expected, metadata_update)

  def testAddKey_KeyDataCorrectNonExpiring(self):
    user = 'user'
    public_key = ssh.Keys.PublicKey('type', 'data', 'comment')
    ssh_keys = ['existing:type data comment']
    expected = {'ssh-keys':
                    'existing:type data comment\nuser:type data comment'}
    metadata_update = self.RunAddSSHKeyToMetadataMessage(
        user, public_key, None, False, ssh_keys)
    self.assertEqual(expected, metadata_update)

  def testAddKey_KeyDataCorrectExpiring(self):
    user = 'user'
    public_key = ssh.Keys.PublicKey('type', 'data', 'comment')
    ssh_keys = []
    expiration = datetime.datetime(2038, 1, 19, 3, 14, 6)
    expected = {'ssh-keys': (
        'user:type data google-ssh '
        '{"userName":"user","expireOn":"2038-01-19T03:14:06+0000"}')}
    metadata_update = self.RunAddSSHKeyToMetadataMessage(
        user, public_key, expiration, False, ssh_keys)
    self.assertEqual(expected, metadata_update)

  def testAddKey_DoesNotReaddExistingKey(self):
    user = 'user'
    public_key = ssh.Keys.PublicKey('type', 'data', 'comment')
    ssh_keys = ['user:type data comment']
    # User has keys available, and no expiration is specified
    # so no update to metadata occurs.
    expected = {}
    metadata_update = self.RunAddSSHKeyToMetadataMessage(
        user, public_key, None, False, ssh_keys)
    self.assertEqual(expected, metadata_update)

  def testAddKey_DropsExpiredKeys(self):
    user = 'user'
    public_key = ssh.Keys.PublicKey('type', 'data', 'comment')
    ssh_keys = [
        'valid:type data comment',
        ('expired:type data google-ssh '
         '{"userName":"user","expireOn":"1970-01-01T00:00:00Z"}'),
    ]
    expected = {'ssh-keys':
                    'valid:type data comment\nuser:type data comment'}
    metadata_update = self.RunAddSSHKeyToMetadataMessage(
        user, public_key, None, False, ssh_keys)
    self.assertEqual(expected, metadata_update)

  @parameterized.named_parameters(
      ('not json', 'foo'),
      ('no expiresOn', '{"userName": "user"}'),
      ('unable to parse expiresOn', '{"userName": "user", "expiresOn": -1"}'))
  def testAddKey_TreatInvalidExpirationsAsUnexpired(self, expiration_text):
    user = 'user'
    public_key = ssh.Keys.PublicKey('type', 'data', 'comment')
    ssh_keys = [
        'invalidexisting:type data google-ssh {}'.format(expiration_text)
    ]
    expected = {'ssh-keys': '\n'.join(ssh_keys + ['user:type data comment'])}
    metadata_update = self.RunAddSSHKeyToMetadataMessage(
        user, public_key, None, False, ssh_keys)
    self.assertEqual(expected, metadata_update)


if __name__ == '__main__':
  test_case.main()
