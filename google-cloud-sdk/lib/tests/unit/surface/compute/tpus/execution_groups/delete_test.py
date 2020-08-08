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

from apitools.base.py.exceptions import HttpNotFoundError
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.compute.tpus import base


class DeleteTest(base.TpuUnitTestBase, waiter_test_base.CloudOperationsBase):

  _NAME = 'tpu-to-be-deleted'
  _TPU_OP_NAME = 'projects/fake-project/locations/central2-a/operations/fake-operation'
  _INSTANCE_OP_NAME = u'fake-operation-random-guid'

  def PreSetUp(self):
    self._SetTrack(calliope_base.ReleaseTrack.ALPHA)
    self._SetApiVersion('v1alpha1')
    self.compute_api_version = 'alpha'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.instances_messages = core_apis.GetMessagesModule(
        'compute', self.compute_api_version)
    self.mock_instance_client = mock.Client(
        core_apis.GetClientClass('compute', self.compute_api_version),
        real_client=core_apis.GetClientInstance(
            'compute', self.compute_api_version, no_http=True))
    self.mock_instance_client.Mock()
    self.addCleanup(self.mock_instance_client.Unmock)
    properties.VALUES.core.user_output_enabled.Set(True)

  def _expectTPUDeleteCall(self, name, tpu_op_name):
    self.mock_tpu_client.projects_locations_nodes.Delete.Expect(
        request=self.tpu_messages.TpuProjectsLocationsNodesDeleteRequest(
            name='projects/fake-project/locations/central2-a/nodes/{}'.format(
                name)),
        response=self.tpu_messages.Operation(
            done=False,
            name=tpu_op_name,
            response=self.tpu_messages.Operation.ResponseValue()
            )
        )

  def _expectTPUDeleteOp(self, tpu_op_name):
    request_type = self.mock_tpu_client.projects_locations_operations.GetRequestType(
        'Get')
    response_type = self.mock_tpu_client.projects_locations_operations.GetResponseType(
        'Get')
    response = response_type(done=True, response=response_type.ResponseValue())
    self.mock_tpu_client.projects_locations_operations.Get.Expect(
        request=request_type(name=tpu_op_name),
        response=response
        )

  def _expectTPUDeleteCallWithHTTPNotFound(self, name, tpu_op_name):
    self.mock_tpu_client.projects_locations_nodes.Delete.Expect(
        request=self.tpu_messages.TpuProjectsLocationsNodesDeleteRequest(
            name='projects/fake-project/locations/central2-a/nodes/{}'.format(
                name)),
        exception=HttpNotFoundError(None, None, None)
        )

  def _expectInstanceDeleteCall(self, name, instance_op_name):
    self.mock_instance_client.instances.Delete.Expect(
        request=self.instances_messages.ComputeInstancesDeleteRequest(
            project='fake-project',
            zone='central2-a',
            instance=name
            ),
        response=self.instances_messages.Operation(
            name=instance_op_name,
            zone='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a',
            operationType='delete',
            targetLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/instances/{}'
            .format(name),
            selfLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/operations/{}'
            .format(instance_op_name),
            status=self.instances_messages.Operation.StatusValueValuesEnum
            .PENDING))

  def _expectInstanceDeleteCallWithHTTPNotFound(self, name, instance_op_name):
    self.mock_instance_client.instances.Delete.Expect(
        request=self.instances_messages.ComputeInstancesDeleteRequest(
            project='fake-project',
            zone='central2-a',
            instance=name
            ),
        exception=HttpNotFoundError(None, None, None))

  def _expectInstanceOperationCall(self, name, instance_op_name):
    self.mock_instance_client.zoneOperations.Wait.Expect(
        request=self.instances_messages.ComputeZoneOperationsWaitRequest(
            operation=instance_op_name,
            project=u'fake-project',
            zone=u'central2-a'),
        response=self._buildOperationResponse(
            name, instance_op_name,
            self.instances_messages.Operation.StatusValueValuesEnum.DONE))

  def _expectInstanceOperationCallWithHTTPNotFound(self, name,
                                                   instance_op_name):
    self.mock_instance_client.zoneOperations.Wait.Expect(
        request=self.instances_messages.ComputeZoneOperationsWaitRequest(
            operation=instance_op_name,
            project=u'fake-project',
            zone=u'central2-a'),
        exception=HttpNotFoundError(None, None, None))

  def _expectTPUOperationCallWithHTTPNotFound(self, name, tpu_op_name):
    result_request_type = self.mock_tpu_client.projects_locations_operations.GetRequestType(
        'Get')
    self.mock_tpu_client.projects_locations_operations.Get.Expect(
        request=result_request_type(name=tpu_op_name),
        exception=HttpNotFoundError(None, None, None)
        )

  def _buildOperationResponse(self, name, instance_op_name, status):
    return self.instances_messages.Operation(
        name=instance_op_name,
        zone='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a',
        operationType='delete',
        targetLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/instances/{}'
        .format(name),
        selfLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/operations/{}'
        .format(instance_op_name),
        status=status)

  def testDeleteCommand(self):
    self._expectTPUDeleteCall(self._NAME, self._TPU_OP_NAME)
    self._expectInstanceDeleteCall(self._NAME, self._INSTANCE_OP_NAME)
    self._expectTPUDeleteOp(self._TPU_OP_NAME)
    self._expectInstanceOperationCall(self._NAME, self._INSTANCE_OP_NAME)
    self.Run("""
      compute tpus execution-groups delete {} --zone=central2-a
    """.format(self._NAME))

  def testDeleteCommandHTTPNotFoundOnNode(self):
    self._expectTPUDeleteCallWithHTTPNotFound(self._NAME, self._TPU_OP_NAME)
    self._expectInstanceDeleteCall(self._NAME, self._INSTANCE_OP_NAME)
    self._expectInstanceOperationCall(self._NAME, self._INSTANCE_OP_NAME)
    self.Run("""
      compute tpus execution-groups delete {} --zone=central2-a
    """.format(self._NAME))
    self.AssertErrContains(
        'TPU Node:{} not found, possibly already deleted.'
        .format(self._NAME), normalize_space=True)

  def testDeleteCommandHTTPNotFoundOnInstance(self):
    self._expectTPUDeleteCall(self._NAME, self._TPU_OP_NAME)
    self._expectInstanceDeleteCallWithHTTPNotFound(self._NAME,
                                                   self._INSTANCE_OP_NAME)
    self._expectTPUDeleteOp(self._TPU_OP_NAME)
    self.Run("""
      compute tpus execution-groups delete {} --zone=central2-a
    """.format(self._NAME))
    self.AssertErrContains(
        'Instance:{} not found, possibly already deleted.'
        .format(self._NAME), normalize_space=True)

  def testDeleteCommandHTTPNotFoundOnPollInstanceOp(self):
    self._expectTPUDeleteCall(self._NAME, self._TPU_OP_NAME)
    self._expectInstanceDeleteCall(self._NAME, self._INSTANCE_OP_NAME)
    self._expectTPUDeleteOp(self._TPU_OP_NAME)
    self._expectInstanceOperationCallWithHTTPNotFound(self._NAME,
                                                      self._INSTANCE_OP_NAME)
    self.Run("""
      compute tpus execution-groups delete {} --zone=central2-a
    """.format(self._NAME))
    self.AssertErrContains(
        'Instance:{} not found, possibly already deleted.'
        .format(self._NAME), normalize_space=True)

  def testDeleteCommandHTTPNotFoundOnPollNodeOp(self):
    self._expectTPUDeleteCall(self._NAME, self._TPU_OP_NAME)
    self._expectInstanceDeleteCall(self._NAME, self._INSTANCE_OP_NAME)
    self._expectTPUOperationCallWithHTTPNotFound(
        self._NAME, self._TPU_OP_NAME)
    self._expectInstanceOperationCall(self._NAME, self._INSTANCE_OP_NAME)
    self.Run("""
      compute tpus execution-groups delete {} --zone=central2-a
    """.format(self._NAME))
    self.AssertErrContains(
        'TPU Node:{} not found, possibly already deleted.'
        .format(self._NAME), normalize_space=True)
