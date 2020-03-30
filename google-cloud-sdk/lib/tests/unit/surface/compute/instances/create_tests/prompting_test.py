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
from googlecloudsdk.command_lib.compute import flags as compute_flags
from tests.lib import test_case
from tests.lib.surface.compute import test_resources
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreatePromptingTest(create_test_base.InstancesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testPromptingWithOneInstance(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    m = self.messages

    self.WriteInput('4\n')
    self.make_requests.side_effect = iter([
        test_resources.ZONES,
        [m.Zone(name='us-central1-b')],
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
          m.ComputeZonesGetRequest(project='my-project', zone='us-central1-b'))
        ],
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
                               'my-project/zones/us-central1-b/machineTypes/'
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
              zone='us-central1-b',
          ))],
    )

    # This tool should not sort the zones as returned from the
    # server. Zone orderings are different on a per-project basis to
    # ensure equal load on all zones.
    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains(
        '"choices": ["europe-west1-a", "europe-west1-b (DELETED)", '
        '"us-central1-a (DEPRECATED)", "us-central1-b"]')

  def testPromptingWithSimpleNamesAndUris(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    m = self.messages

    self.WriteInput('4\n')
    self.make_requests.side_effect = iter([
        test_resources.ZONES,
        [
            m.Zone(name='us-central1-b'),
            m.Zone(name='central3-a'),
            m.Zone(name='central3-b')
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        []  # For the MakeRequests call in Run
    ])

    self.Run("""
        compute instances create
          instance-1
          {compute_uri}/projects/my-project/zones/central3-a/instances/instance-2
          instance-3
          {compute_uri}/projects/my-project/zones/central3-b/instances/instance-4
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        self.zones_list_request,
        [(self.compute.zones, 'Get',
          m.ComputeZonesGetRequest(project='my-project', zone='us-central1-b')),
         (self.compute.zones, 'Get',
          m.ComputeZonesGetRequest(project='my-project', zone='central3-a')),
         (self.compute.zones, 'Get',
          m.ComputeZonesGetRequest(project='my-project', zone='central3-b'))],
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
                               'my-project/zones/us-central1-b/machineTypes/'
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
              zone='us-central1-b',
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
                               'my-project/zones/central3-a/machineTypes/'
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
              zone='central3-a',
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
                               'my-project/zones/us-central1-b/machineTypes/'
                               'n1-standard-1'),
                  metadata=m.Metadata(),
                  name='instance-3',
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
              zone='us-central1-b',
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
                               'my-project/zones/central3-b/machineTypes/'
                               'n1-standard-1'),
                  metadata=m.Metadata(),
                  name='instance-4',
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
              zone='central3-b',
          ))],
    )
    self.AssertErrContains('For the following instances:')
    self.AssertErrContains('instance-1')
    self.AssertErrContains('instance-3')
    self.AssertErrContains('choose a zone:')
    self.AssertErrContains('us-central1-a (DEPRECATED)')
    self.AssertErrContains('us-central1-b')
    self.AssertErrContains('europe-west1-a')
    self.AssertErrContains('europe-west1-b (DELETED)')

  def testPromptingError(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    m = self.messages

    def MakeRequests(*_, **kwargs):
      yield m.Zone(name='central2-a')
      kwargs['errors'].append((500, 'Server Error'))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(r'Could not fetch resource:'):
      self.Run("""
         compute instances create instance-1
         """)

    self.CheckRequests(self.zones_list_request,)
    self.AssertErrContains('Server Error')
    self.AssertErrNotContains('choose a zone:')
    self.AssertErrNotContains('central2-a')

  def testPromptingWithQuiet(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=False)
    self.make_requests.side_effect = iter([
        test_resources.ZONES,
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
    ])

    with self.assertRaisesRegex(
        compute_flags.UnderSpecifiedResourceError,
        r'Underspecified resource \[instance-1\]. Specify the \[--zone\] '
        r'flag\.'):
      self.Run("""
         compute instances create instance-1 --quiet
         """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
