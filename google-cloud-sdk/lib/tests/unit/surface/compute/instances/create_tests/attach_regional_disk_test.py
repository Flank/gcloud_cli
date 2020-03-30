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


class InstancesCreateAttachRegionalDiskBeta(
    create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testRegionalDisk(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --zone central2-a
          --disk name=disk1,scope=regional
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
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
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          source=(self.compute_uri +
                                  '/projects/my-project/regions/central2/'
                                  'disks/disk1'),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  networkTier=self._default_network_tier,
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=[
                              'https://www.googleapis.com/auth/devstorage'
                              '.read_only',
                              'https://www.googleapis.com/auth/logging.write',
                              'https://www.googleapis.com/auth/monitoring'
                              '.write',
                              'https://www.googleapis.com/auth/pubsub',
                              'https://www.googleapis.com/auth/service'
                              '.management.readonly',
                              'https://www.googleapis.com/auth/servicecontrol',
                              'https://www.googleapis.com/auth/trace.append',
                          ]),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True)),
              project='my-project',
              zone='central2-a',
          ))],
    )


class InstancesCreateAttachRegionalDiskAlpha(
    InstancesCreateAttachRegionalDiskBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
