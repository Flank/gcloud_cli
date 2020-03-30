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
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.instance_templates import create_test_base


class InstanceTemplatesCreateTest(
    create_test_base.InstanceTemplatesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testDefaultOptions(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
        """)

    template = self._MakeInstanceTemplate()

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testPerformanceWarningWithStandardPd(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --boot-disk-size 199GB
        """)

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                diskSizeGb=199,
                sourceImage=self._default_image,
            ),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )
    self.AssertErrContains(
        'WARNING: You have selected a disk size of under [200GB]. This may '
        'result in poor I/O performance. For more information, see: '
        'https://developers.google.com/compute/docs/disks#performance.')

  def testCanIpForward(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --can-ip-forward
        """)

    template = self._MakeInstanceTemplate(canIpForward=True)

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithDescription(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --description "Hakuna Matata"
        """)

    template = self._MakeInstanceTemplate(description='Hakuna Matata')

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithNoRestartOnFailure(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --no-restart-on-failure
        """)

    template = self._MakeInstanceTemplate(
        scheduling=m.Scheduling(automaticRestart=False))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithMaintenancePolicy(self):
    self.templateTestWithMaintenancePolicy("""
        compute instance-templates create template-1
          --maintenance-policy TERMINATE
        """)

  def testWithMaintenancePolicyLowerCase(self):
    self.templateTestWithMaintenancePolicy("""
        compute instance-templates create template-1
          --maintenance-policy terminate
        """)

  def templateTestWithMaintenancePolicy(self, cmd):
    m = self.messages
    self.Run(cmd)

    template = self._MakeInstanceTemplate(
        scheduling=m.Scheduling(
            automaticRestart=True,
            onHostMaintenance=(
                m.Scheduling.OnHostMaintenanceValueValuesEnum.TERMINATE)))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithTags(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --tags a,b,c,d
        """)

    template = self._MakeInstanceTemplate(
        tags=m.Tags(items=['a', 'b', 'c', 'd']))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testDefaultOutput(self):
    m = self.messages
    self.make_requests.side_effect = iter([[
        m.Image(
            name='debian-9-stretch-v20170619', selfLink=self._default_image),
    ], [self._instance_templates[0]]])

    self.Run("""
        compute instance-templates create instance-template-1
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                MACHINE_TYPE  PREEMPTIBLE CREATION_TIMESTAMP
            instance-template-1 n1-standard-1             2013-09-06T17:54:10.636-07:00
            """),
        normalize_space=True)

  def testJsonOutput(self):
    m = self.messages
    self.make_requests.side_effect = iter([[
        m.Image(
            name='debian-9-stretch-v20170619', selfLink=self._default_image),
    ], [self._instance_templates[0]]])

    self.Run("""
        compute instance-templates create template-1
          --format json
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            [
              {{
                "creationTimestamp": "2013-09-06T17:54:10.636-07:00",
                "name": "instance-template-1",
                "properties": {{
                  "disks": [
                    {{
                      "autoDelete": true,
                      "boot": true,
                      "deviceName": "device-1",
                      "mode": "READ_WRITE",
                      "source": "disk-1",
                      "type": "PERSISTENT"
                    }}
                  ],
                  "machineType": "n1-standard-1",
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
                  }}
                }},
                "selfLink": "{compute}/projects/my-project/global/instanceTemplates/instance-template-1"
               }}
            ]
            """.format(compute=self.compute_uri)),
        normalize_space=True)

  def testTextOutput(self):
    m = self.messages
    self.make_requests.side_effect = iter([[
        m.Image(
            name='debian-9-stretch-v20170619', selfLink=self._default_image),
    ], [self._instance_templates[0]]])

    self.Run("""
        compute instance-templates create template-1
          --format text
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            ---
            creationTimestamp:                                      2013-09-06T17:54:10.636-07:00
            name:                                                   instance-template-1
            properties.disks[0].autoDelete:                         True
            properties.disks[0].boot:                               True
            properties.disks[0].deviceName:                         device-1
            properties.disks[0].mode:                               READ_WRITE
            properties.disks[0].source:                             disk-1
            properties.disks[0].type:                               PERSISTENT
            properties.machineType:                                 n1-standard-1
            properties.networkInterfaces[0].accessConfigs[0].natIP: 23.251.133.75
            properties.networkInterfaces[0].networkIP:              10.0.0.1
            properties.scheduling.automaticRestart:                 False
            properties.scheduling.onHostMaintenance:                TERMINATE
            properties.scheduling.preemptible:                      False
            selfLink:                                               {compute}/projects/my-project/global/instanceTemplates/instance-template-1
            """.format(compute=self.compute_uri)))

  def testYamlOutput(self):
    m = self.messages
    self.make_requests.side_effect = iter([[
        m.Image(
            name='debian-9-stretch-v20170619', selfLink=self._default_image),
    ], [self._instance_templates[0]]])

    self.Run("""
        compute instance-templates create template-1
          --format yaml
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            ---
            creationTimestamp: '2013-09-06T17:54:10.636-07:00'
            name: instance-template-1
            properties:
              disks:
              - autoDelete: true
                boot: true
                deviceName: device-1
                mode: READ_WRITE
                source: disk-1
                type: PERSISTENT
              machineType: n1-standard-1
              networkInterfaces:
              - accessConfigs:
                - natIP: 23.251.133.75
                networkIP: 10.0.0.1
              scheduling:
                automaticRestart: false
                onHostMaintenance: TERMINATE
                preemptible: false
            selfLink: {compute}/projects/my-project/global/instanceTemplates/instance-template-1
            """.format(compute=self.compute_uri)))

  def testFlagsWithUri(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='my-image',
                selfLink=('{compute}/projects/my-project/global/images/'
                          'my-image'.format(compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --boot-disk-type {compute}/projects/my-project/zones/central1-a/diskTypes/pd-ssd
          --disk name={compute}/projects/my-project/zones/central1-a/disks/disk-1
          --machine-type {compute}/projects/my-project/zones/central1-a/machineTypes/n2-standard-1
          --network {compute}/projects/my-project/global/networks/some-other-network
          --image {compute}/projects/my-project/global/images/my-image
        """.format(compute=self.compute_uri))

    template = self._MakeInstanceTemplate(
        disks=[
            m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=('{compute}/'
                                 'projects/my-project/global/images/'
                                 'my-image'.format(compute=self.compute_uri)),
                    diskType=('{compute}/'
                              'projects/my-project/zones/central1-a/diskTypes/'
                              'pd-ssd'.format(compute=self.compute_uri)),
                ),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
            m.AttachedDisk(
                autoDelete=False,
                boot=False,
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                source=('{compute}/'
                        'projects/my-project/zones/central1-a/disks/'
                        'disk-1'.format(compute=self.compute_uri))),
        ],
        machineType=('{compute}/projects/'
                     'my-project/zones/central1-a/machineTypes/'
                     'n2-standard-1'.format(compute=self.compute_uri)),
        networkInterfaces=[
            m.NetworkInterface(
                accessConfigs=[self._default_access_config],
                network=('{compute}/projects/my-project/global/networks/'
                         'some-other-network'.format(compute=self.compute_uri)))
        ],
    )

    self.CheckRequests(
        [(self.compute.images, 'Get',
          m.ComputeImagesGetRequest(image='my-image', project='my-project'))],
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testPreemptible(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1 --preemptible
        """)

    template = self._MakeInstanceTemplate(
        scheduling=m.Scheduling(automaticRestart=False, preemptible=True),)

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )


class InstanceTemplatesCreateTestBeta(InstanceTemplatesCreateTest,
                                      parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstanceTemplatesCreateTestAlpha(InstanceTemplatesCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def testWithOnHostMaintenance(self):
    self.templateTestWithMaintenancePolicy("""
        compute instance-templates create template-1
          --on-host-maintenance TERMINATE
        """)

  def testWithOnHostMaintenanceLowerCase(self):
    self.templateTestWithMaintenancePolicy("""
        compute instance-templates create template-1
          --on-host-maintenance terminate
        """)

  def testMaintenancePolicyDeprecation(self):
    self.templateTestWithMaintenancePolicy("""
        compute instance-templates create template-1
          --maintenance-policy TERMINATE
        """)
    self.AssertErrContains(
        'WARNING: The --maintenance-policy flag is now deprecated. '
        'Please use `--on-host-maintenance` instead')


if __name__ == '__main__':
  test_case.main()
