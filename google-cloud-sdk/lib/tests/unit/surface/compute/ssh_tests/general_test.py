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

import os

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core.util import retry
from tests.lib import mock_matchers
from tests.lib import test_case
from tests.lib.surface.compute import test_base

import mock


MESSAGES = apis.GetMessagesModule('compute', 'v1')

INSTANCE_WITH_EXTERNAL_ADDRESS = MESSAGES.Instance(
    id=11111,
    name='instance-1',
    networkInterfaces=[
        MESSAGES.NetworkInterface(networkIP='10.240.0.52'),
        MESSAGES.NetworkInterface(
            accessConfigs=[
                MESSAGES.AccessConfig(
                    name='external-nat',
                    natIP='23.251.133.75'),
            ],
        ),
    ],
    status=MESSAGES.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-1'),
    zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-1'))

INSTANCE_WITHOUT_EXTERNAL_ADDRESS = MESSAGES.Instance(
    id=22222,
    name='instance-2',
    networkInterfaces=[
        MESSAGES.NetworkInterface(networkIP='10.240.0.52'),
    ],
    status=MESSAGES.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-2/instances/instance-2'),
    zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-2'))

# An instance resource that has not been allocated an IP address
# yet. Users can get a resource like this if they attempt to SSH into
# an instance that has just been created, but its operation's status
# is not DONE yet.
INSTANCE_WITHOUT_EXTERNAL_ADDRESS_YET = MESSAGES.Instance(
    id=33333,
    name='instance-3',
    networkInterfaces=[
        MESSAGES.NetworkInterface(networkIP='10.240.0.52'),
        MESSAGES.NetworkInterface(
            accessConfigs=[
                MESSAGES.AccessConfig(
                    name='external-nat'),
            ],
        ),
    ],
    status=MESSAGES.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-3'),
    zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-1'))


class SSHTest(test_base.BaseSSHTest, test_case.WithInput):

  def SetUp(self):
    datetime_patcher = mock.patch('datetime.datetime',
                                  test_base.FakeDateTimeWithTimeZone)
    self.addCleanup(datetime_patcher.stop)
    datetime_patcher.start()

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testPlain(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1 --plain
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )

    # Don't require SSH keys
    self.ensure_keys.assert_not_called()

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command without options and identity_file
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=None,
        extra_flags=[],
        tty=None,
        options=None,
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testDryRun(self):
    ssh_build = self.StartObjectPatch(
        ssh.SSHCommand, 'Build', autospec=True, return_value=['ssh', 'cmd'])
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1 --dry-run
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    ssh_build.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand), self.env)

    self.ssh_run.assert_not_called()

    self.AssertOutputEquals('ssh cmd\n')

  def testSimpleCaseWithPort(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1 --ssh-flag='-p 1234'
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=['-p', '1234'],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testWithInaccessibleInstance(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITHOUT_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    with self.AssertRaisesExceptionRegexp(
        ssh_utils.MissingExternalIPAddressError,
        r'Instance \[instance-2\] in zone \[zone-2\] does not have an external '
        r'IP address, so you cannot SSH into it. To add an external IP address '
        r'to the instance, use \[gcloud compute instances '
        r'add-access-config\].'):
      self.Run("""
          compute ssh instance-2 --zone zone-2 --no-tunnel-through-iap
          """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-2',
              project='my-project',
              zone='zone-2'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )
    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # No SSH Command
    self.ssh_init.assert_not_called()

  def testWithNonInitializedInstance(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITHOUT_EXTERNAL_ADDRESS_YET],
        [self.project_resource],
    ])

    with self.AssertRaisesExceptionRegexp(
        ssh_utils.UnallocatedIPAddressError,
        r'Instance \[instance-3\] in zone \[zone-1\] has not been allocated an '
        'external IP address yet. Try rerunning this command later.'):
      self.Run("""
          compute ssh instance-3 --zone zone-1 --no-tunnel-through-iap
          """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-3',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )
    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # No SSH Command
    self.ssh_init.assert_not_called()

  def testWithIllFormattedPositionalArg(self):
    self.make_requests.side_effect = iter([
        ])

    with self.AssertRaisesToolExceptionRegexp(
        r'Expected argument of the form \[USER@\]INSTANCE; received '
        r'\[hapoo@instance-1@instance-2\].'):
      self.Run("""
          compute ssh hapoo@instance-1@instance-2 --zone us-central1-a
          """)

    self.CheckRequests()
    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # No SSH Command
    self.ssh_init.assert_not_called()

  def testWithAlternateUser(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource_without_metadata],
        [],
    ])

    self.Run("""
        compute ssh hapoo@instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
        [(self.compute_v1.projects,
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

    remote = ssh.Remote(self.remote.host, user='hapoo')

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # Polling
    self.poller_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        remote=remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_MS,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        iap_tunnel_args=None)

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
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    self.AssertErrContains('Updating project ssh metadata')

  def testWithRelativeExpiration(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource_without_metadata],
        [],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        --ssh-key-expire-after 1d
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
        [(self.compute_v1.projects,
          'SetCommonInstanceMetadata',
          self.messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=self.messages.Metadata(
                  items=[
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value=('me:{0} google-ssh {{"userName":"me",'
                                 '"expireOn":'
                                 '"2014-01-03T03:04:05+0000"}}').format(
                                     self.pubkey.ToEntry())),
                  ]),

              project='my-project'))],
    )

    remote = ssh.Remote(self.remote.host, user='me')

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # Polling
    self.poller_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        remote=remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_MS,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        iap_tunnel_args=None)

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
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    self.AssertErrContains('Updating project ssh metadata')

  def testWithAbsoluteExpiration(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource_without_metadata],
        [],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        --ssh-key-expiration 2015-01-23T12:34:56+0000
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
        [(self.compute_v1.projects,
          'SetCommonInstanceMetadata',
          self.messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=self.messages.Metadata(
                  items=[
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value=('me:{0} google-ssh {{"userName":"me",'
                                 '"expireOn":'
                                 '"2015-01-23T12:34:56+0000"}}').format(
                                     self.pubkey.ToEntry())),
                  ]),

              project='my-project'))],
    )

    remote = ssh.Remote(self.remote.host, user='me')

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # Polling
    self.poller_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        remote=remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_MS,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        iap_tunnel_args=None)

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
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    self.AssertErrContains('Updating project ssh metadata')

  def testWithSshFlag(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""\
        compute ssh instance-1 --zone zone-1
             --ssh-flag="-vvv"
             --ssh-flag="-o HostName='%INSTANCE%'"
             --ssh-flag="-o InternalIp='%INTERNAL%'"
             --ssh-flag="-o User=\"%USER%\""
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )
    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[
            '-vvv', '-o', 'HostName=\'23.251.133.75\'', '-o',
            'InternalIp=\'10.240.0.52\'', '-o', 'User=me'
        ],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testWithCommand(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""\
        compute ssh instance-1 --zone zone-1 --command "ps -ejH"
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )
    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=['ps', '-ejH'],
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testWithCommandAndSshFlag(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""\
        compute ssh instance-1 --zone zone-1 --ssh-flag="-vvv" --command "/bin/sh" --ssh-flag="-o HostName='%INSTANCE%'" --ssh-flag="-o User=\"%USER%\""
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )
    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=['-vvv', '-o', 'HostName=\'23.251.133.75\'', '-o',
                     'User=me'],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=['/bin/sh'],
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testWithDryRun(self):
    self.ssh_build = self.StartObjectPatch(
        ssh.SSHCommand, 'Build', autospec=True, return_value=['FAKE', 'CMD'])
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""\
        compute ssh instance-1 --zone zone-1
             --ssh-flag="-vvv"
             --command "/bin/sh"
             --ssh-flag="-o HostName='%INSTANCE%'"
             --ssh-flag="-o User=\"%USER%\""
             --dry-run
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )
    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=['-vvv', '-o', 'HostName=\'23.251.133.75\'', '-o',
                     'User=me'],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=['/bin/sh'],
        iap_tunnel_args=None,
        remainder=[])

    # Run not invoked, but build is
    self.ssh_run.assert_not_called()
    self.ssh_build.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand), self.env)
    self.AssertOutputContains('FAKE CMD')

  def testBadImplementationArgs(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments: --zone=ugh'):
      self.Run("""\
          compute --zone=ugh ssh instance-1 --zone zone-1 --command "ls" --dry-run
          """)

    self.AssertErrContains('unrecognized arguments: --zone=ugh')

  def testWithContainer(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""\
        compute ssh instance-1 --zone zone-1 --container my-container
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )
    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=True,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=['sudo', 'docker', 'exec', '-it',
                        'my-container', '/bin/sh'],
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testWithContainerAndCommand(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""\
        compute ssh instance-1 --zone zone-1
          --container=my-container
          --command "ps -ejH"
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )
    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=['sudo', 'docker', 'exec', '-i',
                        'my-container', 'ps', '-ejH'],
        iap_tunnel_args=None,
        remainder=[])

  def testWithContainerAndNoCommandAndPlain(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.assertFalse(os.path.exists(self.private_key_file))
    self.Run("""\
        compute ssh instance-1 --zone zone-1
          --container=my-container
          --plain
        """)

    self.assertFalse(os.path.exists(self.private_key_file))
    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )
    # Don't require SSH keys
    self.ensure_keys.assert_not_called()

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=None,
        extra_flags=[],
        tty=True,
        options=None,
        remote_command=['sudo', 'docker', 'exec', '-it',
                        'my-container', '/bin/sh'],
        iap_tunnel_args=None,
        remainder=[])

  def testSshErrorException(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])
    self.ssh_run.side_effect = ssh.CommandError('ssh', return_code=255)
    with self.assertRaisesRegex(
        ssh.CommandError,
        r'\[ssh\] exited with return code \[255\].'):
      self.Run("""
          compute ssh instance-1 --zone zone-1
          """)

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)

    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(name='instance-1', zone='zone-1'),
        ],

        [INSTANCE_WITH_EXTERNAL_ADDRESS],

        [self.project_resource],
    ])

    self.Run("""
        compute ssh instance-1
        """)

    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance-1'),

        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],

        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )
    self.AssertErrContains(
        'No zone specified. Using zone [zone-1] for instance: [instance-1].')

  def testUriSupport(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""
        compute ssh https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
        """)

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testSshTimeout(self):

    # Polling the instance leads to an unreachable instance.
    self.poller_poll.side_effect = retry.WaitException('msg', 'last', 'state')

    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource_without_metadata],
        [],
    ])

    with self.AssertRaisesExceptionRegexp(
        ssh_utils.NetworkError,
        'Could not SSH into the instance.  It is possible that '
        'your SSH key has not propagated to the instance yet. '
        'Try running this command again.  If you still cannot connect, '
        'verify that the firewall and instance are set to accept '
        'ssh traffic.'):
      self.Run("""
          compute ssh instance-1 --zone zone-1
          """)
    self.AssertErrContains('Updating project ssh metadata')


if __name__ == '__main__':
  test_case.main()
