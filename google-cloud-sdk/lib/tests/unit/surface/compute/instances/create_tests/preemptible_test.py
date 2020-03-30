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


class PreemptibleInstancesCreateTest(create_test_base.InstancesCreateTestBase):
  """Test creation of preemptible VM instances."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testPreemptible(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='us-central2-b'),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --machine-type=n1-standard-1
          --zone=us-central1-b
          --preemptible
          --no-restart-on-failure
          --maintenance-policy=terminate
        """)
    self.CheckRequests(
        [(self.compute.zones, 'Get',
          m.ComputeZonesGetRequest(project='my-project', zone='us-central1-b'))
        ],
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
                              sourceImage=create_test_base.DefaultImageOf(
                                  self.api_version),),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=create_test_base.DefaultPreemptibleMachineTypeOf(
                      self.api_version),
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=m.AccessConfig.TypeValueValuesEnum
                                  .ONE_TO_ONE_NAT)
                          ],
                          network=create_test_base.DefaultNetworkOf(
                              self.api_version))
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=False,
                      onHostMaintenance=m.Scheduling
                      .OnHostMaintenanceValueValuesEnum.TERMINATE,
                      preemptible=True)),
              project='my-project',
              zone='us-central1-b',
          ))],
    )

  def testPreemptibleWithoutRestartOrMaintenance(self):
    """Creates a preemptible VM with just the --preemptible flag.

    Unlike the previous test, doesn't supply the restart-on-failure or
    on-host-maintenance flags.
    """
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='us-central2-b'),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --machine-type=n1-standard-1
          --zone=us-central1-b
          --preemptible
        """)
    self.CheckRequests(
        [(self.compute.zones, 'Get',
          m.ComputeZonesGetRequest(project='my-project', zone='us-central1-b'))
        ],
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
                              sourceImage=create_test_base.DefaultImageOf(
                                  self.api_version),),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=create_test_base.DefaultPreemptibleMachineTypeOf(
                      self.api_version),
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=m.AccessConfig.TypeValueValuesEnum
                                  .ONE_TO_ONE_NAT)
                          ],
                          network=create_test_base.DefaultNetworkOf(
                              self.api_version))
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=False, preemptible=True)),
              project='my-project',
              zone='us-central1-b',
          ))],
    )


if __name__ == '__main__':
  test_case.main()
