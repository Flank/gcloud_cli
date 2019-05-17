# -*- coding: utf-8 -*- #
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
"""Tests for the instances attach-disk subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
import textwrap

from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)

  if api_version == 'v1':
    test_obj._instances = test_resources.INSTANCES_V1
  elif api_version == 'alpha':
    test_obj._instances = test_resources.INSTANCES_ALPHA
  elif api_version == 'beta':
    test_obj._instances = test_resources.INSTANCES_BETA
  else:
    raise ValueError('api_version must be \'v1\', \'alpha\', or \'beta\'.'
                     'Got [{0}].'.format(api_version))


class InstancesAttachDiskTestGA(test_base.BaseTest,
                                test_case.WithOutputCapture):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    SetUp(self, self.api_version)

  def testWithDefaults(self):
    self.make_requests.side_effect = iter([
        [self._instances[0]]
    ])
    msg = self.messages

    self.Run("""
        compute instances attach-disk instance-1
          --zone central2-a
          --disk disk-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'AttachDisk',
          msg.ComputeInstancesAttachDiskRequest(
              attachedDisk=msg.AttachedDisk(
                  mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                  source=(self.compute_uri + '/projects/'
                          'my-project/zones/central2-a/disks/disk-1'),
                  type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())

  def testYamlOutput(self):
    self.make_requests.side_effect = iter([
        [self._instances[0]]
    ])
    self.Run("""
        compute instances attach-disk instance-1
          --format yaml
          --zone central2-a
          --disk disk-1
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            machineType: https://www.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/machineTypes/n1-standard-1
            name: instance-1
            networkInterfaces:
            - accessConfigs:
              - natIP: 23.251.133.75
              networkIP: 10.0.0.1
            scheduling:
              automaticRestart: false
              onHostMaintenance: TERMINATE
              preemptible: false
            selfLink: {compute_uri}/projects/my-project/zones/zone-1/instances/instance-1
            status: RUNNING
            zone: https://www.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1
            """.format(compute_uri=self.compute_uri,
                       api_version=self.api_version)))

  def testJsonOutput(self):
    self.make_requests.side_effect = iter([
        [self._instances[0]]
    ])
    self.Run("""
        compute instances attach-disk instance-1
          --format json
          --zone central2-a
          --disk disk-1
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            [
              {{
                "machineType": "https://www.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/machineTypes/n1-standard-1",
                "name": "instance-1",
                "networkInterfaces": [
                  {{
                    "accessConfigs": [
                      {{
                        "natIP": "23.251.133.75"
                      }}
                    ],
                    "networkIP": "10.0.0.1"
                  }}
                ],
                "scheduling": {{
                  "automaticRestart": false,
                  "onHostMaintenance": "TERMINATE",
                  "preemptible": false
                }},
                "selfLink": "{compute_uri}/projects/my-project/zones/zone-1/instances/instance-1",
                "status": "RUNNING",
                "zone": "https://www.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1"
              }}
            ]
            """.format(compute_uri=self.compute_uri,
                       api_version=self.api_version)))

  def testTextOutput(self):
    self.make_requests.side_effect = iter([
        [self._instances[0]]
    ])
    self.Run("""
        compute instances attach-disk instance-1
          --format text
          --zone central2-a
          --disk disk-1
        """)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            machineType:                                 https://www.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/machineTypes/n1-standard-1
            name:                                        instance-1
            networkInterfaces[0].accessConfigs[0].natIP: 23.251.133.75
            networkInterfaces[0].networkIP:              10.0.0.1
            scheduling.automaticRestart:                 False
            scheduling.onHostMaintenance:                TERMINATE
            scheduling.preemptible:                      False
            selfLink:                                    {compute_uri}/projects/my-project/zones/zone-1/instances/instance-1
            status:                                      RUNNING
            zone:                                        https://www.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1
            """.format(compute_uri=self.compute_uri,
                       api_version=self.api_version)))

  def testWithDeviceName(self):
    msg = self.messages
    self.Run("""
        compute instances attach-disk instance-1
          --zone central2-a
          --disk disk-1
          --device-name my-device
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'AttachDisk',
          msg.ComputeInstancesAttachDiskRequest(
              attachedDisk=msg.AttachedDisk(
                  deviceName='my-device',
                  mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                  source=(self.compute_uri + '/projects/'
                          'my-project/zones/central2-a/disks/disk-1'),
                  type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testWithReadOnly(self):
    msg = self.messages
    self.Run("""
        compute instances attach-disk instance-1
          --zone central2-a
          --disk disk-1
          --mode ro
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'AttachDisk',
          msg.ComputeInstancesAttachDiskRequest(
              attachedDisk=self.messages.AttachedDisk(
                  mode=msg.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
                  source=(self.compute_uri + '/projects/'
                          'my-project/zones/central2-a/disks/disk-1'),
                  type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    msg = self.messages
    self.make_requests.side_effect = iter([
        [
            msg.Instance(name='instance-1', zone='zone-1'),
            msg.Instance(name='instance-1', zone='zone-2'),
            msg.Instance(name='instance-1', zone='zone-3'),
        ],

        [],
    ])
    self.WriteInput('1\n')

    self.Run("""
        compute instances attach-disk instance-1
          --disk disk-1
        """)

    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance-1'),

        [(self.compute.instances,
          'AttachDisk',
          msg.ComputeInstancesAttachDiskRequest(
              attachedDisk=msg.AttachedDisk(
                  mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                  source=(self.compute_uri + '/projects/'
                          'my-project/zones/zone-1/disks/disk-1'),
                  type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )
    self.AssertErrContains('instance-1')
    self.AssertErrContains('zone-1')
    self.AssertErrContains('zone-2')
    self.AssertErrContains('zone-3')

  def testUriSupport(self):
    msg = self.messages
    self.Run("""
      compute instances attach-disk
        {compute_uri}/projects/my-project/zones/central2-a/instances/instance-1
        --disk {compute_uri}/projects/my-project/zones/central2-a/disks/disk-1
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.instances,
          'AttachDisk',
          msg.ComputeInstancesAttachDiskRequest(
              attachedDisk=msg.AttachedDisk(
                  mode=msg.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                  source=(self.compute_uri + '/projects/'
                          'my-project/zones/central2-a/disks/disk-1'),
                  type=msg.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

  def testWithKeyFile(self):
    self.make_requests.side_effect = iter([
        [self._instances[0]]
    ])
    csek_key_file = self.WriteKeyFile()

    self.Run("""
        compute instances attach-disk instance-1
          --zone central2-a
          --disk hamlet
          --csek-key-file {keyfile}
        """.format(keyfile=csek_key_file))

    msgs = self.messages  # avoid long lines below

    self.CheckRequests(
        [(self.compute.instances,
          'AttachDisk',
          msgs.ComputeInstancesAttachDiskRequest(
              attachedDisk=msgs.AttachedDisk(
                  mode=msgs.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                  source=(self.compute_uri + '/projects/'
                          'my-project/zones/central2-a/disks/hamlet'),
                  type=(msgs.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                  diskEncryptionKey=msgs.CustomerEncryptionKey(
                      rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=')),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())

  def testWithKeyFromStdin(self):
    self.make_requests.side_effect = [
        [self._instances[0]]
    ]
    self.WriteInput(self.GetKeyFileContent())

    self.Run("""
        compute instances attach-disk instance-1
          --zone central2-a
          --disk hamlet
          --csek-key-file -
        """)

    msgs = self.messages  # avoid long lines below

    self.CheckRequests(
        [(self.compute.instances,
          'AttachDisk',
          msgs.ComputeInstancesAttachDiskRequest(
              attachedDisk=msgs.AttachedDisk(
                  mode=msgs.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                  source=(self.compute_uri + '/projects/'
                          'my-project/zones/central2-a/disks/hamlet'),
                  type=(msgs.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                  diskEncryptionKey=msgs.CustomerEncryptionKey(
                      rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=')),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())

  def testWithKeyFileRsaWrapped(self):
    csek_key_file = self.WriteKeyFile(include_rsa_encrypted=True)

    with self.assertRaisesRegex(csek_utils.BadKeyTypeException, re.escape(
        'Invalid key type [rsa-encrypted]: this feature is only allowed in the '
        'alpha and beta versions of this command.')):
      self.Run("""
          compute instances attach-disk instance-1
            --zone central2-a
            --disk hamlet
            --csek-key-file {keyfile}
          """.format(keyfile=csek_key_file))

  def testAttachBootDisk(self):
    self.Run("""
        compute instances attach-disk instance-1
          --zone central2-a
          --disk disk-1
          --boot
        """)

    msgs = self.messages  # avoid long lines below

    self.CheckRequests(
        [(self.compute.instances,
          'AttachDisk',
          msgs.ComputeInstancesAttachDiskRequest(
              attachedDisk=msgs.AttachedDisk(
                  mode=msgs.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                  source=(self.compute_uri + '/projects/'
                          'my-project/zones/central2-a/disks/disk-1'),
                  type=msgs.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                  boot=True),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())

  def testZonalDiskForceAttach(self):
    self.Run("""
      compute instances attach-disk instance-1
        --zone central2-a
        --disk wrappedkeydisk
        --force-attach
      """)

    msgs = self.messages  # avoid long lines below

    self.CheckRequests(
        [(self.compute.instances, 'AttachDisk',
          msgs.ComputeInstancesAttachDiskRequest(
              attachedDisk=msgs.AttachedDisk(
                  mode=msgs.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                  source=(self.compute_uri + '/projects/my-project/zones/'
                          'central2-a/disks/wrappedkeydisk'),
                  type=(msgs.AttachedDisk.TypeValueValuesEnum.PERSISTENT)),
              forceAttach=True,
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],)

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())

  def testRegionalDisk(self):
    self.Run("""
        compute instances attach-disk instance-1
          --zone central2-a
          --disk wrappedkeydisk
          --disk-scope regional
        """)

    msgs = self.messages  # avoid long lines below

    self.CheckRequests(
        [(self.compute.instances,
          'AttachDisk',
          msgs.ComputeInstancesAttachDiskRequest(
              attachedDisk=msgs.AttachedDisk(
                  mode=msgs.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                  source=(self.compute_uri + '/projects/my-project/regions/'
                          'central2/disks/wrappedkeydisk'),
                  type=(msgs.AttachedDisk.TypeValueValuesEnum.PERSISTENT)),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())

  def testRegionalDiskForceAttach(self):
    self.Run("""
        compute instances attach-disk instance-1
          --zone central2-a
          --disk wrappedkeydisk
          --disk-scope regional
          --force-attach
        """)

    msgs = self.messages  # avoid long lines below

    self.CheckRequests(
        [(self.compute.instances,
          'AttachDisk',
          msgs.ComputeInstancesAttachDiskRequest(
              attachedDisk=msgs.AttachedDisk(
                  mode=msgs.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                  source=(self.compute_uri + '/projects/my-project/regions/'
                          'central2/disks/wrappedkeydisk'),
                  type=(msgs.AttachedDisk.TypeValueValuesEnum.PERSISTENT)),
              forceAttach=True,
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],
    )

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())


class InstancesAttachDiskTestBeta(InstancesAttachDiskTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testWithKeyFileRsaWrapped(self):
    csek_key_file = self.WriteKeyFile(include_rsa_encrypted=True)

    self.Run("""
        compute instances attach-disk instance-1
          --zone central2-a
          --disk wrappedkeydisk
          --csek-key-file {keyfile}
        """.format(keyfile=csek_key_file))

    msgs = self.messages  # avoid long lines below

    self.CheckRequests(
        [(self.compute.instances, 'AttachDisk',
          msgs.ComputeInstancesAttachDiskRequest(
              attachedDisk=msgs.AttachedDisk(
                  mode=msgs.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                  source=(self.compute_uri + '/projects/'
                          'my-project/zones/central2-a/disks/wrappedkeydisk'),
                  type=(msgs.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                  diskEncryptionKey=msgs.CustomerEncryptionKey(
                      rsaEncryptedKey=test_base.SAMPLE_WRAPPED_CSEK_KEY)),
              instance='instance-1',
              project='my-project',
              zone='central2-a'))],)

    # By default, the resource should not be displayed
    self.assertFalse(self.GetOutput())


class InstancesAttachDiskTestAlpha(InstancesAttachDiskTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
