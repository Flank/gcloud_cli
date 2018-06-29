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

"""Tests for `gcloud compute copy-files`."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.command_lib.util.ssh import ssh
from tests.lib import mock_matchers
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class CopyFilesTest(test_base.BaseSSHTest):
  """Limited set of tests for `compute copy-files` command.

  Since `compute copy-files` shares implementation with `compute scp`, a more
  extensive command with more flags, these tests are meant to only test very
  basic functionality, and to make sure that the appropriate SCPCommand is
  constructed.
  """

  def SetUp(self):
    # No need to specify that we are using the GA api, and the GA command group
    # which is not the case for scp.
    self.instance = self.messages.Instance(
        id=11111,
        name='instance-1',
        networkInterfaces=[
            self.messages.NetworkInterface(
                accessConfigs=[
                    self.messages.AccessConfig(natIP='23.251.133.1'),
                ],
            ),
        ],
        status=self.messages.Instance.StatusValueValuesEnum.RUNNING,
        selfLink=(self.compute_uri + '/projects/my-project/'
                  'zones/zone-1/instances/instance-1'),
        zone=(self.compute_uri + '/projects/my-project/zones/zone-1'))

    self.instance_without_external_ip_address = self.messages.Instance(
        id=22222,
        name='instance-2',
        networkInterfaces=[
            self.messages.NetworkInterface(),
        ],
        status=self.messages.Instance.StatusValueValuesEnum.RUNNING,
        selfLink=(self.compute_uri + '/projects/my-project/'
                  'zones/zone-1/instances/instance-4'),
        zone=(self.compute_uri + '/projects/my-project/zones/zone-1'))

    self.remote = ssh.Remote.FromArg('me@23.251.133.1')
    self.remote_file = ssh.FileReference('~/remote-file', remote=self.remote)
    self.local_dir = ssh.FileReference('~/local-dir')

  def testSimpleCase(self):
    """Base case that makes sure SCPCommand is constructed.

    Note that the only difference against `compute scp` is that this command
    adds the `-r` recursive flag by default.
    """
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project_resource],
    ])

    self.Run("""\
        compute copy-files
          instance-1:~/remote-file
          ~/local-dir --zone zone-1
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

    # SCP Command
    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [self.remote_file],
        self.local_dir,
        identity_file=self.private_key_file,
        extra_flags=None,
        port=None,
        recursive=True,
        compress=False,
        options=dict(self.options, HostKeyAlias='compute.11111'))

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)

    self.AssertErrContains('deprecated')

  def testFlags(self):
    """Test all flags that are allowed for copy-files."""
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project_resource],
    ])

    self.Run("""\
        compute copy-files
          instance-1:~/remote-file
          ~/local-dir --zone zone-1
          --quiet
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

    # SCP Command
    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [self.remote_file],
        self.local_dir,
        identity_file=self.private_key_file,
        extra_flags=None,
        port=None,
        recursive=True,
        compress=False,
        options=dict(self.options, HostKeyAlias='compute.11111'))

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)


if __name__ == '__main__':
  test_case.main()
