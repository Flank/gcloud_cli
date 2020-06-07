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
from tests.lib.surface.compute.instances import create_with_container_test_base as test_base


class InstancesCreateFromContainerWithPrivateIpv6GoogleAccessBeta(
    test_base.InstancesCreateWithContainerTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def CreateRequestWithPrivateIpv6GoogleAccess(self,
                                               private_ipv6_google_access):
    m = self.messages
    if private_ipv6_google_access:
      private_ipv6_google_access_enum = (
          m.Instance.PrivateIpv6GoogleAccessValueValuesEnum(
              private_ipv6_google_access))
    else:
      private_ipv6_google_access_enum = None
    return m.ComputeInstancesInsertRequest(
        instance=m.Instance(
            canIpForward=False,
            disks=[self.default_attached_disk],
            labels=self.default_labels,
            machineType=self.default_machine_type,
            metadata=self.default_metadata,
            name='instance-1',
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[
                        m.AccessConfig(
                            name='external-nat',
                            type=m.AccessConfig.TypeValueValuesEnum
                            .ONE_TO_ONE_NAT)
                    ],
                    network=('{0}/projects/my-project/global/networks/default'
                             .format(self.compute_uri)))
            ],
            privateIpv6GoogleAccess=private_ipv6_google_access_enum,
            scheduling=m.Scheduling(automaticRestart=True),
            serviceAccounts=[self.default_service_account],
            tags=self.default_tags),
        project='my-project',
        zone='central2-a',
    )

  def testWithInheritSubnetPrivateIpv6GoogleAccess(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --private-ipv6-google-access-type inherit-subnetwork
          --container-image=gcr.io/my-docker/test-image
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPrivateIpv6GoogleAccess(
              'INHERIT_FROM_SUBNETWORK'))],
    )

  def testWithOutboundPrivateIpv6GoogleAccess(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --private-ipv6-google-access-type enable-outbound-vm-access
          --container-image=gcr.io/my-docker/test-image
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPrivateIpv6GoogleAccess(
              'ENABLE_OUTBOUND_VM_ACCESS_TO_GOOGLE'))],
    )

  def testWithBidireactionalPrivateIpv6GoogleAccess(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --private-ipv6-google-access-type enable-bidirectional-access
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPrivateIpv6GoogleAccess(
              'ENABLE_BIDIRECTIONAL_ACCESS_TO_GOOGLE'))],
    )


class InstancesCreateFromContainerWithPrivateIpv6GoogleAccessAlpha(
    InstancesCreateFromContainerWithPrivateIpv6GoogleAccessBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
