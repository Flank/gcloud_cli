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
"""Tests of 'gcloud compute networks vpc-access connectors update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers as concepts_handler
from tests.lib import test_case
from tests.lib.surface.compute.networks.vpc_access import base


class ConnectorsUpdateTestAlpha(base.VpcAccessUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'v1alpha1'

  def testConnectorsUpdate_NoRegion(self):
    with self.assertRaises(concepts_handler.ParseError):
      self.Run('compute networks vpc-access connectors update {}'.format(
          self.region_id))

  def testConnectorUpdate_Default(self):
    update_connector = self._MakeConnector(
        min_throughput=self.patch_min_throughput,
        max_throughput=self.patch_max_throughput)
    name = self.connector_relative_name
    mask = ','.join([self.max_throughput_field, self.min_throughput_field])
    self._ExpectUpdate(update_connector, name, mask)

    actual_connector = self.Run(
        'compute networks vpc-access connectors update {} '
        '--region={} --min-throughput={} --max-throughput={}'.format(
            self.connector_id, self.region_id, self.patch_min_throughput,
            self.patch_max_throughput))
    self.assertEqual(actual_connector, actual_connector)

  def testConnectorUpdate_RelativeName(self):
    update_connector = self._MakeConnector(
        min_throughput=self.patch_min_throughput,
        max_throughput=self.patch_max_throughput)
    name = self.connector_relative_name
    mask = ','.join([self.max_throughput_field, self.min_throughput_field])
    self._ExpectUpdate(update_connector, name, mask)

    actual_connector = self.Run(
        'compute networks vpc-access connectors update {} '
        '--region={} --min-throughput={} --max-throughput={}'.format(
            self.connector_relative_name, self.region_id,
            self.patch_min_throughput, self.patch_max_throughput))
    self.assertEqual(actual_connector, actual_connector)

  def testConnectorUpdate_MinThroughputOnly(self):
    update_connector = self._MakeConnector(
        min_throughput=self.patch_min_throughput)
    name = self.connector_relative_name
    mask = self.min_throughput_field
    self._ExpectUpdate(update_connector, name, mask)

    actual_connector = self.Run(
        'compute networks vpc-access connectors update {} '
        '--region={} --min-throughput={}'.format(self.connector_id,
                                                 self.region_id,
                                                 self.patch_min_throughput))
    self.assertEqual(actual_connector, actual_connector)

  def testConnectorUpdate_Async(self):
    update_connector = self._MakeConnector(
        min_throughput=self.patch_min_throughput,
        max_throughput=self.patch_max_throughput)
    name = self.connector_relative_name
    mask = ','.join([self.max_throughput_field, self.min_throughput_field])
    self._ExpectUpdate(update_connector, name, mask, is_async=True)

    self.Run(
        'compute networks vpc-access connectors update {} '
        '--region={} --min-throughput={} --max-throughput={} --async'.format(
            self.connector_relative_name, self.region_id,
            self.patch_min_throughput, self.patch_max_throughput))
    self.AssertErrContains('Request issued for: [{}]'.format(self.connector_id))
    self.AssertErrContains('Check operation [{}] for status.'.format(
        self.operation_relative_name))

  def _MakeConnector(self, min_throughput=None, max_throughput=None):
    return self.messages.Connector(
        # Note `name` should not be set as it's read-only.
        minThroughput=min_throughput,
        maxThroughput=max_throughput)

  def _ExpectUpdate(self,
                    update_connector,
                    connector_name,
                    mask,
                    is_async=False):
    operation = self.messages.Operation(name=self.operation_relative_name)
    self.connectors_client.Patch.Expect(
        request=self.messages.VpcaccessProjectsLocationsConnectorsPatchRequest(
            name=connector_name, connector=update_connector, updateMask=mask),
        response=operation)

    if is_async:
      return

    operation.done = True  # Simulate immediate success.
    self.operations_client.Get.Expect(
        request=self.messages.VpcaccessProjectsLocationsOperationsGetRequest(
            name=operation.name),
        response=operation)

    expected_updated_connector = copy.deepcopy(update_connector)
    expected_updated_connector.name = self.connector_relative_name
    self.connectors_client.Get.Expect(
        request=self.messages.VpcaccessProjectsLocationsConnectorsGetRequest(
            name=expected_updated_connector.name),
        response=expected_updated_connector)
    return expected_updated_connector


if __name__ == '__main__':
  test_case.main()
