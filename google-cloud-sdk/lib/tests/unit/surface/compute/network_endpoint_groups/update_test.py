# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for the network endpoint groups update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base


class NetworkEndpointGroupsUpdateTest(sdk_test_base.WithFakeAuth,
                                      cli_test_base.CliTestBase,
                                      waiter_test_base.Base):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.messages = self.client.MESSAGES_MODULE

    self.operation_status_enum = self.messages.Operation.StatusValueValuesEnum
    self.region = 'us-central1'
    self.zone = 'us-central1-a'

  def _GetOperationMessage(self, operation_name, status, resource_uri=None):
    return self.messages.Operation(
        name=operation_name,
        status=status,
        selfLink='https://compute.googleapis.com/compute/{0}/projects/{1}/zones/'
        '{2}/operations/{3}'.format(self.api_version, self.Project(), self.zone,
                                    operation_name),
        targetLink=resource_uri)

  def _ExpectAttachEndpoints(self, endpoints, operation_suffix='X'):
    request_class = (
        self.messages.ComputeNetworkEndpointGroupsAttachNetworkEndpointsRequest)
    nested_request_class = (
        self.messages.NetworkEndpointGroupsAttachEndpointsRequest)
    self.client.networkEndpointGroups.AttachNetworkEndpoints.Expect(
        request_class(
            networkEndpointGroup='my-neg',
            project=self.Project(),
            zone=self.zone,
            networkEndpointGroupsAttachEndpointsRequest=nested_request_class(
                networkEndpoints=endpoints)),
        self._GetOperationMessage(
            'operation-' + operation_suffix,
            self.operation_status_enum.PENDING))

  def _ExpectDetachEndpoints(self, endpoints, operation_suffix='X'):
    request_class = (
        self.messages.ComputeNetworkEndpointGroupsDetachNetworkEndpointsRequest)
    nested_request_class = (
        self.messages.NetworkEndpointGroupsDetachEndpointsRequest)
    self.client.networkEndpointGroups.DetachNetworkEndpoints.Expect(
        request_class(
            networkEndpointGroup='my-neg',
            project=self.Project(),
            zone=self.zone,
            networkEndpointGroupsDetachEndpointsRequest=nested_request_class(
                networkEndpoints=endpoints)),
        self._GetOperationMessage(
            'operation-' + operation_suffix,
            self.operation_status_enum.PENDING))

  def _ExpectPollAndGet(self, operation_suffix='X'):
    neg_name = 'my-neg'
    neg_uri = ('https://compute.googleapis.com/compute/{0}/projects/{1}/zones/'
               '{2}/networkEndpointGroups/{3}'.format(self.api_version,
                                                      self.Project(), self.zone,
                                                      neg_name))
    self.client.zoneOperations.Wait.Expect(
        self.messages.ComputeZoneOperationsWaitRequest(
            operation='operation-' + operation_suffix,
            zone=self.zone,
            project=self.Project()),
        self._GetOperationMessage(
            'operation-' + operation_suffix,
            self.messages.Operation.StatusValueValuesEnum.DONE, neg_uri))

    self.client.networkEndpointGroups.Get.Expect(
        self.messages.ComputeNetworkEndpointGroupsGetRequest(
            networkEndpointGroup=neg_name, project=self.Project(),
            zone=self.zone),
        self.messages.NetworkEndpointGroup(name=neg_name))

  def testUpdate_AddEndpointSimple(self):
    endpoints = [
        self.messages.NetworkEndpoint(
            instance='my-instance1',
            ipAddress='127.0.0.1',
            port=8888),
    ]
    expected_neg = self.messages.NetworkEndpointGroup(name='my-neg')
    self._ExpectAttachEndpoints(endpoints)
    self._ExpectPollAndGet()
    result = self.Run(
        'compute network-endpoint-groups update my-neg '
        '--add-endpoint instance=my-instance1,ip=127.0.0.1,port=8888 '
        '--zone ' + self.zone)
    self.assertEqual(expected_neg, result)
    self.AssertErrContains('Attaching 1 endpoints to [my-neg].')

  def testUpdate_AddEndpointMultiple(self):
    endpoints = [
        self.messages.NetworkEndpoint(
            instance='my-instance1',
            ipAddress='127.0.0.1',
            port=8888),
        self.messages.NetworkEndpoint(
            instance='my-instance2',
            port=10001),
    ]
    self._ExpectAttachEndpoints(endpoints)
    self._ExpectPollAndGet()
    self.Run(
        'compute network-endpoint-groups update my-neg '
        '--add-endpoint instance=my-instance1,ip=127.0.0.1,port=8888 '
        '--add-endpoint instance=my-instance2,port=10001 '
        '--zone ' + self.zone)
    self.AssertErrContains('Attaching 2 endpoints to [my-neg].')

  def testUpdate_RemoveEndpointSimple(self):
    endpoints = [
        self.messages.NetworkEndpoint(
            instance='my-instance1',
            ipAddress='127.0.0.1',
            port=8888),
    ]
    self._ExpectDetachEndpoints(endpoints)
    self._ExpectPollAndGet()
    self.Run(
        'compute network-endpoint-groups update my-neg '
        '--remove-endpoint instance=my-instance1,ip=127.0.0.1,port=8888 '
        '--zone ' + self.zone)
    self.AssertErrContains('Detaching 1 endpoints from [my-neg].')

  def testUpdate_RemoveEndpointMultiple(self):
    endpoints = [
        self.messages.NetworkEndpoint(
            instance='my-instance1',
            ipAddress='127.0.0.1',
            port=8888),
        self.messages.NetworkEndpoint(
            instance='my-instance2',
            port=10001),
    ]
    self._ExpectDetachEndpoints(endpoints)
    self._ExpectPollAndGet()
    self.Run(
        'compute network-endpoint-groups update my-neg '
        '--remove-endpoint instance=my-instance1,ip=127.0.0.1,port=8888 '
        '--remove-endpoint instance=my-instance2,port=10001 '
        '--zone ' + self.zone)
    self.AssertErrContains('Detaching 2 endpoints from [my-neg].')

  def testUpdate_AddAndRemoveEndpointsMutuallyExclusive(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--add-endpoint | --remove-endpoint) '
        'must be specified.'):
      self.Run(
          'compute network-endpoint-groups update my-neg '
          '--add-endpoint instance=my-instance1,ip=127.0.0.1,port=8888 '
          '--remove-endpoint instance=my-instance2,port=10001 '
          '--zone ' + self.zone)

  def testUpdate_MissingEndpointsGroupFlag(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--add-endpoint | --remove-endpoint) '
        'must be specified.'):
      self.Run(
          'compute network-endpoint-groups update my-neg '
          '--zone ' + self.zone)

  def _GetGlobalOperationMessage(self,
                                 operation_name,
                                 status,
                                 resource_uri=None):
    return self.messages.Operation(
        name=operation_name,
        status=status,
        selfLink='https://compute.googleapis.com/compute/{0}/projects/{1}/global/'
        'operations/{2}'.format(self.api_version, self.Project(),
                                operation_name),
        targetLink=resource_uri)

  def _ExpectAttachGlobalEndpoints(self, endpoints, operation_suffix='X'):
    request_class = (
        self.messages
        .ComputeGlobalNetworkEndpointGroupsAttachNetworkEndpointsRequest)
    nested_request_class = (
        self.messages.GlobalNetworkEndpointGroupsAttachEndpointsRequest)
    self.client.globalNetworkEndpointGroups.AttachNetworkEndpoints.Expect(
        request_class(
            networkEndpointGroup='my-global-neg',
            project=self.Project(),
            globalNetworkEndpointGroupsAttachEndpointsRequest=nested_request_class(
                networkEndpoints=endpoints)),
        self._GetGlobalOperationMessage('operation-' + operation_suffix,
                                        self.operation_status_enum.PENDING))

  def _ExpectDetachGlobalEndpoints(self, endpoints, operation_suffix='X'):
    request_class = (
        self.messages
        .ComputeGlobalNetworkEndpointGroupsDetachNetworkEndpointsRequest)
    nested_request_class = (
        self.messages.GlobalNetworkEndpointGroupsDetachEndpointsRequest)
    self.client.globalNetworkEndpointGroups.DetachNetworkEndpoints.Expect(
        request_class(
            networkEndpointGroup='my-global-neg',
            project=self.Project(),
            globalNetworkEndpointGroupsDetachEndpointsRequest=nested_request_class(
                networkEndpoints=endpoints)),
        self._GetGlobalOperationMessage('operation-' + operation_suffix,
                                        self.operation_status_enum.PENDING))

  def _ExpectGlobalPollAndGet(self, operation_suffix='X'):
    neg_name = 'my-global-neg'
    neg_uri = ('https://compute.googleapis.com/compute/{0}/projects/{1}/global/'
               'networkEndpointGroups/{2}'.format(self.api_version,
                                                  self.Project(), neg_name))
    self.client.globalOperations.Wait.Expect(
        self.messages.ComputeGlobalOperationsWaitRequest(
            operation='operation-' + operation_suffix,
            project=self.Project()),
        self._GetGlobalOperationMessage(
            'operation-' + operation_suffix,
            self.messages.Operation.StatusValueValuesEnum.DONE, neg_uri))
    self.client.globalNetworkEndpointGroups.Get.Expect(
        self.messages.ComputeGlobalNetworkEndpointGroupsGetRequest(
            networkEndpointGroup=neg_name, project=self.Project()),
        self.messages.NetworkEndpointGroup(name=neg_name))

  def testUpdate_AddInternetIpEndpoint(self):
    endpoints = [
        self.messages.NetworkEndpoint(ipAddress='8.8.8.8', port=8080),
    ]
    expected_neg = self.messages.NetworkEndpointGroup(name='my-global-neg')
    self._ExpectAttachGlobalEndpoints(endpoints)
    self._ExpectGlobalPollAndGet()
    result = self.Run('compute network-endpoint-groups update my-global-neg '
                      '--add-endpoint ip=8.8.8.8,port=8080 --global')
    self.assertEqual(expected_neg, result)
    self.AssertErrContains('Attaching 1 endpoints to [my-global-neg].')

  def testUpdate_AddInternetFqdnEndpoint(self):
    endpoints = [
        self.messages.NetworkEndpoint(fqdn='test.example.com', port=8080),
    ]
    expected_neg = self.messages.NetworkEndpointGroup(name='my-global-neg')
    self._ExpectAttachGlobalEndpoints(endpoints)
    self._ExpectGlobalPollAndGet()
    result = self.Run('compute network-endpoint-groups update my-global-neg '
                      '--add-endpoint fqdn=test.example.com,port=8080 --global')
    self.assertEqual(expected_neg, result)
    self.AssertErrContains('Attaching 1 endpoints to [my-global-neg].')

  def testUpdate_RemoveInternetIpEndpoint(self):
    endpoints = [
        self.messages.NetworkEndpoint(ipAddress='8.8.8.8', port=8080),
    ]
    self._ExpectDetachGlobalEndpoints(endpoints)
    self._ExpectGlobalPollAndGet()
    self.Run('compute network-endpoint-groups update my-global-neg '
             '--remove-endpoint ip=8.8.8.8,port=8080 --global')
    self.AssertErrContains('Detaching 1 endpoints from [my-global-neg].')

  def testUpdate_RemoveInternetFqdnEndpoint(self):
    endpoints = [
        self.messages.NetworkEndpoint(fqdn='example.com'),
    ]
    self._ExpectDetachGlobalEndpoints(endpoints)
    self._ExpectGlobalPollAndGet()
    self.Run('compute network-endpoint-groups update my-global-neg '
             '--remove-endpoint fqdn=example.com --global')
    self.AssertErrContains('Detaching 1 endpoints from [my-global-neg].')


class AlphaNetworkEndpointGroupsUpdateTest(NetworkEndpointGroupsUpdateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.messages = self.client.MESSAGES_MODULE

    self.operation_status_enum = self.messages.Operation.StatusValueValuesEnum

  def testUpdate_NonGcpPrivateIpPortType_AddEndpointSimple(self):
    endpoints = [
        self.messages.NetworkEndpoint(ipAddress='127.0.0.1', port=8888)
    ]
    expected_neg = self.messages.NetworkEndpointGroup(name='my-neg')
    self._ExpectAttachEndpoints(endpoints)
    self._ExpectPollAndGet()
    result = self.Run('compute network-endpoint-groups update my-neg '
                      '--add-endpoint ip=127.0.0.1,port=8888 --zone ' +
                      self.zone)
    self.assertEqual(expected_neg, result)
    self.AssertErrContains('Attaching 1 endpoints to [my-neg].')

  def testUpdate_NonGcpPrivateIpPortType_AddEndpointMultiple(self):
    endpoints = [
        self.messages.NetworkEndpoint(ipAddress='127.0.0.1', port=8888),
        self.messages.NetworkEndpoint(ipAddress='127.0.0.2')
    ]
    self._ExpectAttachEndpoints(endpoints)
    self._ExpectPollAndGet()
    self.Run('compute network-endpoint-groups update my-neg '
             '--add-endpoint ip=127.0.0.1,port=8888 '
             '--add-endpoint ip=127.0.0.2 --zone ' + self.zone)
    self.AssertErrContains('Attaching 2 endpoints to [my-neg].')

  def testUpdate_NonGcpPrivateIpPortType_RemoveEndpointSimple(self):
    endpoints = [
        self.messages.NetworkEndpoint(ipAddress='127.0.0.1', port=8888),
    ]
    self._ExpectDetachEndpoints(endpoints)
    self._ExpectPollAndGet()
    self.Run('compute network-endpoint-groups update my-neg '
             '--remove-endpoint ip=127.0.0.1,port=8888 --zone ' + self.zone)
    self.AssertErrContains('Detaching 1 endpoints from [my-neg].')

  def testUpdate_NonGcpPrivateIpPortType_RemoveEndpointMultiple(self):
    endpoints = [
        self.messages.NetworkEndpoint(ipAddress='127.0.0.1', port=8888),
        self.messages.NetworkEndpoint(ipAddress='127.0.0.2')
    ]
    self._ExpectDetachEndpoints(endpoints)
    self._ExpectPollAndGet()
    self.Run('compute network-endpoint-groups update my-neg '
             '--remove-endpoint ip=127.0.0.1,port=8888 '
             '--remove-endpoint ip=127.0.0.2 --zone ' + self.zone)

  def testUpdate_GceVmPrimaryIpType_AddEndpointSimple(self):
    endpoints = [self.messages.NetworkEndpoint(ipAddress='127.0.0.1')]
    expected_neg = self.messages.NetworkEndpointGroup(name='my-neg')
    self._ExpectAttachEndpoints(endpoints)
    self._ExpectPollAndGet()
    result = self.Run('compute network-endpoint-groups update my-neg '
                      '--add-endpoint ip=127.0.0.1 --zone ' + self.zone)
    self.assertEqual(expected_neg, result)
    self.AssertErrContains('Attaching 1 endpoints to [my-neg].')

  def testUpdate_GceVmPrimaryIpType_AddEndpointMultiple(self):
    endpoints = [
        self.messages.NetworkEndpoint(ipAddress='127.0.0.1'),
        self.messages.NetworkEndpoint(ipAddress='127.0.0.2')
    ]
    self._ExpectAttachEndpoints(endpoints)
    self._ExpectPollAndGet()
    self.Run('compute network-endpoint-groups update my-neg '
             '--add-endpoint ip=127.0.0.1 '
             '--add-endpoint ip=127.0.0.2 --zone ' + self.zone)
    self.AssertErrContains('Attaching 2 endpoints to [my-neg].')

  def testUpdate_GceVmPrimaryIpType_RemoveEndpointSimple(self):
    endpoints = [
        self.messages.NetworkEndpoint(ipAddress='127.0.0.1'),
    ]
    self._ExpectDetachEndpoints(endpoints)
    self._ExpectPollAndGet()
    self.Run('compute network-endpoint-groups update my-neg '
             '--remove-endpoint ip=127.0.0.1 --zone ' + self.zone)
    self.AssertErrContains('Detaching 1 endpoints from [my-neg].')

  def testUpdate_GceVmPrimaryIpType_RemoveEndpointMultiple(self):
    endpoints = [
        self.messages.NetworkEndpoint(ipAddress='127.0.0.1'),
        self.messages.NetworkEndpoint(ipAddress='127.0.0.2')
    ]
    self._ExpectDetachEndpoints(endpoints)
    self._ExpectPollAndGet()
    self.Run('compute network-endpoint-groups update my-neg '
             '--remove-endpoint ip=127.0.0.1 '
             '--remove-endpoint ip=127.0.0.2 --zone ' + self.zone)


if __name__ == '__main__':
  test_case.main()
