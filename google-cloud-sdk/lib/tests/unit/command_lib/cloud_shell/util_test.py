# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import os
from apitools.base.py import extra_types
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as apis
from googlecloudsdk.command_lib.cloud_shell import util
from googlecloudsdk.command_lib.util.ssh import ssh
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

KEY_CONTENT = (
    'AAAAB3NzaC1yc2EAAAADAQABAAABAQCwFyCpWwERm3r1/snlgt9907rd5FcV2l'
    'vzdUxt04FCr+uNNusfx/9LUmRPVjHyIXZAcOeqRlnM8kKo765msDdyAn0n36M4LjmXBqnj'
    'edI+4OLhYPCDxGaHfnlOLIY3HCup7JSn1/u7iBddE0KnMQ13oBi010BK5iwNRe1Mr8m1ar'
    '06BK9n3UN/0DrbydTGbqcaOfYzKuMK5aeCEgvxu/TAOHsAG3fhJ0eR5orfRRUdIngP8kjZ'
    'rSrS12IRTEptaiR+NXd4/GVDcm1VvLcX8kyugVy3Md1i7kHV883jz9diMbhC/fVxERJK/7'
    'PfiEb/cYLCqWE6pTAFl+G6M4NvO3Bf')


class PrepareEnvironmentTest(cli_test_base.CliTestBase,
                             sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.client = mock.Client(apis.GetClientClass('cloudshell', 'v1alpha1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

    self.operations_client = mock.Client(
        apis.GetClientClass('cloudshell', 'v1'))
    self.operations_client.Mock()
    self.addCleanup(self.operations_client.Unmock)

    self.messages = apis.GetMessagesModule('cloudshell', 'v1alpha1')
    self.operations_messages = apis.GetMessagesModule('cloudshell', 'v1')

    # TODO(b/72457554): factor out the following to share with compute ssh tests
    self.env = ssh.Environment(ssh.Suite.OPENSSH)
    self.env.ssh = 'ssh'
    self.env.ssh_term = 'ssh'
    self.env.scp = 'scp'
    self.env.keygen = 'ssh-keygen'
    self.StartObjectPatch(ssh.Environment, 'Current', return_value=self.env)
    self.home_dir = os.path.realpath(
        self.CreateTempDir(name=os.path.join('home', 'me')))
    self.ssh_dir = os.path.realpath(
        self.CreateTempDir(name=os.path.join(self.home_dir, '.ssh')))
    self.private_key_file = os.path.join(self.ssh_dir, 'id_rsa')
    self.pubkey = ssh.Keys.PublicKey(
        'ssh-rsa',
        'AAAAB3NzaC1yc2EAAAADAQABAAABAQCwFyCpWwERm3r1/snlgt9907rd5FcV2l'
        'vzdUxt04FCr+uNNusfx/9LUmRPVjHyIXZAcOeqRlnM8kKo765msDdyAn0n36M4LjmXBqnj'
        'edI+4OLhYPCDxGaHfnlOLIY3HCup7JSn1/u7iBddE0KnMQ13oBi010BK5iwNRe1Mr8m1ar'
        '06BK9n3UN/0DrbydTGbqcaOfYzKuMK5aeCEgvxu/TAOHsAG3fhJ0eR5orfRRUdIngP8kjZ'
        'rSrS12IRTEptaiR+NXd4/GVDcm1VvLcX8kyugVy3Md1i7kHV883jz9diMbhC/fVxERJK/7'
        'PfiEb/cYLCqWE6pTAFl+G6M4NvO3Bf', 'me@my-computer')
    self.keys = ssh.Keys(self.private_key_file)
    self.StartObjectPatch(ssh.Keys, 'EnsureKeysExist', autospec=True)
    self.StartObjectPatch(ssh.Keys, 'FromFilename', return_value=self.keys)
    self.StartObjectPatch(
        ssh.Keys, 'GetPublicKey', autospec=True, return_value=self.pubkey)

  def testReturnsConnectionInfo(self):
    self.expectGetEnvironment(
        response=self.makeEnvironment(
            has_key=True,
            running=True,
            user='my-user',
            host='my-host',
            port=123,
        ))

    connection_info = util.PrepareEnvironment(self.makeArgs())
    self.assertEqual(connection_info.user, 'my-user')
    self.assertEqual(connection_info.host, 'my-host')
    self.assertEqual(connection_info.port, 123)

  def testNoKeyNotRunning(self):
    # Given an environment without a key that isn't running
    self.expectGetEnvironment(
        response=self.makeEnvironment(
            has_key=False,
            running=False,
        ))

    # Expect that we both create a key and start the environment
    self.expectCreatePublicKey()
    self.expectStartEnvironment(
        response=self.messages.Operation(name='some-op'))
    self.expectGetOperation(name='some-op')
    self.expectGetEnvironment()
    util.PrepareEnvironment(self.makeArgs())

  def testKeyNotRunning(self):
    # Given an environment that has a key but isn't running
    self.expectGetEnvironment(
        response=self.makeEnvironment(
            has_key=True,
            running=False,
        ))

    # Expect that we start the environment, but don't create a key
    self.expectStartEnvironment(
        response=self.messages.Operation(name='some-op'))
    self.expectGetOperation(name='some-op')
    self.expectGetEnvironment()
    util.PrepareEnvironment(self.makeArgs())

  def testKeyNotRunningNeedsBoost(self):
    # Given an environment that has a key but isn't running
    self.expectGetEnvironment(
        response=self.makeEnvironment(
            has_key=True,
            running=False,
        ))
    self.expectUpdateEnvironment()

    # Expect that we start the environment, but don't create a key
    self.expectStartEnvironment(
        response=self.messages.Operation(name='some-op'))
    self.expectGetOperation(name='some-op')
    self.expectGetEnvironment()

    args = self.makeArgs()
    args.boosted = True
    util.PrepareEnvironment(args)

  def testNoKeyRunning(self):
    # Given an environment without a key that is running
    self.expectGetEnvironment(
        response=self.makeEnvironment(
            has_key=False,
            running=True,
        ))

    # Expect that we create a key, but don't start the environment
    self.expectCreatePublicKey()

    util.PrepareEnvironment(self.makeArgs())

  def testKeyRunning(self):
    # Given a running environment with a key
    self.expectGetEnvironment(
        response=self.makeEnvironment(
            has_key=True,
            running=True,
        ))

    # Expect that we neither create a key or start the environment
    util.PrepareEnvironment(self.makeArgs())

  def testSlowStart(self):
    # Given an environment without a key that is running
    self.expectGetEnvironment(
        response=self.makeEnvironment(
            has_key=True,
            running=False,
        ))

    # Expect that we will start it and poll the operation until it is done
    self.expectStartEnvironment(
        response=self.messages.Operation(name='my-op', done=False))
    self.expectGetOperation(
        'my-op', response=self.makeOperation(name='my-op', done=False))
    self.expectGetOperation(
        'my-op', response=self.makeOperation(name='my-op', done=False))
    self.expectGetOperation(
        'my-op', response=self.makeOperation(name='my-op', done=True))
    self.expectGetEnvironment()
    util.PrepareEnvironment(self.makeArgs())

  def testKeyFormat(self):
    with self.assertRaisesRegex(
        ssh.InvalidKeyError,
        'SSH_ED25519 format of the key is not supported yet.'):
      util.ValidateKeyType('SSH_ED25519',
                           apis.GetMessagesModule('cloudshell', 'v1alpha1'))

  def expectGetEnvironment(self, response=None):
    if response is None:
      response = self.messages.Environment()
    self.client.UsersEnvironmentsService.Get.Expect(
        self.messages.CloudshellUsersEnvironmentsGetRequest(
            name='users/me/environments/default'),
        response=response)

  def expectUpdateEnvironment(self, response=None):
    if response is None:
      response = self.messages.Environment()
    boosted_environment = self.messages.Environment(
        size=self.messages.Environment.SizeValueValuesEnum.BOOSTED)

    self.client.UsersEnvironmentsService.Patch.Expect(
        self.messages.CloudshellUsersEnvironmentsPatchRequest(
            name='users/me/environments/default',
            updateMask='size',
            environment=boosted_environment),
        response=response)

  def expectCreatePublicKey(self):
    self.client.UsersEnvironmentsPublicKeysService.Create.Expect(
        self.messages.CloudshellUsersEnvironmentsPublicKeysCreateRequest(
            parent='users/me/environments/default',
            createPublicKeyRequest=self.messages.CreatePublicKeyRequest(
                key=self.messages.PublicKey(
                    format=self.messages.PublicKey.FormatValueValuesEnum
                    .SSH_RSA,
                    key=base64.b64decode(KEY_CONTENT)))),
        response=self.messages.PublicKey())

  def expectStartEnvironment(self, response=None):
    if response is None:
      response = self.makeOperation(done=True)
    self.client.UsersEnvironmentsService.Start.Expect(
        self.messages.CloudshellUsersEnvironmentsStartRequest(
            name='users/me/environments/default',
            startEnvironmentRequest=self.messages.StartEnvironmentRequest(
                accessToken='access_token')),
        response=response)

  def expectGetOperation(self, name, response=None):
    if response is None:
      response = self.makeOperation(done=True)
    self.operations_client.OperationsService.Get.Expect(
        self.operations_messages.CloudshellOperationsGetRequest(name=name),
        response=response)

  def makeArgs(self):

    class Struct(object):

      def __init__(self, **entries):
        self.__dict__.update(entries)

    return Struct(
        ssh_key_file=None, force_key_file_overwrite=False, boosted=False)

  def makeOperation(self, name='some-op', done=True):
    return self.operations_messages.Operation(
        name=name,
        done=done,
        metadata=self.operations_messages.Operation
        .MetadataValue(additionalProperties=[
            self.operations_messages.Operation.MetadataValue.AdditionalProperty(
                key='state',
                value=extra_types.JsonValue(string_value='XXX'),
            ),
        ]))

  def makeEnvironment(self,
                      running=False,
                      has_key=False,
                      user=None,
                      host=None,
                      port=None):
    state = self.messages.Environment.StateValueValuesEnum.DISABLED
    if running:
      state = self.messages.Environment.StateValueValuesEnum.RUNNING
    public_keys = []
    if has_key:
      public_keys.append(
          self.messages.PublicKey(
              format=self.messages.PublicKey.FormatValueValuesEnum.SSH_RSA,
              key=base64.b64decode(KEY_CONTENT)))
    return self.messages.Environment(
        size=self.messages.Environment.SizeValueValuesEnum.DEFAULT,
        state=state,
        publicKeys=public_keys,
        sshUsername=user,
        sshHost=host,
        sshPort=port,
    )
