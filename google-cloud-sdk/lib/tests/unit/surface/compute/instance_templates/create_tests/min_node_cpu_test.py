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
from tests.lib.surface.compute.instance_templates import create_test_base


class InstanceTemplatesCreateWithMinNodeCpus(
    create_test_base.InstanceTemplatesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testCreateWithNoReservationAffinity(self):
    m = self.messages
    self.Run('compute instance-templates create template-1 '
             '--min-node-cpu=10')

    template = m.InstanceTemplate(
        name='template-1',
        properties=m.InstanceProperties(
            canIpForward=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=self._default_image,),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=create_test_base.DEFAULT_MACHINE_TYPE,
            metadata=m.Metadata(),
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[self._default_access_config],
                    network=self._default_network)
            ],
            serviceAccounts=[
                m.ServiceAccount(
                    email='default', scopes=create_test_base.DEFAULT_SCOPES),
            ],
            scheduling=m.Scheduling(automaticRestart=True, minNodeCpus=10)))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )


class InstanceTemplatesCreateWithMinNodeCpusBeta(
    InstanceTemplatesCreateWithMinNodeCpus):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstanceTemplatesCreateWithMinNodeCpusAlpha(
    InstanceTemplatesCreateWithMinNodeCpusBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
