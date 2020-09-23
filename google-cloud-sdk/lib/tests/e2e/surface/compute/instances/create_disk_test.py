# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Integration tests for creating/using/deleting instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base
from tests.lib.surface.compute import utils


class InstancesCreateDiskTest(e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.replica_zone = 'us-central1-a'
    self.url = 'https://www.googleapis.com/compute/alpha/projects'

  def testInstanceCreationWithCreateDisk(self):
    self.GetInstanceName()
    self.Run(
        'compute instances create {0} '
        '--create-disk size=10GB,name={0}-3,mode=rw,'
        'device-name=data,auto-delete=yes,image-family={1},'
        'image-project=debian-cloud '
        '--create-disk size=10GB,name={0}-4,mode=rw,'
        'description=testDescription,device-name=data-2,auto-delete=no '
        '--zone {2}'.format(self.instance_name, utils.DEBIAN_IMAGE_FAMILY,
                            self.zone))
    self.Run('compute instances describe {0} --zone {1}'.format(
        self.instance_name, self.zone))
    self.AssertNewOutputContainsAll(
        ['deviceName: data', 'mode: READ_WRITE', 'deviceName: data-2'])
    self.Run('compute disks describe {0}-4 --zone {1}'.format(
        self.instance_name, self.zone))
    self.AssertNewOutputContains('description: testDescription')

  def testInstanceCreationWithCreationOfRegionalBootDisk(self):
    self.GetInstanceName()

    # Create a disk
    self.Run('compute disks create {0}-disk --zone=us-central1-f --size=200GB'
             .format(self.instance_name))
    # Create a snap shot from the above disk
    self.Run('compute disks snapshot {0}-disk --snapshot-names={0}-snapshot '
             '--zone=us-central1-f --storage-location=us-central1'.format(
                 self.instance_name))
    # Create on create with an REPD boot disk using the above snapshot
    self.Run(
        'compute instances create {0} '
        '--create-disk boot=yes,size=200GB,name={0}-repd,mode=rw,replica-zones={2},'
        'description=testDescription,device-name=data-2,auto-delete=no,'
        'source-snapshot={0}-snapshot '
        '--zone {1}'.format(self.instance_name, self.zone, self.replica_zone))

    self.Run('compute instances describe {0} --zone {1}'.format(
        self.instance_name, self.zone))
    self.AssertNewOutputNotContains('boot: false', reset=False)

    source_disk = '{0}/{1}/regions/{2}/disks/{3}-repd'.format(
        self.url, self.Project(), self.region, self.instance_name)

    self.AssertNewOutputContainsAll([
        'deviceName: data', 'mode: READ_WRITE', 'deviceName: data-2',
        'boot: true', source_disk
    ])

    self.Run('compute disks describe {0}-repd --region {1}'.format(
        self.instance_name, self.region))
    self.AssertNewOutputContainsAll([
        'description: testDescription', 'replicaZones:',
        '- {0}/{1}/zones/{2}'.format(self.url, self.Project(),
                                     self.replica_zone),
        '- {0}/{1}/zones/{2}'.format(self.url, self.Project(), self.zone)
    ])


if __name__ == '__main__':
  e2e_test_base.main()
