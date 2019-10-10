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
"""Tests for the instances delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


_INSTANCE_DELETE_PROMPT = """\
The following instances will be deleted. Any attached disks configured to be \
auto-deleted will be deleted unless they are attached to any other instances \
or the `--keep-disks` flag is given and specifies them for keeping. \
Deleting a disk is irreversible and any data on the disk will be lost."""


class InstancesDeleteTest(test_base.BaseTest,
                          completer_test_base.CompleterBase):

  def testWithSingleInstance(self):
    self.make_requests.side_effect = iter([
        [],
    ])
    properties.VALUES.core.disable_prompts.Set(True)

    self.Run("""
        compute instances delete
          instance-1
          --zone us-central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central2-a'))],
    )

  def testWithSingleInstanceNoOutput(self):
    self.make_requests.side_effect = iter([
        [],
    ])
    properties.VALUES.core.disable_prompts.Set(True)

    self.Run("""
        compute instances delete
          instance-1
          --zone us-central2-a
          --no-user-output-enabled
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central2-a'))],
    )

    self.AssertErrNotContains('instance-1')
    self.AssertOutputNotContains('instance-1')

  def testWithManyInstances(self):
    self.make_requests.side_effect = iter([
        [],
    ])
    properties.VALUES.core.disable_prompts.Set(True)

    self.Run("""
        compute instances delete
           instance-1 instance-2 instance-3
          --zone us-central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='us-central2-a')),

         (self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-2',
              project='my-project',
              zone='us-central2-a')),

         (self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-3',
              project='my-project',
              zone='us-central2-a'))],
    )

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Instance(name='instance-1', zone='zone-1'),
        ],

        [],
    ])
    self.WriteInput('y\n')

    self.Run("""
        compute instances delete
          instance-1
        """)

    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance-1'),

        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )
    self.AssertErrContains(
        'No zone specified. Using zone [zone-1] for instance: [instance-1].')
    self.AssertErrContains(
        _INSTANCE_DELETE_PROMPT + r'\n - [instance-1] in [zone-1]')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testUriSupport(self):
    self.make_requests.side_effect = iter([
        [],
    ])
    properties.VALUES.core.disable_prompts.Set(True)

    self.Run("""
        compute instances delete
          https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
          instance-2
          --zone https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-2
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1')),

         (self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-2',
              project='my-project',
              zone='zone-2'))],
    )

  def testPromptingWithYes(self):
    self.make_requests.side_effect = iter([
        [],
    ])
    self.WriteInput('y\n')

    self.Run("""
        compute instances delete
          instance-1 instance-2 instance-3
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1')),

         (self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-2',
              project='my-project',
              zone='zone-1')),

         (self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-3',
              project='my-project',
              zone='zone-1'))],
    )
    self.AssertErrContains(
        _INSTANCE_DELETE_PROMPT + r'\n - [instance-1] in [zone-1]'
                                  r'\n - [instance-2] in [zone-1]'
                                  r'\n - [instance-3] in [zone-1]')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testPromptingWithNo(self):
    self.make_requests.side_effect = iter([
        [],
    ])
    self.WriteInput('n\n')

    with self.AssertRaisesToolExceptionRegexp(
        'Deletion aborted by user.'):
      self.Run("""
          compute instances delete
            instance-1 instance-2 instance-3
            --zone zone-1
          """)

    self.CheckRequests()
    self.AssertErrContains(
        _INSTANCE_DELETE_PROMPT + r'\n - [instance-1] in [zone-1]'
                                  r'\n - [instance-2] in [zone-1]'
                                  r'\n - [instance-3] in [zone-1]')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testKeepDisksAndDeleteDisksMutualExclusion(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --delete-disks: At most one of --delete-disks | '
        '--keep-disks may be specified.'):
      self.Run("""
          compute instances delete
            instance-1
            --keep-disks all
            --delete-disks boot
          """)
    self.CheckRequests()

  def testWithDeleteBootDisksAndBootDiskAutoDeleteSetToFalse(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))],
        [],
        [],
    ])

    self.Run("""
        compute instances delete
          instance-1
          --delete-disks boot
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=True,
              deviceName='persistent-disk-0',
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testWithDeleteBootDisksAndBootDiskAutoDeleteSetToTrue(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))],
        [],
    ])

    self.Run("""
        compute instances delete
          instance-1
          --delete-disks boot
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testWithKeepBootDisksAndBootDiskAutoDeleteSetToFalse(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))],
        [],
    ])

    self.Run("""
        compute instances delete
          instance-1
          --keep-disks boot
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testWithKeepBootDisksAndBootDiskAutoDeleteSetToTrue(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))],
        [],
        [],
    ])

    self.Run("""
        compute instances delete
          instance-1
          --keep-disks boot
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=False,
              deviceName='persistent-disk-0',
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testWithDeleteDataDisksAndDataDiskAutoDeleteSetToFalse(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='persistent-disk-1',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-1')),
            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))],
        [],
        [],
    ])

    self.Run("""
        compute instances delete
          instance-1
          --delete-disks data
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=True,
              deviceName='persistent-disk-1',
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testWithDeleteDataDisksAndDataDiskAutoDeleteSetToTrue(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=False,
                    deviceName='persistent-disk-1',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-1')),
            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))],
        [],
    ])

    self.Run("""
        compute instances delete
          instance-1
          --delete-disks data
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testWithKeepDataDisksAndDataDiskAutoDeleteSetToFalse(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='persistent-disk-1',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-1')),
            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))],
        [],
    ])

    self.Run("""
        compute instances delete
          instance-1
          --keep-disks data
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testWithKeepDataDisksAndDataDiskAutoDeleteSetToTrue(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=False,
                    deviceName='persistent-disk-1',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-1')),
            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))],
        [],
        [],
    ])

    self.Run("""
        compute instances delete
          instance-1
          --keep-disks data
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=False,
              deviceName='persistent-disk-1',
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testWithKeepAllDisksAndBootDiskAutoDeleteSetToTrue(self):
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=False,
                    deviceName='persistent-disk-1',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-1')),
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='persistent-disk-2',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-2')),
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=False,
                    deviceName='persistent-disk-3',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-3')),

            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))],
        [],
        [],
    ])

    self.Run("""
        compute instances delete
          instance-1
          --keep-disks all
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=False,
              deviceName='persistent-disk-0',
              instance='instance-1',
              project='my-project',
              zone='zone-1')),
         (self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=False,
              deviceName='persistent-disk-1',
              instance='instance-1',
              project='my-project',
              zone='zone-1')),
         (self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=False,
              deviceName='persistent-disk-3',
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )
    # Don't display the warning about disks if --keep-disks=all
    self.AssertErrContains(
        r'The following instances will be deleted.\n'
        r' - [instance-1] in [zone-1]')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testWithKeepAllDisksAndBootDiskAutoDeleteSetToFalse(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=False,
                    deviceName='persistent-disk-1',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-1')),
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='persistent-disk-2',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-2')),
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=False,
                    deviceName='persistent-disk-3',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-3')),

            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))],
        [],
        [],
    ])

    self.Run("""
        compute instances delete
          instance-1
          --keep-disks all
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=False,
              deviceName='persistent-disk-1',
              instance='instance-1',
              project='my-project',
              zone='zone-1')),
         (self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=False,
              deviceName='persistent-disk-3',
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testWithDeleteAllDisksAndBootDiskAutoDeleteSetToTrue(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='persistent-disk-1',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-1')),
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=False,
                    deviceName='persistent-disk-2',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-2')),
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='persistent-disk-3',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-3')),

            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))],
        [],
        [],
    ])

    self.Run("""
        compute instances delete
          instance-1
          --delete-disks all
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=True,
              deviceName='persistent-disk-1',
              instance='instance-1',
              project='my-project',
              zone='zone-1')),
         (self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=True,
              deviceName='persistent-disk-3',
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testWithDeleteAllDisksAndBootDiskAutoDeleteSetToFalse(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='persistent-disk-1',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-1')),
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=False,
                    deviceName='persistent-disk-2',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-2')),
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='persistent-disk-3',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-3')),

            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))],
        [],
        [],
    ])

    self.Run("""
        compute instances delete
          instance-1
          --delete-disks all
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=True,
              deviceName='persistent-disk-0',
              instance='instance-1',
              project='my-project',
              zone='zone-1')),
         (self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=True,
              deviceName='persistent-disk-1',
              instance='instance-1',
              project='my-project',
              zone='zone-1')),
         (self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=True,
              deviceName='persistent-disk-3',
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testPromptingWhenDisksWithFalseAutoDeletesWillBeDeleted(self):
    self.WriteInput('y\ny\n')
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='persistent-disk-1',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-1')),
                messages.AttachedDisk(
                    autoDelete=True,
                    boot=False,
                    deviceName='persistent-disk-2',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-2')),
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=False,
                    deviceName='persistent-disk-3',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/data-disk-3')),

            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))],
        [],
        [],
    ])

    self.Run("""
        compute instances delete
          instance-1
          --delete-disks all
          --zone zone-1
        """)

    self.AssertErrContains(
        _INSTANCE_DELETE_PROMPT + r'\n - [instance-1] in [zone-1]')
    self.AssertErrContains('PROMPT_CONTINUE')

    self.AssertErrContains(
        r'The following disks are not configured to be automatically deleted '
        r'with instance deletion, but they will be deleted as a result of this '
        r'operation if they are not attached to any other instances:\n'
        r' - [data-disk-1] in [zone-1]\n'
        r' - [data-disk-3] in [zone-1]\n'
        r' - [instance-1] in [zone-1]')
    self.AssertErrContains('PROMPT_CONTINUE')

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=True,
              deviceName='persistent-disk-0',
              instance='instance-1',
              project='my-project',
              zone='zone-1')),
         (self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=True,
              deviceName='persistent-disk-1',
              instance='instance-1',
              project='my-project',
              zone='zone-1')),
         (self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=True,
              deviceName='persistent-disk-3',
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testAutoDeleteModificationWithNonExistentInstance(self):
    properties.VALUES.core.disable_prompts.Set(True)

    def MakeRequests(*_, **kwargs):
      if False:  # pylint: disable=using-constant-test, generator mock
        yield
      kwargs['errors'].append((404, 'Not Found'))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Failed to fetch some instances:
         - Not Found
        """)):
      self.Run("""
          compute instances delete
            instance-1
            --delete-disks all
            --zone zone-1
          """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testAutoDeleteModificationWithFailedSetAutoDeleteRequest(self):
    properties.VALUES.core.disable_prompts.Set(True)

    def MakeRequests(requests, *_, **kwargs):
      _, method, _ = requests[0]

      if method == 'Get':
        yield messages.Instance(
            name='instance-1',
            disks=[
                messages.AttachedDisk(
                    autoDelete=False,
                    boot=True,
                    deviceName='persistent-disk-0',
                    source=('https://compute.googleapis.com/compute/v1/projects/'
                            'my-project/zones/zone-1/disks/instance-1')),
            ],
            zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1'))

      elif method == 'SetDiskAutoDelete':
        kwargs['errors'].append((500, 'Server Error'))

      else:
        self.fail('Did not expect a call on method [{0}].'.format(method))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Some requests to change disk auto-delete behavior failed:
         - Server Error
        """)):
      self.Run("""
          compute instances delete
            instance-1
            --delete-disks all
            --zone zone-1
          """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute_v1.instances,
          'SetDiskAutoDelete',
          messages.ComputeInstancesSetDiskAutoDeleteRequest(
              autoDelete=True,
              deviceName='persistent-disk-0',
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testDeletionWithError(self):
    properties.VALUES.core.disable_prompts.Set(True)

    def MakeRequests(*_, **kwargs):
      if False:  # pylint: disable=using-constant-test, generator mock
        yield
      print('eee')
      kwargs['errors'].append((404, 'Not Found'))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Could not fetch resource:
         - Not Found
        """)):
      self.Run("""
          compute instances delete
            instance-1
            --zone zone-1
          """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Delete',
          messages.ComputeInstancesDeleteRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

  def testDeleteCompleter(self):
    self.AssertCommandArgCompleter(
        command='compute instances delete',
        arg='instance_names',
        module_path='command_lib.compute.completers.InstancesCompleter')


if __name__ == '__main__':
  test_case.main()
