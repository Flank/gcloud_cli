# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import vpn_tunnels_test_base


class ClassicVpnTunnelsUpdateLabelsBetaTest(
    vpn_tunnels_test_base.VpnTunnelsTestBase):

  _TARGET_VPN_GATEWAY_NAME = 'my-target-vpn-gateway'
  _IKE_VERSION = 2
  _PEER_IP_ADDRESS = '71.72.73.74'
  _SHARED_SECRET = 'shared-secret'
  _VPN_TUNNEL_NAME = 'my-vpn-tunnel'
  _FINGERPRINT_1 = b'fingerprint-9876'
  _FINGERPRINT_2 = b'fingerprint-9875'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _MakeVpnTunnel(self, vpn_tunnel_ref, fingerprint, labels=None):
    vpn_tunnel = self.messages.VpnTunnel(
        name=vpn_tunnel_ref.Name(),
        ikeVersion=self._IKE_VERSION,
        peerIp=self._PEER_IP_ADDRESS,
        sharedSecret=self._SHARED_SECRET,
        targetVpnGateway=self.GetTargetVpnGatewayRef(
            self._TARGET_VPN_GATEWAY_NAME).SelfLink(),
        labelFingerprint=fingerprint)
    if labels:
      vpn_tunnel.labels = self.MakeLabelsMessage(
          self.messages.VpnTunnel.LabelsValue, labels)
    return vpn_tunnel

  def _ExpectSetLabels(self, vpn_tunnel_ref, existing_labels,
                       labels_after_update):
    existing_vpn_tunnel = self._MakeVpnTunnel(
        vpn_tunnel_ref, self._FINGERPRINT_1, existing_labels)
    updated_vpn_tunnel = self._MakeVpnTunnel(
        vpn_tunnel_ref, self._FINGERPRINT_2, labels_after_update)
    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=vpn_tunnel_ref)

    self.ExpectGetRequest(vpn_tunnel_ref, existing_vpn_tunnel)
    self.ExpectSetLabelsRequest(vpn_tunnel_ref, labels_after_update,
                                self._FINGERPRINT_1, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(vpn_tunnel_ref, updated_vpn_tunnel)
    return updated_vpn_tunnel

  def _ExpectNoSetLabels(self, vpn_tunnel_ref, existing_labels):
    existing_vpn_tunnel = self._MakeVpnTunnel(
        vpn_tunnel_ref, self._FINGERPRINT_1, existing_labels)
    self.ExpectGetRequest(vpn_tunnel_ref, existing_vpn_tunnel)
    return existing_vpn_tunnel

  def testWithoutFlags(self):
    vpn_tunnel_ref = self.GetVpnTunnelRef(self._VPN_TUNNEL_NAME)
    with self.assertRaisesRegex(
        exceptions.RequiredArgumentException,
        'At least one of --update-labels or '
        '--remove-labels must be specified.'):
      self.Run('compute vpn-tunnels update {0} --region {1}'.format(
          vpn_tunnel_ref.Name(), vpn_tunnel_ref.region))

  def testUpdateAndRemoveLabels(self):
    existing_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                                'value3'))
    labels_to_remove = ('key1', 'key0')
    labels_to_update = (('key2', 'update2'), ('key4', 'value4'))
    labels_after_update = (('key2', 'update2'), ('key3', 'value3'), ('key4',
                                                                     'value4'))
    vpn_tunnel_ref = self.GetVpnTunnelRef(self._VPN_TUNNEL_NAME)
    expected_updated_vpn_tunnel = self._ExpectSetLabels(
        vpn_tunnel_ref, existing_labels, labels_after_update)

    labels_to_update_cmd = ','.join(
        '{0}={1}'.format(pair[0], pair[1]) for pair in labels_to_update)
    labels_to_remove_cmd = ','.join(labels_to_remove)
    response = self.Run('compute vpn-tunnels update {} '
                        '--region {} '
                        '--update-labels {} '
                        '--remove-labels {}'.format(
                            vpn_tunnel_ref.Name(), vpn_tunnel_ref.region,
                            labels_to_update_cmd, labels_to_remove_cmd))
    self.assertEqual(response, expected_updated_vpn_tunnel)

  def testClearLabels(self):
    existing_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                                'value3'))
    labels_after_update = ()

    vpn_tunnel_ref = self.GetVpnTunnelRef(self._VPN_TUNNEL_NAME)
    expected_updated_vpn_tunnel = self._ExpectSetLabels(
        vpn_tunnel_ref, existing_labels, labels_after_update)

    response = self.Run('compute vpn-tunnels update {} '
                        '--region {} '
                        '--clear-labels'.format(vpn_tunnel_ref.Name(),
                                                vpn_tunnel_ref.region))
    self.assertEqual(response, expected_updated_vpn_tunnel)

  def testUpdateWithNoExistingLabels(self):
    existing_labels = ()
    labels_to_update = (('key2', 'update2'), ('key4', 'value4'))
    labels_after_update = labels_to_update

    vpn_tunnel_ref = self.GetVpnTunnelRef(self._VPN_TUNNEL_NAME)
    expected_updated_vpn_tunnel = self._ExpectSetLabels(
        vpn_tunnel_ref, existing_labels, labels_after_update)

    labels_to_update_cmd = ','.join(
        '{0}={1}'.format(pair[0], pair[1]) for pair in labels_to_update)
    response = self.Run('compute vpn-tunnels update {} '
                        '--region {} '
                        '--update-labels {}'.format(vpn_tunnel_ref.Name(),
                                                    vpn_tunnel_ref.region,
                                                    labels_to_update_cmd))
    self.assertEqual(response, expected_updated_vpn_tunnel)

  def testRemoveNonExistingLabels(self):
    existing_labels = (('key1', 'value1'), ('key2', 'value2'))

    vpn_tunnel_ref = self.GetVpnTunnelRef(self._VPN_TUNNEL_NAME)
    existing_vpn_tunnel = self._ExpectNoSetLabels(vpn_tunnel_ref,
                                                  existing_labels)

    response = self.Run('compute vpn-tunnels update {} '
                        '--region {} '
                        '--remove-labels DoesNotExist'.format(
                            vpn_tunnel_ref.Name(), vpn_tunnel_ref.region))
    self.assertEqual(response, existing_vpn_tunnel)

  def testNoNetUpdate(self):
    existing_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                                'value3'))
    labels_to_remove = ('key4')
    labels_to_update = existing_labels
    vpn_tunnel_ref = self.GetVpnTunnelRef(self._VPN_TUNNEL_NAME)
    existing_vpn_tunnel = self._ExpectNoSetLabels(vpn_tunnel_ref,
                                                  existing_labels)

    labels_to_update_cmd = ','.join(
        '{0}={1}'.format(pair[0], pair[1]) for pair in labels_to_update)
    labels_to_remove_cmd = ','.join(labels_to_remove)
    response = self.Run('compute vpn-tunnels update {} '
                        '--region {} '
                        '--update-labels {} '
                        '--remove-labels {}'.format(
                            vpn_tunnel_ref.Name(), vpn_tunnel_ref.region,
                            labels_to_update_cmd, labels_to_remove_cmd))
    self.assertEqual(response, existing_vpn_tunnel)


class ClassicVpnTunnelsUpdateLabelsAlphaTest(
    ClassicVpnTunnelsUpdateLabelsBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class HighAvailabilityVpnTunnelsUpdateLabelsAlphaTest(
    ClassicVpnTunnelsUpdateLabelsAlphaTest):

  _VPN_GATEWAY_NAME = 'my-vpn-gateway'
  _VPN_INTERFACE = 1

  def _MakeVpnTunnel(self, vpn_tunnel_ref, fingerprint, labels=None):
    vpn_tunnel = self.messages.VpnTunnel(
        name=vpn_tunnel_ref.Name(),
        ikeVersion=self._IKE_VERSION,
        peerIp=self._PEER_IP_ADDRESS,
        sharedSecret=self._SHARED_SECRET,
        vpnGateway=self.GetVpnGatewayRef(self._VPN_GATEWAY_NAME).SelfLink(),
        vpnGatewayInterface=self._VPN_INTERFACE,
        labelFingerprint=fingerprint)
    if labels:
      vpn_tunnel.labels = self.MakeLabelsMessage(
          self.messages.VpnTunnel.LabelsValue, labels)
    return vpn_tunnel


if __name__ == '__main__':
  test_case.main()
