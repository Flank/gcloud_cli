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
"""Tests for the connect-to-serial-port subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import properties
from tests.lib import mock_matchers
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock

messages = apis.GetMessagesModule('compute', 'v1')

INSTANCE_WITH_EXTERNAL_ADDRESS = messages.Instance(
    name='instance-1',
    networkInterfaces=[
        messages.NetworkInterface(
            accessConfigs=[
                messages.AccessConfig(
                    name='external-nat',
                    natIP='23.251.133.75'),
            ],
        ),
    ],
    status=messages.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-1'),
    zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-1'))

INSTANCE_WITH_NO_EXTERNAL_ADDRESS = messages.Instance(
    name='instance-2',
    status=messages.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-1'),
    zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-1'))

INSTANCE_WITH_OSLOGIN_ENABLED = messages.Instance(
    id=44444,
    name='instance-4',
    metadata=messages.Metadata(
        items=[
            messages.Metadata.ItemsValueListEntry(
                key='enable-oslogin',
                value='TruE'),
        ]
    ),
    networkInterfaces=[
        messages.NetworkInterface(
            accessConfigs=[
                messages.AccessConfig(
                    name='external-nat',
                    natIP='23.251.133.75'),
            ],
        ),
    ],
    status=messages.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-1'),
    zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-1'))


PUBLIC_KEY = ('ssh-rsa '
              'AAAAB3NzaC1yc2EAAAADAQABAAABAQDkOOCaBZVTxzvjJ7+7YonnZOwIZ2Z7azwP'
              'C+oHbBCbWNBZAwzs63JQlHLibHG6NiNunFwP/lWs5SpLx5eEdxGL+WQmvtldnBdq'
              'JzNE1UHrxPDegysCXxn1fT7KELpLozLhvlfSnWJXbFbDrGB0bTv2U373Zo3BL9XT'
              'Rf3qthdDEMF3GouUH8pGvitHlwcwO1ulpVB0sTIdB7Bu+YPuo1XSuL2n3tXA9n9S'
              '+7kQCoyuXodeBpJoJxzdJeoQXAepLrLA7nl6jRiYZyic0WJeSJm7vmvl1VDAGkyX'
              'loNEhBnvoQFQl5aCwcS8UQnzzwMDflQ+JgsynYN08dLIRGcwkJe9')

PUBLIC_KEY_RESPONSE = ({'status': '200'}, '{0} \n'.format(PUBLIC_KEY))
ENCODED_KEY_RESPONSE = ({'status': '200'},
                        '{0} \n'.format(PUBLIC_KEY).encode('utf-8'))
BAD_KEY_RESPONSE = ({'status': '404'}, '')


class SerialPortTest(test_base.BaseSSHTest):

  def SetUp(self):
    properties.VALUES.core.check_gce_metadata.Set(False)

    self.project_resource = self.GetMessages().Project(
        commonInstanceMetadata=self.GetMessages().Metadata(
            items=[
                self.GetMessages().Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.GetMessages().Metadata.ItemsValueListEntry(
                    key='ssh-keys',
                    value='me:{0}\n'.format(self.public_key_material)),
            ]),
        name='my-project',
    )
    self.mock_http_nocred = self.StartPatch('googlecloudsdk.core.http.Http',
                                            autospec=True)
    self.mock_http_request = mock.Mock()
    self.mock_http_nocred.return_value = self.mock_http_request

    self.gateway = 'ssh-serialport.googleapis.com'
    self.options = {
        'UserKnownHostsFile': self.known_hosts_file,
        'IdentitiesOnly': 'yes',
        'CheckHostIP': 'no',
        'StrictHostKeyChecking': 'yes',
        'ControlPath': 'none',
    }

    datetime_patcher = mock.patch('datetime.datetime',
                                  test_base.FakeDateTimeWithTimeZone)
    self.addCleanup(datetime_patcher.stop)
    datetime_patcher.start()

  def GetMessages(self):
    return messages

  def GetCompute(self):
    return self.compute

  def testSimpleCase(self):
    self.mock_http_request.request.return_value = PUBLIC_KEY_RESPONSE
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""
        compute connect-to-serial-port instance-1 --zone zone-1
        """)
    self.CheckRequests(
        [(self.GetCompute().instances,
          'Get',
          self.GetMessages().ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.GetCompute().projects,
          'Get',
          self.GetMessages().ComputeProjectsGetRequest(
              project='my-project'))])

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        ssh.Remote(self.gateway, user='my-project.zone-1.instance-1.me.port=1'),
        identity_file=self.private_key_file,
        options=self.options,
        port='9600')

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    # Known Hosts
    self.known_hosts_add.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.KnownHosts),
        '[ssh-serialport.googleapis.com]:9600', PUBLIC_KEY, overwrite=True)
    self.known_hosts_write.assert_called_once()
    self.make_requests.assert_not_called()

  def testWithIllFormattedPositionalArg(self):
    self.mock_http_request.request.return_value = PUBLIC_KEY_RESPONSE

    with self.assertRaisesRegex(
        ssh_utils.ArgumentError,
        r'Expected argument of the form \[USER@\]INSTANCE. Received '
        r'\[hapoo@instance-1@instance-2\].'):
      self.Run("""
          compute connect-to-serial-port hapoo@instance-1@instance-2 --zone us-central1-a
          """)

  def testWithAlternateUser(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource_without_metadata],
        [],
    ])
    self.mock_http_request.request.return_value = PUBLIC_KEY_RESPONSE

    self.Run("""
        compute connect-to-serial-port hapoo@instance-1 --zone zone-1
        """)

    self.CheckRequests(
        [(self.GetCompute().instances,
          'Get',
          self.GetMessages().ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.GetCompute().projects,
          'Get',
          self.GetMessages().ComputeProjectsGetRequest(
              project='my-project'))],
        [(self.GetCompute().projects,
          'SetCommonInstanceMetadata',
          self.GetMessages().ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=self.GetMessages().Metadata(
                  items=[
                      self.GetMessages().Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value='hapoo:' + self.public_key_material),
                  ]),

              project='my-project'))],
    )
    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        ssh.Remote(self.gateway,
                   user='my-project.zone-1.instance-1.hapoo.port=1'),
        identity_file=self.private_key_file,
        options=self.options,
        port='9600')

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    # Known Hosts
    self.known_hosts_add.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.KnownHosts),
        '[ssh-serialport.googleapis.com]:9600', PUBLIC_KEY, overwrite=True)
    self.known_hosts_write.assert_called_once()
    self.AssertErrContains('Updating project ssh metadata')

  def testWithRelativeExpiration(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource_without_metadata],
        [],
    ])
    self.mock_http_request.request.return_value = PUBLIC_KEY_RESPONSE

    self.Run("""
        compute connect-to-serial-port instance-1 --zone zone-1
        --ssh-key-expire-after 1d
        """)

    self.CheckRequests(
        [(self.GetCompute().instances,
          'Get',
          self.GetMessages().ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.GetCompute().projects,
          'Get',
          self.GetMessages().ComputeProjectsGetRequest(
              project='my-project'))],
        [(self.GetCompute().projects,
          'SetCommonInstanceMetadata',
          self.GetMessages().ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=self.GetMessages().Metadata(
                  items=[
                      self.GetMessages().Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value=('me:{0} google-ssh {{"userName":"me",'
                                 '"expireOn":'
                                 '"2014-01-03T03:04:05+0000"}}').format(
                                     self.pubkey.ToEntry())),
                  ]),

              project='my-project'))],
    )
    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        ssh.Remote(self.gateway,
                   user='my-project.zone-1.instance-1.me.port=1'),
        identity_file=self.private_key_file,
        options=self.options,
        port='9600')

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    # Known Hosts
    self.known_hosts_add.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.KnownHosts),
        '[ssh-serialport.googleapis.com]:9600', PUBLIC_KEY, overwrite=True)
    self.known_hosts_write.assert_called_once()
    self.AssertErrContains('Updating project ssh metadata')

  def testWithAbsoluteExpiration(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource_without_metadata],
        [],
    ])
    self.mock_http_request.request.return_value = PUBLIC_KEY_RESPONSE

    self.Run("""
        compute connect-to-serial-port instance-1 --zone zone-1
        --ssh-key-expiration 2015-01-23T12:34:56+0000
        """)

    self.CheckRequests(
        [(self.GetCompute().instances,
          'Get',
          self.GetMessages().ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.GetCompute().projects,
          'Get',
          self.GetMessages().ComputeProjectsGetRequest(
              project='my-project'))],
        [(self.GetCompute().projects,
          'SetCommonInstanceMetadata',
          self.GetMessages().ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=self.GetMessages().Metadata(
                  items=[
                      self.GetMessages().Metadata.ItemsValueListEntry(
                          key='ssh-keys',
                          value=('me:{0} google-ssh {{"userName":"me",'
                                 '"expireOn":'
                                 '"2015-01-23T12:34:56+0000"}}').format(
                                     self.pubkey.ToEntry())),
                  ]),

              project='my-project'))],
    )
    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        ssh.Remote(self.gateway,
                   user='my-project.zone-1.instance-1.me.port=1'),
        identity_file=self.private_key_file,
        options=self.options,
        port='9600')

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    # Known Hosts
    self.known_hosts_add.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.KnownHosts),
        '[ssh-serialport.googleapis.com]:9600', PUBLIC_KEY, overwrite=True)
    self.known_hosts_write.assert_called_once()
    self.AssertErrContains('Updating project ssh metadata')

  def testWithAlternatePort(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])
    self.mock_http_request.request.return_value = PUBLIC_KEY_RESPONSE

    self.Run("""
        compute connect-to-serial-port instance-1 --zone zone-1 --port 3
        """)

    self.CheckRequests(
        [(self.GetCompute().instances,
          'Get',
          self.GetMessages().ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.GetCompute().projects,
          'Get',
          self.GetMessages().ComputeProjectsGetRequest(
              project='my-project'))],
    )
    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        ssh.Remote(self.gateway, user='my-project.zone-1.instance-1.me.port=3'),
        identity_file=self.private_key_file,
        options=self.options,
        port='9600')

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testWithAlternateGateway(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])
    self.mock_http_request.request.return_value = PUBLIC_KEY_RESPONSE

    self.Run("""
        compute connect-to-serial-port instance-1 --zone zone-1
        --serial-port-gateway staging-serialport.googleapis.com
        """)

    self.CheckRequests(
        [(self.GetCompute().instances,
          'Get',
          self.GetMessages().ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.GetCompute().projects,
          'Get',
          self.GetMessages().ComputeProjectsGetRequest(
              project='my-project'))],
    )
    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        ssh.Remote('staging-serialport.googleapis.com',
                   user='my-project.zone-1.instance-1.me.port=1'),
        identity_file=self.private_key_file,
        options=self.options,
        port='9600')

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

  def testWithExtraArgs(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])
    self.mock_http_request.request.return_value = PUBLIC_KEY_RESPONSE

    self.Run("""
        compute connect-to-serial-port instance-1 --zone zone-1 --extra-args foo=bar
        """)

    self.CheckRequests(
        [(self.GetCompute().instances,
          'Get',
          self.GetMessages().ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.GetCompute().projects,
          'Get',
          self.GetMessages().ComputeProjectsGetRequest(
              project='my-project'))],
    )
    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        ssh.Remote(self.gateway,
                   user='my-project.zone-1.instance-1.me.port=1.foo=bar'),
        identity_file=self.private_key_file,
        options=self.options,
        port='9600')

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)

    self.WriteInput('1\n')
    self.make_requests.side_effect = iter([
        [
            messages.Instance(name='instance-1', zone='zone-1'),
            messages.Instance(name='instance-1', zone='zone-2'),
        ],

        [INSTANCE_WITH_EXTERNAL_ADDRESS],

        [self.project_resource],
    ])
    self.mock_http_request.request.return_value = PUBLIC_KEY_RESPONSE

    self.Run("""
        compute connect-to-serial-port instance-1
        """)

    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance-1'),

        [(self.GetCompute().instances,
          'Get',
          self.GetMessages().ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],

        [(self.GetCompute().projects,
          'Get',
          self.GetMessages().ComputeProjectsGetRequest(
              project='my-project'))],
    )
    self.AssertErrContains('instance-1')
    self.AssertErrContains('zone-1')
    self.AssertErrContains('zone-2')

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        ssh.Remote(self.gateway,
                   user='my-project.zone-1.instance-1.me.port=1'),
        identity_file=self.private_key_file,
        options=self.options,
        port='9600')

  def testInstanceWithNoExternalIp(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_NO_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])
    self.mock_http_request.request.return_value = PUBLIC_KEY_RESPONSE

    self.Run("""
        compute connect-to-serial-port instance-2 --zone zone-1
        """)

    self.CheckRequests(
        [(self.GetCompute().instances,
          'Get',
          self.GetMessages().ComputeInstancesGetRequest(
              instance='instance-2',
              project='my-project',
              zone='zone-1'))],
        [(self.GetCompute().projects,
          'Get',
          self.GetMessages().ComputeProjectsGetRequest(
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
        ssh.Remote(self.gateway, user='my-project.zone-1.instance-2.me.port=1'),
        identity_file=self.private_key_file,
        options=self.options,
        port='9600')

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    # Known Hosts
    self.known_hosts_add.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.KnownHosts),
        '[ssh-serialport.googleapis.com]:9600', PUBLIC_KEY, overwrite=True)
    self.known_hosts_write.assert_called_once()
    self.make_requests.assert_not_called()

  @mock.patch(
      'googlecloudsdk.api_lib.oslogin.client._GetClient')
  def testInstanceWithOsloginEnabled(self, oslogin_mock):
    properties.VALUES.core.account.Set('user@google.com')
    oslogin_mock.return_value = test_resources.MakeOsloginClient('v1')
    self.mock_http_request.request.return_value = PUBLIC_KEY_RESPONSE
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_OSLOGIN_ENABLED],
        [self.project_resource],
    ])

    self.Run("""
        compute connect-to-serial-port instance-4 --zone zone-1
        """)
    self.CheckRequests(
        [(self.GetCompute().instances,
          'Get',
          self.GetMessages().ComputeInstancesGetRequest(
              instance='instance-4',
              project='my-project',
              zone='zone-1'))],
        [(self.GetCompute().projects,
          'Get',
          self.GetMessages().ComputeProjectsGetRequest(
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
        ssh.Remote(self.gateway,
                   user='my-project.zone-1.instance-4.user_google_com.port=1'),
        identity_file=self.private_key_file,
        options=self.options,
        port='9600')

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    # Known Hosts
    self.known_hosts_add.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.KnownHosts),
        '[ssh-serialport.googleapis.com]:9600', PUBLIC_KEY, overwrite=True)
    self.known_hosts_write.assert_called_once()
    self.make_requests.assert_not_called()

  def testWithEncodedHttpResponse(self):
    self.mock_http_request.request.return_value = ENCODED_KEY_RESPONSE
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.project_resource],
    ])

    self.Run("""
        compute connect-to-serial-port instance-1 --zone zone-1
        """)
    self.CheckRequests(
        [(self.GetCompute().instances,
          'Get',
          self.GetMessages().ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.GetCompute().projects,
          'Get',
          self.GetMessages().ComputeProjectsGetRequest(
              project='my-project'))])

    # Require SSH keys
    self.ensure_keys.assert_called_once_with(
        self.keys, None, allow_passphrase=True)

    # No polling
    self.poller_poll.assert_not_called()

    # SSH Command
    self.ssh_init.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        ssh.Remote(self.gateway, user='my-project.zone-1.instance-1.me.port=1'),
        identity_file=self.private_key_file,
        options=self.options,
        port='9600')

    self.ssh_run.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.SSHCommand),
        self.env, force_connect=True)

    # Known Hosts
    self.known_hosts_add.assert_called_once_with(
        mock_matchers.TypeMatcher(ssh.KnownHosts),
        '[ssh-serialport.googleapis.com]:9600', PUBLIC_KEY, overwrite=True)
    self.known_hosts_write.assert_called_once()
    self.make_requests.assert_not_called()


if __name__ == '__main__':
  test_case.main()
