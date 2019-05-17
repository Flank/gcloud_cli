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
"""Tests for External VPN Gateways labels update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import external_vpn_gateways_test_base


class ExternalVpnGatewaysUpdateLabelsBetaTest(
    external_vpn_gateways_test_base.ExternalVpnGatewaysTestBase):

  _VPN_GATEWAY_NAME = 'my-gateway'
  _INTRFACE_LIST = []
  _FINGERPRINT_1 = b'fingerprint-9876'
  _FINGERPRINT_2 = b'fingerprint-9875'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _MakeGateway(self, gateway_ref, fingerprint, labels=None):
    interface_list = []
    interface_list.append(
        self.messages.ExternalVpnGatewayInterface(id=0, ipAddress='5.6.7.8'))
    external_gateway = self.messages.ExternalVpnGateway(
        name=gateway_ref.Name(),
        redundancyType=self.messages.ExternalVpnGateway
        .RedundancyTypeValueValuesEnum.TWO_IPS_REDUNDANCY,
        interfaces=interface_list,
        labelFingerprint=fingerprint)
    if labels:
      external_gateway.labels = self.MakeLabelsMessage(
          self.messages.ExternalVpnGateway.LabelsValue, labels)
    return external_gateway

  def _ExpectSetLabels(self, gateway_ref, existing_labels, labels_after_update):
    existing_gateway = self._MakeGateway(gateway_ref, self._FINGERPRINT_1,
                                         existing_labels)
    updated_gateway = self._MakeGateway(gateway_ref, self._FINGERPRINT_2,
                                        labels_after_update)
    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=gateway_ref)

    self.ExpectGetRequest(gateway_ref, existing_gateway)
    self.ExpectSetLabelsRequest(gateway_ref, labels_after_update,
                                self._FINGERPRINT_1, operation)
    self.ExpectOperationGetRequest(operation_ref, operation)
    self.ExpectGetRequest(gateway_ref, updated_gateway)
    return updated_gateway

  def _ExpectNoSetLabels(self, gateway_ref, existing_labels):
    existing_gateway = self._MakeGateway(gateway_ref, self._FINGERPRINT_1,
                                         existing_labels)
    self.ExpectGetRequest(gateway_ref, existing_gateway)
    return existing_gateway

  def testWithoutFlags(self):
    gateway_ref = self.GetExternalVpnGatewayRef(self._VPN_GATEWAY_NAME)
    with self.assertRaisesRegex(
        exceptions.RequiredArgumentException,
        'At least one of --update-labels or '
        '--remove-labels must be specified.'):
      self.Run('compute external-vpn-gateways update {0}'.format(
          gateway_ref.Name()))

  def testUpdateAndRemoveLabels(self):
    existing_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                                'value3'))
    labels_to_remove = ('key1', 'key0')
    labels_to_update = (('key2', 'update2'), ('key4', 'value4'))
    labels_after_update = (('key2', 'update2'), ('key3', 'value3'), ('key4',
                                                                     'value4'))
    gateway_ref = self.GetExternalVpnGatewayRef(self._VPN_GATEWAY_NAME)
    expected_updated_gateway = self._ExpectSetLabels(
        gateway_ref, existing_labels, labels_after_update)

    labels_to_update_cmd = ','.join(
        '{0}={1}'.format(pair[0], pair[1]) for pair in labels_to_update)
    labels_to_remove_cmd = ','.join(labels_to_remove)
    response = self.Run('compute external-vpn-gateways update {} '
                        '--update-labels {} '
                        '--remove-labels {}'.format(gateway_ref.Name(),
                                                    labels_to_update_cmd,
                                                    labels_to_remove_cmd))
    self.assertEqual(response, expected_updated_gateway)

  def testClearLabels(self):
    existing_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                                'value3'))
    labels_after_update = ()

    gateway_ref = self.GetExternalVpnGatewayRef(self._VPN_GATEWAY_NAME)
    expected_updated_gateway = self._ExpectSetLabels(
        gateway_ref, existing_labels, labels_after_update)

    response = self.Run('compute external-vpn-gateways update {} '
                        '--clear-labels'.format(gateway_ref.Name()))
    self.assertEqual(response, expected_updated_gateway)

  def testUpdateWithNoExistingLabels(self):
    existing_labels = ()
    labels_to_update = (('key2', 'update2'), ('key4', 'value4'))
    labels_after_update = labels_to_update

    gateway_ref = self.GetExternalVpnGatewayRef(self._VPN_GATEWAY_NAME)
    expected_updated_gateway = self._ExpectSetLabels(
        gateway_ref, existing_labels, labels_after_update)

    labels_to_update_cmd = ','.join(
        '{0}={1}'.format(pair[0], pair[1]) for pair in labels_to_update)
    response = self.Run('compute external-vpn-gateways update {} '
                        '--update-labels {}'.format(gateway_ref.Name(),
                                                    labels_to_update_cmd))
    self.assertEqual(response, expected_updated_gateway)

  def testRemoveNonExistingLabels(self):
    existing_labels = (('key1', 'value1'), ('key2', 'value2'))

    gateway_ref = self.GetExternalVpnGatewayRef(self._VPN_GATEWAY_NAME)
    exising_gateway = self._ExpectNoSetLabels(gateway_ref, existing_labels)

    response = self.Run('compute external-vpn-gateways update {} '
                        '--remove-labels DoesNotExist'.format(
                            gateway_ref.Name()))
    self.assertEqual(response, exising_gateway)

  def testNoNetUpdate(self):
    existing_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                                'value3'))
    labels_to_remove = ('key4')
    labels_to_update = existing_labels
    gateway_ref = self.GetExternalVpnGatewayRef(self._VPN_GATEWAY_NAME)
    existing_gateway = self._ExpectNoSetLabels(gateway_ref, existing_labels)

    labels_to_update_cmd = ','.join(
        '{0}={1}'.format(pair[0], pair[1]) for pair in labels_to_update)
    labels_to_remove_cmd = ','.join(labels_to_remove)
    response = self.Run('compute external-vpn-gateways update {} '
                        '--update-labels {} '
                        '--remove-labels {}'.format(gateway_ref.Name(),
                                                    labels_to_update_cmd,
                                                    labels_to_remove_cmd))
    self.assertEqual(response, existing_gateway)


class ExternalVpnGatewaysUpdateLabelsAlphaTest(
    ExternalVpnGatewaysUpdateLabelsBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
