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


class InstancesCreateImageTest(create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testWithImageInSameProject(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --image my-image
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=(
                              'https://compute.googleapis.com/compute/{0}/projects/'
                              'my-project/global/images/my-image'.format(
                                  self.api)),
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithImageInDifferentProject(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1 --zone central2-a
          --image other-image
          --image-project some-other-project
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._other_image),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithImageInDifferentProjectWithUri(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1 --zone central2-a
          --image other-image
          --image-project https://compute.googleapis.com/compute/{0}/projects/some-other-project
        """.format(self.api_version))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._other_image),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat)],
                      network=self._default_network)],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES
                      ),
                  ],
                  scheduling=m.Scheduling(
                      automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithImageProjectButNoImage(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Must specify either \[--image\] or \[--image-family\] when '
        r'specifying \[--image-project\] flag.'):
      self.Run("""
          compute instances create instance-1
            --image-project some-other-project
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskDeviceNameOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-device-name\] can only be used when creating a new '
        r'boot disk.'):
      self.Run("""
          compute instances create instance-1
            --disk boot=yes,name=my-disk
            --boot-disk-device-name x
            --zone central2-a
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskSizeOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-size\] can only be used when creating a new boot '
        r'disk.'):
      self.Run("""
          compute instances create instance-1
            --disk boot=yes,name=my-disk
            --boot-disk-size 10GB
            --zone central2-a
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskTypeOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-type\] can only be used when creating a new boot '
        r'disk.'):
      self.Run("""
          compute instances create instance-1
            --disk boot=yes,name=my-disk
            --boot-disk-type pd-ssd
            --zone central2-a
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskAutoDeleteOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--no-boot-disk-auto-delete\] can only be used when creating a new '
        'boot disk.'):
      self.Run("""
          compute instances create instance-1
            --disk boot=yes,name=my-disk
            --no-boot-disk-auto-delete
            --zone central2-a
          """)

    self.CheckRequests()

  def testIllegalAutoDeleteValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Value for \[auto-delete\] in \[--disk\] must be \[yes\] or \[no\], '
        r'not \[true\].'):
      self.Run("""
          compute instances create instance-1
            --disk boot=yes,name=my-disk,auto-delete=true
            --zone central2-a
          """)

    self.CheckRequests()

if __name__ == '__main__':
  test_case.main()
