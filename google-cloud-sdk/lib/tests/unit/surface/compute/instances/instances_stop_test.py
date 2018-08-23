# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the instances stop subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import utils
from six.moves import range


class InstancesStopTestBase(test_base.BaseTest):

  def _GetOperationRef(self, name, zone=None, region=None):
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

  def _GetOperationGetRequest(self, operation_ref):
    return (self.api_mock.adapter.apitools_client.zoneOperations, 'Get',
            self.api_mock.messages.ComputeZoneOperationsGetRequest(
                **operation_ref.AsDict()))

  def _GetOperationMessage(self, operation_ref, status, errors=None):
    operation = self.api_mock.messages.Operation(
        name=operation_ref.Name(),
        status=status,
        selfLink=operation_ref.SelfLink())
    if errors:
      operation.error = self.api_mock.messages.Operation.ErrorValue(
          errors=[
              self.api_mock.messages.Operation.ErrorValue.ErrorValueListEntry(
                  code=e['code'], message=e['message']) for e in errors
          ])
    return operation

  def _GetInstancesStopRef(self, name, zone=None):
    return self.api_mock.resources.Parse(
        name,
        params={
            'project': self.Project(),
            'zone': self.api_mock.zone if zone is None else zone
        },
        collection='compute.instances')

  def _CreateInstancesStopRequest(self, stop_ref):
    return self.api_mock.messages.ComputeInstancesStopRequest(
        instance=stop_ref.Name(), project=self.Project(), zone=stop_ref.zone)

  def _GetInstancesStopRequest(self, stop_ref):
    return (self.compute.instances, 'Get',
            self._CreateInstancesStopRequest(stop_ref))

  def _GetInstancesStopMessages(self, stop_ref):
    return self.api_mock.messages.ComputeInstancesStopRequest(
        instance=stop_ref.Name(), selfLink=stop_ref.SelfLink())

  def Project(self):
    return 'my-project'


class InstancesStopTest(InstancesStopTestBase):

  def SetUp(self):
    self.api_mock = utils.ComputeApiMock(
        'v1', project=self.Project(), zone='central2-a').Start()
    self.addCleanup(self.api_mock.Stop)

    self.status_enum = self.api_mock.messages.Operation.StatusValueValuesEnum

  def testSimpleCase(self):
    op_ref = self._GetOperationRef('operation-1')
    stop_ref = self._GetInstancesStopRef('instance-1')
    self.api_mock.batch_responder.ExpectBatch(
        [((self.compute.instances, 'Stop',
           self._CreateInstancesStopRequest(stop_ref)),
          (self._GetOperationMessage(op_ref, self.status_enum.PENDING)))])

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetOperationGetRequest(op_ref), self._GetOperationMessage(
            op_ref, self.status_enum.DONE)),
    ])

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetInstancesStopRequest(stop_ref),
         self._CreateInstancesStopRequest(stop_ref)),
    ])

    self.Run('compute instances stop instance-1 --zone central2-a')

    self.AssertOutputEquals('')
    self.AssertErrContains('Stopping instance(s) instance-1')

  def testStopManyInstances(self):
    num_instances = 3
    op_refs = [
        self._GetOperationRef('operation-%d' % i) for i in range(num_instances)
    ]
    stop_refs = [
        self._GetInstancesStopRef('instance-%d' % i)
        for i in range(num_instances)
    ]

    self.api_mock.batch_responder.ExpectBatch(
        [((self.compute.instances, 'Stop', self._CreateInstancesStopRequest(
            stop_refs[i])),
          (self._GetOperationMessage(op_refs[i], self.status_enum.PENDING)))
         for i in range(num_instances)])

    self.api_mock.batch_responder.ExpectBatch([(self._GetOperationGetRequest(
        op_refs[i]), self._GetOperationMessage(op_refs[i],
                                               self.status_enum.DONE))
                                               for i in range(num_instances)])

    self.api_mock.batch_responder.ExpectBatch([(self._GetInstancesStopRequest(
        stop_refs[i]), self._CreateInstancesStopRequest(stop_refs[i]))
                                               for i in range(num_instances)])

    self.Run("""
        compute instances stop
          instance-0 instance-1 instance-2
          --zone central2-a
        """)

    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Stopping instance(s) instance-0, instance-1, instance-2')
    for ref in stop_refs:
      self.AssertErrContains('Updated [%s].' % ref)

  def testUriSupport(self):
    op_ref = self._GetOperationRef('operation-1')
    stop_ref = self._GetInstancesStopRef('instance-1')
    self.api_mock.batch_responder.ExpectBatch(
        [((self.compute.instances, 'Stop',
           self._CreateInstancesStopRequest(stop_ref)),
          (self._GetOperationMessage(op_ref, self.status_enum.PENDING)))])

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetOperationGetRequest(op_ref), self._GetOperationMessage(
            op_ref, self.status_enum.DONE)),
    ])

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetInstancesStopRequest(stop_ref),
         self._CreateInstancesStopRequest(stop_ref)),
    ])

    self.Run("""
        compute instances stop
          https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/instance-1
        """.format(self.resource_api))

    self.AssertOutputEquals('')
    self.AssertErrContains('Stopping instance(s) instance-1')

  def testInstanceStopOneAsync(self):
    op_ref = self._GetOperationRef('operation-1')
    stop_ref = self._GetInstancesStopRef('instance-1')
    self.api_mock.batch_responder.ExpectBatch(
        [((self.compute.instances, 'Stop',
           self._CreateInstancesStopRequest(stop_ref)),
          (self._GetOperationMessage(op_ref, self.status_enum.PENDING)))])

    self.Run('compute instances stop instance-1 --zone central2-a --async')

    self.AssertOutputEquals('')
    self.AssertErrContains('Stop instance in progress for [{}].'.format(op_ref))
    self.AssertErrContains(
        'Use [gcloud compute operations describe URI] command to check the '
        'status of the operation(s).')

  def testInstancesStopManyAsync(self):
    num_instances = 3
    op_refs = [
        self._GetOperationRef('operation-%d' % i) for i in range(num_instances)
    ]
    stop_refs = [
        self._GetInstancesStopRef('instance-%d' % i)
        for i in range(num_instances)
    ]

    self.api_mock.batch_responder.ExpectBatch(
        [((self.compute.instances, 'Stop', self._CreateInstancesStopRequest(
            stop_refs[i])),
          (self._GetOperationMessage(op_refs[i], self.status_enum.PENDING)))
         for i in range(num_instances)])

    self.Run("""
        compute instances stop
          instance-0 instance-1 instance-2
          --zone central2-a --async
        """)

    self.AssertOutputEquals('')
    for op_ref in op_refs:
      self.AssertErrContains(
          'Stop instance in progress for [{}].'.format(op_ref))
    self.AssertErrContains(
        'Use [gcloud compute operations describe URI] command to check the '
        'status of the operation(s).')


class InstancesStopTestAlpha(InstancesStopTestBase):

  def SetUp(self):
    # Select API track to set up self.messages, self.compute.
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

    self.api_mock = utils.ComputeApiMock(
        'alpha', project=self.Project(), zone='central2-a').Start()
    self.addCleanup(self.api_mock.Stop)

    self.status_enum = self.api_mock.messages.Operation.StatusValueValuesEnum

  def _CreateInstancesStopRequest(self, stop_ref, discard_local_ssd):
    return self.api_mock.messages.ComputeInstancesStopRequest(
        instance=stop_ref.Name(),
        project=self.Project(),
        zone=stop_ref.zone,
        discardLocalSsd=discard_local_ssd)

  def _GetInstancesStopRequest(self, stop_ref):
    return (self.compute.instances, 'Get',
            self.api_mock.messages.ComputeInstancesStopRequest(
                instance=stop_ref.Name(),
                project=self.Project(),
                zone=stop_ref.zone))

  def testDiscardLocalSsd(self):
    op_ref = self._GetOperationRef('operation-1')
    stop_ref = self._GetInstancesStopRef('instance-1')
    self.api_mock.batch_responder.ExpectBatch(
        [((self.compute.instances, 'Stop', self._CreateInstancesStopRequest(
            stop_ref, True)), (self._GetOperationMessage(
                op_ref, self.status_enum.PENDING)))])

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetOperationGetRequest(op_ref), self._GetOperationMessage(
            op_ref, self.status_enum.DONE)),
    ])

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetInstancesStopRequest(stop_ref),
         self._CreateInstancesStopRequest(stop_ref, True)),
    ])

    self.Run('compute instances stop instance-1 --zone central2-a '
             '--discard-local-ssd')

    self.AssertOutputEquals('')
    self.AssertErrContains('Stopping instance(s) instance-1')

  def testDiscardLocalSsdFalse(self):
    op_ref = self._GetOperationRef('operation-1')
    stop_ref = self._GetInstancesStopRef('instance-1')
    self.api_mock.batch_responder.ExpectBatch(
        [((self.compute.instances, 'Stop', self._CreateInstancesStopRequest(
            stop_ref, False)), (self._GetOperationMessage(
                op_ref, self.status_enum.PENDING)))])

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetOperationGetRequest(op_ref), self._GetOperationMessage(
            op_ref, self.status_enum.DONE)),
    ])

    self.api_mock.batch_responder.ExpectBatch([
        (self._GetInstancesStopRequest(stop_ref),
         self._CreateInstancesStopRequest(stop_ref, False)),
    ])

    self.Run('compute instances stop instance-1 --zone central2-a '
             '--no-discard-local-ssd')

    self.AssertOutputEquals('')
    self.AssertErrContains('Stopping instance(s) instance-1')


if __name__ == '__main__':
  test_case.main()
