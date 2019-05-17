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
"""Tests of 'gcloud compute networks vpc-access connectors describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.networks.vpc_access import base


class ConnectorsDescribeTestBeta(base.VpcAccessUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'v1beta1'

  def testConnectorsDescribe(self):
    expected_connector = self.messages.Connector(
        name=self.connector_relative_name)
    self._ExpectDescribe(expected_connector)

    actual_connector = self.Run(
        'compute networks vpc-access connectors describe {} --region={}'.format(
            self.connector_id, self.region_id))
    self.assertEqual(actual_connector, expected_connector)

  def testConnectorsDescribe_UsingRelativeConnectorName(self):
    expected_connector = self.messages.Connector(
        name=self.connector_relative_name)
    self._ExpectDescribe(expected_connector)

    actual_connector = self.Run(
        'compute networks vpc-access connectors describe {}'.format(
            self.connector_relative_name))
    self.assertEqual(actual_connector, expected_connector)

  def _ExpectDescribe(self, expected_connector):
    self.connectors_client.Get.Expect(
        request=self.messages.VpcaccessProjectsLocationsConnectorsGetRequest(
            name=expected_connector.name),
        response=expected_connector)


class ConnectorsDescribeTestAlpha(ConnectorsDescribeTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'v1alpha1'


if __name__ == '__main__':
  test_case.main()
