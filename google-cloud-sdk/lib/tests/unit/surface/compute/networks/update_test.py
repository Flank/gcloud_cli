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
"""Tests for the update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base


class UpdateTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase,
                 waiter_test_base.Base):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.mock_client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version),
        real_client=core_apis.GetClientInstance(
            'compute', self.api_version, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def _GetOperationMessage(self, operation_name, status, resource_uri=None):
    return self.messages.Operation(
        name='https://compute.googleapis.com/compute/{0}/projects/{1}/global/'
        'operations/{2}'.format(self.api_version, 'fake-project',
                                operation_name),
        status=status,
        selfLink='https://compute.googleapis.com/compute/{0}/projects/{1}/'
        'global/operations/{2}'.format(self.api_version, 'fake-project',
                                       operation_name),
        targetLink=resource_uri)

  def testUpdate_bgpRoutingMode(self):
    expected = self.messages.Network()
    expected.routingConfig = self.messages.NetworkRoutingConfig()
    expected.routingConfig.routingMode = (
        self.messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.GLOBAL)

    self.mock_client.networks.Patch.Expect(
        self.messages.ComputeNetworksPatchRequest(
            project='fake-project',
            network='my-network',
            networkResource=expected),
        self.messages.Operation(name='myop'))

    self.Run("""
        compute networks update my-network --bgp-routing-mode=global
        """)

  def testUpdate_switchToCustomSubnetMode_yes(self):
    self.mock_client.networks.SwitchToCustomMode.Expect(
        self.messages.ComputeNetworksSwitchToCustomModeRequest(
            project='fake-project', network='my-network'),
        self._GetOperationMessage(
            operation_name='myop',
            status=self.messages.Operation.StatusValueValuesEnum.PENDING))
    self.mock_client.globalOperations.Wait.Expect(
        self.messages.ComputeGlobalOperationsWaitRequest(
            project='fake-project', operation='myop'),
        self.messages.Operation(
            name='myop',
            status=self.messages.Operation.StatusValueValuesEnum.DONE))

    self.mock_client.networks.Get.Expect(
        self.messages.ComputeNetworksGetRequest(
            project='fake-project', network='my-network'),
        response=self.messages.Network(
            name='my-network', IPv4Range='10.240.0.0/16'))

    self.WriteInput('y\n')
    self.Run("""
        compute networks update my-network --switch-to-custom-subnet-mode
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Switching network to custom-mode')

  def testUpdate_switchToCustomSubnetMode_async(self):
    self.mock_client.networks.SwitchToCustomMode.Expect(
        self.messages.ComputeNetworksSwitchToCustomModeRequest(
            project='fake-project', network='my-network'),
        self.messages.Operation(name='myop'))

    self.WriteInput('y\n')
    self.Run("""
        compute networks update my-network --switch-to-custom-subnet-mode --async
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Update in progress for network my-network '
        '[https://compute.googleapis.com/compute/v1/'
        'projects/fake-project/global/operations/myop] '
        'Run the [gcloud compute operations describe] command to check the '
        'status of this operation.\n')

  def testUpdate_switchToCustomSubnetMode_no(self):
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run("""
          compute networks update my-network --switch-to-custom-subnet-mode
          """)
    self.AssertErrContains('Aborted by user.')

  def testUpdateMtu_success(self):
    expected = self.messages.Network()

    expected.mtu = 1500
    self.mock_client.networks.Patch.Expect(
        self.messages.ComputeNetworksPatchRequest(
            project='fake-project',
            network='my-network',
            networkResource=expected), self.messages.Operation(name='myop'))

    self.WriteInput('y\n')
    self.Run("""compute networks update my-network --mtu 1500""")

  def testUpdateMtu_no(self):
    self.WriteInput('n\n')

    with self.assertRaises(console_io.OperationCancelledError):
      self.Run("""compute networks update my-network --mtu 1500""")
    self.AssertErrContains('Aborted by user.')


class UpdateTestBeta(UpdateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'
    self.messages = core_apis.GetMessagesModule('compute', 'beta')
    self.mock_client = mock.Client(
        core_apis.GetClientClass('compute', 'beta'),
        real_client=core_apis.GetClientInstance(
            'compute', 'beta', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)


class UpdateTestAlpha(UpdateTestBeta):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')
    self.mock_client = mock.Client(
        core_apis.GetClientClass('compute', 'alpha'),
        real_client=core_apis.GetClientInstance(
            'compute', 'alpha', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)


if __name__ == '__main__':
  test_case.main()
