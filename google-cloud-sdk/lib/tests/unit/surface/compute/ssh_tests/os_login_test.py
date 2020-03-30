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
from googlecloudsdk.api_lib.util import apis_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import properties
from tests.lib import mock_matchers
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


MESSAGES = apis.GetMessagesModule('compute', 'v1')


INSTANCE_WITH_OSLOGIN_ENABLED = MESSAGES.Instance(
    id=44444,
    name='instance-4',
    metadata=MESSAGES.Metadata(
        items=[
            MESSAGES.Metadata.ItemsValueListEntry(
                key='enable-oslogin',
                value='TruE'),
        ]
    ),
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

INSTANCE_WITH_OSLOGIN_DISABLED = MESSAGES.Instance(
    id=55555,
    name='instance-5',
    metadata=MESSAGES.Metadata(
        items=[
            MESSAGES.Metadata.ItemsValueListEntry(
                key='enable-oslogin',
                value='false'),
        ]
    ),
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


# TODO(b/149328730): Add a unit test for impersonating a service account.
class SSHOsloginTest(test_base.BaseSSHTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')

  @mock.patch(
      'googlecloudsdk.api_lib.oslogin.client._GetClient')
  def testSimpleCase(self, oslogin_mock):
    properties.VALUES.core.account.Set('user@google.com')
    self.remote = ssh.Remote('23.251.133.75', user='user_google_com')
    oslogin_mock.return_value = test_resources.MakeOsloginClient('v1')

    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_OSLOGIN_ENABLED],
        [self.project_resource],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
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

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.44444'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  @mock.patch(
      'googlecloudsdk.api_lib.oslogin.client._GetClient')
  def testSelectMatchingUser(self, oslogin_mock):
    properties.VALUES.core.account.Set('user@google.com')
    self.remote = ssh.Remote('23.251.133.75', user='testaccount')
    oslogin_mock.return_value = test_resources.MakeOsloginClient(
        'v1', use_extended_profile=True)

    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_OSLOGIN_ENABLED],
        [self.project_resource],
    ])

    self.Run("""
        compute ssh testaccount@instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
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

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.44444'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  @mock.patch(
      'googlecloudsdk.api_lib.oslogin.client._GetClient')
  def testRequestNonOsloginUser(self, oslogin_mock):
    properties.VALUES.core.account.Set('user@google.com')
    self.remote = ssh.Remote('23.251.133.75', user='user_google_com')
    oslogin_mock.return_value = test_resources.MakeOsloginClient('v1')

    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_OSLOGIN_ENABLED],
        [self.project_resource],
    ])

    self.Run("""
        compute ssh someotheruser@instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
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

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.44444'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    self.AssertErrContains('Using OS Login user [user_google_com] instead '
                           'of requested user [someotheruser]')

  @mock.patch(
      'googlecloudsdk.api_lib.oslogin.client._GetClient')
  def testGetPrimaryUser(self, oslogin_mock):
    properties.VALUES.core.account.Set('user@google.com')
    self.remote = ssh.Remote('23.251.133.75', user='myaccount')
    oslogin_mock.return_value = test_resources.MakeOsloginClient(
        'v1', use_extended_profile=True)

    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_OSLOGIN_ENABLED],
        [self.project_resource],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
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

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.44444'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  @mock.patch(
      'googlecloudsdk.api_lib.oslogin.client._GetClient')
  def testOsloginEnabledOnProject(self, oslogin_mock):
    properties.VALUES.core.account.Set('user@google.com')
    self.remote = ssh.Remote('23.251.133.75', user='user_google_com')
    oslogin_mock.return_value = test_resources.MakeOsloginClient('v1')

    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource_with_oslogin_enabled],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
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

  @mock.patch(
      'googlecloudsdk.api_lib.oslogin.client._GetClient')
  def testOsloginEnabledOnProjectButDisabledOnInstance(self, oslogin_mock):
    # Should fall through to alternate authentication.
    properties.VALUES.core.account.Set('user@google.com')
    self.remote = ssh.Remote('23.251.133.75', user='me')
    oslogin_mock.return_value = test_resources.MakeOsloginClient('v1')

    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_OSLOGIN_DISABLED],
        [self.project_resource_with_oslogin_enabled],
        [],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
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
                          key='enable-oslogin',
                          value='true'),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value='me:' + self.public_key_material),
                  ]),

              project='my-project'))],
    )

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.55555'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  @mock.patch(
      'googlecloudsdk.api_lib.oslogin.client._GetClient')
  def testUnknownOsloginApiVarsion(self, oslogin_mock):
    # Should fall through to alternate authentication.
    properties.VALUES.core.account.Set('user@google.com')
    self.remote = ssh.Remote('23.251.133.75', user='me')
    oslogin_mock.side_effect = apis_util.UnknownVersionError('oslogin',
                                                             'v1')

    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_OSLOGIN_ENABLED],
        [self.project_resource],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
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

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.44444'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)


if __name__ == '__main__':
  test_case.main()
