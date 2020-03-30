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
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.cli_test_base import MockArgumentError
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateDiskFromSnapshotTestGA(
    create_test_base.InstancesCreateTestBase, parameterized.TestCase):
  """Test creation of VM instances with create disk(s)."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  @parameterized.parameters([('', 'my-backup'),
                             (('https://compute.googleapis.com/compute/'
                               '{}/projects/my-project/global/snapshots/'),
                              'my-backup')])
  def testCreateBootDiskWithSnapshotFlag(self, snapshot_path, snapshot_name):
    m = self.messages

    self.make_requests.side_effect = iter([
        [m.Zone(name='central2-a')],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    snapshot_arg = snapshot_path.format(self.api_version) + snapshot_name
    self.Run("""
        compute instances create instance-1
          --source-snapshot {}
          --zone central2-a
        """.format(snapshot_arg))

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
                              sourceSnapshot=(
                                  'https://compute.googleapis.com/compute/{0}/projects/'
                                  'my-project/global/snapshots/{1}'.format(
                                      self.api_version, snapshot_name)),),
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

  def testCreateBootDiskWithSnapshotAndImageFlagFails(self):
    with self.assertRaisesRegex(
        MockArgumentError,
        r'argument --image: At most one of --image \| --image-family \| '
        r'--source-snapshot may be specified.'):
      self.Run("""
          compute instances create vm
            --image=foo --source-snapshot=my-snapshot
          """)

  def testCreateDiskWithSnapshotProperty(self):
    msg = self.messages
    self.Run("""
        compute instances create hamlet
          --zone central2-a
          --create-disk source-snapshot=my-backup
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
                              sourceImage=self._default_image,),
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      msg.AttachedDisk(
                          autoDelete=True,
                          boot=False,
                          initializeParams=msg.AttachedDiskInitializeParams(
                              sourceSnapshot=(self.compute_uri +
                                              '/projects/my-project/global/'
                                              'snapshots/my-backup'),),
                          mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=create_test_base.DefaultMachineTypeOf(self.api),
                  metadata=msg.Metadata(),
                  name='hamlet',
                  networkInterfaces=[
                      msg.NetworkInterface(
                          accessConfigs=[
                              msg.AccessConfig(
                                  name='external-nat',
                                  type=self._one_to_one_nat)
                          ],
                          network=create_test_base.DefaultNetworkOf(self.api))
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

  def testCreateDiskSnapshotAndImagePropertyFails(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Must specify exactly one of \[image\], \[image-family\], or '
        r'\[source-snapshot\] for a \[--create-disk\]. '
        r'These fields are mutually exclusive.'):
      self.Run("""
          compute instances create vm
            --create-disk image=foo,source-snapshot=my-snapshot
          """)


class InstancesCreateDiskFromSnapshotTestBeta(
    InstancesCreateDiskFromSnapshotTestGA):
  """Test creation of VM instances with create disk(s)."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testCreateDiskWithAllProperties(self):
    m = self.messages

    self.Run('compute instances create hamlet '
             '  --zone central2-a --erase-windows-vss-signature'
             '  --create-disk name=disk-1,size=10GB,mode=ro,type=SSD,'
             'source-snapshot=my-snapshot,device-name=data,auto-delete=yes')

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  eraseWindowsVssSignature=True,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=False,
                          deviceName='data',
                          initializeParams=m.AttachedDiskInitializeParams(
                              diskName='disk-1',
                              diskSizeGb=10,
                              sourceSnapshot=(self.compute_uri +
                                              '/projects/my-project/global/'
                                              'snapshots/my-snapshot'),
                              diskType=(self.compute_uri +
                                        '/projects/my-project/zones/central2-a/'
                                        'diskTypes/SSD')),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=self._default_machine_type,
                  metadata=m.Metadata(),
                  name='hamlet',
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


class InstancesCreateDiskFromSnapshotTestAlpha(
    InstancesCreateDiskFromSnapshotTestBeta):
  """Tests creation of VM instances with create disk(s)."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def testCreateDiskSnapshotAndImagePropertyFails(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Must specify exactly one of \[image\], \[image-family\], '
        r'\[image-csek-required\], \[source-snapshot\], or '
        r'\[source-snapshot-csek-required\] for a \[--create-disk\]. '
        r'These fields are mutually exclusive.'):
      self.Run("""
          compute instances create vm
            --create-disk image=foo,source-snapshot=my-snapshot
          """)


if __name__ == '__main__':
  test_case.main()
