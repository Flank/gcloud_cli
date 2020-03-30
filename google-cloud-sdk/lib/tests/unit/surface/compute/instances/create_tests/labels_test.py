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
from tests.lib.cli_test_base import MockArgumentError
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateWithLabelsTest(create_test_base.InstancesCreateTestBase):
  """Test creation of instances with labels."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.project_get_request = [
        (self.compute.projects, 'Get',
         self.messages.ComputeProjectsGetRequest(project='my-project'))
    ]

  def testCreateWithLabels(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
        ],
        [
            m.Project(defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
       compute instances create instance-with-labels
       --zone=central2-a
       --labels=k0=v0,k-1=v-1
       --labels=foo=bar
       """)

    labels_in_request = (('foo', 'bar'), ('k-1', 'v-1'), ('k0', 'v0'))
    self.CheckRequests(
        [(self.compute.zones, 'Get',
          m.ComputeZonesGetRequest(project='my-project', zone='central2-a'))],
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
                              sourceImage=create_test_base.DefaultImageOf('v1'),
                          ),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  labels=m.Instance.LabelsValue(additionalProperties=[
                      m.Instance.LabelsValue.AdditionalProperty(
                          key=pair[0], value=pair[1])
                      for pair in labels_in_request
                  ]),
                  metadata=m.Metadata(),
                  machineType=create_test_base.DefaultMachineTypeOf(
                      self.api_version),
                  name='instance-with-labels',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=m.AccessConfig.TypeValueValuesEnum
                                  .ONE_TO_ONE_NAT)
                          ],
                          network=create_test_base.DefaultNetworkOf('v1'))
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True)),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testCreateWithInvalidLabels(self):
    with self.assertRaises(MockArgumentError):
      self.Run("""
          compute instances create instance-with-labels
            --zone=central2-a
            --labels=inv@lid-key=inv@l!d-value
          """)


if __name__ == '__main__':
  test_case.main()
