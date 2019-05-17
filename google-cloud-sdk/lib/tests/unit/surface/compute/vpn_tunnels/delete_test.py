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
"""Tests for the vpn-tunnels delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.exceptions import ToolException
from tests.lib import test_case
from tests.lib.surface.compute import utils
from tests.lib.surface.compute import vpn_tunnels_test_base
from six.moves import range  # pylint: disable=redefined-builtin


class VpnTunnelsDeleteGATest(vpn_tunnels_test_base.VpnTunnelsTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.api_mock = utils.ComputeApiMock(
        self._GetApiName(), project=self.Project()).Start()
    self.addCleanup(self.api_mock.Stop)

  def TearDown(self):
    self.api_mock.batch_responder.AssertDone()

  def _MakeOperationGetRequest(self, operation_ref):
    return (self.region_operations, 'Get',
            self.messages.ComputeRegionOperationsGetRequest(
                **operation_ref.AsDict()))

  def testDeleteSingleVpnTunnel(self):
    name = 'my-tunnel'
    vpn_tunnel_ref = self.GetVpnTunnelRef(name)
    operation_ref = self.GetOperationRef('operation-1')
    pending_operation = self.MakeOperationMessage(
        operation_ref, self.messages.Operation.StatusValueValuesEnum.PENDING,
        vpn_tunnel_ref)
    done_operation = self.MakeOperationMessage(
        operation_ref, self.messages.Operation.StatusValueValuesEnum.DONE,
        vpn_tunnel_ref)

    self.ExpectDeleteRequest(vpn_tunnel_ref, pending_operation)

    self.api_mock.batch_responder.ExpectBatch(
        [(self._MakeOperationGetRequest(operation_ref), pending_operation)])
    self.api_mock.batch_responder.ExpectBatch(
        [(self._MakeOperationGetRequest(operation_ref), done_operation)])

    self.Run('compute vpn-tunnels delete {} --region {}'.format(
        name, self.REGION))

  def testDeleteMultipleVpnTunnels(self):
    names = []
    operation_refs = []
    pending_operations = []
    done_operations = []
    for index in range(0, 3):
      name = 'my-vpn-tunnel-{}'.format(index)
      vpn_tunnel_ref = self.GetVpnTunnelRef(name)
      operation_ref = self.GetOperationRef('operation-{}'.format(index))
      operation_refs.append(operation_ref)
      pending_operation = self.MakeOperationMessage(
          operation_ref, self.messages.Operation.StatusValueValuesEnum.PENDING,
          vpn_tunnel_ref)
      done_operation = self.MakeOperationMessage(
          operation_ref, self.messages.Operation.StatusValueValuesEnum.DONE,
          vpn_tunnel_ref)
      self.ExpectDeleteRequest(vpn_tunnel_ref, pending_operation)
      names.append(name)
      pending_operations.append(pending_operation)
      done_operations.append(done_operation)

    self.api_mock.batch_responder.ExpectBatch([(self._MakeOperationGetRequest(
        operation_refs[n]), pending_operations[n]) for n in range(0, 3)])
    self.api_mock.batch_responder.ExpectBatch([(self._MakeOperationGetRequest(
        operation_refs[n]), done_operations[n]) for n in range(0, 3)])

    self.Run('compute vpn-tunnels delete {} --region {}'.format(
        ' '.join(names), self.REGION))

  def testReplyingNoToPromptAborts(self):
    self.WriteInput('n\n')
    with self.assertRaises(ToolException):
      self.Run('compute vpn-tunnels delete my-tunnel --region {}'.format(
          self.REGION))
    self.AssertErrContains('Deletion aborted by user.')


class VpnTunnelsDeleteBetaTest(VpnTunnelsDeleteGATest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class VpnTunnelsDeleteAlphaTest(VpnTunnelsDeleteBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
