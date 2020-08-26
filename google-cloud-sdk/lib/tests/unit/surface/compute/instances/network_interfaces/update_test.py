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
"""Tests for instances network-interfaces update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class UpdateNetworkInterfaceTest(sdk_test_base.WithFakeAuth,
                                 cli_test_base.CliTestBase):
  """Base class for testing instance update network interface command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api = 'v1'

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('compute', self.api),
        real_client=core_apis.GetClientInstance(
            'compute', self.api, no_http=True))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)
    self.messages = self.apitools_client.MESSAGES_MODULE

    self.resources = resources.Registry()
    self.resources.RegisterApiByName('compute', self.api)
    self.service = self.apitools_client.instances
    self.zone_operations = self.apitools_client.zoneOperations

  def _GetInstance(self, name, zone=None):
    params = {'project': self.Project()}
    params['zone'] = zone

    instance_ref = self.resources.Parse(
        name, params=params, collection='compute.instances')
    instance = self.messages.Instance(networkInterfaces=[
        self.messages.NetworkInterface(name='nic0'),
        self.messages.NetworkInterface(name='nic11'),
    ])

    return instance, instance_ref

  def _GetOperation(self, instance_ref):
    operation_ref = self.resources.Parse(
        'operation-1',
        params={'project': self.Project(),
                'zone': instance_ref.zone},
        collection='compute.zoneOperations')
    operation = self.messages.Operation(
        name=operation_ref.Name(),
        status=self.messages.Operation.StatusValueValuesEnum.DONE,
        selfLink=operation_ref.SelfLink(),
        targetLink=instance_ref.SelfLink())
    return operation, operation_ref

  def _ExpectInstanceGetRequest(self, instance, instance_ref, exception=None):
    request_type = self.messages.ComputeInstancesGetRequest

    self.service.Get.Expect(
        request=request_type(**instance_ref.AsDict()),
        response=instance,
        exception=exception)

  def _ExpectOperationGetRequest(self, operation, operation_ref):
    self.zone_operations.Get.Expect(
        self.messages.ComputeZoneOperationsGetRequest(
            operation=operation_ref.operation,
            zone=operation_ref.zone,
            project=self.Project()), operation)

  def _ExpectOperationWaitRequest(self, operation, operation_ref):
    self.zone_operations.Wait.Expect(
        self.messages.ComputeZoneOperationsWaitRequest(
            operation=operation_ref.operation,
            zone=operation_ref.zone,
            project=self.Project()), operation)

  def _ExpectOperationPollingRequest(self, operation, operation_ref):
    self._ExpectOperationWaitRequest(operation, operation_ref)

  def testUpdateDefaultNic(self):
    instance, instance_ref = self._GetInstance('instance-1', zone='atlanta')
    operation, operation_ref = self._GetOperation(instance_ref)
    request = self.messages.ComputeInstancesUpdateNetworkInterfaceRequest(
        instance='instance-1',
        networkInterfaceResource=self.messages.NetworkInterface(
            aliasIpRanges=[
                self.messages.AliasIpRange(
                    ipCidrRange='10.128.1.0/24',
                    subnetworkRangeName=None,),
                self.messages.AliasIpRange(
                    ipCidrRange='/32',
                    subnetworkRangeName='r1',),
            ]),
        project=self.Project(),
        zone='atlanta',
        networkInterface='nic0')

    self._ExpectInstanceGetRequest(instance, instance_ref)
    self.service.UpdateNetworkInterface.Expect(request, response=operation)
    self._ExpectOperationPollingRequest(operation, operation_ref)
    self._ExpectInstanceGetRequest(instance, instance_ref)

    self.Run(
        'compute instances network-interfaces update instance-1 --zone atlanta '
        ' --aliases "10.128.1.0/24;r1:/32"')

  def testUpdateNamedNic(self):
    instance, instance_ref = self._GetInstance('instance-1', zone='atlanta')
    operation, operation_ref = self._GetOperation(instance_ref)
    request = self.messages.ComputeInstancesUpdateNetworkInterfaceRequest(
        instance='instance-1',
        networkInterfaceResource=self.messages.NetworkInterface(
            aliasIpRanges=[
                self.messages.AliasIpRange(
                    ipCidrRange='10.128.1.0/24',
                    subnetworkRangeName=None,),
                self.messages.AliasIpRange(
                    ipCidrRange='/32',
                    subnetworkRangeName='r1',),
            ]),
        project=self.Project(),
        zone='atlanta',
        networkInterface='nic11')

    self._ExpectInstanceGetRequest(instance, instance_ref)
    self.service.UpdateNetworkInterface.Expect(request, response=operation)
    self._ExpectOperationPollingRequest(operation, operation_ref)
    self._ExpectInstanceGetRequest(instance, instance_ref)

    self.Run(
        'compute instances network-interfaces update instance-1 --zone atlanta '
        ' --network-interface nic11 --aliases "10.128.1.0/24;r1:/32"')

  def testUpdateKeepsExistingData(self):
    instance, instance_ref = self._GetInstance('instance-1', zone='atlanta')
    instance.networkInterfaces.append(
        self.messages.NetworkInterface(name='nic3', network='fake-network-url'))
    operation, operation_ref = self._GetOperation(instance_ref)
    request = self.messages.ComputeInstancesUpdateNetworkInterfaceRequest(
        instance='instance-1',
        networkInterfaceResource=self.messages.NetworkInterface(
            aliasIpRanges=[
                self.messages.AliasIpRange(
                    ipCidrRange='10.128.1.0/24',
                    subnetworkRangeName=None,),
                self.messages.AliasIpRange(
                    ipCidrRange='/32',
                    subnetworkRangeName='r1',),
            ]),
        project=self.Project(),
        zone='atlanta',
        networkInterface='nic3')

    self._ExpectInstanceGetRequest(instance, instance_ref)
    self.service.UpdateNetworkInterface.Expect(request, response=operation)
    self._ExpectOperationPollingRequest(operation, operation_ref)
    self._ExpectInstanceGetRequest(instance, instance_ref)

    self.Run(
        'compute instances network-interfaces update instance-1 --zone atlanta '
        ' --network-interface nic3 --aliases "10.128.1.0/24;r1:/32"')

  def testUpdateClearAliases(self):
    instance, instance_ref = self._GetInstance('instance-1', zone='atlanta')
    operation, operation_ref = self._GetOperation(instance_ref)
    request = self.messages.ComputeInstancesUpdateNetworkInterfaceRequest(
        instance='instance-1',
        networkInterfaceResource=self.messages.NetworkInterface(
            aliasIpRanges=[]),
        project=self.Project(),
        zone='atlanta',
        networkInterface='nic0')

    self._ExpectInstanceGetRequest(instance, instance_ref)
    self.service.UpdateNetworkInterface.Expect(request, response=operation)
    self._ExpectOperationPollingRequest(operation, operation_ref)
    self._ExpectInstanceGetRequest(instance, instance_ref)

    self.Run(
        'compute instances network-interfaces update instance-1 --zone atlanta '
        ' --aliases ""')

  def testUpdateNonexistentNic(self):
    instance, instance_ref = self._GetInstance('instance-1', zone='atlanta')

    self._ExpectInstanceGetRequest(instance, instance_ref)

    with self.assertRaisesRegex(
        calliope_exceptions.UnknownArgumentException,
        r'Instance does not have a network interface \[not-a-nic]'):
      self.Run('compute instances network-interfaces update instance-1 '
               '--zone atlanta --network-interface not-a-nic '
               '--aliases "10.128.1.0/24;r1:/32"')


class UpdateNetworkInterfaceTestBeta(UpdateNetworkInterfaceTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api = 'beta'

  def _GetNetworkUrl(self, name, project=None):
    return 'https://compute.googleapis.com/compute/{api}/projects/{project}/global/networks/{network}'.format(
        api=self.api, project=project or self.Project(), network=name)

  def _GetSubnetworkUrl(self, name, project=None):
    return 'https://compute.googleapis.com/compute/{api}/projects/{project}/regions/atlanta/subnetworks/{subnetwork}'.format(
        api=self.api, project=project or self.Project(), subnetwork=name)

  def testNetworkMigrationAllParams(self):
    instance, instance_ref = self._GetInstance('instance-1', zone='atlanta-a')
    operation, operation_ref = self._GetOperation(instance_ref)
    request = self.messages.ComputeInstancesUpdateNetworkInterfaceRequest(
        instance='instance-1',
        networkInterfaceResource=self.messages.NetworkInterface(
            aliasIpRanges=[
                self.messages.AliasIpRange(
                    ipCidrRange='10.128.1.0/24',
                    subnetworkRangeName=None,
                ),
                self.messages.AliasIpRange(
                    ipCidrRange='/32',
                    subnetworkRangeName='r1',
                ),
            ],
            network=self._GetNetworkUrl('net1'),
            subnetwork=self._GetSubnetworkUrl('sub1'),
            networkIP='10.0.0.2'),
        project=self.Project(),
        zone='atlanta-a',
        networkInterface='nic0')

    self._ExpectInstanceGetRequest(instance, instance_ref)
    self.service.UpdateNetworkInterface.Expect(request, response=operation)
    self._ExpectOperationPollingRequest(operation, operation_ref)
    self._ExpectInstanceGetRequest(instance, instance_ref)

    self.Run("""
        compute instances network-interfaces update instance-1 --zone atlanta-a
        --network=net1
        --subnetwork=sub1
        --private-network-ip=10.0.0.2
        --aliases "10.128.1.0/24;r1:/32"
        """)

  def testNetworkMigrationNetworkOnly(self):
    instance, instance_ref = self._GetInstance('instance-1', zone='atlanta-a')
    operation, operation_ref = self._GetOperation(instance_ref)
    request = self.messages.ComputeInstancesUpdateNetworkInterfaceRequest(
        instance='instance-1',
        networkInterfaceResource=self.messages.NetworkInterface(
            network=self._GetNetworkUrl('net1')),
        project=self.Project(),
        zone='atlanta-a',
        networkInterface='nic0')

    self._ExpectInstanceGetRequest(instance, instance_ref)
    self.service.UpdateNetworkInterface.Expect(request, response=operation)
    self._ExpectOperationPollingRequest(operation, operation_ref)
    self._ExpectInstanceGetRequest(instance, instance_ref)

    self.Run("""
        compute instances network-interfaces update instance-1 --zone atlanta-a
        --network=net1
        """)

  def testNetworkMigrationSubnetworkOnly(self):
    instance, instance_ref = self._GetInstance('instance-1', zone='atlanta-a')
    operation, operation_ref = self._GetOperation(instance_ref)
    request = self.messages.ComputeInstancesUpdateNetworkInterfaceRequest(
        instance='instance-1',
        networkInterfaceResource=self.messages.NetworkInterface(
            subnetwork=self._GetSubnetworkUrl('sub1')),
        project=self.Project(),
        zone='atlanta-a',
        networkInterface='nic0')

    self._ExpectInstanceGetRequest(instance, instance_ref)
    self.service.UpdateNetworkInterface.Expect(request, response=operation)
    self._ExpectOperationPollingRequest(operation, operation_ref)
    self._ExpectInstanceGetRequest(instance, instance_ref)

    self.Run("""
        compute instances network-interfaces update instance-1 --zone atlanta-a
        --subnetwork=sub1
        """)

  def testNetworkMigrationNoIp(self):
    instance, instance_ref = self._GetInstance('instance-1', zone='atlanta-a')
    operation, operation_ref = self._GetOperation(instance_ref)
    request = self.messages.ComputeInstancesUpdateNetworkInterfaceRequest(
        instance='instance-1',
        networkInterfaceResource=self.messages.NetworkInterface(
            network=self._GetNetworkUrl('net1'),
            subnetwork=self._GetSubnetworkUrl('sub1')),
        project=self.Project(),
        zone='atlanta-a',
        networkInterface='nic0')

    self._ExpectInstanceGetRequest(instance, instance_ref)
    self.service.UpdateNetworkInterface.Expect(request, response=operation)
    self._ExpectOperationPollingRequest(operation, operation_ref)
    self._ExpectInstanceGetRequest(instance, instance_ref)

    self.Run("""
        compute instances network-interfaces update instance-1 --zone atlanta-a
        --network=net1
        --subnetwork=sub1
        """)

  def testNetworkMigrationCrossProject(self):
    instance, instance_ref = self._GetInstance('instance-1', zone='atlanta-a')
    operation, operation_ref = self._GetOperation(instance_ref)
    request = self.messages.ComputeInstancesUpdateNetworkInterfaceRequest(
        instance='instance-1',
        networkInterfaceResource=self.messages.NetworkInterface(
            network=self._GetNetworkUrl('net1', 'other-project'),
            subnetwork=self._GetSubnetworkUrl('sub1', 'other-project')),
        project=self.Project(),
        zone='atlanta-a',
        networkInterface='nic0')

    self._ExpectInstanceGetRequest(instance, instance_ref)
    self.service.UpdateNetworkInterface.Expect(request, response=operation)
    self._ExpectOperationPollingRequest(operation, operation_ref)
    self._ExpectInstanceGetRequest(instance, instance_ref)

    self.Run("""
        compute instances network-interfaces update instance-1 --zone atlanta-a
        --network=projects/other-project/global/networks/net1
        --subnetwork=projects/other-project/regions/atlanta/subnetworks/sub1
        """)


class UpdateNetworkInterfaceTestAlpha(UpdateNetworkInterfaceTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api = 'alpha'


if __name__ == '__main__':
  test_case.main()
