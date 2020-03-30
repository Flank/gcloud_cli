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
"""Tests for the Service API message wrapper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import service
from tests.lib import test_case
from tests.lib.api_lib.run import base


class ServiceTest(base.ServerlessApiBase):

  def SetUp(self):
    self.service = service.Service.New(self.mock_serverless_client,
                                       self.Project())

  def testLatestPercentTrafficByLatestRevision(self):
    self.service.status.traffic.extend([
        self.serverless_messages.TrafficTarget(latestRevision=True, percent=80),
        self.serverless_messages.TrafficTarget(
            revisionName='rev.2', percent=20)
    ])
    self.assertEqual(self.service.latest_percent_traffic, 80)

  def testLatestPercentTrafficByRevisionName(self):
    self.service.status.latestReadyRevisionName = 'rev.1'
    self.service.status.traffic.extend([
        self.serverless_messages.TrafficTarget(
            revisionName='rev.1', percent=80),
        self.serverless_messages.TrafficTarget(
            revisionName='rev.2', percent=20)
    ])
    self.assertEqual(self.service.latest_percent_traffic, 80)

  def testLatestPercentTrafficSumsMultipleLatestTargets(self):
    self.service.status.latestReadyRevisionName = 'rev.1'
    self.service.status.traffic.extend([
        self.serverless_messages.TrafficTarget(
            revisionName='rev.1', percent=50),
        self.serverless_messages.TrafficTarget(
            revisionName='rev.1', percent=30),
        self.serverless_messages.TrafficTarget(
            revisionName='rev.2', percent=20)
    ])
    self.assertEqual(self.service.latest_percent_traffic, 80)

  def testLatestPercentTrafficHandlesZeroPercentTarget(self):
    self.service.status.latestReadyRevisionName = 'rev.1'
    self.service.status.traffic.extend([
        self.serverless_messages.TrafficTarget(
            revisionName='rev.1', percent=80),
        self.serverless_messages.TrafficTarget(
            revisionName='rev.1', tag='candidate'),
        self.serverless_messages.TrafficTarget(
            revisionName='rev.2', percent=20)
    ])
    self.assertEqual(self.service.latest_percent_traffic, 80)


if __name__ == '__main__':
  test_case.main()
