# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for instances update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute import scope
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.compute import instances_labels_test_base

_DEFAULT_CPU_PLATFORM = 'CpuPlatform'


class UpdateLabelsTestBeta(instances_labels_test_base.InstancesLabelsTestBase):

  def testUpdateAndRemoveLabels(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')

    instance_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (
        ('key2', 'update2'), ('key3', 'value3'), ('key4', 'value4'))

    instance = self._MakeInstanceProto(
        instance_ref, labels=instance_labels, fingerprint=b'fingerprint-42')
    updated_instance = self._MakeInstanceProto(
        instance_ref, labels=edited_labels)

    operation_ref = self._GetOperationRef('operation-1', 'atlanta')
    operation = self._MakeOperationMessage(operation_ref, instance_ref)

    self._ExpectGetRequest(instance_ref, instance)
    self._ExpectLabelsSetRequest(
        instance_ref, edited_labels, b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(instance_ref, updated_instance)

    response = self.Run(
        'compute instances update {} --update-labels {} '
        '--remove-labels key1,key0'
        .format(
            instance_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])))
    self.assertEqual(response, updated_instance)

  def testUpdateClearLabels(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')

    instance_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    edited_labels = ()

    instance = self._MakeInstanceProto(
        instance_ref, labels=instance_labels, fingerprint=b'fingerprint-42')
    updated_instance = self._MakeInstanceProto(
        instance_ref, labels=edited_labels)

    operation_ref = self._GetOperationRef('operation-1', 'atlanta')
    operation = self._MakeOperationMessage(operation_ref, instance_ref)

    self._ExpectGetRequest(instance_ref, instance)
    self._ExpectLabelsSetRequest(
        instance_ref, edited_labels, b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(instance_ref, updated_instance)

    response = self.Run(
        'compute instances update {} --clear-labels'
        .format(instance_ref.SelfLink()))
    self.assertEqual(response, updated_instance)

  def testUpdateWithNoLabels(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')

    update_labels = (('key2', 'update2'), ('key4', 'value4'))

    instance = self._MakeInstanceProto(
        instance_ref, labels=(), fingerprint=b'fingerprint-42')
    updated_instance = self._MakeInstanceProto(
        instance_ref, labels=update_labels)
    operation_ref = self._GetOperationRef('operation-1', 'atlanta')
    operation = self._MakeOperationMessage(operation_ref, instance_ref)

    self._ExpectGetRequest(instance_ref, instance)
    self._ExpectLabelsSetRequest(
        instance_ref, update_labels, b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(instance_ref, updated_instance)

    response = self.Run(
        'compute instances update {} --update-labels {} '
        .format(
            instance_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])
        ))
    self.assertEqual(response, updated_instance)

  def testRemoveWithNoLabelsOnInstance(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')
    instance = self._MakeInstanceProto(
        instance_ref, labels={}, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(instance_ref, instance)

    response = self.Run(
        'compute instances update {} --remove-labels DoesNotExist'
        .format(instance_ref.SelfLink()))
    self.assertEqual(response, instance)

  def testNoNetUpdate(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')

    instance_labels = (
        ('key1', 'value1'), ('key2', 'value2'), ('key3', 'value3'))
    update_labels = (
        ('key1', 'value1'), ('key3', 'value3'), ('key4', 'value4'))

    instance = self._MakeInstanceProto(
        instance_ref, labels=instance_labels, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(instance_ref, instance)

    response = self.Run(
        'compute instances update {} --update-labels {} --remove-labels key4'
        .format(
            instance_ref.SelfLink(),
            ','.join(['{0}={1}'.format(pair[0], pair[1])
                      for pair in update_labels])
        ))
    self.assertEqual(response, instance)

  def testScopePrompt(self):
    instance_ref = self._GetInstanceRef('instance-1', zone='atlanta')
    instance = self._MakeInstanceProto(instance_ref, labels=[])
    self._ExpectGetRequest(instance_ref, instance)

    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.StartPatch('googlecloudsdk.command_lib.compute.instances.flags'
                    '.InstanceZoneScopeLister',
                    return_value={scope.ScopeEnum.ZONE:
                                  [self.messages.Zone(name='atlanta')]},
                   )
    self.Run('compute instances update instance-1 --remove-labels key0')
    self.AssertErrContains(
        'No zone specified. Using zone [atlanta] for instance: [instance-1].')


class UpdateTestBaseClass(sdk_test_base.WithFakeAuth,
                          cli_test_base.CliTestBase, waiter_test_base.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.client_class = core_apis.GetClientClass('compute', self.api_version)
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)

  def Client(self):
    return api_mock.Client(
        self.client_class,
        real_client=core_apis.GetClientInstance(
            'compute', self.api_version, no_http=True))

  def _GetOperationRef(self, name, zone):
    return self.resources.Parse(
        name,
        params={'project': self.Project(),
                'zone': zone},
        collection='compute.zoneOperations')

  def _GetInstanceRef(self, name, zone):
    return self.resources.Parse(
        name,
        params={'project': self.Project(),
                'zone': zone},
        collection='compute.instances')

  def _GetOperationMessage(self, operation_ref, status, resource_ref=None):
    return self.messages.Operation(
        name=operation_ref.Name(),
        status=status,
        selfLink=operation_ref.SelfLink(),
        targetLink=resource_ref.SelfLink() if resource_ref else None)


class SetMinCpuPlatformTest(UpdateTestBaseClass):

  def ExpectSetMinCpuPlatform(self, client, cpu_platform=_DEFAULT_CPU_PLATFORM):
    messages = self.messages
    client.instances.SetMinCpuPlatform.Expect(
        messages.ComputeInstancesSetMinCpuPlatformRequest(
            instancesSetMinCpuPlatformRequest=
            messages.InstancesSetMinCpuPlatformRequest(
                minCpuPlatform=cpu_platform),
            project=self.Project(),
            zone='central2-a',
            instance='instance-1'),
        self._GetOperationMessage(
            self._GetOperationRef('operation-X', 'central2-a'),
            messages.Operation.StatusValueValuesEnum.PENDING))

  def testWithOperationPolling(self):
    with self.Client() as client:
      self.ExpectSetMinCpuPlatform(client)

      client.zoneOperations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
              operation='operation-X',
              zone='central2-a',
              project=self.Project()),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              self.messages.Operation.StatusValueValuesEnum.DONE,
              self._GetInstanceRef('instance-1', 'central2-a')))
      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='fake-project', zone='central2-a'),
          self.messages.Instance(name='instance-1'))

      self.Run("""
          compute instances update instance-1
            --zone central2-a
            --min-cpu-platform CpuPlatform
          """)
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Changing minimum CPU platform of instance [instance-1]')

  def testNoMinCpuPlatformDefaults(self):
    with self.Client() as client:
      self.ExpectSetMinCpuPlatform(client, None)

      client.zoneOperations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
              operation='operation-X',
              zone='central2-a',
              project=self.Project()),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              self.messages.Operation.StatusValueValuesEnum.DONE,
              self._GetInstanceRef('instance-1', 'central2-a')))
      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='fake-project', zone='central2-a'),
          self.messages.Instance(name='instance-1'))

      self.Run("""
          compute instances update instance-1
            --zone central2-a
            --min-cpu-platform ""
            --format=disable
          """)
      self.AssertOutputEquals('')
      self.AssertErrContains(
          'Changing minimum CPU platform of instance [instance-1]')


class SetMinCpuPlatformTestBeta(SetMinCpuPlatformTest):

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class SetMinCpuPlatformTestAlpha(SetMinCpuPlatformTestBeta):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


class DeletionProtectionTest(UpdateTestBaseClass, parameterized.TestCase):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def ExpectSetDeletionProtection(self, client, deletion_protection):
    messages = self.messages
    client.instances.SetDeletionProtection.Expect(
        messages.ComputeInstancesSetDeletionProtectionRequest(
            deletionProtection=deletion_protection,
            project=self.Project(),
            zone='central2-a',
            resource='instance-1'),
        self._GetOperationMessage(
            self._GetOperationRef('operation-X', 'central2-a'),
            messages.Operation.StatusValueValuesEnum.PENDING))

  @parameterized.named_parameters(
      ('SetTrue', '--deletion-protection', True),
      ('SetFalse', '--no-deletion-protection', False))
  def testUpdateDeletionProtection(self, flag, deletion_protection):
    with self.Client() as client:
      self.ExpectSetDeletionProtection(client,
                                       deletion_protection=deletion_protection)

      client.zoneOperations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
              operation='operation-X',
              zone='central2-a',
              project=self.Project()),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              self.messages.Operation.StatusValueValuesEnum.DONE,
              self._GetInstanceRef('instance-1', 'central2-a')))
      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='fake-project', zone='central2-a'),
          self.messages.Instance(name='instance-1'))

      self.Run('compute instances update instance-1 '
               '--zone central2-a {}'.format(flag))
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Setting deletion protection of instance [instance-1] to [{}]'
        .format(deletion_protection))

  def testUpdateDeletionProtectionDefault(self):
    self.Run('compute instances update instance-1 '
             '--zone central2-a')
    self.AssertOutputEquals('')
    self.AssertErrNotContains(
        'Setting deletion protection of instance [instance-1] to')


class InstancesSetShieldedVMConfigAlphaTest(UpdateTestBaseClass,
                                            parameterized.TestCase):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def ExpectShieldedVMConfig(self, client, shielded_vm_config):
    messages = self.messages
    client.instances.UpdateShieldedVmConfig.Expect(
        messages.ComputeInstancesUpdateShieldedVmConfigRequest(
            instance='instance-1',
            project=self.Project(),
            shieldedVmConfig=shielded_vm_config,
            zone='central2-a'),
        self._GetOperationMessage(
            self._GetOperationRef('operation-X', 'central2-a'),
            messages.Operation.StatusValueValuesEnum.PENDING))

  def testWithDefaults(self):
    self.Run("""
        compute instances update instance-1
          --zone central2-a
        """)
    self.AssertOutputEquals('')
    self.AssertErrNotContains(
        'Setting shieldedVMConfig  of instance [instance-1]')

  @parameterized.named_parameters(
      ('-EnableSecureBoot', '--shielded-vm-secure-boot', True, None, None),
      ('-EnableVtpm', '--shielded-vm-vtpm', None, True, None),
      ('-EnableIntegrity', '--shielded-vm-integrity-monitoring', None, None,
       True),
      ('-DisableSecureBoot', '--no-shielded-vm-secure-boot', False, None, None),
      ('-DisableVtpm', '--no-shielded-vm-vtpm', None, False, None),
      ('-DisableIntegrity', '--no-shielded-vm-integrity-monitoring', None, None,
       False),
      ('-ESecureBootEvtpm', '--shielded-vm-secure-boot --shielded-vm-vtpm',
       True, True, None), ('-DSecureBootDvtpm',
                           '--no-shielded-vm-secure-boot --no-shielded-vm-vtpm',
                           False, False, None),
      ('-ESecureBootDvtpm', '--shielded-vm-secure-boot --no-shielded-vm-vtpm',
       True, False, None),
      ('-DSecureBootEvtpm', '--no-shielded-vm-secure-boot --shielded-vm-vtpm',
       False, True, None),
      ('-DSecureBootEvtpmEintegrity',
       ('--no-shielded-vm-secure-boot --shielded-vm-vtpm '
        '--shielded-vm-integrity-monitoring'), False, True, True),
      ('-ESecureBootEvtpmEintegrity',
       ('--shielded-vm-secure-boot --shielded-vm-vtpm '
        '--shielded-vm-integrity-monitoring'), True, True, True))
  def testShieldedVMConfig(self, cmd_flag, enable_secure_boot, enable_vtpm,
                           enable_integrity_monitoring):

    messages = self.messages
    shieldedvmconfig = messages.ShieldedVmConfig(
        enableSecureBoot=enable_secure_boot,
        enableVtpm=enable_vtpm,
        enableIntegrityMonitoring=enable_integrity_monitoring)

    with self.Client() as client:
      self.ExpectShieldedVMConfig(client,
                                  shielded_vm_config=shieldedvmconfig)

      client.zoneOperations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
              operation='operation-X',
              zone='central2-a',
              project=self.Project()),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              self.messages.Operation.StatusValueValuesEnum.DONE,
              self._GetInstanceRef('instance-1', 'central2-a')))
      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='fake-project', zone='central2-a'),
          self.messages.Instance(name='instance-1'))

      self.Run('compute instances update instance-1 '
               '--zone central2-a {}'.format(cmd_flag))
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Setting shieldedVMConfig  of instance [instance-1]')


class InstancesSetShieldedVMConfigBetaTest(
    InstancesSetShieldedVMConfigAlphaTest):

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class InstancesSetShieldedVMIntegrityPolicyAlphaTest(UpdateTestBaseClass,
                                                     parameterized.TestCase):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def ExpectShieldedVMIntegrityPolicy(self, client,
                                      shielded_vm_integrity_policy):
    messages = self.messages
    client.instances.SetShieldedVmIntegrityPolicy.Expect(
        messages.ComputeInstancesSetShieldedVmIntegrityPolicyRequest(
            instance='instance-1',
            project=self.Project(),
            shieldedVmIntegrityPolicy=shielded_vm_integrity_policy,
            zone='central2-a'),
        self._GetOperationMessage(
            self._GetOperationRef('operation-X', 'central2-a'),
            messages.Operation.StatusValueValuesEnum.PENDING))

  def testWithDefaults(self):
    self.Run("""
        compute instances update instance-1
          --zone central2-a
        """)
    self.AssertOutputEquals('')
    self.AssertErrNotContains(
        'Setting shieldedVMIntegrityPolicy of instance [instance-1]')

  @parameterized.named_parameters(
      ('-LearnIntegrityPolicy', '--shielded-vm-learn-integrity-policy', True),)
  def testShieldedVMIntegrityPolicy(self, cmd_flag, learn_integrity_policy):

    messages = self.messages
    shieldedvm_integrity_policy = messages.ShieldedVmIntegrityPolicy(
        updateAutoLearnPolicy=learn_integrity_policy)

    with self.Client() as client:
      self.ExpectShieldedVMIntegrityPolicy(
          client, shielded_vm_integrity_policy=shieldedvm_integrity_policy)

      client.zoneOperations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
              operation='operation-X',
              zone='central2-a',
              project=self.Project()),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              self.messages.Operation.StatusValueValuesEnum.DONE,
              self._GetInstanceRef('instance-1', 'central2-a')))
      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='fake-project', zone='central2-a'),
          self.messages.Instance(name='instance-1'))

      self.Run('compute instances update instance-1 '
               '--zone central2-a {}'.format(cmd_flag))
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Setting shieldedVMIntegrityPolicy of instance [instance-1]')


class InstancesSetShieldedVMIntegrityPolicyBetaTest(
    InstancesSetShieldedVMIntegrityPolicyAlphaTest):

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class DisplayDeviceTest(UpdateTestBaseClass, parameterized.TestCase):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def ExpectUpdateDisplayDevice(self, client, enable_display):
    messages = self.messages
    client.instances.UpdateDisplayDevice.Expect(
        messages.ComputeInstancesUpdateDisplayDeviceRequest(
            displayDevice=messages.DisplayDevice(enableDisplay=enable_display),
            project=self.Project(),
            zone='central2-a',
            instance='instance-1'),
        self._GetOperationMessage(
            self._GetOperationRef('operation-X', 'central2-a'),
            messages.Operation.StatusValueValuesEnum.PENDING))

  @parameterized.named_parameters(
      ('SetTrue', '--enable-display-device', True),
      ('SetFalse', '--no-enable-display-device', False))
  def testUpdateDisplayDevice(self, flag, enable_display):
    with self.Client() as client:
      self.ExpectUpdateDisplayDevice(client, enable_display)

      client.zoneOperations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
              operation='operation-X',
              zone='central2-a',
              project=self.Project()),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              self.messages.Operation.StatusValueValuesEnum.DONE,
              self._GetInstanceRef('instance-1', 'central2-a')))
      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='fake-project', zone='central2-a'),
          self.messages.Instance(name='instance-1'))

      self.Run('compute instances update instance-1 '
               '--zone central2-a {}'.format(flag))
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Updating display device of instance [instance-1]')


if __name__ == '__main__':
  test_case.main()
