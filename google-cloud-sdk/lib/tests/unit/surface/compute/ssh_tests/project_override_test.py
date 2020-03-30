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


class SSHInstanceProjectOverrideTest(test_base.BaseSSHTest):

  def SetUp(self):
    self.remote = ssh.Remote('75.251.133.23', user='me')
    self.instance = MESSAGES.Instance(
        id=11111,
        name='instance-1',
        networkInterfaces=[
            MESSAGES.NetworkInterface(
                accessConfigs=[
                    MESSAGES.AccessConfig(
                        name='external-nat', natIP='75.251.133.23'),
                ],),
        ],
        status=MESSAGES.Instance.StatusValueValuesEnum.RUNNING,
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/asdf-project/'
            'zones/zone-1/instances/instance-1'),
        zone=('https://compute.googleapis.com/compute/v1/projects/asdf-project/'
              'zones/zone-1'))
    self.project = self.v1_messages.Project(
        commonInstanceMetadata=self.v1_messages.Metadata(items=[
            self.v1_messages.Metadata.ItemsValueListEntry(key='a', value='b'),
            self.v1_messages.Metadata.ItemsValueListEntry(
                key='ssh-keys',
                value='me:{0}\n'.format(self.public_key_material)),
        ]),
        name='asdf-project',
    )

  def testOverrideImplicit(self):
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project],
    ])

    self.Run("""\
        compute ssh https://compute.googleapis.com/compute/v1/projects/asdf-project/zones/zone-1/instances/instance-1 -- -vvv
        """)

    self.CheckRequests(
        [(self.compute_v1.instances, 'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='asdf-project', zone='zone-1'))],
        [(self.compute_v1.projects, 'Get',
          self.messages.ComputeProjectsGetRequest(project='asdf-project'))],
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
        remainder=['-vvv'])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand), self.env, force_connect=True)

  def testOverrideExplicit(self):
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project],
    ])

    self.Run("""\
        compute ssh https://compute.googleapis.com/compute/v1/projects/asdf-project/zones/zone-1/instances/instance-1 --project my-project -- -vvv
        """)

    self.CheckRequests(
        [(self.compute_v1.instances, 'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='asdf-project', zone='zone-1'))],
        [(self.compute_v1.projects, 'Get',
          self.messages.ComputeProjectsGetRequest(project='asdf-project'))],
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
        remainder=['-vvv'])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand), self.env, force_connect=True)


if __name__ == '__main__':
  test_case.main()
