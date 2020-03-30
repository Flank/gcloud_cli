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
from googlecloudsdk.command_lib.util.ssh import ssh
from tests.lib import mock_matchers
from tests.lib import test_case
from tests.lib.surface.compute import test_base


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

INSTANCE_WITH_GUEST_ATTRIBUTES_ENABLED = MESSAGES.Instance(
    id=66666,
    name='instance-6',
    metadata=MESSAGES.Metadata(
        items=[
            MESSAGES.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes',
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
              'zones/zone-1/instances/instance-6'),
    zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-1'))


INSTANCE_WITH_GUEST_ATTRIBUTES_DISABLED = MESSAGES.Instance(
    id=77777,
    name='instance-7',
    metadata=MESSAGES.Metadata(
        items=[
            MESSAGES.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes',
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
              'zones/zone-1/instances/instance-7'),
    zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-1'))

GUEST_ATTRIBUTES_CONTENTS = MESSAGES.GuestAttributes(
    queryPath='hostkeys/',
    queryValue=MESSAGES.GuestAttributesValue(
        items=[
            MESSAGES.GuestAttributesEntry(
                key='ssh-rsa',
                namespace='hostkeys',
                value='AAAAB3NzaC1yc2EAAAADAQABAAABAQCo4bTdpLeTwhpAOmHe'),
        ],
    ),
    selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-6/guestAttributes/'))

GUEST_ATTRIBUTES_CONTENTS_NEWLINE = MESSAGES.GuestAttributes(
    queryPath='hostkeys/',
    queryValue=MESSAGES.GuestAttributesValue(
        items=[
            MESSAGES.GuestAttributesEntry(
                key='ssh-rsa',
                namespace='hostkeys',
                value=('AAAAB3NzaC1yc2EAAAADAQABAAABAQCo4bTdpLeTwhpAOmHe\n'
                       'compute.1234 ssh-rsa AAAAB3NzaC1yc2EAA')),
        ],
    ),
    selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-6/guestAttributes/'))

GUEST_ATTRIBUTES_CONTENTS_INVALID_KEY = MESSAGES.GuestAttributes(
    queryPath='hostkeys/',
    queryValue=MESSAGES.GuestAttributesValue(
        items=[
            MESSAGES.GuestAttributesEntry(
                key='ssh-rsa',
                namespace='hostkeys',
                value='AAAAB3NzaC1yc2EAAAADAQABAAABAQCo4bT@#$#@$^%@$^$^&*'),
        ],
    ),
    selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-6/guestAttributes/'))

GUEST_ATTRIBUTES_CONTENTS_INVALID_KEY_TYPE = MESSAGES.GuestAttributes(
    queryPath='hostkeys/',
    queryValue=MESSAGES.GuestAttributesValue(
        items=[
            MESSAGES.GuestAttributesEntry(
                key='ssh-badtype',
                namespace='hostkeys',
                value='AAAAB3NzaC1yc2EAAAADAQABAAABAQCo4bTdpLeTwhpAOmHe'),
        ],
    ),
    selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-6/guestAttributes/'))


class GuestAttributesEnabledTest(test_base.BaseSSHTest):

  def testSimpleCase(self):
    # Guest Attributes enabled with host keys returned should cause
    # StrictHostKeyChecking to be set to 'yes'.
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_GUEST_ATTRIBUTES_ENABLED],
        [self.project_resource],
        [GUEST_ATTRIBUTES_CONTENTS],
    ])

    self.Run("""
        compute ssh instance-6 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-6',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
        [(self.compute.instances,
          'GetGuestAttributes',
          self.messages.ComputeInstancesGetGuestAttributesRequest(
              instance='instance-6',
              project='my-project',
              queryPath='hostkeys/',
              zone='zone-1'))],
    )

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # Check KnownHosts Add
    self.known_hosts_addmultiple.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.KnownHosts),
        'compute.66666',
        ['ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCo4bTdpLeTwhpAOmHe'],
        overwrite=False)

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, StrictHostKeyChecking='yes',
                     HostKeyAlias='compute.66666'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testHostKeyWithNewline(self):
    # Guest Attributes enabled with host keys returned should cause
    # StrictHostKeyChecking to be set to 'yes' and key data after the
    # newline character should be truncated.
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_GUEST_ATTRIBUTES_ENABLED],
        [self.project_resource],
        [GUEST_ATTRIBUTES_CONTENTS_NEWLINE],
    ])

    self.Run("""
        compute ssh instance-6 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-6',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
        [(self.compute.instances,
          'GetGuestAttributes',
          self.messages.ComputeInstancesGetGuestAttributesRequest(
              instance='instance-6',
              project='my-project',
              queryPath='hostkeys/',
              zone='zone-1'))],
    )

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # Check KnownHosts Add
    self.known_hosts_addmultiple.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.KnownHosts),
        'compute.66666',
        ['ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCo4bTdpLeTwhpAOmHe'],
        overwrite=False)

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, StrictHostKeyChecking='yes',
                     HostKeyAlias='compute.66666'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testInvalidHostKey(self):
    # No valid keys are returned, so nothing is written to known hosts and
    # StrictHostKeyChecking stays set to the default value.
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_GUEST_ATTRIBUTES_ENABLED],
        [self.project_resource],
        [GUEST_ATTRIBUTES_CONTENTS_INVALID_KEY],
    ])

    self.Run("""
        compute ssh instance-6 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-6',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
        [(self.compute.instances,
          'GetGuestAttributes',
          self.messages.ComputeInstancesGetGuestAttributesRequest(
              instance='instance-6',
              project='my-project',
              queryPath='hostkeys/',
              zone='zone-1'))],
    )

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # No host keys to add since it is an invalid type
    self.known_hosts_addmultiple.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options,
                     HostKeyAlias='compute.66666'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testInvalidHostKeyType(self):
    # No valid keys are returned, so nothing is written to known hosts and
    # StrictHostKeyChecking stays set to the default value.
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_GUEST_ATTRIBUTES_ENABLED],
        [self.project_resource],
        [GUEST_ATTRIBUTES_CONTENTS_INVALID_KEY_TYPE],
    ])

    self.Run("""
        compute ssh instance-6 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-6',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
        [(self.compute.instances,
          'GetGuestAttributes',
          self.messages.ComputeInstancesGetGuestAttributesRequest(
              instance='instance-6',
              project='my-project',
              queryPath='hostkeys/',
              zone='zone-1'))],
    )

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # No host keys to add since it is an invalid type
    self.known_hosts_addmultiple.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options,
                     HostKeyAlias='compute.66666'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testEnabledAtProjectLevel(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource_with_guest_attr_enabled],
        [GUEST_ATTRIBUTES_CONTENTS],
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
        [(self.compute.instances,
          'GetGuestAttributes',
          self.messages.ComputeInstancesGetGuestAttributesRequest(
              instance='instance-1',
              project='my-project',
              queryPath='hostkeys/',
              zone='zone-1'))],
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
        options=dict(self.options, StrictHostKeyChecking='yes',
                     HostKeyAlias='compute.11111'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testEnabledAtProjectDisabledAtInstance(self):
    # Instance value overrides project value, so Guest Attributes won't
    # be retrieved and StrictHostKeyChecking should be set to 'no'.
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_GUEST_ATTRIBUTES_DISABLED],
        [self.project_resource_with_guest_attr_enabled],
    ])

    self.Run("""
        compute ssh instance-7 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-7',
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
        options=dict(self.options, StrictHostKeyChecking='no',
                     HostKeyAlias='compute.77777'),
        remote_command=None,
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)


if __name__ == '__main__':
  test_case.main()
