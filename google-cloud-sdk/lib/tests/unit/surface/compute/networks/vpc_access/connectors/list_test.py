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
"""Tests of 'gcloud compute networks vpc-access connectors list' command."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.networks.vpc_access import base


class ConnectorsListTest(base.VpcAccessUnitTestBase):

  def testConnectorsList(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    expected_connectors = self._MakeConnectors()
    self._ExpectList(expected_connectors)
    self.Run(
        'compute networks vpc-access connectors list --region={}'.format(
            self.region_id))

    self.AssertOutputEquals(
        """\
        CONNECTOR_ID    REGION       NETWORK       IP_CIDR_RANGE  STATUS
        my-connector-0  us-central1  my-network-0  10.132.0.0/28  READY
        my-connector-1  us-central1  my-network-1  10.128.0.0/28  CREATING
        my-connector-2  us-central1  my-network-2  10.142.0.0/28  DELETING
        """,
        normalize_space=True)

  def testConnectorsListUri(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    expected_connectors = self._MakeConnectors()
    self._ExpectList(expected_connectors)
    self.Run(
        'compute networks vpc-access connectors list --region={} --uri'.format(
            self.region_id))

    # pylint: disable=line-too-long
    self.AssertOutputEquals(
        """\
        https://vpcaccess.googleapis.com/{api_version}/projects/{project}/locations/{location}/connectors/my-connector-0
        https://vpcaccess.googleapis.com/{api_version}/projects/{project}/locations/{location}/connectors/my-connector-1
        https://vpcaccess.googleapis.com/{api_version}/projects/{project}/locations/{location}/connectors/my-connector-2
        """.format(
            api_version=self.api_version,
            project=self.project_id,
            location=self.region_id),
        normalize_space=True)
    # pylint: enable=line-too-long

  def _MakeConnectors(self):
    connectors = []
    connectors.append(
        self._MakeConnector(
            'my-connector-0', 'my-network-0', '10.132.0.0/28',
            self.messages.Connector.StatusValueValuesEnum('READY')))
    connectors.append(
        self._MakeConnector(
            'my-connector-1', 'my-network-1', '10.128.0.0/28',
            self.messages.Connector.StatusValueValuesEnum('CREATING')))
    connectors.append(
        self._MakeConnector(
            'my-connector-2', 'my-network-2', '10.142.0.0/28',
            self.messages.Connector.StatusValueValuesEnum('DELETING')))
    return connectors

  def _MakeConnector(self, connector_id, network, ip_cidr_range, status):
    connector_prefix = 'projects/{}/locations/{}/connectors/'.format(
        self.project_id, self.region_id)
    return self.messages.Connector(
        name=connector_prefix + connector_id,
        id=connector_id,
        network=network,
        ipCidrRange=ip_cidr_range,
        status=status)

  def _ExpectList(self, expected_connectors):
    self.connectors_client.List.Expect(
        request=self.messages.VpcaccessProjectsLocationsConnectorsListRequest(
            parent=self.region_relative_name),
        response=self.messages.ListConnectorsResponse(
            connectors=expected_connectors))


if __name__ == '__main__':
  test_case.main()
