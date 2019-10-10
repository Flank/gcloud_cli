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
"""Tests for the get-nat-mapping-info subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import router_test_base


class BetaGetNatMappingInfoTest(router_test_base.RouterTestBase):

  def SetUp(self):
    self.SelectApi(calliope_base.ReleaseTrack.BETA, 'beta')

    self.mappings = [
        self.messages.VmEndpointNatMappings(
            instanceName='instance-{}'.format(i),
            interfaceNatMappings=[
                self.messages.VmEndpointNatMappingsInterfaceNatMappings(
                    natIpPortRanges=[
                        '35.0.0.1:{}-{}'.format(str(64 * i), str(64 * i + 63))
                    ],
                    numTotalNatPorts=64,
                    sourceAliasIpRange='',
                    sourceVirtualIp='10.0.0.{}'.format(i))
            ]) for i in range(10)
    ]

  def testSimple(self):
    self.mock_client.routers.GetNatMappingInfo.Expect(
        request=self.messages.ComputeRoutersGetNatMappingInfoRequest(
            project='fake-project', region='us-central1', router='my-router'),
        response=self.messages.VmEndpointNatMappingsList(result=self.mappings))

    self.Run("""
        compute routers get-nat-mapping-info my-router --region us-central1
        """)

    for i in range(10):
      self.AssertOutputContains(self._ConvertMappingToString(i))

  def testWithPagination(self):
    self.mock_client.routers.GetNatMappingInfo.Expect(
        request=self.messages.ComputeRoutersGetNatMappingInfoRequest(
            project='fake-project',
            region='us-central1',
            router='my-router',
            maxResults=5),
        response=self.messages.VmEndpointNatMappingsList(
            result=self.mappings[:5], nextPageToken='npt'))

    self.mock_client.routers.GetNatMappingInfo.Expect(
        request=self.messages.ComputeRoutersGetNatMappingInfoRequest(
            project='fake-project',
            region='us-central1',
            router='my-router',
            pageToken='npt',
            maxResults=5),
        response=self.messages.VmEndpointNatMappingsList(
            result=self.mappings[5:]))

    self.Run("""
        compute routers get-nat-mapping-info my-router --region us-central1
        --page-size 5
        """)

    for i in range(10):
      self.AssertOutputContains(self._ConvertMappingToString(i))

  def testWithLimit(self):
    self.mock_client.routers.GetNatMappingInfo.Expect(
        request=self.messages.ComputeRoutersGetNatMappingInfoRequest(
            project='fake-project', region='us-central1', router='my-router'),
        response=self.messages.VmEndpointNatMappingsList(result=self.mappings))

    self.Run("""
        compute routers get-nat-mapping-info my-router --region us-central1
        --limit 6
        """)

    for i in range(6):
      self.AssertOutputContains(self._ConvertMappingToString(i))

    for i in range(6, 10):
      self.AssertOutputNotContains(self._ConvertMappingToString(i))

  def testWithSortBy(self):
    self.mock_client.routers.GetNatMappingInfo.Expect(
        request=self.messages.ComputeRoutersGetNatMappingInfoRequest(
            project='fake-project', region='us-central1', router='my-router'),
        response=self.messages.VmEndpointNatMappingsList(result=self.mappings))

    self.Run("""
        compute routers get-nat-mapping-info my-router --region us-central1
        --sort-by ~instanceName
        """)

    # Output should be sorted by instanceName descending.
    self.AssertOutputContains(
        textwrap.dedent("""\
        instanceName: instance-2
        interfaceNatMappings:
        - natIpPortRanges:
          - 35.0.0.1:128-191
          numTotalNatPorts: 64
          sourceAliasIpRange: ''
          sourceVirtualIp: 10.0.0.2
        ---
        instanceName: instance-1
        interfaceNatMappings:
        - natIpPortRanges:
          - 35.0.0.1:64-127
          numTotalNatPorts: 64
          sourceAliasIpRange: ''
          sourceVirtualIp: 10.0.0.1"""))

  def testWithFilter(self):
    self.mock_client.routers.GetNatMappingInfo.Expect(
        request=self.messages.ComputeRoutersGetNatMappingInfoRequest(
            project='fake-project', region='us-central1', router='my-router'),
        response=self.messages.VmEndpointNatMappingsList(result=self.mappings))

    self.Run("""
        compute routers get-nat-mapping-info my-router --region us-central1
             --filter "instanceName:instance-9"
        """)

    for i in range(9):
      self.AssertOutputNotContains(self._ConvertMappingToString(i))

    self.AssertOutputContains(self._ConvertMappingToString(9))

  def _ConvertMappingToString(self, index):
    return textwrap.dedent("""\
        instanceName: instance-{0}
        interfaceNatMappings:
        - natIpPortRanges:
          - 35.0.0.1:{1}-{2}
          numTotalNatPorts: 64
          sourceAliasIpRange: ''
          sourceVirtualIp: 10.0.0.{3}
    """.format(index, str(64 * index), str(64 * index + 63), index))


class AlphaGetNatMappingInfoTest(router_test_base.RouterTestBase):

  def SetUp(self):
    self.SelectApi(calliope_base.ReleaseTrack.ALPHA, 'alpha')
    self.mappings = []

  def testNatNameFilter(self):
    self.mock_client.routers.GetNatMappingInfo.Expect(
        request=self.messages.ComputeRoutersGetNatMappingInfoRequest(
            project='fake-project', region='us-central1', router='my-router',
            natName='my-nat'),
        response=self.messages.VmEndpointNatMappingsList(result=self.mappings))

    self.Run("""
        compute routers get-nat-mapping-info my-router --region us-central1
             --nat-name=my-nat
        """)

if __name__ == '__main__':
  test_case.main()
