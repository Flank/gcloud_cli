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
"""Tests for the instances create-with-container subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_with_container_test_base as test_base


class InstancesCreateFromContainerWithPublicDnsTest(
    test_base.InstancesCreateWithContainerTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def CreateRequestWithPublicDns(self, set_ptr=None, ptr_domain_name=None):
    m = self.messages

    access_config = m.AccessConfig(
        name='external-nat',
        type=m.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)

    if set_ptr is not None:
      access_config.setPublicPtr = bool(set_ptr)
    if ptr_domain_name is not None:
      access_config.publicPtrDomainName = ptr_domain_name

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
                    accessConfigs=[access_config],
                    network=('{0}/projects/my-project/global/networks/default'
                             .format(self.compute_uri)))
            ],
            scheduling=m.Scheduling(automaticRestart=True),
            serviceAccounts=[self.default_service_account],
            tags=self.default_tags),
        project='my-project',
        zone='central2-a',
    )

  def testPublicDnsDisabledByDefault(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert', self.CreateRequestWithPublicDns())],
    )

  def testEnablePtr(self):
    self.Run("""
        compute instances create-with-container instance-1 --public-ptr
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPublicDns(set_ptr=True))],
    )

  def testDisablePtr(self):
    self.Run("""
        compute instances create-with-container instance-1 --no-public-ptr
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPublicDns(set_ptr=False))],
    )

  def testSetPtrDomainName(self):
    self.Run("""
        compute instances create-with-container instance-1
          --public-ptr --public-ptr-domain example.com
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithPublicDns(
              set_ptr=True, ptr_domain_name='example.com'))],
    )

  def testDisablePtrDomainName(self):
    self.Run("""
        compute instances create-with-container instance-1
          --no-public-ptr-domain
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert', self.CreateRequestWithPublicDns())],
    )

  def testInvalidPublicPtrSettings(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-ptr: At most one of --public-ptr | --no-public-ptr '
        'may be specified.'):
      self.Run("""
          compute instances create-with-container instance-1 --no-public-ptr
            --public-ptr
            --zone central2-a
            --container-image=gcr.io/my-docker/test-image
          """)

    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-ptr-domain: At most one of --public-ptr-domain | '
        '--no-public-ptr-domain may be specified.'):
      self.Run("""
          compute instances create-with-container instance-1
            --no-public-ptr-domain
            --public-ptr-domain example.com
            --zone central2-a
            --container-image=gcr.io/my-docker/test-image
          """)


class InstancesCreateFromContainerWithPublicDnsTestBeta(
    InstancesCreateFromContainerWithPublicDnsTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstancesCreateFromContainerWithPublicDnsTestAlpha(
    InstancesCreateFromContainerWithPublicDnsTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def testInvalidPublicDnsSettings(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --public-dns: At most one of --public-dns | '
        '--no-public-dns may be specified.'):
      self.Run("""
          compute instances create-with-container instance-1 --no-public-dns
            --public-dns
            --zone central2-a
            --container-image=gcr.io/my-docker/test-image
          """)


if __name__ == '__main__':
  test_case.main()
