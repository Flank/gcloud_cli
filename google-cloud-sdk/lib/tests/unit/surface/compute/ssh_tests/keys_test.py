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

import io
import textwrap

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.util.ssh import ssh
from tests.lib import mock_matchers
from tests.lib import test_case
from tests.lib.surface.compute import test_base

import mock
import six

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


class SSHTest(test_base.BaseSSHTest, test_case.WithInput):

  def SetUp(self):
    datetime_patcher = mock.patch('datetime.datetime',
                                  test_base.FakeDateTimeWithTimeZone)
    self.addCleanup(datetime_patcher.stop)
    datetime_patcher.start()

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
        iap_tunnel_args=None,
        remainder=[])

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

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
        max_wait_ms=ssh_utils.SSH_KEY_PROPAGATION_TIMEOUT_MS,
        options=dict(self.options, HostKeyAlias='compute.11111'),
        iap_tunnel_args=None)

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
        iap_tunnel_args=None,
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


if __name__ == '__main__':
  test_case.main()
