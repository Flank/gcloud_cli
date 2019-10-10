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
"""Tests for target VPN gateways update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import vpn_gateways_test_base


class VpnGatewaysUpdateLabelsGaTest(
    vpn_gateways_test_base.VpnGatewaysTestBase):

  _VPN_GATEWAY_NAME = 'my-vpn-gateway'
  _NETWORK = 'network1'
  _FINGERPRINT_1 = b'fingerprint-9876'
  _FINGERPRINT_2 = b'fingerprint-9875'

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.GA)

  def _MakeVpnGateway(self, vpn_gateway_ref, fingerprint, labels=None):
    vpn_gateway = self.messages.VpnGateway(
        name=vpn_gateway_ref.Name(),
        network=self.GetNetworkRef(self._NETWORK).SelfLink(),
        labelFingerprint=fingerprint)
    if labels:
      vpn_gateway.labels = self.MakeLabelsMessage(
          self.messages.VpnGateway.LabelsValue, labels)
    return vpn_gateway

  def _ExpectSetLabels(self, vpn_gateway_ref, existing_labels,
                       labels_after_update):
    existing_vpn_gateway = self._MakeVpnGateway(
        vpn_gateway_ref, self._FINGERPRINT_1, existing_labels)
    updated_vpn_gateway = self._MakeVpnGateway(
        vpn_gateway_ref, self._FINGERPRINT_2, labels_after_update)
    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=vpn_gateway_ref)

    self.ExpectGetRequest(vpn_gateway_ref, existing_vpn_gateway)
    self.ExpectSetLabelsRequest(vpn_gateway_ref, labels_after_update,
                                self._FINGERPRINT_1, operation)
    self.ExpectOperationGetRequest(operation_ref, operation)
    self.ExpectGetRequest(vpn_gateway_ref, updated_vpn_gateway)
    return updated_vpn_gateway

  def _ExpectNoSetLabels(self, vpn_gateway_ref, existing_labels):
    existing_vpn_gateway = self._MakeVpnGateway(
        vpn_gateway_ref, self._FINGERPRINT_1, existing_labels)
    self.ExpectGetRequest(vpn_gateway_ref, existing_vpn_gateway)
    return existing_vpn_gateway

  def testWithoutFlags(self):
    vpn_gateway_ref = self.GetVpnGatewayRef(self._VPN_GATEWAY_NAME)
    with self.assertRaisesRegex(
        exceptions.RequiredArgumentException,
        'At least one of --update-labels or '
        '--remove-labels must be specified.'):
      self.Run('compute vpn-gateways update {0} --region {1}'.format(
          vpn_gateway_ref.Name(), vpn_gateway_ref.region))

  def testUpdateAndRemoveLabels(self):
    existing_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                                'value3'))
    labels_to_remove = ('key1', 'key0')
    labels_to_update = (('key2', 'update2'), ('key4', 'value4'))
    labels_after_update = (('key2', 'update2'), ('key3', 'value3'), ('key4',
                                                                     'value4'))
    vpn_gateway_ref = self.GetVpnGatewayRef(self._VPN_GATEWAY_NAME)
    expected_updated_vpn_gateway = self._ExpectSetLabels(
        vpn_gateway_ref, existing_labels, labels_after_update)

    labels_to_update_cmd = ','.join(
        '{0}={1}'.format(pair[0], pair[1]) for pair in labels_to_update)
    labels_to_remove_cmd = ','.join(labels_to_remove)
    response = self.Run('compute vpn-gateways update {} '
                        '--region {} '
                        '--update-labels {} '
                        '--remove-labels {}'.format(
                            vpn_gateway_ref.Name(), vpn_gateway_ref.region,
                            labels_to_update_cmd, labels_to_remove_cmd))
    self.assertEqual(response, expected_updated_vpn_gateway)

  def testClearLabels(self):
    existing_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                                'value3'))
    labels_after_update = ()

    vpn_gateway_ref = self.GetVpnGatewayRef(self._VPN_GATEWAY_NAME)
    expected_updated_vpn_gateway = self._ExpectSetLabels(
        vpn_gateway_ref, existing_labels, labels_after_update)

    response = self.Run('compute vpn-gateways update {} '
                        '--region {} '
                        '--clear-labels'.format(vpn_gateway_ref.Name(),
                                                vpn_gateway_ref.region))
    self.assertEqual(response, expected_updated_vpn_gateway)

  def testUpdateWithNoExistingLabels(self):
    existing_labels = ()
    labels_to_update = (('key2', 'update2'), ('key4', 'value4'))
    labels_after_update = labels_to_update

    vpn_gateway_ref = self.GetVpnGatewayRef(self._VPN_GATEWAY_NAME)
    expected_updated_vpn_gateway = self._ExpectSetLabels(
        vpn_gateway_ref, existing_labels, labels_after_update)

    labels_to_update_cmd = ','.join(
        '{0}={1}'.format(pair[0], pair[1]) for pair in labels_to_update)
    response = self.Run('compute vpn-gateways update {} '
                        '--region {} '
                        '--update-labels {}'.format(vpn_gateway_ref.Name(),
                                                    vpn_gateway_ref.region,
                                                    labels_to_update_cmd))
    self.assertEqual(response, expected_updated_vpn_gateway)

  def testRemoveNonExistingLabels(self):
    existing_labels = (('key1', 'value1'), ('key2', 'value2'))

    vpn_gateway_ref = self.GetVpnGatewayRef(self._VPN_GATEWAY_NAME)
    existing_vpn_gateway = self._ExpectNoSetLabels(vpn_gateway_ref,
                                                   existing_labels)

    response = self.Run('compute vpn-gateways update {} '
                        '--region {} '
                        '--remove-labels DoesNotExist'.format(
                            vpn_gateway_ref.Name(), vpn_gateway_ref.region))
    self.assertEqual(response, existing_vpn_gateway)

  def testNoNetUpdate(self):
    existing_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                                'value3'))
    labels_to_remove = ('key4')
    labels_to_update = existing_labels
    vpn_gateway_ref = self.GetVpnGatewayRef(self._VPN_GATEWAY_NAME)
    existing_vpn_gateway = self._ExpectNoSetLabels(vpn_gateway_ref,
                                                   existing_labels)

    labels_to_update_cmd = ','.join(
        '{0}={1}'.format(pair[0], pair[1]) for pair in labels_to_update)
    labels_to_remove_cmd = ','.join(labels_to_remove)
    response = self.Run('compute vpn-gateways update {} '
                        '--region {} '
                        '--update-labels {} '
                        '--remove-labels {}'.format(
                            vpn_gateway_ref.Name(), vpn_gateway_ref.region,
                            labels_to_update_cmd, labels_to_remove_cmd))
    self.assertEqual(response, existing_vpn_gateway)


class VpnGatewaysUpdateLabelsBetaTest(
    VpnGatewaysUpdateLabelsGaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)


class VpnGatewaysUpdateLabelsAlphaTest(
    VpnGatewaysUpdateLabelsBetaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)

if __name__ == '__main__':
  test_case.main()
