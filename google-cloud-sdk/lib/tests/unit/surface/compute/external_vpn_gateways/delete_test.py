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
"""Tests for the external VPN gateways delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import external_vpn_gateways_test_base
from tests.lib.surface.compute import utils


class ExternalVpnGatewayDeleteBetaTest(
    external_vpn_gateways_test_base.ExternalVpnGatewaysTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.api_mock = utils.ComputeApiMock(
        self._GetApiName(), project=self.Project()).Start()
    self.addCleanup(self.api_mock.Stop)

  def TearDown(self):
    self.api_mock.batch_responder.AssertDone()

  def _MakeOperationGetRequest(self, operation_ref):
    return (self.global_operations, 'Get',
            self.messages.ComputeGlobalOperationsGetRequest(
                **operation_ref.AsDict()))

  def testDeleteSingleExternalVpnGateway(self):
    name = 'my-gateway'
    gateway_ref = self.GetExternalVpnGatewayRef(name)
    operation_ref = self.GetOperationRef('operation-1')
    pending_operation = self.MakeOperationMessage(
        operation_ref, self.messages.Operation.StatusValueValuesEnum.PENDING,
        gateway_ref)
    done_operation = self.MakeOperationMessage(
        operation_ref, self.messages.Operation.StatusValueValuesEnum.DONE,
        gateway_ref)

    self.ExpectDeleteRequest(gateway_ref, pending_operation)

    self.api_mock.batch_responder.ExpectBatch(
        [(self._MakeOperationGetRequest(operation_ref), pending_operation)])
    self.api_mock.batch_responder.ExpectBatch(
        [(self._MakeOperationGetRequest(operation_ref), done_operation)])

    self.Run('compute external-vpn-gateways delete {}'.format(name))

  def testDeleteMultipleExternalVpnGateways(self):
    names = ['my-gateway-{}'.format(n) for n in range(0, 3)]
    gateway_refs = [self.GetExternalVpnGatewayRef(name) for name in names]
    operation_refs = [
        self.GetOperationRef('operation-{}'.format(n)) for n in range(0, 3)
    ]
    pending_operations = [
        self.MakeOperationMessage(
            operation_refs[0],
            self.messages.Operation.StatusValueValuesEnum.PENDING,
            gateway_refs[0]),
        self.MakeOperationMessage(
            operation_refs[1],
            self.messages.Operation.StatusValueValuesEnum.PENDING,
            gateway_refs[1]),
        self.MakeOperationMessage(
            operation_refs[2],
            self.messages.Operation.StatusValueValuesEnum.PENDING,
            gateway_refs[2]),
    ]
    done_operations = [
        self.MakeOperationMessage(
            operation_refs[0],
            self.messages.Operation.StatusValueValuesEnum.DONE,
            gateway_refs[0]),
        self.MakeOperationMessage(
            operation_refs[1],
            self.messages.Operation.StatusValueValuesEnum.DONE,
            gateway_refs[1]),
        self.MakeOperationMessage(
            operation_refs[2],
            self.messages.Operation.StatusValueValuesEnum.DONE, gateway_refs[2])
    ]

    for n in range(0, 3):
      self.ExpectDeleteRequest(gateway_refs[n], pending_operations[n])

    self.api_mock.batch_responder.ExpectBatch([(self._MakeOperationGetRequest(
        operation_refs[n]), pending_operations[n]) for n in range(0, 3)])
    self.api_mock.batch_responder.ExpectBatch([(self._MakeOperationGetRequest(
        operation_refs[n]), done_operations[n]) for n in range(0, 3)])

    self.Run('compute external-vpn-gateways delete {}'.format(' '.join(names)))


class ExternalVpnGatewayDeleteAlphaTest(ExternalVpnGatewayDeleteBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
