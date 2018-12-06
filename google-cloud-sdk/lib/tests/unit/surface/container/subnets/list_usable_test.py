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

"""Tests for container.subnets.list_usable."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.container import base


class ListUsableTestBeta(base.BetaTestBase, base.SubnetsTestBase,
                         test_case.WithOutputCapture):
  """gcloud beta track using container v1beta1 API."""

  def testMissingProject(self):
    properties.VALUES.core.project.Set(None)
    with self.assertRaises(properties.RequiredPropertyError):
      self.Run(self.subnets_command_base + ' list-usable')

  def testListAggregate(self):
    subnets = [
        self._MakeUsableSubnet(
            network='my-networkA',
            subnetwork='my-subnetA',
            ipCidrRange='1.1.1.1/10',
            secondaryIpRanges=[
                self._MakeUsableSubnetworkSecondaryRange(
                    rangeName='pods-range',
                    ipCidrRange='10.1.0.0/19',
                    status=self.unused),
                self._MakeUsableSubnetworkSecondaryRange(
                    rangeName='svc-range',
                    ipCidrRange='10.2.0.0/19',
                    status=self.in_use_service),
                self._MakeUsableSubnetworkSecondaryRange(
                    rangeName='extra-range',
                    ipCidrRange='10.3.0.0/19',
                    status=self.in_use_shareable_pod)
            ]),
        self._MakeUsableSubnet(
            network='my-networkB',
            subnetwork='my-subnetB',
            ipCidrRange='2.2.2.2/10',
            secondaryIpRanges=[
                self._MakeUsableSubnetworkSecondaryRange(
                    rangeName='secondaryRange',
                    ipCidrRange='10.1.0.0/19',
                    status=self.in_use_managed_pod)
            ]),
        self._MakeUsableSubnet(
            network='my-networkC',
            subnetwork='my-subnetC',
            ipCidrRange='3.3.3.3/10')
    ]

    resp = self._MakeListUsableSubnetworksResponse(subnets)
    self._ExpectListUsableSubnets(resp)
    self.Run(self.subnets_command_base + ' list-usable')
    self.AssertOutputEquals(
        """\
PROJECT REGION NETWORK SUBNET RANGE
fake-project-id us-central1 my-networkA my-subnetA 1.1.1.1/10
    +----------------------+---------------+-----------------------------+
    | SECONDARY_RANGE_NAME | IP_CIDR_RANGE |            STATUS           |
    +----------------------+---------------+-----------------------------+
    | pods-range           | 10.1.0.0/19   | usable for pods or services |
    | svc-range            | 10.2.0.0/19   | unusable                    |
    | extra-range          | 10.3.0.0/19   | usable for pods             |
    +----------------------+---------------+-----------------------------+
fake-project-id us-central1 my-networkB my-subnetB 2.2.2.2/10
    +----------------------+---------------+----------+
    | SECONDARY_RANGE_NAME | IP_CIDR_RANGE |  STATUS  |
    +----------------------+---------------+----------+
    | secondaryRange       | 10.1.0.0/19   | unusable |
    +----------------------+---------------+----------+
fake-project-id us-central1 my-networkC my-subnetC 3.3.3.3/10
""",
        normalize_space=True)

  def testListAggregateWithWarnings(self):
    msg1 = 'some message from cluster apiserver'
    msg2 = 'some other message from cluster apiserver'
    subnets = [
        self._MakeUsableSubnet(
            network='my-networkA',
            subnetwork='my-subnetA',
            ipCidrRange='1.1.1.1/10',
            statusMessage=msg1),
        self._MakeUsableSubnet(
            network='my-networkB',
            subnetwork='my-subnetB',
            ipCidrRange='2.2.2.2/10',
            statusMessage=msg1),
        self._MakeUsableSubnet(
            network='my-networkC',
            subnetwork='my-subnetC',
            ipCidrRange='3.3.3.3/10',
            statusMessage=msg2)
    ]

    resp = self._MakeListUsableSubnetworksResponse(subnets)
    self._ExpectListUsableSubnets(resp)
    self.Run(self.subnets_command_base + ' list-usable')
    self.AssertOutputEquals(
        """\
PROJECT REGION NETWORK SUBNET RANGE
fake-project-id us-central1 my-networkA my-subnetA 1.1.1.1/10
fake-project-id us-central1 my-networkB my-subnetB 2.2.2.2/10
fake-project-id us-central1 my-networkC my-subnetC 3.3.3.3/10
""",
        normalize_space=True)
    self.AssertErrEquals('WARNING: %s\nWARNING: %s\n' % (msg1, msg2))

  def testListAggregateURI(self):
    subnets = [self._MakeUsableSubnet(network='my-networkA',
                                      subnetwork='my-subnetA',
                                      ipCidrRange='1.1.1.1/10'),
               self._MakeUsableSubnet(network='my-networkB',
                                      subnetwork='my-subnetB',
                                      ipCidrRange='2.2.2.2/10')]

    resp = self._MakeListUsableSubnetworksResponse(subnets)
    self._ExpectListUsableSubnets(resp)
    self.Run(self.subnets_command_base + ' list-usable --uri')
    self.AssertOutputEquals("""\
https://www.googleapis.com/compute/v1/projects/fake-project-id/regions/us-central1/subnetworks/my-subnetA
https://www.googleapis.com/compute/v1/projects/fake-project-id/regions/us-central1/subnetworks/my-subnetB
""", normalize_space=True)


class ListUsableTestAlpha(base.AlphaTestBase, ListUsableTestBeta):
  """gcloud alpha track using container v1alpha1 API."""


if __name__ == '__main__':
  test_case.main()
