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
from tests.lib.surface.compute.instances import test_resources

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


def DefaultMachineTypeOf(api_version):
  return (
      'https://compute.googleapis.com/compute/{ver}/projects/my-project/zones/'
      'central2-a/machineTypes/n1-standard-1').format(ver=api_version)


def DefaultPreemptibleMachineTypeOf(api_version):
  return (
      'https://compute.googleapis.com/compute/{ver}/projects/my-project/zones/'
      'us-central1-b/machineTypes/n1-standard-1').format(ver=api_version)


def DefaultNetworkOf(api_version):
  return ('https://compute.googleapis.com/compute/{ver}/projects/my-project/'
          'global/networks/default').format(ver=api_version)


def DefaultImageOf(api_version):
  return ('https://compute.googleapis.com/compute/{ver}/projects/debian-cloud/'
          'global/images/family/debian-10').format(ver=api_version)


def DefaultConfidentialVmImageOf(api_version):
  return ('https://compute.googleapis.com/compute/{ver}/projects/'
          'ubuntu-os-cloud/global/images/family/ubuntu-1804-lts'.format(
              ver=api_version))


def NvdimmDiskTypeOf(api_version):
  return ('https://compute.googleapis.com/compute/{ver}/projects/my-project/'
          'zones/central2-a/diskTypes/aep-nvdimm').format(ver=api_version)


def SsdDiskTypeOf(api_version):
  return ('https://compute.googleapis.com/compute/{ver}/projects/my-project/'
          'zones/central2-a/diskTypes/local-ssd').format(ver=api_version)


def OtherImageOf(api_version):
  return ('https://compute.googleapis.com/compute/{ver}/projects/'
          'some-other-project/global/images/other-image'.format(
              ver=api_version))


def AcceleratorTypeOf(api_version, name):
  return ('https://compute.googleapis.com/compute/{ver}/projects/my-project/'
          'zones/central2-a/acceleratorTypes/{name}'.format(
              ver=api_version, name=name))


class InstancesCreateTestBase(test_base.BaseTest):
  """Base class for all compute instances create tests."""

  def SetUp(self):
    self.SelectApi(self.api_version)
    self._default_image = DefaultImageOf(self.api_version)
    self._default_confidential_vm_image = (
        DefaultConfidentialVmImageOf(self.api_version))
    self._default_machine_type = DefaultMachineTypeOf(self.api_version)
    self._default_network = DefaultNetworkOf(self.api_version)
    self._one_to_one_nat = (
        self.messages.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)
    self._other_image = OtherImageOf(self.api_version)
    self._nvdimm_disk_type = NvdimmDiskTypeOf(self.api_version)
    self._ssd_disk_type = SsdDiskTypeOf(self.api_version)
    self._default_network_tier = None

    if self.api_version == 'v1':
      self._instances = test_resources.INSTANCES_V1
    elif self.api_version == 'alpha':
      self._instances = test_resources.INSTANCES_ALPHA
    elif self.api_version == 'beta':
      self._instances = test_resources.INSTANCES_BETA
    else:
      raise ValueError("api_version must be \'v1\', \'beta\', or \'alpha\'. "
                       'Got [{0}].'.format(self.api_version))

    random.seed(1)
    system_random_patcher = mock.patch(
        'random.SystemRandom', new=lambda: random)
    self.addCleanup(system_random_patcher.stop)
    system_random_patcher.start()

    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
        [
            self.messages.Project(
                defaultServiceAccount='default@service.account'),
        ],
        [],
    ])

  def Project(self):
    project = super(InstancesCreateTestBase, self).Project()
    if project:
      return project
    return 'my-project'
