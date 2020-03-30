# Lint as: python3
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

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateBootDiskImageTest(create_test_base.InstancesCreateTestBase
                                      ):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testAttachmentOfExistingBootDisk(self):
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

    # Ensures that the boot disk is placed at index 0 of the disks
    # list.
    self.Run("""
        compute instances create instance-1
          --disk name=disk-2
          --disk name=disk-1,boot=yes
          --zone central2-a
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
                          autoDelete=False,
                          boot=True,
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/'
                                  'disks/disk-1'),
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/'
                                  'disks/disk-2'),
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testAttachmentOfExistingBootDiskWithNonExistentBootDisk(self):
    m = self.messages

    def MakeRequests(*_, **kwargs):
      if kwargs['requests'][0][0] == self.compute.zones:
        # This is the zonal get for deprecation warning.
        yield m.Zone(name='central2-a')
      else:
        # This is where the boot disk is fetched.
        kwargs['errors'].append((404, 'Not Found'))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Could not fetch resource:
         - Not Found
        """)):
      self.Run("""
          compute instances create instance-1
            --disk name=disk-2
            --disk name=disk-1,boot=yes
            --zone central2-a
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
                          autoDelete=False,
                          boot=True,
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/'
                                  'disks/disk-1'),
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          source=(self.compute_uri +
                                  '/projects/my-project/zones/central2-a/'
                                  'disks/disk-2'),
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[
                      m.NetworkInterface(
                          accessConfigs=[
                              m.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES,
                      ),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithNonExistentImage(self):
    m = self.messages

    def MakeRequests(*_, **kwargs):
      print(kwargs)
      if kwargs['requests'][0][0] == self.compute.zones:
        yield m.Zone(name='central2-a')
      else:
        kwargs['errors'].append((404, 'Not Found'))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Could not fetch resource:
         - Not Found
        """)):
      self.Run("""
          compute instances create instance-1
            --image non-existent-image
            --zone central2-a
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
                              sourceImage=(self.compute_uri +
                                           '/projects/my-project/global/images/'
                                           'non-existent-image'),),
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
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES,
                      ),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testPerformanceWarningWithStandardPd(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --boot-disk-size 199GB
          --zone central2-a
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
                              diskSizeGb=199,
                              sourceImage=self._default_image,
                          ),
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
                                  type=self._one_to_one_nat)
                          ],
                          network=self._default_network)
                  ],
                  serviceAccounts=[
                      m.ServiceAccount(
                          email='default',
                          scopes=create_test_base.DEFAULT_SCOPES),
                  ],
                  scheduling=m.Scheduling(automaticRestart=True),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )
    self.AssertErrContains(
        'WARNING: You have selected a disk size of under [200GB]. This may '
        'result in poor I/O performance. For more information, see: '
        'https://developers.google.com/compute/docs/disks#performance.')


if __name__ == '__main__':
  test_case.main()
