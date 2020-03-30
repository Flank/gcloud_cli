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
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateWithDisplayDevice(create_test_base.InstancesCreateTestBase
                                      ):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testCreateWithDisplayDevice(self):
    m = self.messages
    self.Run('compute instances create instance-1 '
             '--zone central2-a '
             '--enable-display-device')

    self.CheckRequests(self.zone_get_request, self.project_get_request, [
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
                 displayDevice=m.DisplayDevice(enableDisplay=True),
                 machineType=self._default_machine_type,
                 metadata=m.Metadata(),
                 name='instance-1',
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
                         email='default',
                         scopes=create_test_base.DEFAULT_SCOPES),
                 ],
                 scheduling=m.Scheduling(automaticRestart=True),
             ),
             project='my-project',
             zone='central2-a'))
    ])


if __name__ == '__main__':
  test_case.main()
