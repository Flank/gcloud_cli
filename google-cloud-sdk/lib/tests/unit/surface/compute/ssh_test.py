# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

import io
import os
import textwrap

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import apis_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute import iap_tunnel
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.util import retry
from tests.lib import completer_test_base
from tests.lib import mock_matchers
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock
import six

_INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY = 'with_external_ip_address'
_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY = 'without_external_ip_address'

MESSAGES = apis.GetMessagesModule('compute', 'v1')

INSTANCE_WITH_EXTERNAL_ADDRESS = MESSAGES.Instance(
    id=11111,
    name='instance-1',
    networkInterfaces=[
        MESSAGES.NetworkInterface(
            accessConfigs=[
                MESSAGES.AccessConfig(
                    name='external-nat',
                    natIP='23.251.133.75'),
            ],
        ),
    ],
    status=MESSAGES.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-1'),
    zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-1'))

INSTANCE_WITHOUT_EXTERNAL_ADDRESS = MESSAGES.Instance(
    id=22222,
    name='instance-2',
    networkInterfaces=[
        MESSAGES.NetworkInterface(networkIP='10.240.0.52'),
    ],
    status=MESSAGES.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-2/instances/instance-2'),
    zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-2'))

# An instance resource that has not been allocated an IP address
# yet. Users can get a resource like this if they attempt to SSH into
# an instance that has just been created, but its operation's status
# is not DONE yet.
INSTANCE_WITHOUT_EXTERNAL_ADDRESS_YET = MESSAGES.Instance(
    id=33333,
    name='instance-3',
    networkInterfaces=[
        MESSAGES.NetworkInterface(
            accessConfigs=[
                MESSAGES.AccessConfig(
                    name='external-nat'),
            ],
        ),
    ],
    status=MESSAGES.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-3'),
    zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-1'))


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
        MESSAGES.NetworkInterface(
            accessConfigs=[
                MESSAGES.AccessConfig(
                    name='external-nat',
                    natIP='23.251.133.75'),
            ],
        ),
    ],
    status=MESSAGES.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-1'),
    zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
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
        MESSAGES.NetworkInterface(
            accessConfigs=[
                MESSAGES.AccessConfig(
                    name='external-nat',
                    natIP='23.251.133.75'),
            ],
        ),
    ],
    status=MESSAGES.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-1'),
    zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-1'))


class SSHTest(test_base.BaseSSHTest, test_case.WithInput):

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
          compute ssh instance-2 --zone zone-2
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
          compute ssh instance-3 --zone zone-1
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
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_SEC,
        options=dict(self.options, HostKeyAlias='compute.11111'))

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
        extra_flags=['-vvv', '-o', 'HostName=\'23.251.133.75\'', '-o',
                     'User=me'],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testWithStrictHostKeyChecking(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        --strict-host-key-checking yes
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
        options=dict(self.options, StrictHostKeyChecking='yes',
                     HostKeyAlias='compute.11111'),
        remote_command=None,
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
        remainder=[])

  def testWithKeyPropagationDelay(self):

    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource_without_metadata],
        [],
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
        [(self.compute_v1.projects,
          'SetCommonInstanceMetadata',
          self.messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=self.messages.Metadata(
                  items=[
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value='me:' + self.public_key_material),
                  ]),

              project='my-project'))],
    )
    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # Polling
    self.poller_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_SEC,
        options=dict(self.options, HostKeyAlias='compute.11111'))

    self.poller_poll.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        self.env, force_connect=True)

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=self.remote,
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        remote_command=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    self.AssertErrContains('Updating project ssh metadata')

  def testWithSSHKeyWithNonAscii(self):
    # Ensure that a non-ASCII public key doesn't cause a crash.
    # Same with non-ASCII local username

    modified_public_key_material = str(self.public_key_material) + '\u0394'
    self.pubkey.comment += '\u0394'

    ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer
        """)
    project_resource_with_existing_key = self.messages.Project(
        commonInstanceMetadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='ssh-keys',
                    value=ssh_keys),
            ]),
        name='my-project',
    )

    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [project_resource_with_existing_key],
        [],
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
        [(self.compute_v1.projects,
          'SetCommonInstanceMetadata',
          self.messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=self.messages.Metadata(
                  items=[
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value=(ssh_keys + str('me') + ':' +
                                 modified_public_key_material)),
                  ]),

              project='my-project'))],
    )
    self.AssertErrContains('Updating project ssh metadata')

  def testWithNoSSHKeysProjectMetadata(self):

    project_resource_with_other_metadata = self.messages.Project(
        commonInstanceMetadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
            ]),
        name='my-project',
    )
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [project_resource_with_other_metadata],
        [],
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
        [(self.compute_v1.projects,
          'SetCommonInstanceMetadata',
          self.messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=self.messages.Metadata(
                  items=[
                      self.messages.Metadata.ItemsValueListEntry(
                          key='a',
                          value='b'),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value='me:' + self.public_key_material),
                  ]),

              project='my-project'))],
    )
    self.AssertErrContains('Updating project ssh metadata')

  def testWithManySSHKeysProjectMetadata(self):

    ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpBFilw+qXCrkbxzk3jQ+Bx/wLpPozc6Nz1A/LjHWlmXJ94js9PVHPwhg7JbiMlakn5rHEPRNEHF9S2m6lOIV1s0KCZR1FYpQArB312KCbH8TtovPwAOgcwcosEn54Ewko5EOCpQAMYdEs4qMAOR7tGA5Opi/rEx9S5n3DohZ5XIcbtRshgMDllYN6OAdck3WN2tj4JWjUrUXRI3BVxKTxlmH9zRqIta6Ph2M/+/DYnQa+jyAzYXiErqqmylT/OReYXxhSVbM+GLsuW82On+wa8DrL8YomHejwKAkZZgH9LGw6QIwI8GNWyF0SbMx1fYnEedp1DSi0Kt2gfIcah+0Z me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC5n+uTbZOqqMapxVy621kJbpEvPiiy40rkU7d43WUQC00HPvXeN68ZzXiXgpRFtdJi9UbmmuTuPWgwkKI+Ifx/khM0BDTb9akJJnAizp26zbYoCQTxxzwvrv0DXTaMUThTdw6RVEKYVm69QoAQXpj0O06BHgb7Vp0si240Ny9xFMDfm0LURcemw0/GkakYbEa3LCpC8qNA+hjFc7LP6F//MbgxLgJPMM9e63SlxvAYfkJMzX/nCVcT55a01ng3VXihtt4+ERHhtJfZaPnAoMqagvi1iBQLPreP8euXjtZyHLiUtdYOJV6tuUFNyTeB1I0H2ll3ikDHJjpYGsSv/ffZ me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+NC6tKzpT0GiYwscFoD8n/MdktvymPO8ncn2pAIAy34yiworwx9hLlOeMDsHaFb5LoT3qgqPoiaH1KWmFILKGtb/s9xqzpGZQFPu62nE4zd6Fa82c0rREtIfvst6EbclWSS4uLSn+Pmb6AQBZm3hubbslUMRZzj0vihyVi1y0rboL2U4X8ROZwQzZKG8iQf6k0A31Nb77DOqxQD4twPs2TCU5Hzc7mGWZGDbrUljWNyLJFBoTRDVa+Llc7aKP3MEzR20VcXB1SbB1BZr93MpQkQ+hpmoMAxikmhR6EpRfDs+pw2lHdBuOljhdJhOIZLudJAEfLwZw/4B9rZo9J6xn me@my-computer
        """)

    project_resource_with_many_ssh_keys = self.messages.Project(
        commonInstanceMetadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.messages.Metadata.ItemsValueListEntry(
                    key='ssh-keys',
                    value=ssh_keys),
            ]),
        name='my-project',
    )
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [project_resource_with_many_ssh_keys],
        [],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        """)

    new_ssh_keys = ssh_keys + 'me:' + self.public_key_material

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
                          key='a',
                          value='b'),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value=new_ssh_keys),
                  ]),

              project='my-project'))],
    )
    self.AssertErrContains('Updating project ssh metadata')

  def testWithManySSHKeysInLegacyProjectMetadata(self):

    ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpBFilw+qXCrkbxzk3jQ+Bx/wLpPozc6Nz1A/LjHWlmXJ94js9PVHPwhg7JbiMlakn5rHEPRNEHF9S2m6lOIV1s0KCZR1FYpQArB312KCbH8TtovPwAOgcwcosEn54Ewko5EOCpQAMYdEs4qMAOR7tGA5Opi/rEx9S5n3DohZ5XIcbtRshgMDllYN6OAdck3WN2tj4JWjUrUXRI3BVxKTxlmH9zRqIta6Ph2M/+/DYnQa+jyAzYXiErqqmylT/OReYXxhSVbM+GLsuW82On+wa8DrL8YomHejwKAkZZgH9LGw6QIwI8GNWyF0SbMx1fYnEedp1DSi0Kt2gfIcah+0Z me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC5n+uTbZOqqMapxVy621kJbpEvPiiy40rkU7d43WUQC00HPvXeN68ZzXiXgpRFtdJi9UbmmuTuPWgwkKI+Ifx/khM0BDTb9akJJnAizp26zbYoCQTxxzwvrv0DXTaMUThTdw6RVEKYVm69QoAQXpj0O06BHgb7Vp0si240Ny9xFMDfm0LURcemw0/GkakYbEa3LCpC8qNA+hjFc7LP6F//MbgxLgJPMM9e63SlxvAYfkJMzX/nCVcT55a01ng3VXihtt4+ERHhtJfZaPnAoMqagvi1iBQLPreP8euXjtZyHLiUtdYOJV6tuUFNyTeB1I0H2ll3ikDHJjpYGsSv/ffZ me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+NC6tKzpT0GiYwscFoD8n/MdktvymPO8ncn2pAIAy34yiworwx9hLlOeMDsHaFb5LoT3qgqPoiaH1KWmFILKGtb/s9xqzpGZQFPu62nE4zd6Fa82c0rREtIfvst6EbclWSS4uLSn+Pmb6AQBZm3hubbslUMRZzj0vihyVi1y0rboL2U4X8ROZwQzZKG8iQf6k0A31Nb77DOqxQD4twPs2TCU5Hzc7mGWZGDbrUljWNyLJFBoTRDVa+Llc7aKP3MEzR20VcXB1SbB1BZr93MpQkQ+hpmoMAxikmhR6EpRfDs+pw2lHdBuOljhdJhOIZLudJAEfLwZw/4B9rZo9J6xn me@my-computer
        """)

    project_resource_with_many_ssh_keys = self.messages.Project(
        commonInstanceMetadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.messages.Metadata.ItemsValueListEntry(
                    key='sshKeys',
                    value=ssh_keys),
            ]),
        name='my-project',
    )
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [project_resource_with_many_ssh_keys],
        [],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        """)

    new_ssh_key = 'me:' + self.public_key_material

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
                          key='a',
                          value='b'),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value=new_ssh_key),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='sshKeys',
                          value=ssh_keys),
                  ]),

              project='my-project'))],
    )
    self.AssertErrContains('Updating project ssh metadata')

  def testWithExistingSSHKeyInLegacyProjectMetadata(self):

    ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpBFilw+qXCrkbxzk3jQ+Bx/wLpPozc6Nz1A/LjHWlmXJ94js9PVHPwhg7JbiMlakn5rHEPRNEHF9S2m6lOIV1s0KCZR1FYpQArB312KCbH8TtovPwAOgcwcosEn54Ewko5EOCpQAMYdEs4qMAOR7tGA5Opi/rEx9S5n3DohZ5XIcbtRshgMDllYN6OAdck3WN2tj4JWjUrUXRI3BVxKTxlmH9zRqIta6Ph2M/+/DYnQa+jyAzYXiErqqmylT/OReYXxhSVbM+GLsuW82On+wa8DrL8YomHejwKAkZZgH9LGw6QIwI8GNWyF0SbMx1fYnEedp1DSi0Kt2gfIcah+0Z me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC5n+uTbZOqqMapxVy621kJbpEvPiiy40rkU7d43WUQC00HPvXeN68ZzXiXgpRFtdJi9UbmmuTuPWgwkKI+Ifx/khM0BDTb9akJJnAizp26zbYoCQTxxzwvrv0DXTaMUThTdw6RVEKYVm69QoAQXpj0O06BHgb7Vp0si240Ny9xFMDfm0LURcemw0/GkakYbEa3LCpC8qNA+hjFc7LP6F//MbgxLgJPMM9e63SlxvAYfkJMzX/nCVcT55a01ng3VXihtt4+ERHhtJfZaPnAoMqagvi1iBQLPreP8euXjtZyHLiUtdYOJV6tuUFNyTeB1I0H2ll3ikDHJjpYGsSv/ffZ me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+NC6tKzpT0GiYwscFoD8n/MdktvymPO8ncn2pAIAy34yiworwx9hLlOeMDsHaFb5LoT3qgqPoiaH1KWmFILKGtb/s9xqzpGZQFPu62nE4zd6Fa82c0rREtIfvst6EbclWSS4uLSn+Pmb6AQBZm3hubbslUMRZzj0vihyVi1y0rboL2U4X8ROZwQzZKG8iQf6k0A31Nb77DOqxQD4twPs2TCU5Hzc7mGWZGDbrUljWNyLJFBoTRDVa+Llc7aKP3MEzR20VcXB1SbB1BZr93MpQkQ+hpmoMAxikmhR6EpRfDs+pw2lHdBuOljhdJhOIZLudJAEfLwZw/4B9rZo9J6xn me@my-computer
        """)

    ssh_keys = ssh_keys + 'me:' + self.public_key_material
    project_resource_with_many_ssh_keys = self.messages.Project(
        commonInstanceMetadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.messages.Metadata.ItemsValueListEntry(
                    key='sshKeys',
                    value=ssh_keys),
            ]),
        name='my-project',
    )
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [project_resource_with_many_ssh_keys],
        [],
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

  def testWithSSHKeysInNormalAndLegacyProjectMetadata(self):
    ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpBFilw+qXCrkbxzk3jQ+Bx/wLpPozc6Nz1A/LjHWlmXJ94js9PVHPwhg7JbiMlakn5rHEPRNEHF9S2m6lOIV1s0KCZR1FYpQArB312KCbH8TtovPwAOgcwcosEn54Ewko5EOCpQAMYdEs4qMAOR7tGA5Opi/rEx9S5n3DohZ5XIcbtRshgMDllYN6OAdck3WN2tj4JWjUrUXRI3BVxKTxlmH9zRqIta6Ph2M/+/DYnQa+jyAzYXiErqqmylT/OReYXxhSVbM+GLsuW82On+wa8DrL8YomHejwKAkZZgH9LGw6QIwI8GNWyF0SbMx1fYnEedp1DSi0Kt2gfIcah+0Z me@my-computer
        """)

    legacy_ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC5n+uTbZOqqMapxVy621kJbpEvPiiy40rkU7d43WUQC00HPvXeN68ZzXiXgpRFtdJi9UbmmuTuPWgwkKI+Ifx/khM0BDTb9akJJnAizp26zbYoCQTxxzwvrv0DXTaMUThTdw6RVEKYVm69QoAQXpj0O06BHgb7Vp0si240Ny9xFMDfm0LURcemw0/GkakYbEa3LCpC8qNA+hjFc7LP6F//MbgxLgJPMM9e63SlxvAYfkJMzX/nCVcT55a01ng3VXihtt4+ERHhtJfZaPnAoMqagvi1iBQLPreP8euXjtZyHLiUtdYOJV6tuUFNyTeB1I0H2ll3ikDHJjpYGsSv/ffZ me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+NC6tKzpT0GiYwscFoD8n/MdktvymPO8ncn2pAIAy34yiworwx9hLlOeMDsHaFb5LoT3qgqPoiaH1KWmFILKGtb/s9xqzpGZQFPu62nE4zd6Fa82c0rREtIfvst6EbclWSS4uLSn+Pmb6AQBZm3hubbslUMRZzj0vihyVi1y0rboL2U4X8ROZwQzZKG8iQf6k0A31Nb77DOqxQD4twPs2TCU5Hzc7mGWZGDbrUljWNyLJFBoTRDVa+Llc7aKP3MEzR20VcXB1SbB1BZr93MpQkQ+hpmoMAxikmhR6EpRfDs+pw2lHdBuOljhdJhOIZLudJAEfLwZw/4B9rZo9J6xn me@my-computer
        """)

    project_resource_with_many_ssh_keys = self.messages.Project(
        commonInstanceMetadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.messages.Metadata.ItemsValueListEntry(
                    key='ssh-keys',
                    value=ssh_keys),
                self.messages.Metadata.ItemsValueListEntry(
                    key='sshKeys',
                    value=legacy_ssh_keys),
            ]),
        name='my-project',
    )
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [project_resource_with_many_ssh_keys],
        [],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        """)

    new_ssh_keys = ssh_keys + 'me:' + self.public_key_material

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
                          key='a',
                          value='b'),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value=new_ssh_keys),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='sshKeys',
                          value=legacy_ssh_keys),
                  ]),

              project='my-project'))],
    )
    self.AssertErrContains('Updating project ssh metadata')

  def testWithExistingSSHKeyInProjectMetadataWithLegacyKeys(self):

    ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpBFilw+qXCrkbxzk3jQ+Bx/wLpPozc6Nz1A/LjHWlmXJ94js9PVHPwhg7JbiMlakn5rHEPRNEHF9S2m6lOIV1s0KCZR1FYpQArB312KCbH8TtovPwAOgcwcosEn54Ewko5EOCpQAMYdEs4qMAOR7tGA5Opi/rEx9S5n3DohZ5XIcbtRshgMDllYN6OAdck3WN2tj4JWjUrUXRI3BVxKTxlmH9zRqIta6Ph2M/+/DYnQa+jyAzYXiErqqmylT/OReYXxhSVbM+GLsuW82On+wa8DrL8YomHejwKAkZZgH9LGw6QIwI8GNWyF0SbMx1fYnEedp1DSi0Kt2gfIcah+0Z me@my-computer
        """)

    legacy_ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC5n+uTbZOqqMapxVy621kJbpEvPiiy40rkU7d43WUQC00HPvXeN68ZzXiXgpRFtdJi9UbmmuTuPWgwkKI+Ifx/khM0BDTb9akJJnAizp26zbYoCQTxxzwvrv0DXTaMUThTdw6RVEKYVm69QoAQXpj0O06BHgb7Vp0si240Ny9xFMDfm0LURcemw0/GkakYbEa3LCpC8qNA+hjFc7LP6F//MbgxLgJPMM9e63SlxvAYfkJMzX/nCVcT55a01ng3VXihtt4+ERHhtJfZaPnAoMqagvi1iBQLPreP8euXjtZyHLiUtdYOJV6tuUFNyTeB1I0H2ll3ikDHJjpYGsSv/ffZ me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+NC6tKzpT0GiYwscFoD8n/MdktvymPO8ncn2pAIAy34yiworwx9hLlOeMDsHaFb5LoT3qgqPoiaH1KWmFILKGtb/s9xqzpGZQFPu62nE4zd6Fa82c0rREtIfvst6EbclWSS4uLSn+Pmb6AQBZm3hubbslUMRZzj0vihyVi1y0rboL2U4X8ROZwQzZKG8iQf6k0A31Nb77DOqxQD4twPs2TCU5Hzc7mGWZGDbrUljWNyLJFBoTRDVa+Llc7aKP3MEzR20VcXB1SbB1BZr93MpQkQ+hpmoMAxikmhR6EpRfDs+pw2lHdBuOljhdJhOIZLudJAEfLwZw/4B9rZo9J6xn me@my-computer
        """)

    ssh_keys = ssh_keys + 'me:' + self.public_key_material
    project_resource_with_many_ssh_keys = self.messages.Project(
        commonInstanceMetadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.messages.Metadata.ItemsValueListEntry(
                    key='ssh-keys',
                    value=ssh_keys),
                self.messages.Metadata.ItemsValueListEntry(
                    key='sshKeys',
                    value=legacy_ssh_keys),
            ]),
        name='my-project',
    )
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [project_resource_with_many_ssh_keys],
        [],
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

  def testWithExistingLegacySSHKeyInProjectMetadataWithKeys(self):

    ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpBFilw+qXCrkbxzk3jQ+Bx/wLpPozc6Nz1A/LjHWlmXJ94js9PVHPwhg7JbiMlakn5rHEPRNEHF9S2m6lOIV1s0KCZR1FYpQArB312KCbH8TtovPwAOgcwcosEn54Ewko5EOCpQAMYdEs4qMAOR7tGA5Opi/rEx9S5n3DohZ5XIcbtRshgMDllYN6OAdck3WN2tj4JWjUrUXRI3BVxKTxlmH9zRqIta6Ph2M/+/DYnQa+jyAzYXiErqqmylT/OReYXxhSVbM+GLsuW82On+wa8DrL8YomHejwKAkZZgH9LGw6QIwI8GNWyF0SbMx1fYnEedp1DSi0Kt2gfIcah+0Z me@my-computer
        """)

    legacy_ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC5n+uTbZOqqMapxVy621kJbpEvPiiy40rkU7d43WUQC00HPvXeN68ZzXiXgpRFtdJi9UbmmuTuPWgwkKI+Ifx/khM0BDTb9akJJnAizp26zbYoCQTxxzwvrv0DXTaMUThTdw6RVEKYVm69QoAQXpj0O06BHgb7Vp0si240Ny9xFMDfm0LURcemw0/GkakYbEa3LCpC8qNA+hjFc7LP6F//MbgxLgJPMM9e63SlxvAYfkJMzX/nCVcT55a01ng3VXihtt4+ERHhtJfZaPnAoMqagvi1iBQLPreP8euXjtZyHLiUtdYOJV6tuUFNyTeB1I0H2ll3ikDHJjpYGsSv/ffZ me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+NC6tKzpT0GiYwscFoD8n/MdktvymPO8ncn2pAIAy34yiworwx9hLlOeMDsHaFb5LoT3qgqPoiaH1KWmFILKGtb/s9xqzpGZQFPu62nE4zd6Fa82c0rREtIfvst6EbclWSS4uLSn+Pmb6AQBZm3hubbslUMRZzj0vihyVi1y0rboL2U4X8ROZwQzZKG8iQf6k0A31Nb77DOqxQD4twPs2TCU5Hzc7mGWZGDbrUljWNyLJFBoTRDVa+Llc7aKP3MEzR20VcXB1SbB1BZr93MpQkQ+hpmoMAxikmhR6EpRfDs+pw2lHdBuOljhdJhOIZLudJAEfLwZw/4B9rZo9J6xn me@my-computer
        """)

    legacy_ssh_keys = legacy_ssh_keys + 'me:' + self.public_key_material
    project_resource_with_many_ssh_keys = self.messages.Project(
        commonInstanceMetadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.messages.Metadata.ItemsValueListEntry(
                    key='ssh-keys',
                    value=ssh_keys),
                self.messages.Metadata.ItemsValueListEntry(
                    key='sshKeys',
                    value=legacy_ssh_keys),
            ]),
        name='my-project',
    )
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [project_resource_with_many_ssh_keys],
        [],
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

  def testWithManySSHKeysLegacyInstanceMetadata(self):

    ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpBFilw+qXCrkbxzk3jQ+Bx/wLpPozc6Nz1A/LjHWlmXJ94js9PVHPwhg7JbiMlakn5rHEPRNEHF9S2m6lOIV1s0KCZR1FYpQArB312KCbH8TtovPwAOgcwcosEn54Ewko5EOCpQAMYdEs4qMAOR7tGA5Opi/rEx9S5n3DohZ5XIcbtRshgMDllYN6OAdck3WN2tj4JWjUrUXRI3BVxKTxlmH9zRqIta6Ph2M/+/DYnQa+jyAzYXiErqqmylT/OReYXxhSVbM+GLsuW82On+wa8DrL8YomHejwKAkZZgH9LGw6QIwI8GNWyF0SbMx1fYnEedp1DSi0Kt2gfIcah+0Z me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC5n+uTbZOqqMapxVy621kJbpEvPiiy40rkU7d43WUQC00HPvXeN68ZzXiXgpRFtdJi9UbmmuTuPWgwkKI+Ifx/khM0BDTb9akJJnAizp26zbYoCQTxxzwvrv0DXTaMUThTdw6RVEKYVm69QoAQXpj0O06BHgb7Vp0si240Ny9xFMDfm0LURcemw0/GkakYbEa3LCpC8qNA+hjFc7LP6F//MbgxLgJPMM9e63SlxvAYfkJMzX/nCVcT55a01ng3VXihtt4+ERHhtJfZaPnAoMqagvi1iBQLPreP8euXjtZyHLiUtdYOJV6tuUFNyTeB1I0H2ll3ikDHJjpYGsSv/ffZ me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+NC6tKzpT0GiYwscFoD8n/MdktvymPO8ncn2pAIAy34yiworwx9hLlOeMDsHaFb5LoT3qgqPoiaH1KWmFILKGtb/s9xqzpGZQFPu62nE4zd6Fa82c0rREtIfvst6EbclWSS4uLSn+Pmb6AQBZm3hubbslUMRZzj0vihyVi1y0rboL2U4X8ROZwQzZKG8iQf6k0A31Nb77DOqxQD4twPs2TCU5Hzc7mGWZGDbrUljWNyLJFBoTRDVa+Llc7aKP3MEzR20VcXB1SbB1BZr93MpQkQ+hpmoMAxikmhR6EpRfDs+pw2lHdBuOljhdJhOIZLudJAEfLwZw/4B9rZo9J6xn me@my-computer
        """)

    instance = self.messages.Instance(
        id=INSTANCE_WITH_EXTERNAL_ADDRESS.id,
        name=INSTANCE_WITH_EXTERNAL_ADDRESS.name,
        networkInterfaces=INSTANCE_WITH_EXTERNAL_ADDRESS.networkInterfaces,
        status=INSTANCE_WITH_EXTERNAL_ADDRESS.status,
        selfLink=INSTANCE_WITH_EXTERNAL_ADDRESS.selfLink,
        zone=INSTANCE_WITH_EXTERNAL_ADDRESS.zone,
        metadata=self.messages.Metadata(
            fingerprint=b'deadbeef',
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.messages.Metadata.ItemsValueListEntry(
                    key='sshKeys',
                    value=ssh_keys)
            ]
        )
    )
    self.make_requests.side_effect = iter([
        [instance],
        [self.project_resource],
        [],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        """)

    new_ssh_keys = ssh_keys + 'me:' + self.public_key_material

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
        [(self.compute_v1.instances,
          'SetMetadata',
          self.messages.ComputeInstancesSetMetadataRequest(
              instance=instance.name,
              metadata=self.messages.Metadata(
                  fingerprint=b'deadbeef',
                  items=[
                      self.messages.Metadata.ItemsValueListEntry(
                          key='a',
                          value='b'),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='sshKeys',
                          value=new_ssh_keys),
                  ]),
              zone='zone-1',
              project='my-project'))],
    )
    self.AssertErrContains('Updating instance ssh metadata')

  def testWithManySSHKeysBlockProjectSshKeysSet(self):

    instance_limited_ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+NC6tKzpT0GiYwscFoD8n/MdktvymPO8ncn2pAIAy34yiworwx9hLlOeMDsHaFb5LoT3qgqPoiaH1KWmFILKGtb/s9xqzpGZQFPu62nE4zd6Fa82c0rREtIfvst6EbclWSS4uLSn+Pmb6AQBZm3hubbslUMRZzj0vihyVi1y0rboL2U4X8ROZwQzZKG8iQf6k0A31Nb77DOqxQD4twPs2TCU5Hzc7mGWZGDbrUljWNyLJFBoTRDVa+Llc7aKP3MEzR20VcXB1SbB1BZr93MpQkQ+hpmoMAxikmhR6EpRfDs+pw2lHdBuOljhdJhOIZLudJAEfLwZw/4B9rZo9J6xn me@my-computer
        """)

    instance = self.messages.Instance(
        id=INSTANCE_WITH_EXTERNAL_ADDRESS.id,
        name=INSTANCE_WITH_EXTERNAL_ADDRESS.name,
        networkInterfaces=INSTANCE_WITH_EXTERNAL_ADDRESS.networkInterfaces,
        status=INSTANCE_WITH_EXTERNAL_ADDRESS.status,
        selfLink=INSTANCE_WITH_EXTERNAL_ADDRESS.selfLink,
        zone=INSTANCE_WITH_EXTERNAL_ADDRESS.zone,
        metadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='block-project-ssh-keys',
                    value='TruE'),
                self.messages.Metadata.ItemsValueListEntry(
                    key='ssh-keys',
                    value=instance_limited_ssh_keys),
            ]
        )
    )

    self.make_requests.side_effect = iter([
        [instance],
        [self.project_resource],
        []
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        """)

    new_instance_ssh_keys = (instance_limited_ssh_keys +
                             'me:' + self.public_key_material)

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
        [(self.compute_v1.instances,
          'SetMetadata',
          self.messages.ComputeInstancesSetMetadataRequest(
              instance='instance-1',
              metadata=self.messages.Metadata(
                  items=[
                      self.messages.Metadata.ItemsValueListEntry(
                          key='block-project-ssh-keys',
                          value='TruE'),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value=new_instance_ssh_keys),
                  ]),
              zone='zone-1',
              project='my-project'))],
    )
    self.AssertErrContains('Updating instance ssh metadata')

  def testWithManySSHKeysCannotWriteProjectMetadata(self):
    # Scenario:
    # * Project has sshKeys metadata
    # * Instance has ssh-keys metadata, but no sshKeys metadata
    # * `gcloud compute ssh` attempts to write project metadata (since instance
    #   has no sshKeys metadata), but fails because of permission reasons.
    # * Then, it writes ssh-keys of the relevant instance

    project_ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpBFilw+qXCrkbxzk3jQ+Bx/wLpPozc6Nz1A/LjHWlmXJ94js9PVHPwhg7JbiMlakn5rHEPRNEHF9S2m6lOIV1s0KCZR1FYpQArB312KCbH8TtovPwAOgcwcosEn54Ewko5EOCpQAMYdEs4qMAOR7tGA5Opi/rEx9S5n3DohZ5XIcbtRshgMDllYN6OAdck3WN2tj4JWjUrUXRI3BVxKTxlmH9zRqIta6Ph2M/+/DYnQa+jyAzYXiErqqmylT/OReYXxhSVbM+GLsuW82On+wa8DrL8YomHejwKAkZZgH9LGw6QIwI8GNWyF0SbMx1fYnEedp1DSi0Kt2gfIcah+0Z me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC5n+uTbZOqqMapxVy621kJbpEvPiiy40rkU7d43WUQC00HPvXeN68ZzXiXgpRFtdJi9UbmmuTuPWgwkKI+Ifx/khM0BDTb9akJJnAizp26zbYoCQTxxzwvrv0DXTaMUThTdw6RVEKYVm69QoAQXpj0O06BHgb7Vp0si240Ny9xFMDfm0LURcemw0/GkakYbEa3LCpC8qNA+hjFc7LP6F//MbgxLgJPMM9e63SlxvAYfkJMzX/nCVcT55a01ng3VXihtt4+ERHhtJfZaPnAoMqagvi1iBQLPreP8euXjtZyHLiUtdYOJV6tuUFNyTeB1I0H2ll3ikDHJjpYGsSv/ffZ me@my-computer
        """)

    instance_limited_ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+NC6tKzpT0GiYwscFoD8n/MdktvymPO8ncn2pAIAy34yiworwx9hLlOeMDsHaFb5LoT3qgqPoiaH1KWmFILKGtb/s9xqzpGZQFPu62nE4zd6Fa82c0rREtIfvst6EbclWSS4uLSn+Pmb6AQBZm3hubbslUMRZzj0vihyVi1y0rboL2U4X8ROZwQzZKG8iQf6k0A31Nb77DOqxQD4twPs2TCU5Hzc7mGWZGDbrUljWNyLJFBoTRDVa+Llc7aKP3MEzR20VcXB1SbB1BZr93MpQkQ+hpmoMAxikmhR6EpRfDs+pw2lHdBuOljhdJhOIZLudJAEfLwZw/4B9rZo9J6xn me@my-computer
        """)

    instance = self.messages.Instance(
        id=INSTANCE_WITH_EXTERNAL_ADDRESS.id,
        name=INSTANCE_WITH_EXTERNAL_ADDRESS.name,
        networkInterfaces=INSTANCE_WITH_EXTERNAL_ADDRESS.networkInterfaces,
        status=INSTANCE_WITH_EXTERNAL_ADDRESS.status,
        selfLink=INSTANCE_WITH_EXTERNAL_ADDRESS.selfLink,
        zone=INSTANCE_WITH_EXTERNAL_ADDRESS.zone,
        metadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='block-project-ssh-keys',
                    value='false'),
                self.messages.Metadata.ItemsValueListEntry(
                    key='ssh-keys',
                    value=instance_limited_ssh_keys),
            ]
        )
    )

    project_resource_with_many_ssh_keys = self.messages.Project(
        commonInstanceMetadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.messages.Metadata.ItemsValueListEntry(
                    key='ssh-keys',
                    value=project_ssh_keys),
            ]),
        name='my-project',
    )
    self.make_requests.side_effect = iter([
        [instance],
        [project_resource_with_many_ssh_keys],
        ssh_utils.SetProjectMetadataError('bad permissions'),
        []
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        """)

    new_project_ssh_keys = (project_ssh_keys +
                            'me:' + self.public_key_material)
    new_instance_ssh_keys = (instance_limited_ssh_keys +
                             'me:' + self.public_key_material)

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
                          key='a',
                          value='b'),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value=new_project_ssh_keys),
                  ]),

              project='my-project'))],
        [(self.compute_v1.instances,
          'SetMetadata',
          self.messages.ComputeInstancesSetMetadataRequest(
              instance='instance-1',
              metadata=self.messages.Metadata(
                  items=[
                      self.messages.Metadata.ItemsValueListEntry(
                          key='block-project-ssh-keys',
                          value='false'),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value=new_instance_ssh_keys),
                  ]),
              zone='zone-1',
              project='my-project'))],
    )

    self.AssertErrContains('Updating project ssh metadata')
    self.AssertErrContains('Updating instance ssh metadata')

  def testWithSSHKeyInProjectWithManyOtherSSHKeys(self):

    ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpBFilw+qXCrkbxzk3jQ+Bx/wLpPozc6Nz1A/LjHWlmXJ94js9PVHPwhg7JbiMlakn5rHEPRNEHF9S2m6lOIV1s0KCZR1FYpQArB312KCbH8TtovPwAOgcwcosEn54Ewko5EOCpQAMYdEs4qMAOR7tGA5Opi/rEx9S5n3DohZ5XIcbtRshgMDllYN6OAdck3WN2tj4JWjUrUXRI3BVxKTxlmH9zRqIta6Ph2M/+/DYnQa+jyAzYXiErqqmylT/OReYXxhSVbM+GLsuW82On+wa8DrL8YomHejwKAkZZgH9LGw6QIwI8GNWyF0SbMx1fYnEedp1DSi0Kt2gfIcah+0Z me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC5n+uTbZOqqMapxVy621kJbpEvPiiy40rkU7d43WUQC00HPvXeN68ZzXiXgpRFtdJi9UbmmuTuPWgwkKI+Ifx/khM0BDTb9akJJnAizp26zbYoCQTxxzwvrv0DXTaMUThTdw6RVEKYVm69QoAQXpj0O06BHgb7Vp0si240Ny9xFMDfm0LURcemw0/GkakYbEa3LCpC8qNA+hjFc7LP6F//MbgxLgJPMM9e63SlxvAYfkJMzX/nCVcT55a01ng3VXihtt4+ERHhtJfZaPnAoMqagvi1iBQLPreP8euXjtZyHLiUtdYOJV6tuUFNyTeB1I0H2ll3ikDHJjpYGsSv/ffZ me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+NC6tKzpT0GiYwscFoD8n/MdktvymPO8ncn2pAIAy34yiworwx9hLlOeMDsHaFb5LoT3qgqPoiaH1KWmFILKGtb/s9xqzpGZQFPu62nE4zd6Fa82c0rREtIfvst6EbclWSS4uLSn+Pmb6AQBZm3hubbslUMRZzj0vihyVi1y0rboL2U4X8ROZwQzZKG8iQf6k0A31Nb77DOqxQD4twPs2TCU5Hzc7mGWZGDbrUljWNyLJFBoTRDVa+Llc7aKP3MEzR20VcXB1SbB1BZr93MpQkQ+hpmoMAxikmhR6EpRfDs+pw2lHdBuOljhdJhOIZLudJAEfLwZw/4B9rZo9J6xn me@my-computer
        """) + 'me:' + self.public_key_material

    project_resource_with_many_ssh_keys = self.messages.Project(
        commonInstanceMetadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.messages.Metadata.ItemsValueListEntry(
                    key='ssh-keys',
                    value=ssh_keys),
            ]),
        name='my-project',
    )
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [project_resource_with_many_ssh_keys],
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

  def testWithManySSHKeysInProjectWithSpacesBetweenThem(self):

    ssh_keys = textwrap.dedent("""\



        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer



        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpBFilw+qXCrkbxzk3jQ+Bx/wLpPozc6Nz1A/LjHWlmXJ94js9PVHPwhg7JbiMlakn5rHEPRNEHF9S2m6lOIV1s0KCZR1FYpQArB312KCbH8TtovPwAOgcwcosEn54Ewko5EOCpQAMYdEs4qMAOR7tGA5Opi/rEx9S5n3DohZ5XIcbtRshgMDllYN6OAdck3WN2tj4JWjUrUXRI3BVxKTxlmH9zRqIta6Ph2M/+/DYnQa+jyAzYXiErqqmylT/OReYXxhSVbM+GLsuW82On+wa8DrL8YomHejwKAkZZgH9LGw6QIwI8GNWyF0SbMx1fYnEedp1DSi0Kt2gfIcah+0Z me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC5n+uTbZOqqMapxVy621kJbpEvPiiy40rkU7d43WUQC00HPvXeN68ZzXiXgpRFtdJi9UbmmuTuPWgwkKI+Ifx/khM0BDTb9akJJnAizp26zbYoCQTxxzwvrv0DXTaMUThTdw6RVEKYVm69QoAQXpj0O06BHgb7Vp0si240Ny9xFMDfm0LURcemw0/GkakYbEa3LCpC8qNA+hjFc7LP6F//MbgxLgJPMM9e63SlxvAYfkJMzX/nCVcT55a01ng3VXihtt4+ERHhtJfZaPnAoMqagvi1iBQLPreP8euXjtZyHLiUtdYOJV6tuUFNyTeB1I0H2ll3ikDHJjpYGsSv/ffZ me@my-computer





        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+NC6tKzpT0GiYwscFoD8n/MdktvymPO8ncn2pAIAy34yiworwx9hLlOeMDsHaFb5LoT3qgqPoiaH1KWmFILKGtb/s9xqzpGZQFPu62nE4zd6Fa82c0rREtIfvst6EbclWSS4uLSn+Pmb6AQBZm3hubbslUMRZzj0vihyVi1y0rboL2U4X8ROZwQzZKG8iQf6k0A31Nb77DOqxQD4twPs2TCU5Hzc7mGWZGDbrUljWNyLJFBoTRDVa+Llc7aKP3MEzR20VcXB1SbB1BZr93MpQkQ+hpmoMAxikmhR6EpRfDs+pw2lHdBuOljhdJhOIZLudJAEfLwZw/4B9rZo9J6xn me@my-computer

        """)

    project_resource_with_extra_metadata = self.messages.Project(
        commonInstanceMetadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.messages.Metadata.ItemsValueListEntry(
                    key='ssh-keys',
                    value=ssh_keys),
            ]),
        name='my-project',
    )

    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [project_resource_with_extra_metadata],
        [],
    ])

    self.Run("""
        compute ssh instance-1 --zone zone-1
        """)

    ssh_keys = textwrap.dedent("""\
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpBFilw+qXCrkbxzk3jQ+Bx/wLpPozc6Nz1A/LjHWlmXJ94js9PVHPwhg7JbiMlakn5rHEPRNEHF9S2m6lOIV1s0KCZR1FYpQArB312KCbH8TtovPwAOgcwcosEn54Ewko5EOCpQAMYdEs4qMAOR7tGA5Opi/rEx9S5n3DohZ5XIcbtRshgMDllYN6OAdck3WN2tj4JWjUrUXRI3BVxKTxlmH9zRqIta6Ph2M/+/DYnQa+jyAzYXiErqqmylT/OReYXxhSVbM+GLsuW82On+wa8DrL8YomHejwKAkZZgH9LGw6QIwI8GNWyF0SbMx1fYnEedp1DSi0Kt2gfIcah+0Z me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC5n+uTbZOqqMapxVy621kJbpEvPiiy40rkU7d43WUQC00HPvXeN68ZzXiXgpRFtdJi9UbmmuTuPWgwkKI+Ifx/khM0BDTb9akJJnAizp26zbYoCQTxxzwvrv0DXTaMUThTdw6RVEKYVm69QoAQXpj0O06BHgb7Vp0si240Ny9xFMDfm0LURcemw0/GkakYbEa3LCpC8qNA+hjFc7LP6F//MbgxLgJPMM9e63SlxvAYfkJMzX/nCVcT55a01ng3VXihtt4+ERHhtJfZaPnAoMqagvi1iBQLPreP8euXjtZyHLiUtdYOJV6tuUFNyTeB1I0H2ll3ikDHJjpYGsSv/ffZ me@my-computer
        me:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+NC6tKzpT0GiYwscFoD8n/MdktvymPO8ncn2pAIAy34yiworwx9hLlOeMDsHaFb5LoT3qgqPoiaH1KWmFILKGtb/s9xqzpGZQFPu62nE4zd6Fa82c0rREtIfvst6EbclWSS4uLSn+Pmb6AQBZm3hubbslUMRZzj0vihyVi1y0rboL2U4X8ROZwQzZKG8iQf6k0A31Nb77DOqxQD4twPs2TCU5Hzc7mGWZGDbrUljWNyLJFBoTRDVa+Llc7aKP3MEzR20VcXB1SbB1BZr93MpQkQ+hpmoMAxikmhR6EpRfDs+pw2lHdBuOljhdJhOIZLudJAEfLwZw/4B9rZo9J6xn me@my-computer
        """)
    new_ssh_keys = ssh_keys + 'me:' + self.public_key_material

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
                          key='a',
                          value='b'),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value=new_ssh_keys),
                  ]),
              project='my-project'))],
    )
    self.AssertErrContains('Updating project ssh metadata')

  def testKeyRemoval(self):

    ssh_key = textwrap.dedent("""\
        ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwqx8+h4c6K0ipqLqXt1y4ohpbk6PxDdWzprGxNFrsir/QrOy6iQBAyvlbAb/kM5RaNkjliakfmNEMBH3/tmhBIEmSAsZ0dfhwBof0Hm+bRFI475ik/p7QKSpPXf2nCgG3QF75jfLrk+4R6P+0w3zxbq63LxrB7umUxTA2tGMqgNIW0OQ/w2mfl4DfFTTXQeJ4/Gu6grpl1+Mi7RwtV9RPE5UuveXpcj7htiqj8sv8Zip9kVE7lNQFB0xdy1pcUw93ddo4lbGIJX7PTS0fvXfFdnAZ4huVrdqCOBBMApSx3QdRYUnyz+PrxasQIu7pK8Cl0yACBFUbMhMazqzo2485 me@my-computer
        """)

    # Fills up a buffer with enough ssh_keys until we go just over
    # the max size allowed.
    buf = io.StringIO()
    i = 0
    while len(buf.getvalue()) < self.max_metadata_value_size_in_bytes:
      buf.write('user-')
      buf.write(six.text_type(i))
      buf.write(':')
      buf.write(ssh_key)
      i += 1
    ssh_keys = buf.getvalue()

    project_resource_with_extra_metadata = self.messages.Project(
        commonInstanceMetadata=self.messages.Metadata(
            items=[
                self.messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.messages.Metadata.ItemsValueListEntry(
                    key='ssh-keys',
                    value=ssh_keys),
            ]),
        name='my-project',
    )

    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [project_resource_with_extra_metadata],
        [],
    ])

    # If all went well, the first two keys should have been evicted.
    ssh_keys = '\n'.join(ssh_keys.split('\n')[2:])

    new_ssh_keys = ssh_keys + 'me:' + self.public_key_material

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

        [(self.compute_v1.projects,
          'SetCommonInstanceMetadata',
          self.messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=self.messages.Metadata(
                  items=[
                      self.messages.Metadata.ItemsValueListEntry(
                          key='a',
                          value='b'),
                      self.messages.Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value=new_ssh_keys),
                  ]),

              project='my-project'))],
    )

    # Ensures that log messages were written for the two keys removed.
    self.AssertErrContains(
        'The following SSH key will be removed from your project '
        'because your SSH keys metadata value has reached its '
        'maximum allowed size of 262144 bytes: user-0')
    self.AssertErrContains(
        'The following SSH key will be removed from your project '
        'because your SSH keys metadata value has reached its '
        'maximum allowed size of 262144 bytes: user-1')
    self.AssertErrContains('Updating project ssh metadata')

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
        compute ssh https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
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
        remainder=['-v', '1 2 3', 'a | b', 'b\'y'])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)


class SshCompletionTests(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    self.make_requests.side_effect = iter([
        [test_resources.INSTANCES_V1[0]],
    ])

  def testSshCompletionWithoutZone(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))
    self.RunCompletion('compute ssh in',
                       ['instance-1\\ --zone=zone-1',
                        'instance-2\\ --zone=zone-1',
                        'instance-3\\ --zone=zone-1'])

  def testSshCompletionWithZone(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))
    self.RunCompletion('compute ssh --zone=zone-1 in',
                       ['instance-1',
                        'instance-2',
                        'instance-3'])


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
        selfLink=('https://www.googleapis.com/compute/v1/projects/asdf-project/'
                  'zones/zone-1/instances/instance-1'),
        zone=('https://www.googleapis.com/compute/v1/projects/asdf-project/'
              'zones/zone-1'))
    self.project = self.v1_messages.Project(
        commonInstanceMetadata=self.v1_messages.Metadata(items=[
            self.v1_messages.Metadata.ItemsValueListEntry(
                key='a', value='b'),
            self.v1_messages.Metadata.ItemsValueListEntry(
                key='ssh-keys',
                value='me:{0}\n'.format(self.public_key_material)),
        ]),
        name='asdf-project',)

  def testOverrideImplicit(self):
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project],
    ])

    self.Run("""\
        compute ssh https://www.googleapis.com/compute/v1/projects/asdf-project/zones/zone-1/instances/instance-1 -- -vvv
        """)

    self.CheckRequests(
        [(self.compute_v1.instances, 'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='asdf-project', zone='zone-1'))],
        [(self.compute_v1.projects, 'Get',
          self.messages.ComputeProjectsGetRequest(project='asdf-project'))],)
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
        remainder=['-vvv'])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testOverrideExplicit(self):
    self.make_requests.side_effect = iter([
        [self.instance],
        [self.project],
    ])

    self.Run("""\
        compute ssh https://www.googleapis.com/compute/v1/projects/asdf-project/zones/zone-1/instances/instance-1 --project my-project -- -vvv
        """)

    self.CheckRequests(
        [(self.compute_v1.instances, 'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='asdf-project', zone='zone-1'))],
        [(self.compute_v1.projects, 'Get',
          self.messages.ComputeProjectsGetRequest(project='asdf-project'))],)
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
        remainder=['-vvv'])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)


class SSHPrivateIpTest(test_base.BaseSSHTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')

    # Common test vars
    self.remote = ssh.Remote('10.240.0.52', user='john')

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
                    'Google" -q` = 22222 ] || exit 23']),
            mock.call(
                mock_matchers.TypeMatcher(ssh.SSHCommand),
                remote=self.remote,
                identity_file=self.private_key_file,
                extra_flags=[],
                tty=None,
                options=dict(self.options, HostKeyAlias='compute.22222'),
                remote_command=None,
                remainder=[])],
        any_order=True
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
        r'Established connection with host 10.240.0.52 but was unable to '
        r'confirm ID of the instance.'):
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
                    'Google" -q` = 22222 ] || exit 23']),
            mock.call(
                mock_matchers.TypeMatcher(ssh.SSHCommand),
                remote=self.remote,
                identity_file=self.private_key_file,
                options=dict(self.options, HostKeyAlias='compute.22222'),
                remote_command=None,
                extra_flags=[],
                tty=None,
                remainder=[],
            )],
        any_order=True
    )

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)


class SSHOsloginTest(test_base.BaseSSHTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  @mock.patch(
      'googlecloudsdk.api_lib.oslogin.client._GetClient')
  def testSimpleCase(self, oslogin_mock):
    properties.VALUES.core.account.Set('user@google.com')
    self.remote = ssh.Remote('23.251.133.75', user='user_google_com')
    oslogin_mock.return_value = test_resources.MakeOsloginClient('v1alpha')

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
        'v1alpha', use_extended_profile=True)

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
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  @mock.patch(
      'googlecloudsdk.api_lib.oslogin.client._GetClient')
  def testGetPrimaryUser(self, oslogin_mock):
    properties.VALUES.core.account.Set('user@google.com')
    self.remote = ssh.Remote('23.251.133.75', user='myaccount')
    oslogin_mock.return_value = test_resources.MakeOsloginClient(
        'v1alpha', use_extended_profile=True)

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
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  @mock.patch(
      'googlecloudsdk.api_lib.oslogin.client._GetClient')
  def testOsloginEnabledOnProject(self, oslogin_mock):
    properties.VALUES.core.account.Set('user@google.com')
    self.remote = ssh.Remote('23.251.133.75', user='user_google_com')
    oslogin_mock.return_value = test_resources.MakeOsloginClient('v1alpha')

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
    oslogin_mock.return_value = test_resources.MakeOsloginClient('v1alpha')

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
                                                             'v1alpha')

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
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)


class SSHTunnelThroughIapTestBeta(test_base.BaseSSHTest,
                                  parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.SelectApi(self.track.prefix)
    self.instances = {
        _INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY: self.messages.Instance(
            id=11111,
            name='instance-1',
            networkInterfaces=[
                self.messages.NetworkInterface(
                    name='nic0',
                    networkIP='10.240.0.52',
                    accessConfigs=[
                        self.messages.AccessConfig(natIP='23.251.133.1'),
                    ],
                ),
            ],
            status=self.messages.Instance.StatusValueValuesEnum.RUNNING,
            selfLink=(
                'https://www.googleapis.com/compute/{}/projects/my-project/'
                'zones/zone-1/instances/instance-1').format(self.track.prefix),
            zone=('https://www.googleapis.com/compute/{}/projects/my-project/'
                  'zones/zone-1').format(self.track.prefix)),
        _INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY: self.messages.Instance(
            id=22222,
            name='instance-2',
            networkInterfaces=[
                self.messages.NetworkInterface(
                    name='nic0',
                    networkIP='10.240.0.53',
                ),
            ],
            status=self.messages.Instance.StatusValueValuesEnum.RUNNING,
            selfLink=(
                'https://www.googleapis.com/compute/{}/projects/my-project/'
                'zones/zone-1/instances/instance-2').format(self.track.prefix),
            zone=('https://www.googleapis.com/compute/{}/projects/my-project/'
                  'zones/zone-1').format(self.track.prefix)),
    }

  @parameterized.parameters((_INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY,),
                            (_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY,))
  @mock.patch.object(iap_tunnel, 'IapTunnelConnectionHelper', autospec=True)
  def testSimpleCase(self, test_instance_key, helper_cls_mock):
    helper_mock = mock.MagicMock()
    helper_mock.GetLocalPort.return_value = 8822
    helper_cls_mock.return_value = helper_mock

    test_instance = self.instances[test_instance_key]
    self.make_requests.side_effect = iter([
        [test_instance],
        [self.project_resource],
    ])

    self.Run('compute ssh {} --zone zone-1 --tunnel-through-iap'.format(
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
    )

    # IAP Tunnel Connection Helpers
    helper_cls_mock.assert_called_once_with(
        mock.ANY, 'my-project', 'zone-1', test_instance.name, 'nic0', 22)
    helper_mock.StartListener.assert_called_once_with()
    helper_mock.StopListener.assert_called_once_with()

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=ssh.Remote.FromArg('me@localhost'),
        port='8822',
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options,
                     HostKeyAlias='compute.%s' % test_instance.id),
        remote_command=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  @parameterized.parameters((_INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY,),
                            (_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY,))
  @mock.patch.object(iap_tunnel, 'IapTunnelConnectionHelper', autospec=True)
  def testWithAlternateUser(self, test_instance_key, helper_cls_mock):
    helper_mock = mock.MagicMock()
    helper_mock.GetLocalPort.return_value = 8822
    helper_poller_mock = mock.MagicMock()
    helper_poller_mock.GetLocalPort.return_value = 9922
    helper_cls_mock.side_effect = [helper_mock, helper_poller_mock]

    test_instance = self.instances[test_instance_key]
    self.make_requests.side_effect = iter([
        [test_instance],
        [self.project_resource_without_metadata],
        [],
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

    # IAP Tunnel Connection Helpers
    self.assertEqual(helper_cls_mock.call_count, 2)
    helper_mock.StartListener.assert_called_once_with()
    helper_mock.StopListener.assert_called_once_with()
    helper_poller_mock.StartListener.assert_called_once_with(
        accept_multiple_connections=True)
    helper_poller_mock.StopListener.assert_called_once_with()

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # Polling
    remote = ssh.Remote.FromArg('hapoo@localhost')
    self.poller_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        remote=remote,
        port='9922',
        identity_file=self.private_key_file,
        extra_flags=[],
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_SEC,
        options=dict(self.options,
                     HostKeyAlias='compute.%s' % test_instance.id))

    self.poller_poll.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        self.env, force_connect=True)

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        remote=remote,
        port='8822',
        identity_file=self.private_key_file,
        extra_flags=[],
        tty=None,
        options=dict(self.options,
                     HostKeyAlias='compute.%s' % test_instance.id),
        remote_command=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    self.AssertErrContains('Updating project ssh metadata')

  @parameterized.parameters((_INSTANCE_WITH_EXTERNAL_IP_ADDRESS_KEY,),
                            (_INSTANCE_WITHOUT_EXTERNAL_IP_ADDRESS_KEY,))
  @mock.patch.object(iap_tunnel, 'IapTunnelConnectionHelper', autospec=True)
  def testWithPollingTimeout(self, test_instance_key, helper_cls_mock):
    helper_mock = mock.MagicMock()
    helper_mock.GetLocalPort.return_value = 8822
    helper_poller_mock = mock.MagicMock()
    helper_poller_mock.GetLocalPort.return_value = 9922
    helper_cls_mock.side_effect = [helper_mock, helper_poller_mock]

    # Polling the instance leads to an unreachable instance.
    self.poller_poll.side_effect = retry.WaitException('msg', 'last', 'state')

    test_instance = self.instances[test_instance_key]
    self.make_requests.side_effect = iter([
        [test_instance],
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

    # IAP Tunnel Connection Helpers
    self.assertEqual(helper_cls_mock.call_count, 2)
    helper_mock.StartListener.assert_called_once_with()
    helper_mock.StopListener.assert_called_once_with()
    helper_poller_mock.StartListener.assert_called_once_with(
        accept_multiple_connections=True)
    helper_poller_mock.StopListener.assert_called_once_with()

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # Polling
    remote = ssh.Remote.FromArg('hapoo@localhost')
    self.poller_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        remote=remote,
        port='9922',
        identity_file=self.private_key_file,
        extra_flags=[],
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_SEC,
        options=dict(self.options,
                     HostKeyAlias='compute.%s' % test_instance.id))
    self.poller_poll.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHPoller),
        self.env, force_connect=True)

    self.ssh_run.assert_not_called()

    self.AssertErrContains('Updating project ssh metadata')


class SSHTunnelThroughIapTestAlpha(SSHTunnelThroughIapTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
