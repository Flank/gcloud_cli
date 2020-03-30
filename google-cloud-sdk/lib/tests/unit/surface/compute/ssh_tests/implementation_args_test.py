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
from tests.lib import sdk_test_base
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


#  The unit test environment ends up pulling in the argparse distributed with
#  python (1.2) instead of the one installed in third_party (1.2.1). The two
#  differ, in particular (1.2) causes the SSHTestImplementationArgs
#  tests to fail. The BundledBase mixin grabs the desired third_party version.
class SSHImplementationArgsTest(sdk_test_base.BundledBase,
                                test_base.BaseSSHTest):

  def testWithImplementationArgs(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""\
        compute ssh instance-1 --zone zone-1 -- -vvv
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
        remainder=['-vvv'])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testWithCommandAndImplementationArgs(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run(['compute', 'ssh', 'instance-1', '--zone', 'zone-1', '--command',
              '"/bin/sh"', '--', '-v', '1 2 3', 'a | b', 'b\'y'])

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
        remote_command=['"/bin/sh"'],
        iap_tunnel_args=None,
        remainder=['-v', '1 2 3', 'a | b', 'b\'y'])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

if __name__ == '__main__':
  test_case.main()
