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
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateGeneralTest(create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testDefaultOptions(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
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
                          sourceImage=self._default_image,
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

    self.AssertOutputNotContains('Please use --image-family')

  def testUserOutputDisabled(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --zone central2-a --no-user-output-enabled
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
                          sourceImage=self._default_image,
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

    self.AssertErrNotContains('instance-1')
    self.AssertOutputNotContains('instance-1')

  def testCanIpForward(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --can-ip-forward
          --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=True,
                  deletionProtection=False,
                  disks=[m.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      initializeParams=m.AttachedDiskInitializeParams(
                          sourceImage=self._default_image,
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

  def testWithDescription(self):
    m = self.messages
    self.Run("""
        compute instances create instance-1
          --description "My Very Excellent Mother Just Served Us Nine Pizzas"
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
                          sourceImage=self._default_image,
                      ),
                      mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                      type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)],
                  description=(
                      'My Very Excellent Mother Just Served Us Nine Pizzas'),
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

  def testWithInvalidServiceAccount(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--service-account]: Invalid format: expected '
        r'default or user@domain\.com, received user@google.com='
        r'https://www\.googleapis\.com/auth/trace\.append'
    ):
      self.Run("""
          compute instances create instance-1
            --service-account user@google.com=https://www.googleapis.com/auth/trace.append
            --zone central2-a
          """)

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request)

  def testWithNoRestartOnFailure(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --no-restart-on-failure
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
                          sourceImage=self._default_image,
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
                      automaticRestart=False),
              ),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testWithTags(self):
    m = self.messages

    self.Run("""
        compute instances create instance-1
          --tags a,b,c,d
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
                          sourceImage=self._default_image,
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
                  tags=m.Tags(
                      items=['a', 'b', 'c', 'd'])),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testDefaultOutput(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='zone-1')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        self._instances
    ])

    self.Run("""
        compute instances create instance-1 instance-2 instance-3 --zone zone-1
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       ZONE   MACHINE_TYPE  PREEMPTIBLE INTERNAL_IP EXTERNAL_IP   STATUS
            instance-1 zone-1 n1-standard-1             10.0.0.1    23.251.133.75 RUNNING
            instance-2 zone-1 n1-standard-1             10.0.0.2    23.251.133.74 RUNNING
            instance-3 zone-1 n1-standard-2             10.0.0.3    23.251.133.76 RUNNING
            """), normalize_space=True)

  def testOutput(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='zone-1')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        self._instances
    ])

    self.Run("""
        compute instances create instance-1 instance-2 instance-3
          --format json
          --zone zone-1
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            [
              {{
                "machineType": "https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/machineTypes/n1-standard-1",
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
                "zone": "https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1"
              }},
              {{
                "machineType": "https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/machineTypes/n1-standard-1",
                "name": "instance-2",
                "networkInterfaces": [
                  {{
                    "accessConfigs": [
                      {{
                        "natIP": "23.251.133.74"
                      }}
                    ],
                    "networkIP": "10.0.0.2"
                  }}
                ],
                "scheduling": {{
                  "automaticRestart": false,
                  "onHostMaintenance": "TERMINATE",
                  "preemptible": false
                }},
                "selfLink": "{compute_uri}/projects/my-project/zones/zone-1/instances/instance-2",
                "status": "RUNNING",
                "zone": "https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1"
              }},
              {{
                "machineType": "https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/machineTypes/n1-standard-2",
                "name": "instance-3",
                "networkInterfaces": [
                  {{
                    "accessConfigs": [
                      {{
                        "natIP": "23.251.133.76"
                      }}
                    ],
                    "networkIP": "10.0.0.3"
                  }}
                ],
                "scheduling": {{
                  "automaticRestart": false,
                  "onHostMaintenance": "TERMINATE",
                  "preemptible": false
                }},
                "selfLink": "{compute_uri}/projects/my-project/zones/zone-1/instances/instance-3",
                "status": "RUNNING",
                "zone": "https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1"
              }}
            ]
            """.format(compute_uri=self.compute_uri)))

  def testInvalidUri(self):
    with self.assertRaisesRegex(
        resources.InvalidResourceException, r'could not parse resource '
        r'\[https://compute.googleapis.com/compute/zones/central3-a/instances/'
        r'instance-2\]: unknown api version None'):
      self.Run("""
         compute instances create https://compute.googleapis.com/compute/zones/central3-a/instances/instance-2
         """)

    self.CheckRequests()

  def testFlagsWithUri(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central1-a')
        ],
        [
            m.Address(
                name='address-1',
                address='74.125.28.139'),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

    self.Run("""
        compute instances create instance-1
          --zone {uri}/projects/my-project/zones/central1-a
          --boot-disk-type {uri}/projects/my-project/zones/central1-a/diskTypes/pd-ssd
          --disk name={uri}/projects/my-project/zones/central1-a/disks/disk-1
          --machine-type {uri}/projects/my-project/zones/central1-a/machineTypes/n2-standard-1
          --network {uri}/projects/my-project/global/networks/some-other-network
          --image {uri}/projects/my-project/global/images/my-image
          --address {uri}/projects/my-project/regions/central1/addresses/address-1
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.zones,
          'Get',
          m.ComputeZonesGetRequest(
              project='my-project',
              zone=('central1-a')))],
        [(self.compute.addresses,
          'Get',
          m.ComputeAddressesGetRequest(
              address='address-1',
              project='my-project',
              region='central1'))],
        self.project_get_request,

        [(self.compute.instances,
          'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=(
                                  self.compute_uri +
                                  '/projects/my-project/global/images/'
                                  'my-image'),
                              diskType=(
                                  self.compute_uri +
                                  '/projects/my-project/zones/central1-a/'
                                  'diskTypes/pd-ssd'),
                          ),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
                      m.AttachedDisk(
                          autoDelete=False,
                          boot=False,
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
                          source=(
                              self.compute_uri +
                              '/projects/my-project/zones/central1-a/disks/'
                              'disk-1')),
                  ],
                  machineType=(self.compute_uri + '/projects/'
                               'my-project/zones/central1-a/machineTypes/'
                               'n2-standard-1'),
                  metadata=m.Metadata(),
                  name='instance-1',
                  networkInterfaces=[m.NetworkInterface(
                      accessConfigs=[m.AccessConfig(
                          name='external-nat',
                          type=self._one_to_one_nat,
                          natIP='74.125.28.139')],
                      network=(self.compute_uri + '/projects/'
                               'my-project/global/networks/'
                               'some-other-network'))],
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
              zone=('central1-a'),
          ))],
    )


if __name__ == '__main__':
  test_case.main()
