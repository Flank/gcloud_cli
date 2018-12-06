# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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


class ConnectorsCreateTest(base.VpcAccessUnitTestBase):

  def testConnectorsCreate_NoRegion(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    with self.assertRaises(concepts_handler.ParseError):
      self.Run('compute networks vpc-access connectors create {} '
               '--type={} --network={} --range={}'.format(
                   self.connector_id, self.type_extended, self.network_id,
                   self.ip_cidr_range))

  def testConnectorCreate_DefaultType(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    connector_to_create = self._MakeConnectorExtended()
    expected_connector = self._ExpecteCreate(connector_to_create)
    actual_connector = self.Run(
        'compute networks vpc-access connectors create {} '
        '--region={} --network={} --range={}'.format(
            self.connector_id, self.region_id, self.network_id,
            self.ip_cidr_range))

    self.assertEqual(actual_connector, expected_connector)

  def testConnectorCreate_Extended(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    connector_to_create = self._MakeConnectorExtended()
    expected_connector = self._ExpecteCreate(connector_to_create)
    actual_connector = self.Run(
        'compute networks vpc-access connectors create {} '
        '--region={} --type={} --network={} --range={}'.format(
            self.connector_id, self.region_id, self.type_extended,
            self.network_id, self.ip_cidr_range))

    self.assertEqual(actual_connector, expected_connector)

  def testConnectorCreate_Basic(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    connector_to_create = self._MakeConnectorBasic()
    expected_connector = self._ExpecteCreate(connector_to_create)
    actual_connector = self.Run(
        'compute networks vpc-access connectors create {} '
        '--region={} --type={} --network={}'.format(
            self.connector_id, self.region_id, self.type_basic,
            self.network_id))

    self.assertEqual(actual_connector, expected_connector)

  def testConnectorCreate_ExtendedAsync(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    connector_to_create = self._MakeConnectorExtended()
    self._ExpecteCreate(connector_to_create, is_async=True)
    self.Run('compute networks vpc-access connectors create {} '
             '--region={} --type={} --network={} --range={} --async'.format(
                 self.connector_id, self.region_id, self.type_extended,
                 self.network_id, self.ip_cidr_range))

    self.AssertErrContains('Create request issued for: [{}]'.format(
        self.connector_id))
    self.AssertErrContains('Check operation [{}] for status.'.format(
        self.operation_id))

  def testConnectorCreate_BasicAsync(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    connector_to_create = self._MakeConnectorBasic()
    self._ExpecteCreate(connector_to_create, is_async=True)
    self.Run('compute networks vpc-access connectors create {} '
             '--region={} --type={} --network={} --async'.format(
                 self.connector_id, self.region_id, self.type_basic,
                 self.network_id))

    self.AssertErrContains('Create request issued for: [{}]'.format(
        self.connector_id))
    self.AssertErrContains('Check operation [{}] for status.'.format(
        self.operation_id))

  def testConnectorCreate_ExtendedUsingRelativeConnectorName(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    connector_to_create = self._MakeConnectorExtended()
    expected_connector = self._ExpecteCreate(connector_to_create)
    actual_connector = self.Run(
        'compute networks vpc-access connectors create {} '
        '--type={} --network={} --range={}'.format(
            self.connector_relative_name, self.type_extended, self.network_id,
            self.ip_cidr_range))

    self.assertEqual(actual_connector, expected_connector)

  def testConnectorCreate_BasicUsingRelativeConnectorName(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    connector_to_create = self._MakeConnectorBasic()
    expected_connector = self._ExpecteCreate(connector_to_create)
    actual_connector = self.Run(
        'compute networks vpc-access connectors create {} '
        '--type={} --network={}'.format(self.connector_relative_name,
                                        self.type_basic, self.network_id))

    self.assertEqual(actual_connector, expected_connector)

  def _MakeConnectorExtended(self):
    return self.messages.Connector(
        # Note `name` should not be set as it's read-only.
        id=self.connector_id,
        type=self.type_extended,
        network=self.network_id,
        ipCidrRange=self.ip_cidr_range)

  def _MakeConnectorBasic(self):
    return self.messages.Connector(
        # Note `name` should not be set as it's read-only.
        id=self.connector_id,
        type=self.type_basic,
        network=self.network_id)

  def _ExpecteCreate(self, connector_to_create, is_async=False):
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
