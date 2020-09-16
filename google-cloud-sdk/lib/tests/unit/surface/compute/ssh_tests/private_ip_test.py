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
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import exceptions as core_exceptions
from tests.lib import mock_matchers
from tests.lib import test_case
from tests.lib.surface.compute import test_base

import mock


MESSAGES = apis.GetMessagesModule('compute', 'v1')

INTERNAL_IP = '10.240.0.52'

INSTANCE_WITHOUT_EXTERNAL_ADDRESS = MESSAGES.Instance(
    id=22222,
    name='instance-2',
    networkInterfaces=[
        MESSAGES.NetworkInterface(networkIP=INTERNAL_IP),
    ],
    status=MESSAGES.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-2/instances/instance-2'),
    zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-2'))


class SSHPrivateIpTest(test_base.BaseSSHTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')

    # Common test vars
    self.remote = ssh.Remote(INTERNAL_IP, user='john')

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITHOUT_EXTERNAL_ADDRESS],
        [self.project_resource],
        [],
    ])

    self.Run("""compute ssh john@instance-1 --zone zone-1 --internal-ip""")

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # SSH Command
    self.ssh_init.assert_has_calls(
        [
            mock.call(
                mock_matchers.TypeMatcher(ssh.SSHCommand),
                remote=self.remote,
                identity_file=self.private_key_file,
                options=dict(self.options, HostKeyAlias='compute.22222'),
                remote_command=[
                    '[ `curl "http://metadata.google.internal/'
                    'computeMetadata/v1/instance/id" -H "Metadata-Flavor: '
                    'Google" -q` = 22222 ] || exit 23'],
            ),
            mock.call(
                mock_matchers.TypeMatcher(ssh.SSHCommand),
                remote=self.remote,
                identity_file=self.private_key_file,
                extra_flags=[],
                tty=None,
                options=dict(self.options, HostKeyAlias='compute.22222'),
                remote_command=None,
                iap_tunnel_args=None,
                remainder=[],
            ),
        ],
        any_order=True,
    )

    self.ssh_run.assert_has_calls([
        mock.call(mock_matchers.TypeMatcher(ssh.SSHCommand), self.env,
                  force_connect=True),
        mock.call(mock_matchers.TypeMatcher(ssh.SSHCommand), self.env,
                  force_connect=True)])
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
                          key='a',
                          value='b'),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value='john:' + self.public_key_material),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='sshKeys',
                          value='me:{0}\n'.format(self.public_key_material)),
                  ]),

              project='my-project'))],
    )

  def testMismatchedInstanceId(self):
    self.ssh_run.return_value = 23
    self.make_requests.side_effect = iter([
        [INSTANCE_WITHOUT_EXTERNAL_ADDRESS],
        [self.project_resource],
        [],
    ])

    with self.AssertRaisesExceptionRegexp(
        core_exceptions.NetworkIssueError,
        r'Established connection with host {} but was unable to '
        r'confirm ID of the instance.'.format(INTERNAL_IP)):
      self.Run("""compute ssh john@instance-1 --zone zone-1 --internal-ip""")

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
                          key='a',
                          value='b'),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value='john:' + self.public_key_material),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='sshKeys',
                          value='me:{0}\n'.format(self.public_key_material)),
                  ]),

              project='my-project'))],
    )
    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # SSH Command
    self.ssh_init.assert_has_calls(
        [
            mock.call(
                mock_matchers.TypeMatcher(ssh.SSHCommand),
                remote=self.remote,
                identity_file=self.private_key_file,
                options=dict(self.options, HostKeyAlias='compute.22222'),
                remote_command=[
                    '[ `curl "http://metadata.google.internal/'
                    'computeMetadata/v1/instance/id" -H "Metadata-Flavor: '
                    'Google" -q` = 22222 ] || exit 23'],
            ),
            mock.call(
                mock_matchers.TypeMatcher(ssh.SSHCommand),
                remote=self.remote,
                identity_file=self.private_key_file,
                options=dict(self.options, HostKeyAlias='compute.22222'),
                remote_command=None,
                extra_flags=[],
                tty=None,
                iap_tunnel_args=None,
                remainder=[],
            ),
        ],
        any_order=True,
    )

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testDisableInternalIpVerification(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITHOUT_EXTERNAL_ADDRESS],
        [self.project_resource],
        [],
    ])

    self.Run('compute ssh john@instance-1 --zone zone-1 --internal-ip '
             '--no-verify-internal-ip')

    # Only expect one call since we're skipping the IP verification connection.
    self.ssh_init.assert_called_once()
    self.ssh_run.assert_called_once()
    self.AssertErrContains(
        'Skipping internal IP verification connection and connecting to [{}] '
        'in the current subnet.'.format(INTERNAL_IP))


if __name__ == '__main__':
  test_case.main()
