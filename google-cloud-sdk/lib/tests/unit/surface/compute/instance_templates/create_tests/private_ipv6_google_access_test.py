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
from tests.lib.surface.compute.instance_templates import create_test_base


class InstanceTemplatesCreateWithPrivateIpv6GoogleAccessBeta(
    create_test_base.InstanceTemplatesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def CreateRequestWithPrivateIpv6GoogleAccess(self,
                                               private_ipv6_google_access):
    m = self.messages
    if private_ipv6_google_access:
      private_ipv6_google_access_enum = (
          m.InstanceProperties.PrivateIpv6GoogleAccessValueValuesEnum(
              private_ipv6_google_access))
    else:
      private_ipv6_google_access_enum = None
    prop = m.InstanceProperties(
        canIpForward=False,
        disks=[
            m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=self._default_image,),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
        ],
        machineType=create_test_base.DEFAULT_MACHINE_TYPE,
        metadata=m.Metadata(),
        networkInterfaces=[
            m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=self._default_network)
        ],
        privateIpv6GoogleAccess=private_ipv6_google_access_enum,
        serviceAccounts=[
            m.ServiceAccount(
                email='default', scopes=create_test_base.DEFAULT_SCOPES),
        ],
        scheduling=m.Scheduling(automaticRestart=True),
    )
    template = m.InstanceTemplate(name='template-1', properties=prop)

    return m.ComputeInstanceTemplatesInsertRequest(
        instanceTemplate=template,
        project='my-project',
    )

  def testWithInheritSubnetPrivateIpv6GoogleAccess(self):
    self.Run("""
        compute instance-templates create template-1
          --private-ipv6-google-access-type inherit-subnetwork
        """)

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          self.CreateRequestWithPrivateIpv6GoogleAccess(
              'INHERIT_FROM_SUBNETWORK'))],
    )

  def testWithOutboundPrivateIpv6GoogleAccess(self):
    self.Run("""
          compute instance-templates create template-1
            --private-ipv6-google-access-type enable-outbound-vm-access
          """)

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          self.CreateRequestWithPrivateIpv6GoogleAccess(
              'ENABLE_OUTBOUND_VM_ACCESS_TO_GOOGLE'))],
    )

  def testWithBidireactionalPrivateIpv6GoogleAccess(self):
    self.Run("""
          compute instance-templates create template-1
            --private-ipv6-google-access-type enable-bidirectional-access
          """)

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          self.CreateRequestWithPrivateIpv6GoogleAccess(
              'ENABLE_BIDIRECTIONAL_ACCESS_TO_GOOGLE'))],
    )


class InstanceTemplatesCreateWithPrivateIpv6GoogleAccessAlpha(
    InstanceTemplatesCreateWithPrivateIpv6GoogleAccessBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
