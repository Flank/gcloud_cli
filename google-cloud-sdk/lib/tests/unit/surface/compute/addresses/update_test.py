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
"""Tests for addresses update."""

from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.compute import (
    addresses_labels_test_base)


class UpdateLabelsTestBeta(addresses_labels_test_base.AddressesLabelsTestBase):

  def testUpdateMissingNameOrLabels(self):
    address_ref = self._GetAddressRef('address-1', region='us-central1')
    with self.assertRaisesRegex(calliope_exceptions.RequiredArgumentException,
                                'At least one of --update-labels or '
                                '--remove-labels must be specified.'):
      self.Run('compute addresses update {0} --region {1}'
               .format(address_ref.Name(), address_ref.region))

  def testGlobalUpdateAndRemoveLabels(self):
    address_ref = self._GetAddressRef('address-1')

    address_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                               'value3'))
    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (('key2', 'update2'), ('key3', 'value3'), ('key4',
                                                               'value4'))

    address = self._MakeAddressProto(
        labels=address_labels, fingerprint=b'fingerprint-42')
    updated_address = self._MakeAddressProto(labels=edited_labels)

    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, address_ref)

    self._ExpectGetRequest(address_ref, address)
    self._ExpectLabelsSetRequest(address_ref, edited_labels, b'fingerprint-42',
                                 operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(address_ref, updated_address)

    response = self.Run(
        'compute addresses update {0} --update-labels {1} '
        '--remove-labels key1,key0'.format(address_ref.SelfLink(), ','.join(
            ['{0}={1}'.format(pair[0], pair[1]) for pair in update_labels])))
    self.assertEqual(response, updated_address)

  def testGlobalClearLabels(self):
    address_ref = self._GetAddressRef('address-1')

    address_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                               'value3'))
    edited_labels = ()

    address = self._MakeAddressProto(
        labels=address_labels, fingerprint=b'fingerprint-42')
    updated_address = self._MakeAddressProto(labels=edited_labels)

    operation_ref = self._GetOperationRef('operation-1')
    operation = self._MakeOperationMessage(operation_ref, address_ref)

    self._ExpectGetRequest(address_ref, address)
    self._ExpectLabelsSetRequest(address_ref, edited_labels, b'fingerprint-42',
                                 operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(address_ref, updated_address)

    response = self.Run(
        'compute addresses update {0} --clear-labels'
        .format(address_ref.SelfLink()))
    self.assertEqual(response, updated_address)

  def testRegionUpdateAndRemoveLabels(self):
    address_ref = self._GetAddressRef('address-1', region='us-central1')

    address_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                               'value3'))
    update_labels = (('key2', 'update2'), ('key4', 'value4'))
    edited_labels = (('key2', 'update2'), ('key3', 'value3'), ('key4',
                                                               'value4'))

    address = self._MakeAddressProto(
        labels=address_labels, fingerprint=b'fingerprint-42')
    updated_address = self._MakeAddressProto(labels=edited_labels)

    operation_ref = self._GetOperationRef('operation-1', 'us-central1')
    operation = self._MakeOperationMessage(operation_ref, address_ref)

    self._ExpectGetRequest(address_ref, address)
    self._ExpectLabelsSetRequest(address_ref, edited_labels, b'fingerprint-42',
                                 operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(address_ref, updated_address)

    response = self.Run(
        'compute addresses update {0} --update-labels {1} '
        '--remove-labels key1,key0'.format(address_ref.SelfLink(), ','.join(
            ['{0}={1}'.format(pair[0], pair[1]) for pair in update_labels])))
    self.assertEqual(response, updated_address)

  def testUpdateWithNoLabels(self):
    address_ref = self._GetAddressRef('address-1', region='us-central1')

    update_labels = (('key2', 'update2'), ('key4', 'value4'))

    address = self._MakeAddressProto(labels=(), fingerprint=b'fingerprint-42')
    updated_address = self._MakeAddressProto(labels=update_labels)
    operation_ref = self._GetOperationRef('operation-1', 'us-central1')
    operation = self._MakeOperationMessage(operation_ref, address_ref)

    self._ExpectGetRequest(address_ref, address)
    self._ExpectLabelsSetRequest(address_ref, update_labels, b'fingerprint-42',
                                 operation)
    self._ExpectOperationGetRequest(operation_ref, operation)
    self._ExpectGetRequest(address_ref, updated_address)

    response = self.Run(
        'compute addresses update {0} --update-labels {1} '
        .format(address_ref.SelfLink(), ','.join(
            ['{0}={1}'.format(pair[0], pair[1]) for pair in update_labels])))
    self.assertEqual(response, updated_address)

  def testRemoveWithNoLabelsOnAddress(self):
    address_ref = self._GetAddressRef('address-1', region='us-central1')
    address = self._MakeAddressProto(labels={}, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(address_ref, address)

    response = self.Run(
        'compute addresses update {0} --remove-labels DoesNotExist'
        .format(address_ref.SelfLink()))
    self.assertEqual(response, address)

  def testNoNetUpdate(self):
    address_ref = self._GetAddressRef('address-1', region='us-central1')

    address_labels = (('key1', 'value1'), ('key2', 'value2'), ('key3',
                                                               'value3'))
    update_labels = (('key1', 'value1'), ('key3', 'value3'), ('key4', 'value4'))

    address = self._MakeAddressProto(
        labels=address_labels, fingerprint=b'fingerprint-42')

    self._ExpectGetRequest(address_ref, address)

    response = self.Run(
        'compute addresses update {0} --update-labels {1} '
        '--remove-labels key4'.format(address_ref.SelfLink(), ','.join(
            ['{0}={1}'.format(pair[0], pair[1]) for pair in update_labels])))
    self.assertEqual(response, address)

  def testScopePrompt(self):
    address_ref = self._GetAddressRef('address-1', region='us-central1')
    address = self._MakeAddressProto(labels=[])
    self._ExpectGetRequest(address_ref, address)

    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.regions.service.List',
        return_value=[
            self.messages.Region(name='us-central1'),
            self.messages.Region(name='us-central2')
        ],)
    self.WriteInput('2\n')
    self.Run('compute addresses update address-1 --remove-labels key0')
    self.AssertErrEquals(
        textwrap.dedent("""\
            For the following address:
             - [address-1]
            choose a region or global:
             [1] global
             [2] region: us-central1
             [3] region: us-central2
            Please enter your numeric choice:{0}
            """.format('  ')))


if __name__ == '__main__':
  test_case.main()
