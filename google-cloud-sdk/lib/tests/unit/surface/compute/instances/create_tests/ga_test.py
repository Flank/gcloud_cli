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
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.compute import utils
from tests.lib.surface.compute.instances import create_test_base


class InstancesCreateGaTest(create_test_base.InstancesCreateTestBase,
                            sdk_test_base.WithFakeAuth, waiter_test_base.Base):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.api_mock = utils.ComputeApiMock(
        self.api_version, project=self.Project(), zone='central2-a').Start()
    self.addCleanup(self.api_mock.Stop)
    self.status_enum = self.api_mock.messages.Operation.StatusValueValuesEnum

  def TearDown(self):
    self.api_mock.batch_responder.AssertDone()

  def GetInstanceRef(self, name, zone=None):
    return self.api_mock.resources.Parse(
        name,
        params={
            'project': self.Project(),
            'zone': zone or self.api_mock.zone
        },
        collection='compute.instances')

  def GetImageRef(self, name, project=None):
    return self.api_mock.resources.Create(
        'compute.images', image=name, project=project or self.Project())

  def GetNetworkRef(self, name, project=None):
    return self.api_mock.resources.Parse(
        name, params={'project': self.Project()}, collection='compute.networks')

  def GetMachineTypeRef(self, name, zone=None, project=None):
    return self.api_mock.resources.Parse(
        name,
        params={
            'project': project or self.Project(),
            'zone': zone or self.api_mock.zone
        },
        collection='compute.machineTypes')

  def GetOperationRef(self, name, zone=None, region=None):
    params = {'project': self.Project()}
    if region:
      collection = 'compute.regionOperations'
      params['region'] = region
    elif zone:
      collection = 'compute.zoneOperations'
      params['zone'] = zone
    else:
      collection = 'compute.zoneOperations'
      params['zone'] = self.api_mock.zone

    return self.api_mock.resources.Parse(name, params, collection=collection)

  def GetOperationMessage(self, operation_ref, status, errors=None):
    operation_cls = self.api_mock.messages.Operation
    operation = operation_cls(
        name=operation_ref.Name(),
        status=status,
        selfLink=operation_ref.SelfLink())
    if errors:
      operations_errors = []
      for e in errors:
        operations_errors.append(
            operation_cls.ErrorValue.ErrorsValueListEntry(
                code=e['code'], message=e['message']))
      operation.error = operation_cls.ErrorValue(errors=operations_errors)
    return operation

  def GetCreateInstanceRequest(self,
                               instance_ref,
                               image_ref=None,
                               machine_type_ref=None,
                               network_ref=None):
    image_ref = (
        image_ref or
        self.GetImageRef('family/debian-9', project='debian-cloud'))
    machine_type_ref = (
        machine_type_ref or self.GetMachineTypeRef('n1-standard-1'))
    network_ref = self.GetNetworkRef('default')
    m = self.api_mock.messages
    payload = m.ComputeInstancesInsertRequest(
        instance=m.Instance(
            canIpForward=False,
            deletionProtection=False,
            disks=[
                m.AttachedDisk(
                    autoDelete=True,
                    boot=True,
                    initializeParams=m.AttachedDiskInitializeParams(
                        sourceImage=image_ref.SelfLink(),),
                    mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                    type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
            ],
            machineType=machine_type_ref.SelfLink(),
            metadata=m.Metadata(),
            name=instance_ref.instance,
            networkInterfaces=[
                m.NetworkInterface(
                    accessConfigs=[
                        m.AccessConfig(
                            name='external-nat',
                            type=m.AccessConfig.TypeValueValuesEnum
                            .ONE_TO_ONE_NAT)
                    ],
                    network=network_ref.SelfLink())
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
    return (self.api_mock.adapter.apitools_client.instances, 'Insert', payload)

  def testDefaultOptions_Async(self):
    instance_ref1 = self.GetInstanceRef('instance-1')
    instance_ref2 = self.GetInstanceRef('instance-2')
    operation_ref1 = self.GetOperationRef('operation-1')
    operation_ref2 = self.GetOperationRef('operation-2')
    self.api_mock.batch_responder.ExpectBatch([
        (self.GetCreateInstanceRequest(instance_ref1),
         self.GetOperationMessage(operation_ref1, self.status_enum.PENDING)),
        (self.GetCreateInstanceRequest(instance_ref2),
         self.GetOperationMessage(operation_ref2, self.status_enum.PENDING)),
    ])
    self.Run('compute instances create {} {} --zone {} --async'.format(
        instance_ref1.instance, instance_ref2.instance, instance_ref1.zone))

    self.CheckRequests(self.zone_get_request)

    self.assertMultiLineEqual(
        'NOTE: The users will be charged for public IPs when VMs are created.\n'
        'Instance creation in progress for [{}]: {}\n'
        'Instance creation in progress for [{}]: {}\n'
        'Use [gcloud compute operations describe URI] command '
        'to check the status of the operation(s).\n'.format(
            instance_ref1.instance, operation_ref1.SelfLink(),
            instance_ref2.instance, operation_ref2.SelfLink()), self.GetErr())
    self.AssertOutputEquals('')


if __name__ == '__main__':
  test_case.main()
