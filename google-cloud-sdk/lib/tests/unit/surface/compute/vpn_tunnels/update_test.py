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
"""Tests for VPN tunnels update."""

from __future__ import absolute_import
from __future__ import unicode_literals
import copy
import textwrap

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import vpn_tunnels_labels_test_base


class UpdateLabelsTestBeta(
    vpn_tunnels_labels_test_base.VpnTunnelsLabelsTestBase):

  def SetUp(self):
    super(vpn_tunnels_labels_test_base.VpnTunnelsLabelsTestBase, self).SetUp()
    self.vpn_tunnel_ref = self._GetVpnTunnelRef('gw-1', region='us-central1')

  def testUpdateMissingNameOrLabels(self):
    with self.assertRaisesRegex(exceptions.RequiredArgumentException,
                                'At least one of --update-labels or '
                                '--remove-labels must be specified.'):
      self.Run('compute vpn-tunnels update {0} --region {1}'.format(
          self.vpn_tunnel_ref.Name(), self.vpn_tunnel_ref.region))

  def testUpdateAndRemoveLabels(self):
    vpn_tunnel_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                                  'value3'))
    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (('key2', 'update2'), ('key3', 'value3'), ('key4',
                                                               'value4'))

    vpn_tunnel = self._MakeVpnTunnelProto(
        labels=vpn_tunnel_labels, fingerprint=b'fingerprint-42')
    updated_vpn_tunnel = self._MakeVpnTunnelProto(labels=edited_labels)

    operation_ref = self._GetOperationRef('operation-1', 'us-central1')
    operation = self._MakeOperationMessage(operation_ref, self.vpn_tunnel_ref)

    self._ExpectGetRequest(self.vpn_tunnel_ref, vpn_tunnel)
    self._ExpectLabelsSetRequest(self.vpn_tunnel_ref, edited_labels,
                                 b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(self.vpn_tunnel_ref, updated_vpn_tunnel)

    response = self.Run(
        'compute vpn-tunnels update {0} --update-labels {1} '
        '--remove-labels key1,key0'.format(
            self.vpn_tunnel_ref.SelfLink(), ','.join(
                '{0}={1}'.format(pair[0], pair[1]) for pair in update_labels)))
    self.assertEqual(response, updated_vpn_tunnel)

  def testUpdateClearLabels(self):
    vpn_tunnel_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                                  'value3'))
    edited_labels = ()

    vpn_tunnel = self._MakeVpnTunnelProto(
        labels=vpn_tunnel_labels, fingerprint=b'fingerprint-42')
    updated_vpn_tunnel = self._MakeVpnTunnelProto(labels=edited_labels)

    operation_ref = self._GetOperationRef('operation-1', 'us-central1')
    operation = self._MakeOperationMessage(operation_ref, self.vpn_tunnel_ref)

    self._ExpectGetRequest(self.vpn_tunnel_ref, vpn_tunnel)
    self._ExpectLabelsSetRequest(self.vpn_tunnel_ref, edited_labels,
                                 b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(self.vpn_tunnel_ref, updated_vpn_tunnel)

    response = self.Run('compute vpn-tunnels update {0} --clear-labels'.format(
        self.vpn_tunnel_ref.SelfLink()))
    self.assertEqual(response, updated_vpn_tunnel)

  def testUpdateWithNoLabels(self):
    update_labels = (('key2', 'update2'), ('key4', 'value4'))

    vpn_tunnel = self._MakeVpnTunnelProto(
        labels=(), fingerprint=b'fingerprint-42')
    updated_vpn_tunnel = self._MakeVpnTunnelProto(labels=update_labels)
    operation_ref = self._GetOperationRef('operation-1', 'us-central1')
    operation = self._MakeOperationMessage(operation_ref, self.vpn_tunnel_ref)

    self._ExpectGetRequest(self.vpn_tunnel_ref, vpn_tunnel)
    self._ExpectLabelsSetRequest(self.vpn_tunnel_ref, update_labels,
                                 b'fingerprint-42', operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(self.vpn_tunnel_ref, updated_vpn_tunnel)

    response = self.Run(
        'compute vpn-tunnels update {0} --update-labels {1} '.format(
            self.vpn_tunnel_ref.SelfLink(), ','.join(
                '{0}={1}'.format(pair[0], pair[1]) for pair in update_labels)))
    self.assertEqual(response, updated_vpn_tunnel)

  def testRemoveWithNoLabelsOnVpnTunnel(self):
    vpn_tunnel = self._MakeVpnTunnelProto(
        labels={}, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(self.vpn_tunnel_ref, vpn_tunnel)

    response = self.Run(
        'compute vpn-tunnels update {0} --remove-labels DoesNotExist'.format(
            self.vpn_tunnel_ref.SelfLink()))
    self.assertEqual(response, vpn_tunnel)

  def testNoNetUpdate(self):
    vpn_tunnel_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                                  'value3'))
    update_labels = copy.deepcopy(vpn_tunnel_labels)

    vpn_tunnel = self._MakeVpnTunnelProto(
        labels=vpn_tunnel_labels, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(self.vpn_tunnel_ref, vpn_tunnel)

    response = self.Run(
        'compute vpn-tunnels update {0} --update-labels {1} '
        '--remove-labels key4'.format(self.vpn_tunnel_ref.SelfLink(), ','.join(
            '{0}={1}'.format(pair[0], pair[1]) for pair in update_labels)))
    self.assertEqual(response, vpn_tunnel)

  def testScopePrompt(self):
    vpn_tunnel = self._MakeVpnTunnelProto(labels=[])
    self._ExpectGetRequest(self.vpn_tunnel_ref, vpn_tunnel)

    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.regions.service.List',
        return_value=[
            self.messages.Region(name='us-central1'),
            self.messages.Region(name='us-central2')
        ],
    )
    self.WriteInput('1\n')
    self.Run('compute vpn-tunnels update gw-1 --remove-labels key0')
    self.AssertErrEquals(
        textwrap.dedent("""\
            For the following VPN Tunnel:
             - [gw-1]
            choose a region:
             [1] us-central1
             [2] us-central2
            Please enter your numeric choice:{0}
            """.format('  ')))


if __name__ == '__main__':
  test_case.main()
