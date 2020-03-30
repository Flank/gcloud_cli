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
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateTest(create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testDefaultZone(self):
    m = self.messages

    properties.VALUES.compute.zone.Set('central2-a')
    self.Run("""
        compute instances create instance-1
        """)

    self.AssertErrNotContains('choose a zone')
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
                              sourceImage=self._default_image,),
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

  def testZoneAndDeprecationWithYes(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    m = self.messages

    self.WriteInput('1\ny\n')
    self.make_requests.side_effect = iter([
        [
            m.Zone(name='central2-a'),
            m.Zone(name='central2-b'),
        ],
        [
            m.Zone(
                name='central2-a',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00'),
            ),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    self.Run("""
        compute instances create instance-1
        """)

    self.CheckRequests(
        self.zones_list_request,
        [(self.compute.zones, 'Get',
          m.ComputeZonesGetRequest(project='my-project', zone='central2-a'))],
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
                              sourceImage=self._default_image,),
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

    self.AssertErrContains('instance-1')
    self.AssertErrContains('central2-a')
    self.AssertErrContains('central2-b')
    self.AssertErrContains(
        r'WARNING: The following selected zone is deprecated. All resources in '
        r'this zone will be deleted after the turndown date.\n'
        r' - [central2-a] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDeprecationWithOneZoneWorksWithYes(self):
    m = self.messages

    self.WriteInput('Y\n')
    self.make_requests.side_effect = iter([
        [
            m.Zone(
                name='central2-a',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00')),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    self.Run("""
        compute instances create instance-1
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
                              sourceImage=self._default_image,),
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
        r'WARNING: The following selected zone is deprecated. All resources in '
        r'this zone will be deleted after the turndown date.\n'
        r' - [central2-a] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDeprecationWorkWithOneZoneWithYes(self):
    m = self.messages

    self.WriteInput('y\n')
    self.make_requests.side_effect = iter([
        [
            m.Zone(
                name='central2-a',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00'),
            ),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    self.Run("""
        compute instances create instance-1 --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.zones, 'Get',
          m.ComputeZonesGetRequest(project='my-project', zone='central2-a'))],
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
                              sourceImage=self._default_image,),
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
        r'WARNING: The following selected zone is deprecated. All resources in '
        r'this zone will be deleted after the turndown date.\n'
        r' - [central2-a] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDeprecationWorkWithOneZoneWithNo(self):
    m = self.messages

    self.WriteInput('n\n')
    self.make_requests.side_effect = iter([
        [
            m.Zone(
                name='central2-b',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00'))
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    with self.AssertRaisesToolExceptionRegexp('Creation aborted by user.'):
      self.Run("""
          compute instances create instance-1 --zone central2-b
          """)

    self.CheckRequests(
        [(self.compute.zones, 'Get',
          m.ComputeZonesGetRequest(project='my-project', zone='central2-b'))],)

    self.AssertErrContains(
        r'WARNING: The following selected zone is deprecated. All resources in '
        r'this zone will be deleted after the turndown date.\n'
        r' - [central2-b] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDeprecationWorkWithManyZonesWithYes(self):
    m = self.messages

    self.WriteInput('y\n')
    self.make_requests.side_effect = iter([
        [
            m.Zone(
                name='central1-a',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
                    deleted='2015-05-07T00:00.000-07:00'),
            ),
            m.Zone(
                name='central1-b',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00'),
            ),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        []  # For the MakeRequests call in run
    ])

    self.Run("""
        compute instances create
          https://compute.googleapis.com/compute/{api}/projects/my-project/zones/central1-a/instances/instance-1
          https://compute.googleapis.com/compute/{api}/projects/my-project/zones/central1-b/instances/instance-2
        """.format(api=self.api))

    self.CheckRequests(
        [(self.compute.zones, 'Get',
          m.ComputeZonesGetRequest(project='my-project', zone='central1-a')),
         (self.compute.zones, 'Get',
          m.ComputeZonesGetRequest(project='my-project', zone='central1-b'))],
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
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=(self.compute_uri + '/projects/'
                               'my-project/zones/central1-a/machineTypes/'
                               'n1-standard-1'),
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
              zone='central1-a',
          )),
         (self.compute.instances, 'Insert',
          m.ComputeInstancesInsertRequest(
              instance=m.Instance(
                  canIpForward=False,
                  deletionProtection=False,
                  disks=[
                      m.AttachedDisk(
                          autoDelete=True,
                          boot=True,
                          initializeParams=m.AttachedDiskInitializeParams(
                              sourceImage=self._default_image,),
                          mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                          type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                  ],
                  machineType=(self.compute_uri + '/projects/'
                               'my-project/zones/central1-b/machineTypes/'
                               'n1-standard-1'),
                  metadata=m.Metadata(),
                  name='instance-2',
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
              zone='central1-b',
          ))],
    )

    self.AssertErrContains(
        r'WARNING: The following selected zones are deprecated. All resources '
        r'in these zones will be deleted after their turndown date.\n'
        r' - [central1-a] 2015-05-07T00:00.000-07:00\n'
        r' - [central1-b] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDeprecationWorkWithZonalFetchError(self):
    m = self.messages

    def MakeRequests(*_, **kwargs):
      if kwargs['requests'][0][0] == self.compute.zones:
        yield m.Zone(name='central2-a')
        kwargs['errors'].append((500, 'Server Error'))
      elif kwargs['requests'][0][0] == self.compute.images:
        yield m.Image(
            name='debian-8-jessie-v20151130', selfLink=self._default_image)
      elif kwargs['requests'][0][0] == self.compute.projects:
        yield m.Project(defaultServiceAccount='default@service.account')
      else:
        yield

    self.make_requests.side_effect = MakeRequests

    self.Run("""
          compute instances create instance-1 --zone central2-a --quiet
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
                              sourceImage=self._default_image,),
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

  def testDeprecationWorkWithQuietFlag(self):
    m = self.messages

    self.make_requests.side_effect = iter([
        [
            m.Zone(
                name='central2-a',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00'),
            ),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    self.Run("""
        compute instances create instance-1 --zone central2-a --quiet
        """)

    self.CheckRequests(
        [(self.compute.zones, 'Get',
          m.ComputeZonesGetRequest(project='my-project', zone='central2-a'))],
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
                              sourceImage=self._default_image,),
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
    self.AssertErrNotContains('PROMPT_CONTINUE')

  def testZoneDeprecatedWarningNo(self):
    m = self.messages

    self.WriteInput('n\n')
    self.make_requests.side_effect = iter([
        [
            m.Zone(
                name='central2-a',
                deprecated=m.DeprecationStatus(
                    state=m.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00')),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])
    with self.AssertRaisesToolExceptionRegexp('Creation aborted by user.'):
      self.Run("""
          compute instances create instance-1
            --zone central2-a
          """)

    self.CheckRequests(self.zone_get_request,)
    self.AssertErrContains(
        r'WARNING: The following selected zone is deprecated. All resources in '
        r'this zone will be deleted after the turndown date.\n'
        r' - [central2-a] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')


if __name__ == '__main__':
  test_case.main()
