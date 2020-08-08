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
"""Tests for the instances set-disk-auto-delete subcommand."""

from __future__ import absolute_import
from __future__ import division
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
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/us-central1-a/disks/disk-1'),
                    autoDelete=False),
                messages.AttachedDisk(
                    deviceName='device-2',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/us-central1-a/disks/disk-2')),
                messages.AttachedDisk(
                    deviceName='device-3',
                    source=('projects/my-project/regions/us-central1/disks/'
                            'disk-2')),
                messages.AttachedDisk(
                    deviceName='device-4',
                    source=('projects/my-project/zones/us-central1-a/disks/'
                            'disk-4')),
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
          --device-name device-2
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
              deviceName='device-2',
              autoDelete=False))],
    )

  def testWithDeviceNameThatExistsNoChange(self):
    self.Run("""
        compute instances set-disk-auto-delete
          instance-1
          --zone us-central1-a
          --device-name device-1
          --no-auto-delete
        """)

    self.AssertErrContains(
        'No change requested; skipping update for [instance-1].')

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central1-a'))],
    )

  def testWithDeviceNameThatDoesNotExist(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'No disk with device name \[device-na\] is attached to instance '
        r'\[instance-1\] in zone \[us-central1-a\].'):
      self.Run("""
        compute instances set-disk-auto-delete
          instance-1
          --auto-delete
          --device-name device-na
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

  def testWithDiskThatExistsNoChange(self):
    self.Run("""
        compute instances set-disk-auto-delete
          instance-1
          --zone us-central1-a
          --disk disk-1
          --no-auto-delete
        """)

    self.AssertErrContains(
        'No change requested; skipping update for [instance-1].')

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central1-a'))],
    )

  def testWithDiskThatDoesNotExist(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Disk \[disk-na\] is not attached to instance \[instance-1\] in zone '
        r'\[us-central1-a\].'):
      self.Run("""
        compute instances set-disk-auto-delete
          instance-1
          --auto-delete
          --disk disk-na
          --zone us-central1-a
        """)

  def testWithAmbiguousDisk(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('1\n')
    self.Run("""
        compute instances set-disk-auto-delete
          instance-1
          --auto-delete
          --disk disk-2
          --zone us-central1-a
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
              deviceName='device-2',
              autoDelete=True))],
    )

  def testWithAmbiguousDiskNoSelection(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Found multiple disks matching \[disk-2\] attached to instance '
        r'\[instance-1\] in zone \[us-central1-a\].'):
      self.Run("""
          compute instances set-disk-auto-delete
            instance-1
            --auto-delete
            --disk disk-2
            --zone us-central1-a
          """)

  def testWithRegionalDisk(self):
    self.Run("""
        compute instances set-disk-auto-delete
          instance-1
          --auto-delete
          --disk https://compute.googleapis.com/compute/v1/projects/my-project/regions/us-central1/disks/disk-2
          --zone us-central1-a
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
              deviceName='device-3',
              autoDelete=True))],
    )

  def testWithPartialRegionalDisk(self):
    self.Run("""
        compute instances set-disk-auto-delete
          instance-1
          --auto-delete
          --disk disk-4
          --zone us-central1-a
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
              deviceName='device-4',
              autoDelete=True))],
    )

  def testUriSupport(self):
    self.Run("""
        compute instances set-disk-auto-delete
          https://compute.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instances/instance-1
          --disk https://compute.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/disks/disk-1
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
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/us-central1-a/disks/disk-1')),
                messages.AttachedDisk(
                    deviceName='device-2',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
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
