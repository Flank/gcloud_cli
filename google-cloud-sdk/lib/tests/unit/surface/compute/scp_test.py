# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Tests for `gcloud beta compute scp`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute import iap_tunnel
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import retry
from tests.lib import mock_matchers
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock

_INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY = 'with_external_ip_address'
_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY = 'without_external_ip_address'


class ScpBaseTest(test_base.BaseSSHTest):

  def SetUp(self):
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
            selfLink=(self.compute_uri + '/projects/my-project/'
                      'zones/zone-1/instances/instance-1'),
            zone=(self.compute_uri + '/projects/my-project/zones/zone-1')),
        _INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY: self.messages.Instance(
            id=22222,
            name='instance-2',
            networkInterfaces=[
                self.messages.NetworkInterface(networkIP='10.240.0.53'),
            ],
            status=self.messages.Instance.StatusValueValuesEnum.RUNNING,
            selfLink=(self.compute_uri + '/projects/my-project/'
                      'zones/zone-1/instances/instance-4'),
            zone=(self.compute_uri + '/projects/my-project/zones/zone-1')),
    }
    self.instance = self.instances[_INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY]
    self.instance_without_external_ip_address = self.instances[
        _INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY]


class ScpTest(ScpBaseTest):

  def SetUp(self):
    self.remote = ssh.Remote.FromArg('me@23.251.133.1')
    self.remote_file = ssh.FileReference('~/remote-file', remote=self.remote)
    self.local_dir = ssh.FileReference('~/local-dir')

    datetime_patcher = mock.patch('datetime.datetime',
                                  test_base.FakeDateTimeWithTimeZone)
    self.addCleanup(datetime_patcher.stop)
    datetime_patcher.start()

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project_resource],
    ])

    self.Run("""\
        compute scp
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
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        iap_tunnel_args=None)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)

  def testPlain(self):
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project_resource],
    ])

    self.Run("""\
        compute scp --plain
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

    # Don't require SSH keys
    self.ensure_keys.assert_not_called()

    # No polling
    self.poller_poll.assert_not_called()

    # SCP Command without options and identity_file
    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [self.remote_file],
        self.local_dir,
        identity_file=None,
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=None,
        iap_tunnel_args=None)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)

  def testDryRun(self):
    scp_build = self.StartObjectPatch(
        ssh.SCPCommand, 'Build', return_value=['scp', 'cmd'])
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project_resource],
    ])

    self.Run("""\
        compute scp --dry-run
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
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        iap_tunnel_args=None)

    scp_build.assert_called_once_with(self.env)

    self.scp_run.assert_not_called()

    self.AssertOutputEquals('scp cmd\n')

  def testFlags(self):
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project_resource],
    ])

    self.Run("""\
        compute scp
          instance-1:~/remote-file
          ~/local-dir --zone zone-1
          --quiet --compress --recurse --port 2222 --scp-flag='-F'
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
        extra_flags=['-F'],
        port='2222',
        recursive=True,
        compress=True,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        iap_tunnel_args=None)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)

  def testDisableForceConnect(self):
    properties.VALUES.ssh.putty_force_connect.Set(False)
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project_resource],
    ])

    self.Run("""\
        compute scp
          instance-1:~/remote-file
          ~/local-dir --zone zone-1
        """)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=False)

  def testWithAlternateUser(self):
    project_resource = self.messages.Project(
        name='my-project',
    )
    self.make_requests.side_effect = iter([
        [self.instance],
        [project_resource],
        [],
    ])

    self.Run("""\
        compute scp
          hapoo@instance-1:~/remote-file
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

    remote = ssh.Remote(self.remote.host, user='hapoo')
    remote_file = ssh.FileReference('~/remote-file', remote=remote)
    # Polling
    self.poller_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        remote=remote,
        identity_file=self.private_key_file,
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_MS,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        extra_flags=None,
        iap_tunnel_args=None)
    self.poller_poll.assert_called_once()

    # SCP Command
    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [remote_file],
        self.local_dir,
        identity_file=self.private_key_file,
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        iap_tunnel_args=None)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)

  def testWithRelativeExpiration(self):
    project_resource = self.messages.Project(
        name='my-project',
    )
    self.make_requests.side_effect = iter([
        [self.instance],
        [project_resource],
        [],
    ])

    self.Run("""\
        compute scp
          instance-1:~/remote-file
          ~/local-dir --zone zone-1
          --ssh-key-expire-after 1d
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
                          key='ssh-keys',
                          value=('me:{0} google-ssh {{"userName":"me",'
                                 '"expireOn":'
                                 '"2014-01-03T03:04:05+0000"}}').format(
                                     self.pubkey.ToEntry())),
                  ]),

              project='my-project'))],
    )

    remote = ssh.Remote(self.remote.host, user='me')
    remote_file = ssh.FileReference('~/remote-file', remote=remote)
    # Polling
    self.poller_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        remote=remote,
        identity_file=self.private_key_file,
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_MS,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        extra_flags=None,
        iap_tunnel_args=None)
    self.poller_poll.assert_called_once()

    # SCP Command
    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [remote_file],
        self.local_dir,
        identity_file=self.private_key_file,
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        iap_tunnel_args=None)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)

  def testWithAbsoluteExpiration(self):
    project_resource = self.messages.Project(
        name='my-project',
    )
    self.make_requests.side_effect = iter([
        [self.instance],
        [project_resource],
        [],
    ])

    self.Run("""\
        compute scp
          instance-1:~/remote-file
          ~/local-dir --zone zone-1
          --ssh-key-expiration 2015-01-23T12:34:56+0000
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
                          key='ssh-keys',
                          value=('me:{0} google-ssh {{"userName":"me",'
                                 '"expireOn":'
                                 '"2015-01-23T12:34:56+0000"}}').format(
                                     self.pubkey.ToEntry())),
                  ]),

              project='my-project'))],
    )

    remote = ssh.Remote(self.remote.host, user='me')
    remote_file = ssh.FileReference('~/remote-file', remote=remote)
    # Polling
    self.poller_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        remote=remote,
        identity_file=self.private_key_file,
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_MS,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        extra_flags=None,
        iap_tunnel_args=None)
    self.poller_poll.assert_called_once()

    # SCP Command
    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [remote_file],
        self.local_dir,
        identity_file=self.private_key_file,
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        iap_tunnel_args=None)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)

  def testWithPollingTimeout(self):
    self.poller_poll.side_effect = retry.WaitException('msg', 'result', 'state')
    project_resource = self.messages.Project(
        name='my-project',
    )
    self.make_requests.side_effect = iter([
        [self.instance],
        [project_resource],
        [],
    ])

    with self.AssertRaisesExceptionMatches(
        ssh_utils.NetworkError, 'Could not SSH into the instance'):
      self.Run("""\
          compute scp
            hapoo@instance-1:~/remote-file
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

    remote = ssh.Remote(self.remote.host, user='hapoo')
    # Polling
    self.poller_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        remote=remote,
        identity_file=self.private_key_file,
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_MS,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        extra_flags=None,
        iap_tunnel_args=None)
    self.poller_poll.assert_called_once()

    self.scp_run.assert_not_called()

  def testWithHostWithoutExternalIPAddress(self):
    self.make_requests.side_effect = iter([
        [self.instance_without_external_ip_address],
        [self.project_resource],
    ])

    with self.AssertRaisesExceptionRegexp(
        ssh_utils.MissingExternalIPAddressError,
        r'Instance \[instance-2\] in zone \[zone-1\] does not have an external '
        'IP address, so you cannot SSH into it. To add an external IP address '
        r'to the instance, use \[gcloud compute instances '
        r'add-access-config\].'):
      self.Run("""\
          compute scp
            instance-2:~/remote-file
             ~/local-dir
            --zone zone-1 --no-tunnel-through-iap
          """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-2',
              project='my-project',
              zone='zone-1'))],
        [(self.compute.projects,
          'Get',
          self.messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )

  def testWithManyLocalFilesToRemoteDestination(self):
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project_resource],
    ])

    self.Run("""\
        compute scp
          ~/local-file-1
          ~/local-file-2
          ~/local-file-3
          instance-1:~/remote-dir
          --zone zone-1
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

    remote_dir = ssh.FileReference('~/remote-dir', remote=self.remote)

    # SCP Command
    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [
            ssh.FileReference('~/local-file-1'),
            ssh.FileReference('~/local-file-2'),
            ssh.FileReference('~/local-file-3'),
        ],
        remote_dir,
        identity_file=self.private_key_file,
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        iap_tunnel_args=None)

  def testWithManyRemoteFilesToLocalDestination(self):
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project_resource],
    ])

    self.Run(r"""
        compute scp
          instance-1:~/remote-file-1
          instance-1:~/remote-file-2
          instance-1:~/remote-file-3
          ~/local-dir
          --zone zone-1
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

    remote = ssh.Remote('23.251.133.1', user='me')

    # SCP Command
    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [
            ssh.FileReference('~/remote-file-1', remote=remote),
            ssh.FileReference('~/remote-file-2', remote=remote),
            ssh.FileReference('~/remote-file-3', remote=remote),
        ],
        self.local_dir,
        identity_file=self.private_key_file,
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        iap_tunnel_args=None)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)

  def testLocalToLocalFileCopyingFails(self):
    with self.AssertRaisesExceptionRegexp(
        ssh.InvalidConfigurationError,
        r'Source\(s\) must be remote when destination is local.'):
      self.Run("""\
          compute scp
            ~/local-file-1
            ~/local-file-2
            --zone zone-1
          """)

    self.CheckRequests()

  def testRemoteToRemoteFileCopyingFails(self):
    with self.AssertRaisesExceptionRegexp(
        ssh.InvalidConfigurationError,
        'All sources must be local files when destination is remote.'):
      self.Run("""\
          compute scp
            instance-1:~/remote-src
            instance-2:~/remote-dest
            --zone zone-1
          """)

    self.CheckRequests()

  def testManyRemoteHostsToLocalCopyingFails(self):
    with self.AssertRaisesExceptionRegexp(
        ssh.InvalidConfigurationError,
        'All sources must refer to the same remote'):
      self.Run("""\
          compute scp
            instance-1:~/remote-src-1
            instance-2:~/remote-src-2
            ~/dest
            --zone zone-1
          """)

    self.CheckRequests()

  def testScpError(self):
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project_resource],
    ])
    self.scp_run.side_effect = ssh.CommandError('scp', return_code=255)
    with self.assertRaisesRegex(
        ssh.CommandError,
        r'\[scp\] exited with return code \[255\].'):
      self.Run("""\
          compute scp
          instance-1:~/remote-file
          ~/local-dir
          --zone zone-1
          """)

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)

    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(name='instance-1', zone='zone-1'),
        ],

        [self.instance],

        [self.project_resource],
    ])

    self.Run("""\
        compute scp
          instance-1:~/remote-file
          ~/local-dir
        """)

    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance-1'),

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
    self.AssertErrContains(
        'No zone specified. Using zone [zone-1] for instance: [instance-1].')

    # SCP Command
    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [self.remote_file],
        self.local_dir,
        identity_file=self.private_key_file,
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        iap_tunnel_args=None)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)


class ScpOsloginTest(test_base.BaseSSHTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)

    self.instance_with_oslogin_enabled = self.messages.Instance(
        id=44444,
        name='instance-4',
        metadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='enable-oslogin',
                    value='TruE'),
            ]
        ),
        networkInterfaces=[
            self.messages.NetworkInterface(
                accessConfigs=[
                    self.messages.AccessConfig(
                        name='external-nat',
                        natIP='23.251.133.75'),
                ],
            ),
        ],
        status=self.messages.Instance.StatusValueValuesEnum.RUNNING,
        selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/instances/instance-1'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1'))

  @mock.patch(
      'googlecloudsdk.api_lib.oslogin.client._GetClient')
  def testSimpleCase(self, oslogin_mock):
    properties.VALUES.core.account.Set('user@google.com')
    self.remote = ssh.Remote.FromArg('user_google_com@23.251.133.75')
    self.remote_file = ssh.FileReference('~/remote-file', remote=self.remote)
    self.local_dir = ssh.FileReference('~/local-dir')
    oslogin_mock.return_value = test_resources.MakeOsloginClient('v1beta')

    self.make_requests.side_effect = iter([
        [self.instance_with_oslogin_enabled],
        [self.project_resource],
    ])

    self.Run("""\
        compute scp
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
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=dict(self.options, HostKeyAlias='compute.44444'),
        iap_tunnel_args=None)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)

  @mock.patch(
      'googlecloudsdk.api_lib.oslogin.client._GetClient')
  def testOverrideUsername(self, oslogin_mock):
    properties.VALUES.core.account.Set('user@google.com')
    self.remote = ssh.Remote.FromArg('user_google_com@23.251.133.75')
    self.remote_file = ssh.FileReference('~/remote-file', remote=self.remote)
    self.local_dir = ssh.FileReference('~/local-dir')
    oslogin_mock.return_value = test_resources.MakeOsloginClient('v1beta')

    self.make_requests.side_effect = iter([
        [self.instance_with_oslogin_enabled],
        [self.project_resource],
    ])

    self.Run("""\
        compute scp
          someotheruser@instance-1:~/remote-file
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
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=dict(self.options, HostKeyAlias='compute.44444'),
        iap_tunnel_args=None)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)

    self.AssertErrContains('Using OS Login user [user_google_com] instead '
                           'of requested user [someotheruser]')


class SCPPrivateIpTest(test_base.BaseSSHTest, parameterized.TestCase):

  def _SetUpForTrack(self, track, api_version):
    self.track = track
    self.SelectApi(api_version)
    self.instance_with_internal_ip_address = self.messages.Instance(
        id=33333,
        name='instance-3',
        networkInterfaces=[
            self.messages.NetworkInterface(networkIP='10.240.0.52'),
        ],
        status=self.messages.Instance.StatusValueValuesEnum.RUNNING,
        selfLink=('https://compute.googleapis.com/compute/{}/projects/my-project/'
                  'zones/zone-1/instances/instance-3').format(api_version),
        zone=('https://compute.googleapis.com/compute/{}/projects/my-project/'
              'zones/zone-1').format(api_version))

  @parameterized.named_parameters(
      ('GA', calliope_base.ReleaseTrack.GA, 'v1'),
      ('Beta', calliope_base.ReleaseTrack.BETA, 'beta'),
      ('Alpha', calliope_base.ReleaseTrack.ALPHA, 'alpha'),
  )
  def testWithInternalIPAddress(self, track, api_version):
    self._SetUpForTrack(track, api_version)
    self.make_requests.side_effect = iter([
        [self.instance_with_internal_ip_address],
        [self.project_resource],
    ])

    self.Run("""
      compute scp
      ~/local-file-1 instance-3:~/remote-dir
      --zone zone-1 --internal-ip
      """)
    self.CheckRequests(
        [(self.compute.instances, 'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-3', project='my-project', zone='zone-1'))],
        [(self.compute.projects, 'Get',
          self.messages.ComputeProjectsGetRequest(project='my-project'))],
    )
    self.remote = ssh.Remote.FromArg('me@10.240.0.52')
    self.remote_dir = ssh.FileReference('~/remote-dir', self.remote)
    self.local_file = ssh.FileReference('~/local-file-1')

    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand), [self.local_file],
        self.remote_dir,
        identity_file=self.private_key_file,
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=dict(self.options, HostKeyAlias='compute.33333'),
        iap_tunnel_args=None)

    self.ssh_init.assert_has_calls(
        [
            mock.call(
                mock_matchers.TypeMatcher(ssh.SSHCommand),
                remote=self.remote,
                identity_file=self.private_key_file,
                options=dict(self.options, HostKeyAlias='compute.33333'),
                remote_command=[
                    '[ `curl "http://metadata.google.internal/'
                    'computeMetadata/v1/instance/id" -H "Metadata-Flavor: '
                    'Google" -q` = 33333 ] || exit 23'
                ]),
        ],
        any_order=True)


class ScpTunnelThroughIapTestGA(ScpBaseTest, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi('v1' if self.track.prefix is None else self.track.prefix)

  @parameterized.parameters((_INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY, True),
                            (_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY, True),
                            (_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY, False))
  def testSimpleCase(self, test_instance_key, explicit_flag):
    test_instance = self.instances[test_instance_key]
    self.make_requests.side_effect = iter([
        [test_instance],
        [self.project_resource],
    ])

    self.Run('compute scp {}:~/remote-file ~/local-dir --zone zone-1{}'.format(
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

    # SCP Command
    remote_file = ssh.FileReference(
        '~/remote-file',
        remote=ssh.Remote.FromArg('me@compute.%s' % test_instance.id))
    local_dir = ssh.FileReference('~/local-dir')
    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [remote_file],
        local_dir,
        identity_file=self.private_key_file,
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=dict(self.options,
                     HostKeyAlias='compute.%s' % test_instance.id),
        iap_tunnel_args=expected_tunnel_args)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)

  @parameterized.parameters((_INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY,),
                            (_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY,))
  def testWithAlternateUser(self, test_instance_key):
    project_resource = self.messages.Project(
        name='my-project',
    )
    test_instance = self.instances[test_instance_key]
    self.make_requests.side_effect = iter([
        [test_instance],
        [project_resource],
        [],
    ])

    self.Run('compute scp hapoo@{}:~/remote-file ~/local-dir '
             '--zone zone-1 --tunnel-through-iap'.format(test_instance.name))
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
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_MS,
        options=dict(self.options,
                     HostKeyAlias='compute.%s' % test_instance.id),
        extra_flags=None,
        iap_tunnel_args=expected_tunnel_args)
    self.poller_poll.assert_called_once()

    # SCP Command
    remote_file = ssh.FileReference('~/remote-file', remote=remote)
    self.scp_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        [remote_file],
        ssh.FileReference('~/local-dir'),
        identity_file=self.private_key_file,
        extra_flags=[],
        port=None,
        recursive=False,
        compress=False,
        options=dict(self.options,
                     HostKeyAlias='compute.%s' % test_instance.id),
        iap_tunnel_args=expected_tunnel_args)

    self.scp_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SCPCommand),
        self.env, force_connect=True)

  @parameterized.parameters((_INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY,),
                            (_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY,))
  def testWithPollingTimeout(self, test_instance_key):
    self.poller_poll.side_effect = retry.WaitException('msg', 'result', 'state')
    project_resource = self.messages.Project(
        name='my-project',
    )
    test_instance = self.instances[test_instance_key]
    self.make_requests.side_effect = iter([
        [test_instance],
        [project_resource],
        [],
    ])

    with self.AssertRaisesExceptionMatches(
        ssh_utils.NetworkError, 'Could not SSH into the instance'):
      self.Run('compute scp hapoo@{}:~/remote-file ~/local-dir '
               '--zone zone-1 --tunnel-through-iap'.format(test_instance.name))

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
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_MS,
        options=dict(self.options,
                     HostKeyAlias='compute.%s' % test_instance.id),
        extra_flags=None,
        iap_tunnel_args=expected_tunnel_args)
    self.poller_poll.assert_called_once()

    self.scp_run.assert_not_called()


class ScpTunnelThroughIapTestBeta(ScpTunnelThroughIapTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ScpTunnelThroughIapTestAlpha(ScpTunnelThroughIapTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
