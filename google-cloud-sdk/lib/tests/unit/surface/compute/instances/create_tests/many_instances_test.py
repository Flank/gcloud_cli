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
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateManyInstancesTest(create_test_base.InstancesCreateTestBase
                                      ):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def _MakeInsertRequest(self, instance_ref):
    m = self.messages
    return m.ComputeInstancesInsertRequest(
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
            name=instance_ref.instance,
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[
                        m.AccessConfig(
                            name='external-nat', type=self._one_to_one_nat)
                    ],
                    network=self._default_network)
            ],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default', scopes=create_test_base.DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True),
        ),
        project=instance_ref.project,
        zone=instance_ref.zone,
    )

  def testManyInstances(self):
    instance_refs = [
        resources.REGISTRY.Create(   # pylint: disable=g-complex-comprehension
            'compute.instances',
            instance='instance-{}'.format(i),
            zone='central2-a',
            project=self.Project()) for i in range(3)
    ]

    self.Run('compute instances create {} --zone central2-a'.format(' '.join(
        i.instance for i in instance_refs)))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self._MakeInsertRequest(instance_refs[i])) for i in range(3)],
    )

  def testManyInstances_ViaUri(self):
    properties.VALUES.core.project.Set('should-not-be-used')
    instance_refs = [
        resources.REGISTRY.Create(   # pylint: disable=g-complex-comprehension
            'compute.instances',
            instance='instance-{}'.format(i),
            zone='central2-a',
            project=self.Project()) for i in range(3)
    ]

    self.Run('compute instances create {}'.format(' '.join(
        i.SelfLink() for i in instance_refs)))

    self.CheckRequests(
        self.zone_get_request,
        self.project_get_request,
        [(self.compute.instances, 'Insert',
          self._MakeInsertRequest(instance_refs[i])) for i in range(3)],
    )


if __name__ == '__main__':
  test_case.main()
