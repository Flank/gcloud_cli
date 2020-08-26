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
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateShieldedInstanceConfigGATest(
    create_test_base.InstancesCreateTestBase, parameterized.TestCase):
  """Test creation of VM instances with shielded VM config for v1 API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  # TODO(b/120429236): remove tests for shielded-vm flag after migration to
  # shielded-instance flags is complete.
  @parameterized.named_parameters(
      ('-InstanceEnableSecureBoot', '--shielded-secure-boot', True, None, None),
      ('-InstanceEnableVtpm', '--shielded-vtpm', None, True, None),
      ('-InstanceEnableIntegrity', '--shielded-integrity-monitoring', None,
       None, True), ('-InstanceDisableSecureBoot', '--no-shielded-secure-boot',
                     False, None, None),
      ('-InstanceDisableVtpm', '--no-shielded-vtpm', None, False, None),
      ('-InstanceDisableIntegrity', '--no-shielded-integrity-monitoring', None,
       None, False),
      ('-InstanceESecureBootEvtpm', '--shielded-secure-boot --shielded-vtpm',
       True, True, None),
      ('-InstanceDSecureBootDvtpm',
       '--no-shielded-secure-boot --no-shielded-vtpm', False, False, None),
      ('-InstanceESecureBootDvtpm', '--shielded-secure-boot --no-shielded-vtpm',
       True, False, None),
      ('-InstanceDSecureBootEvtpm', '--no-shielded-secure-boot --shielded-vtpm',
       False, True, None),
      ('-InstanceDSecureBootEvtpmEIntegrity',
       ('--no-shielded-secure-boot --shielded-vtpm'
        ' --shielded-integrity-monitoring'), False, True, True))
  def testCreateSVMCkWithAllProperties(self, cmd_flag, enable_secure_boot,
                                       enable_vtpm,
                                       enable_integrity_monitoring):
    m = self.messages

    self.Run('compute instances create instance-1 '
             '  --zone central2-a {}'.format(cmd_flag))

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
                  minCpuPlatform=None,
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
                  shieldedInstanceConfig=m.ShieldedInstanceConfig(
                      enableSecureBoot=enable_secure_boot,
                      enableVtpm=enable_vtpm,
                      enableIntegrityMonitoring=enable_integrity_monitoring)),
              project='my-project',
              zone='central2-a',
          ))],
    )


class InstancesCreateShieldedInstanceConfigBetaTest(
    InstancesCreateShieldedInstanceConfigGATest):
  """Test creation of VM instances with shielded VM config for Beta API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstancesCreateShieldedInstanceConfigAlphaTest(
    InstancesCreateShieldedInstanceConfigGATest):
  """Test creation of VM instances with shielded VM config for alpha API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


class InstancesCreateConfidentialInstanceConfigBetaTest(
    create_test_base.InstancesCreateTestBase, parameterized.TestCase):
  """Test creation of VM instances with Confidential Instance config."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  @parameterized.named_parameters(
      ('EnableConfidentialCompute', '--confidential-compute', True),
      ('DisableConfidentialCompute', '--no-confidential-compute', False))
  def testCreateVM(self, cmd_flag, enable_confidential_compute):
    m = self.messages
    self.Run('compute instances create instance-1 '
             '  --zone central2-a {}'.format(cmd_flag))

    expected_image = self._default_image
    expected_machine_type = self._default_machine_type
    if enable_confidential_compute:
      expected_image = self._default_confidential_vm_image
      expected_machine_type = self._default_confidential_vm_machine_type

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
                             sourceImage=expected_image),
                         mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                         type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
                 ],
                 machineType=expected_machine_type,
                 metadata=m.Metadata(),
                 minCpuPlatform=None,
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
                 confidentialInstanceConfig=m.ConfidentialInstanceConfig(
                     enableConfidentialCompute=enable_confidential_compute)),
             project='my-project',
             zone='central2-a',
         ))
    ])


class InstancesCreateConfidentialInstanceConfigAlphaTest(
    InstancesCreateConfidentialInstanceConfigBetaTest):
  """Test creation of VM instances with Confidential Instance config."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

if __name__ == '__main__':
  test_case.main()
