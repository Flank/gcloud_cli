# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for the ssh subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute import iap_tunnel
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core.util import retry
from tests.lib import mock_matchers
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


_INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY = 'with_external_ip_address'
_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY = 'without_external_ip_address'

MESSAGES = apis.GetMessagesModule('compute', 'v1')


class SSHTunnelThroughIapTestGA(test_base.BaseSSHTest,
                                parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi('v1' if self.track.prefix is None else self.track.prefix)

    self.instances = {
        _INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY: self.messages.Instance(
            id=11111,
            name='instance-1',
            networkInterfaces=[
                self.messages.NetworkInterface(
                    networkIP='10.240.0.52',
                    accessConfigs=[
                        self.messages.AccessConfig(natIP='23.251.133.1'),
                    ],
                ),
            ],
            status=self.messages.Instance.StatusValueValuesEnum.RUNNING,
            selfLink=(
                'https://compute.googleapis.com/compute/{}/projects/my-project/'
                'zones/zone-1/instances/instance-1').format(self.track.prefix),
            zone=('https://compute.googleapis.com/compute/{}/projects/my-project/'
                  'zones/zone-1').format(self.track.prefix)),
        _INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY: self.messages.Instance(
            id=22222,
            name='instance-2',
            networkInterfaces=[
                self.messages.NetworkInterface(networkIP='10.240.0.53'),
            ],
            status=self.messages.Instance.StatusValueValuesEnum.RUNNING,
            selfLink=(
                'https://compute.googleapis.com/compute/{}/projects/my-project/'
                'zones/zone-1/instances/instance-2').format(self.track.prefix),
            zone=('https://compute.googleapis.com/compute/{}/projects/my-project/'
                  'zones/zone-1').format(self.track.prefix)),
    }

  @parameterized.parameters((_INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY, True),
                            (_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY, True),
                            (_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY, False))
  def testSimpleCase(self, test_instance_key, explicit_flag):
    test_instance = self.instances[test_instance_key]
    self.make_requests.side_effect = iter([
        [test_instance],
        [self.project_resource],
    ])

    self.Run('compute ssh {} --zone zone-1{}'.format(
        test_instance.name,
        ' --tunnel-through-iap' if explicit_flag else ''))

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance=test_instance.name,
              project='my-project',
              zone='zone-1'))],
        [(self.compute.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    expected_tunnel_args = iap_tunnel.SshTunnelArgs()
    expected_tunnel_args.track = self.track.prefix
    expected_tunnel_args.project = 'my-project'
    expected_tunnel_args.zone = 'zone-1'
    expected_tunnel_args.instance = test_instance.name

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=ssh.Remote.FromArg('me@compute.%s' % test_instance.id),
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options,
                     HostKeyAlias='compute.%s' % test_instance.id),
        remote_command=None,
        iap_tunnel_args=expected_tunnel_args,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  @parameterized.parameters((_INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY,),
                            (_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY,))
  def testWithAlternateUser(self, test_instance_key):
    test_instance = self.instances[test_instance_key]
    self.make_requests.side_effect = iter([
        [test_instance],
        [self.project_resource_without_metadata],
        [None],
    ])

    self.Run('compute ssh hapoo@{} --zone zone-1 --tunnel-through-iap'.format(
        test_instance.name))

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance=test_instance.name,
              project='my-project',
              zone='zone-1'))],
        [(self.compute.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
        [(self.compute.projects,
          'SetCommonInstanceMetadata',
          self.messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=self.messages.Metadata(
                  items=[
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value='hapoo:' + self.public_key_material),
                  ]),

              project='my-project'))],
    )

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    expected_tunnel_args = iap_tunnel.SshTunnelArgs()
    expected_tunnel_args.track = self.track.prefix
    expected_tunnel_args.project = 'my-project'
    expected_tunnel_args.zone = 'zone-1'
    expected_tunnel_args.instance = test_instance.name

    # Polling
    remote = ssh.Remote.FromArg('hapoo@compute.%s' % test_instance.id)
    self.poller_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        remote=remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_MS,
        options=dict(self.options,
                     HostKeyAlias='compute.%s' % test_instance.id),
        iap_tunnel_args=expected_tunnel_args)

    self.poller_poll.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        self.env, force_connect=True)

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options,
                     HostKeyAlias='compute.%s' % test_instance.id),
        remote_command=None,
        iap_tunnel_args=expected_tunnel_args,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    self.AssertErrContains('Updating project ssh metadata')

  @parameterized.parameters((_INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY,),
                            (_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY,))
  def testWithPollingTimeout(self, test_instance_key):
    # Polling the instance leads to an unreachable instance.
    self.poller_poll.side_effect = retry.WaitException('msg', 'last', 'state')

    test_instance = self.instances[test_instance_key]
    self.make_requests.side_effect = iter([
        [test_instance],
        [self.project_resource_without_metadata],
        [None],
        [None],
    ])

    with self.AssertRaisesExceptionRegexp(
        ssh_utils.NetworkError,
        'Could not SSH into the instance.  It is possible that '
        'your SSH key has not propagated to the instance yet. '
        'Try running this command again.  If you still cannot connect, '
        'verify that the firewall and instance are set to accept '
        'ssh traffic.'):
      self.Run('compute ssh hapoo@{} --zone zone-1 --tunnel-through-iap'.format(
          test_instance.name))

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance=test_instance.name,
              project='my-project',
              zone='zone-1'))],
        [(self.compute.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
        [(self.compute.projects,
          'SetCommonInstanceMetadata',
          self.messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=self.messages.Metadata(
                  items=[
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value='hapoo:' + self.public_key_material),
                  ]),

              project='my-project'))],
    )

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    expected_tunnel_args = iap_tunnel.SshTunnelArgs()
    expected_tunnel_args.track = self.track.prefix
    expected_tunnel_args.project = 'my-project'
    expected_tunnel_args.zone = 'zone-1'
    expected_tunnel_args.instance = test_instance.name

    # Polling
    remote = ssh.Remote.FromArg('hapoo@compute.%s' % test_instance.id)
    self.poller_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        remote=remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_MS,
        options=dict(self.options,
                     HostKeyAlias='compute.%s' % test_instance.id),
        iap_tunnel_args=expected_tunnel_args)

    self.poller_poll.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        self.env, force_connect=True)

    self.ssh_run.assert_not_called()

    self.AssertErrContains('Updating project ssh metadata')


class SSHTunnelThroughIapTestBeta(SSHTunnelThroughIapTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class SSHTunnelThroughIapTestAlpha(SSHTunnelThroughIapTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
