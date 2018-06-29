# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the instances set-disk-auto-delete subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class InstancesSetDiskAutoDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    deviceName='device-1',
                    source=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/us-central1-a/disks/disk-1')),
                messages.AttachedDisk(
                    deviceName='device-2',
                    source=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/us-central1-a/disks/disk-2')),
            ])],

        [],
    ])

  def testWithDeviceNameThatExists(self):
    self.Run("""
        compute instances set-disk-auto-delete
          instance-1
          --zone us-central1-a
          --device-name device-1
          --auto-delete
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central1-a',
              deviceName='device-1',
              autoDelete=True))],
    )

  def testWithDeviceNameThatExistsNoAutoDelete(self):
    self.Run("""
        compute instances set-disk-auto-delete
          instance-1
          --zone us-central1-a
          --device-name device-1
          --no-auto-delete
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central1-a',
              deviceName='device-1',
              autoDelete=False))],
    )

  def testWithDeviceNameThatDoesNotExist(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'No disk with device name \[device-3\] is attached to instance '
        r'\[instance-1\] in zone \[us-central1-a\].'):
      self.Run("""
        compute instances set-disk-auto-delete
          instance-1
          --auto-delete
          --device-name device-3
          --zone us-central1-a
        """)

  def testWithDiskThatExists(self):
    self.Run("""
        compute instances set-disk-auto-delete
          instance-1
          --zone us-central1-a
          --disk disk-1
          --auto-delete
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central1-a',
              deviceName='device-1',
              autoDelete=True))],
    )

  def testWithDiskThatDoesNotExist(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Disk \[disk-3\] is not attached to instance \[instance-1\] in zone '
        r'\[us-central1-a\].'):
      self.Run("""
        compute instances set-disk-auto-delete
          instance-1
          --auto-delete
          --disk disk-3
          --zone us-central1-a
        """)

  def testUriSupport(self):
    self.Run("""
        compute instances set-disk-auto-delete
          https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instances/instance-1
          --disk https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/disks/disk-1
          --auto-delete
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central1-a',
              deviceName='device-1',
              autoDelete=True))],
    )

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Instance(name='instance-1', zone='us-central1-a'),
        ],

        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    deviceName='device-1',
                    source=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/us-central1-a/disks/disk-1')),
                messages.AttachedDisk(
                    deviceName='device-2',
                    source=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/us-central1-a/disks/disk-2')),
            ])],

        [],
    ])

    self.Run("""
        compute instances set-disk-auto-delete
          instance-1
          --disk disk-1
          --auto-delete
        """)

    self.AssertErrContains(
        'No zone specified. Using zone [us-central1-a] '
        'for instance: [instance-1].')
    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance-1'),

        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central1-a',
              deviceName='device-1',
              autoDelete=True))],
    )


if __name__ == '__main__':
  test_case.main()
