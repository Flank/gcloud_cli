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
"""Base class for `compute instances create` tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import random

from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock

DEFAULT_SCOPES = sorted([
    'https://www.googleapis.com/auth/devstorage.read_only',
    'https://www.googleapis.com/auth/logging.write',
    'https://www.googleapis.com/auth/monitoring.write',
    'https://www.googleapis.com/auth/servicecontrol',
    'https://www.googleapis.com/auth/service.management.readonly',
    'https://www.googleapis.com/auth/pubsub',
    'https://www.googleapis.com/auth/trace.append',
])

DEFAULT_MACHINE_TYPE = 'n1-standard-1'

_DEFAULT_IMAGE = (
    '{compute_uri}/projects/debian-cloud/global/images/family/debian-10')

_DEFAULT_NETWORK = ('{compute_uri}/projects/my-project/'
                    'global/networks/default')

_INSTANCE_TEMPLATES = {
    'v1': test_resources.INSTANCE_TEMPLATES_V1,
    'beta': test_resources.INSTANCE_TEMPLATES_BETA,
    'alpha': test_resources.INSTANCE_TEMPLATES_ALPHA,
}


class InstanceTemplatesCreateTestBase(test_base.BaseTest):
  """Base class for compute instance-templates create tests."""

  def SetUp(self):
    self.SelectApi(self.api_version)

    self._instance_templates = _INSTANCE_TEMPLATES[self.api_version]

    self._default_image = _DEFAULT_IMAGE.format(compute_uri=self.compute_uri)
    self._default_network = _DEFAULT_NETWORK.format(
        compute_uri=self.compute_uri)
    self._one_to_one_nat = (
        self.messages.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)

    self._default_access_config = self.messages.AccessConfig(
        name='external-nat', type=self._one_to_one_nat)

    random.seed(1)
    system_random_patcher = mock.patch(
        'random.SystemRandom', new=lambda: random)
    self.addCleanup(system_random_patcher.stop)
    system_random_patcher.start()

    self.make_requests.side_effect = iter([
        [
            self.messages.Image(
                name='debian-10-buster-v20200326',
                selfLink=self._default_image),
        ],
        [],
    ])

    self.get_default_image_requests = [
        (self.compute.images, 'GetFromFamily',
         self.messages.ComputeImagesGetFromFamilyRequest(
             family='debian-10', project='debian-cloud'))
    ]

  def _MakeInstanceTemplate(self, **kwargs):
    """Returns a function that creates default templates given custom values."""

    default_disk = self.messages.AttachedDisk(
        autoDelete=True,
        boot=True,
        initializeParams=self.messages.AttachedDiskInitializeParams(
            sourceImage=self._default_image,),
        mode=self.messages.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
        type=self.messages.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    default_metadata = self.messages.Metadata()
    default_network_interface = self.messages.NetworkInterface(
        accessConfigs=[self._default_access_config],
        network=self._default_network)
    default_service_account = self.messages.ServiceAccount(
        email='default', scopes=DEFAULT_SCOPES)
    default_scheduling = self.messages.Scheduling(automaticRestart=True)

    template = self.messages.InstanceTemplate(
        name='template-1',
        description=kwargs.get('description', None),
        properties=self.messages.InstanceProperties(
            canIpForward=kwargs.get('canIpForward', False),
            disks=kwargs.get('disks', [default_disk]),
            machineType=kwargs.get('machineType', DEFAULT_MACHINE_TYPE),
            metadata=kwargs.get('metadata', default_metadata),
            labels=kwargs.get('labels', None),
            networkInterfaces=kwargs.get('networkInterfaces',
                                         [default_network_interface]),
            serviceAccounts=kwargs.get('serviceAccounts',
                                       [default_service_account]),
            scheduling=kwargs.get('scheduling', default_scheduling),
            guestAccelerators=kwargs.get('guestAccelerators', []),
            minCpuPlatform=kwargs.get('minCpuPlatform', None),
            reservationAffinity=kwargs.get('reservationAffinity', None),
            tags=kwargs.get('tags', None)))

    return template
