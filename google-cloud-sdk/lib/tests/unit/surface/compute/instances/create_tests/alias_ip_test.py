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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstanceWithAliasIpRangesTest(create_test_base.InstancesCreateTestBase):
  """Test creation of instance with alias IP ranges."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testAliasIpRanges(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
          --network-interface network=default,address=,aliases=range1:1.2.3.4;range2:/24;/32
          --network-interface network=some-net,private-network-ip=10.0.0.1,address=8.8.8.8,aliases=range1:1.2.3.0/24
          --network-interface subnet=some-subnet
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          msg.ComputeInstancesInsertRequest(
              instance=msg.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      msg.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=msg.AttachedDiskInitializeParams(
                              sourceImage=(self.compute_uri +
                                           '/projects/my-project/global/images/'
                                           'family/yorik'),),
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=create_test_base.DefaultMachineTypeOf(
                      self.api_version),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=create_test_base.DefaultNetworkOf(
                              self.api_version),
                          aliasIpRanges=[
                              msg.AliasIpRange(
                                  subnetworkRangeName='range1',
                                  ipCidrRange='1.2.3.4'),
                              msg.AliasIpRange(
                                  subnetworkRangeName='range2',
                                  ipCidrRange='/24'),
                              msg.AliasIpRange(ipCidrRange='/32')
                          ]),
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  natIP='8.8.8.8',
                                  type=self._one_to_one_nat)
                          ],
                          network=('https://compute.googleapis.com/compute/v1/'
                                   'projects/my-project/global/networks/'
                                   'some-net'),
                          networkIP='10.0.0.1',
                          aliasIpRanges=[
                              msg.AliasIpRange(
                                  subnetworkRangeName='range1',
                                  ipCidrRange='1.2.3.0/24')
                          ]),
                      msg.NetworkInterface(
                          subnetwork=(
                              'https://compute.googleapis.com/compute/v1/'
                              'projects/my-project/regions/central2/'
                              'subnetworks/some-subnet'),
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                      ),
                  ],
                  serviceAccounts=[
                      msg.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=msg.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testInvalidAliasIpRangeFormat(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'An alias IP range must contain range name and IP '
        r'range'):
      self.Run("""
          compute instances create instance-1
          --zone central2-a
          --network-interface network=default,aliases=range1:abc:def;
          """)


if __name__ == '__main__':
  test_case.main()
