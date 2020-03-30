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


class ImageFamilies(create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testImageFamilyFlag(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image-family yorik
        """)

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
                              self.api_version))
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

  def testImageFamilyURI(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image-family '{0}/projects/my-project/global/images/family/yorik'
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
                              self.api_version))
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

  def testImageFamilyURIImageFlag(self):
    msg = self.messages

    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --image '{0}/projects/my-project/global/images/family/yorik'
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
                              self.api_version))
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

  def testAliasWithReplacement(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
        [
            self.messages.Image(
                name='debian-8-jessie-v20151130',
                selfLink=('https://compute.googleapis.com/compute/v1/'
                          'projects/debian-cloud/global/'
                          'images/debian-8-jessie-v20151130'),
            )
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    self.Run("""
        compute instances create instance-1
          --zone central2-a --image debian-8
        """)

    self.AssertErrContains('Please use --image-family=debian-8 and'
                           ' --image-project=debian-cloud instead.')

  def testAliasWithoutReplacement(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
        [
            self.messages.Image(
                name='debian-8-jessie-v20151130',
                selfLink=('https://compute.googleapis.com/compute/v1/'
                          'projects/debian-cloud/global/'
                          'images/debian-8-jessie-v20151130'),
            )
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    self.Run("""
        compute instances create instance-1
          --zone central2-a --image opensuse-13
        """)

    self.AssertErrContains('Please use --image-family and'
                           ' --image-project instead.')

if __name__ == '__main__':
  test_case.main()
