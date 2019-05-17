# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for the vpn-gateways delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import utils
from tests.lib.surface.compute import vpn_gateways_test_base
from six.moves import range  # pylint: disable=redefined-builtin


class VpnGatewayDeleteBetaTest(vpn_gateways_test_base.VpnGatewaysTestBase):

  def SetUp(self):
    self._SetUpReleaseTrack()
    self.api_mock = utils.ComputeApiMock(
        self._GetApiName(self.track), project=self.Project()).Start()
    self.addCleanup(self.api_mock.Stop)

  def TearDown(self):
    self.api_mock.batch_responder.AssertDone()

  def _SetUpReleaseTrack(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)

  def _MakeOperationGetRequest(self, operation_ref):
    return (self.region_operations, 'Get',
            self.messages.ComputeRegionOperationsGetRequest(
                **operation_ref.AsDict()))

  def testDeleteSingleVpnGateway(self):
    name = 'my-vpn-gateway'
    vpn_gateway_ref = self.GetVpnGatewayRef(name)
    operation_ref = self.GetOperationRef('operation-1')
    pending_operation = self.MakeOperationMessage(
        operation_ref, self.messages.Operation.StatusValueValuesEnum.PENDING,
        vpn_gateway_ref)
    done_operation = self.MakeOperationMessage(
        operation_ref, self.messages.Operation.StatusValueValuesEnum.DONE,
        vpn_gateway_ref)

    self.ExpectDeleteRequest(vpn_gateway_ref, pending_operation)

    self.api_mock.batch_responder.ExpectBatch(
        [(self._MakeOperationGetRequest(operation_ref), pending_operation)])
    self.api_mock.batch_responder.ExpectBatch(
        [(self._MakeOperationGetRequest(operation_ref), done_operation)])

    self.Run('compute vpn-gateways delete {} --region {}'.format(
        name, self.REGION))

  def testDeleteMultipleVpnGateways(self):
    names = []
    operation_refs = []
    pending_operations = []
    done_operations = []
    for index in range(0, 3):
      name = 'my-vpn-gateway-{}'.format(index)
      vpn_gateway_ref = self.GetVpnGatewayRef(name)
      operation_ref = self.GetOperationRef('operation-{}'.format(index))
      operation_refs.append(operation_ref)
      pending_operation = self.MakeOperationMessage(
          operation_ref, self.messages.Operation.StatusValueValuesEnum.PENDING,
          vpn_gateway_ref)
      done_operation = self.MakeOperationMessage(
          operation_ref, self.messages.Operation.StatusValueValuesEnum.DONE,
          vpn_gateway_ref)
      self.ExpectDeleteRequest(vpn_gateway_ref, pending_operation)
      names.append(name)
      pending_operations.append(pending_operation)
      done_operations.append(done_operation)

    self.api_mock.batch_responder.ExpectBatch([(self._MakeOperationGetRequest(
        operation_refs[n]), pending_operations[n]) for n in range(0, 3)])
    self.api_mock.batch_responder.ExpectBatch([(self._MakeOperationGetRequest(
        operation_refs[n]), done_operations[n]) for n in range(0, 3)])

    self.Run('compute vpn-gateways delete {} --region {}'.format(
        ' '.join(names), self.REGION))


class VpnGatewayDeleteAlphaTest(VpnGatewayDeleteBetaTest):

  def _SetUpReleaseTrack(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
