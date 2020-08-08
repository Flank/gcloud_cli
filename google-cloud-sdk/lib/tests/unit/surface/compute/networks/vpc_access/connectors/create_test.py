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
"""Tests of 'gcloud compute networks vpc-access connectors create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers as concepts_handler
from tests.lib import test_case
from tests.lib.surface.compute.networks.vpc_access import base


class ConnectorsCreateTestGa(base.VpcAccessUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testConnectorsCreate_NoRegion(self):
    with self.assertRaises(concepts_handler.ParseError):
      self.Run('compute networks vpc-access connectors create {} '
               '--network={} --range={}'.format(
                   self.connector_id, self.network_id, self.ip_cidr_range))

  def testConnectorCreate_Default(self):
    connector_to_create = self._MakeConnector()
    expected_connector = self._ExpectCreate(connector_to_create)
    actual_connector = self.Run(
        'compute networks vpc-access connectors create {} '
        '--region={} --network={} --range={}'.format(
            self.connector_id, self.region_id, self.network_id,
            self.ip_cidr_range))
    self.assertEqual(actual_connector, expected_connector)

  def testConnectorCreate_ThroughputsSet(self):
    connector_to_create = self._MakeConnector()
    expected_connector = self._ExpectCreate(connector_to_create)
    actual_connector = self.Run(
        'compute networks vpc-access connectors create {} '
        '--region={} --network={} --range={} --min-throughput={} '
        '--max-throughput={}'.format(self.connector_id, self.region_id,
                                     self.network_id, self.ip_cidr_range,
                                     self.min_throughput, self.max_throughput))
    self.assertEqual(actual_connector, expected_connector)

  def testConnectorCreate_Async(self):
    connector_to_create = self._MakeConnector()
    self._ExpectCreate(connector_to_create, is_async=True)
    self.Run('compute networks vpc-access connectors create {} '
             '--region={} --network={} --range={} --async'.format(
                 self.connector_id, self.region_id, self.network_id,
                 self.ip_cidr_range))
    self.AssertErrContains('Create request issued for: [{}]'.format(
        self.connector_id))
    self.AssertErrContains('Check operation [{}] for status.'.format(
        self.operation_relative_name))

  def testConnectorCreate_UsingRelativeConnectorName(self):
    connector_to_create = self._MakeConnector()
    expected_connector = self._ExpectCreate(connector_to_create)
    actual_connector = self.Run(
        'compute networks vpc-access connectors create {} '
        '--network={} --range={}'.format(self.connector_relative_name,
                                         self.network_id, self.ip_cidr_range))
    self.assertEqual(actual_connector, expected_connector)

  def _MakeConnector(self):
    return self.messages.Connector(
        # Note `name` should not be set as it's read-only.
        network=self.network_id,
        ipCidrRange=self.ip_cidr_range,
        minThroughput=self.min_throughput,
        maxThroughput=self.max_throughput)

  def _ExpectCreate(self, connector_to_create, is_async=False):
    operation = self.messages.Operation(name=self.operation_relative_name)
    self.connectors_client.Create.Expect(
        request=self.messages.VpcaccessProjectsLocationsConnectorsCreateRequest(
            connector=connector_to_create,
            parent=self.region_relative_name,
            connectorId=self.connector_id),
        response=operation)

    if is_async:
      return

    operation.done = True  # Simulate immediate success.
    self.operations_client.Get.Expect(
        request=self.messages.VpcaccessProjectsLocationsOperationsGetRequest(
            name=operation.name),
        response=operation)

    # The Get request to fetch the created instance needs an instance name.
    expected_created_connector = copy.deepcopy(connector_to_create)
    expected_created_connector.name = self.connector_relative_name
    self.connectors_client.Get.Expect(
        request=self.messages.VpcaccessProjectsLocationsConnectorsGetRequest(
            name=expected_created_connector.name),
        response=expected_created_connector)
    return expected_created_connector


class ConnectorsCreateTestBeta(ConnectorsCreateTestGa):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'v1beta1'


class ConnectorsCreateTestAlpha(ConnectorsCreateTestGa):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'v1alpha1'

  def testConnectorsCreate_NoRegion(self):
    with self.assertRaises(concepts_handler.ParseError):
      self.Run('compute networks vpc-access connectors create {} '
               '--network={} --range={}'.format(self.connector_id,
                                                self.network_id,
                                                self.ip_cidr_range))

  def testConnectorCreate_Default(self):
    connector_to_create = self._MakeConnector()
    expected_connector = self._ExpectCreate(connector_to_create)
    actual_connector = self.Run(
        'compute networks vpc-access connectors create {} '
        '--region={} --network={} --range={}'.format(
            self.connector_id, self.region_id, self.network_id,
            self.ip_cidr_range))
    self.assertEqual(actual_connector, expected_connector)

  def testConnectorCreate_ThroughputsSet(self):
    # Throughput not supported in alpha.
    pass

  def testConnectorCreate_Async(self):
    connector_to_create = self._MakeConnector()
    self._ExpectCreate(connector_to_create, is_async=True)
    self.Run('compute networks vpc-access connectors create {} '
             '--region={} --network={} --range={} --async'.format(
                 self.connector_id, self.region_id, self.network_id,
                 self.ip_cidr_range))
    self.AssertErrContains('Create request issued for: [{}]'.format(
        self.connector_id))
    self.AssertErrContains('Check operation [{}] for status.'.format(
        self.operation_relative_name))

  def testConnectorCreate_UsingRelativeConnectorName(self):
    connector_to_create = self._MakeConnector()
    expected_connector = self._ExpectCreate(connector_to_create)
    actual_connector = self.Run(
        'compute networks vpc-access connectors create {} '
        '--network={} --range={}'.format(self.connector_relative_name,
                                         self.network_id, self.ip_cidr_range))
    self.assertEqual(actual_connector, expected_connector)

  def testConnectorCreate(self):
    connector_to_create = self._MakeConnector()
    expected_connector = self._ExpectCreate(connector_to_create)
    actual_connector = self.Run(
        'compute networks vpc-access connectors create {} '
        '--region={} --network={} --range={}'.format(self.connector_id,
                                                     self.region_id,
                                                     self.network_id,
                                                     self.ip_cidr_range))
    self.assertEqual(actual_connector, expected_connector)

  def testConnectorCreateAsync(self):
    connector_to_create = self._MakeConnector()
    self._ExpectCreate(connector_to_create, is_async=True)
    self.Run('compute networks vpc-access connectors create {} '
             '--region={} --network={} --range={} --async'.format(
                 self.connector_id, self.region_id, self.network_id,
                 self.ip_cidr_range))
    self.AssertErrContains('Create request issued for: [{}]'.format(
        self.connector_id))
    self.AssertErrContains('Check operation [{}] for status.'.format(
        self.operation_relative_name))

  def testConnectorCreateUsingRelativeConnectorName(self):
    connector_to_create = self._MakeConnector()
    expected_connector = self._ExpectCreate(connector_to_create)
    actual_connector = self.Run(
        'compute networks vpc-access connectors create {} '
        '--network={} --range={}'.format(self.connector_relative_name,
                                         self.network_id, self.ip_cidr_range))
    self.assertEqual(actual_connector, expected_connector)

  def _MakeConnector(self):
    return self.messages.Connector(
        # Note `name` should not be set as it's read-only.
        id=self.connector_id,
        network=self.network_id,
        ipCidrRange=self.ip_cidr_range,
        minThroughput=self.min_throughput,
        maxThroughput=self.max_throughput)

  def _ExpectCreate(self, connector_to_create, is_async=False):
    operation = self.messages.Operation(name=self.operation_relative_name)
    self.connectors_client.Create.Expect(
        request=self.messages.VpcaccessProjectsLocationsConnectorsCreateRequest(
            connector=connector_to_create, parent=self.region_relative_name),
        response=operation)

    if is_async:
      return

    operation.done = True  # Simulate immediate success.
    self.operations_client.Get.Expect(
        request=self.messages.VpcaccessProjectsLocationsOperationsGetRequest(
            name=operation.name),
        response=operation)

    # The Get request to fetch the created instance needs an instance name.
    expected_created_connector = copy.deepcopy(connector_to_create)
    expected_created_connector.name = self.connector_relative_name
    self.connectors_client.Get.Expect(
        request=self.messages.VpcaccessProjectsLocationsConnectorsGetRequest(
            name=expected_created_connector.name),
        response=expected_created_connector)
    return expected_created_connector


if __name__ == '__main__':
  test_case.main()
