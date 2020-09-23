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
from tests.lib.surface.compute.instances import create_with_container_test_base as create_test_base


class InstancesCreateWithNestedVirtualizationAlpha(
    create_test_base.InstancesCreateWithContainerTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def CreateRequestWithNestedVirtualization(self,
                                            enable_nested_virtualization):

    m = self.messages
    # We want both True and False to pass in explicitly, but None should look
    # like an unsupplied message.
    if enable_nested_virtualization is not None:
      nested_message = m.AdvancedMachineFeatures(
          enableNestedVirtualization=enable_nested_virtualization)
    else:
      nested_message = None

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
            scheduling=m.Scheduling(automaticRestart=True),
            serviceAccounts=[self.default_service_account],
            tags=self.default_tags,
            # This is the important part.
            advancedMachineFeatures=nested_message,
        ),
        project='my-project',
        zone='central2-a',
    )

  def testDefaultNested(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
        """)

    # Should say None.
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNestedVirtualization(None))]
    )

  def testNestedEnabled(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --enable-nested-virtualization
        """)

    # Should match True.
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNestedVirtualization(True))]
    )

  def testNestedDisbled_NoEnable(self):
    self.Run("""
        compute instances create-with-container instance-1
          --zone central2-a
          --container-image=gcr.io/my-docker/test-image
          --no-enable-nested-virtualization
        """)

    # Should also be False.
    self.CheckRequests(
        self.zone_get_request,
        self.cos_images_list_request,
        [(self.compute.instances, 'Insert',
          self.CreateRequestWithNestedVirtualization(False))]
    )


if __name__ == '__main__':
  test_case.main()
