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


class InstancesCreateWithPublicDns(create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def CreateRequestWithPublicDns(self,
                                 set_public_dns=None,
                                 set_ptr=None,
                                 ptr_domain_name=None):
    m = self.messages
    access_config = m.AccessConfig(
        name='external-nat',
        networkTier=self._default_network_tier,
        type=self._one_to_one_nat)

    if set_public_dns is not None:
      access_config.setPublicDns = bool(set_public_dns)
    if set_ptr is not None:
      access_config.setPublicPtr = bool(set_ptr)
    if ptr_domain_name is not None:
      access_config.publicPtrDomainName = ptr_domain_name

    return m.ComputeInstancesInsertRequest(
        instance=m.Instance(
            canIpForward=False,
            deletionProtection=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=self._default_machine_type,
            metadata=m.Metadata(),
            name='instance-1',
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[access_config],
                    network=self._default_network)
            ],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default', scopes=create_test_base.DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        ),
        project='my-project',
        zone='central2-a',
    )

  def testPublicDnsDisabledByDefault(self):
    self.Run("""
        compute instances create instance-1
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPublicDns())],)

  def testEnablePublicDns(self):
    self.Run("""
        compute instances create instance-1 --public-dns
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPublicDns(set_public_dns=True))],)

  def testDisablePublicDns(self):
    self.Run("""
        compute instances create instance-1 --no-public-dns
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPublicDns(set_public_dns=False))],)

  def testInvalidPublicDnsSettings(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-dns: At most one of --public-dns | --no-public-dns '
        'may be specified.'):
      self.Run("""
          compute instances create instance-1 --no-public-dns
            --public-dns
            --zone central2-a
          """)


if __name__ == '__main__':
  test_case.main()
