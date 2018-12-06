# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Unit tests for api_lib/compute/iap_websocket_tunnel_utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import iap_tunnel_websocket_utils as utils
from tests.lib import cli_test_base
from tests.lib import parameterized


class IapTunnelWebSocketUtilsTest(
    cli_test_base.CliTestBase, parameterized.TestCase):

  @parameterized.parameters(
      (('my-project', 'a-zone', 'instance1', 'nic0', 22, '', None),
       'wss://tunnel.cloudproxy.app/v4/connect',
       ['instance=instance1', 'interface=nic0', 'port=22', 'project=my-project',
        'zone=a-zone']),
      (('my-project', 'a-zone', 'instance1', 'nic0', 22,
        'ws://tunnel2.cloudproxy.app/v3', None),
       'ws://tunnel2.cloudproxy.app/v3/connect',
       ['instance=instance1', 'interface=nic0', 'port=22', 'project=my-project',
        'zone=a-zone']),
  )
  def testCreateConnectUrl(self, target, expected_base, expected_query):
    tunnel_target = utils.IapTunnelTargetInfo(*target)
    created_url = utils.CreateWebSocketConnectUrl(tunnel_target)
    created_url_parts = created_url.split('?', 1)
    self.assertEqual(created_url_parts[0], expected_base)
    self.assertEqual(sorted(created_url_parts[1].split('&')), expected_query)

  @parameterized.parameters(
      (('my-project', 'b-zone', 'instance2', 'nic1', 23, '', None), 'abc', 123,
       'wss://tunnel.cloudproxy.app/v4/reconnect', ['ack=123', 'sid=abc']),
      (('my-project', 'b-zone', 'instance2', 'nic1', 23,
        'ws://tunnel2.cloudproxy.app/v3', None), 'abcd', 1234,
       'ws://tunnel2.cloudproxy.app/v3/reconnect', ['ack=1234', 'sid=abcd']),
  )
  def testCreateReconnectUrl(self, target, sid, ack_bytes, expected_base,
                             expected_query):
    tunnel_target = utils.IapTunnelTargetInfo(*target)
    created_url = utils.CreateWebSocketReconnectUrl(tunnel_target, sid,
                                                    ack_bytes)
    created_url_parts = created_url.split('?', 1)
    self.assertEqual(created_url_parts[0], expected_base)
    self.assertEqual(sorted(created_url_parts[1].split('&')), expected_query)

  @parameterized.parameters(
      (('', 'a-zone', 'instance1', 'nic0', 22, '', None),
       utils.MissingTunnelParameter,
       'Missing required tunnel argument: project'),
      (('my-project', '', 'instance1', 'nic0', 22, '', None),
       utils.MissingTunnelParameter,
       'Missing required tunnel argument: zone'),
      (('my-project', 'a-zone', '', 'nic0', 22, '', None),
       utils.MissingTunnelParameter,
       'Missing required tunnel argument: instance'),
      (('my-project', 'a-zone', 'instance1', '', 22, '', None),
       utils.MissingTunnelParameter,
       'Missing required tunnel argument: interface'),
      (('my-project', 'a-zone', 'instance1', 'nic0', 0, '', None),
       utils.MissingTunnelParameter,
       'Missing required tunnel argument: port'),
  )
  def testInit_MissingTargetParam(self, target, expected_error,
                                  expected_message):
    tunnel_target = utils.IapTunnelTargetInfo(*target)
    with self.AssertRaisesExceptionMatches(expected_error, expected_message):
      utils.ValidateParameters(tunnel_target)

  @parameterized.parameters(
      (0, b'\x00\x07\x00\x00\x00\x00\x00\x00\x00\x00'),
      (1, b'\x00\x07\x00\x00\x00\x00\x00\x00\x00\x01'),
      (65534, b'\x00\x07\x00\x00\x00\x00\x00\x00\xff\xfe'),
      (2**64 - 1, b'\x00\x07\xff\xff\xff\xff\xff\xff\xff\xff'),
  )
  def testCreateSubprotocolAckFrame(self, ack_bytes, expected_bytes):
    self.assertEqual(utils.CreateSubprotocolAckFrame(ack_bytes),
                     expected_bytes)

  @parameterized.parameters(
      (2**64, utils.InvalidWebSocketSubprotocolData),
      (-1, utils.InvalidWebSocketSubprotocolData),
      (-2, utils.InvalidWebSocketSubprotocolData),
  )
  def testCreateSubprotocolAckFrameInvalidInput(self, ack_bytes,
                                                expected_error):
    with self.AssertRaisesExceptionMatches(expected_error, ''):
      utils.CreateSubprotocolAckFrame(ack_bytes)

  @parameterized.parameters(
      (b'\x99abcde', b'\x00\x04\x00\x00\x00\x06\x99abcde'),
      (b'', b'\x00\x04\x00\x00\x00\x00'),
      (b'\x88\x82\x0489\xea\x07\xd0',
       b'\x00\x04\x00\x00\x00\x08\x88\x82\x0489\xea\x07\xd0'),
      (b'\x00', b'\x00\x04\x00\x00\x00\x01\x00'),
  )
  def testCreateSubprotocolDataFrame(self, bytes_to_send, expected_bytes):
    self.assertEqual(utils.CreateSubprotocolDataFrame(bytes_to_send),
                     expected_bytes)

  @parameterized.parameters(
      (b'\x00\x00\x00\x00\x061abcde', 103899490, b'cde'),
      (b'\x00\x00\x00\x00zz11', 2054828337, b''),
      (b'\x00\x00\x00\x00\x00\x00\x00\x00', 0, b''),
  )
  def testExtractSubprotocolAck(self, binary_data, expected_data,
                                expected_bytes_left):
    data, bytes_left = utils.ExtractSubprotocolAck(binary_data)
    self.assertEqual(data, expected_data)
    self.assertEqual(bytes_left, expected_bytes_left)

  @parameterized.parameters(
      (b'', utils.IncompleteData),
      (b'\x00', utils.IncompleteData),
      (b'\x00\x00\x02', utils.IncompleteData),
      (b'\x00\x00\x00\x04abc', utils.IncompleteData),
  )
  def testExtractSubprotocolAckIncompleteData(self, binary_data,
                                              expected_error):
    with self.AssertRaisesExceptionMatches(expected_error, ''):
      utils.ExtractSubprotocolAck(binary_data)

  @parameterized.parameters(
      (b'\x00\x00\x00\x061abcde', b'1abcde', b''),
      (b'\x00\x00\x00\x00zz', b'', b'zz'),
      (b'\x00\x00\x00\x01Q', b'Q', b''),
  )
  def testExtractSubprotocolConnectSuccessSid(self, binary_data, expected_data,
                                              expected_bytes_left):
    data, bytes_left = utils.ExtractSubprotocolConnectSuccessSid(binary_data)
    self.assertEqual(data, expected_data)
    self.assertEqual(bytes_left, expected_bytes_left)

  @parameterized.parameters(
      (b'', utils.IncompleteData),
      (b'\x00', utils.IncompleteData),
      (b'\x00\x00\x02', utils.IncompleteData),
      (b'\x00\x00\x00\x04abc', utils.IncompleteData),
  )
  def testExtractSubprotocolConnectSuccessSidIncompleteData(self, binary_data,
                                                            expected_error):
    with self.AssertRaisesExceptionMatches(expected_error, ''):
      utils.ExtractSubprotocolConnectSuccessSid(binary_data)

  @parameterized.parameters(
      (b'\x00\x00\x00\x06\x99abcde', b'\x99abcde', b''),
      (b'\x00\x00\x00\x00z#', b'', b'z#'),
      (b'\x00\x00\x00\x08\x88\x82\x0489\xea\x07\xd0\x00\x04',
       b'\x88\x82\x0489\xea\x07\xd0', b'\x00\x04'),
      (b'\x00\x00\x00\x01\x00', b'\x00', b''),
  )
  def testExtractSubprotocolData(self, binary_data, expected_data,
                                 expected_bytes_left):
    data, bytes_left = utils.ExtractSubprotocolData(binary_data)
    self.assertEqual(data, expected_data)
    self.assertEqual(bytes_left, expected_bytes_left)

  @parameterized.parameters(
      (b'', utils.IncompleteData),
      (b'\x00', utils.IncompleteData),
      (b'\x00\x00\x02', utils.IncompleteData),
      (b'\x00\x00\x00\x04abc', utils.IncompleteData),
  )
  def testExtractSubprotocolDataIncompleteData(self, binary_data,
                                               expected_error):
    with self.AssertRaisesExceptionMatches(expected_error, ''):
      utils.ExtractSubprotocolData(binary_data)

  @parameterized.parameters(
      (b'\x00\x00\x00\x00\x00\x00\x0b\xd5', 3029, b''),
      (b'\x00\x00\x00\x00\x00\x00\x0b\xd6zz', 3030, b'zz'),
  )
  def testExtractSubprotocolReconnectSuccessAck(
      self, binary_data, expected_data, expected_bytes_left):
    data, bytes_left = utils.ExtractSubprotocolReconnectSuccessAck(binary_data)
    self.assertEqual(data, expected_data)
    self.assertEqual(bytes_left, expected_bytes_left)

  @parameterized.parameters(
      (b'', utils.IncompleteData),
      (b'\x00', utils.IncompleteData),
      (b'\x00\x00\x00\x00\x00\x00\x0b', utils.IncompleteData),
  )
  def testExtractSubprotocolReconnectSuccessAckIncompleteData(self, binary_data,
                                                              expected_error):
    with self.AssertRaisesExceptionMatches(expected_error, ''):
      utils.ExtractSubprotocolReconnectSuccessAck(binary_data)

  @parameterized.parameters(
      (b'\x00\x07\x00\x00\x00\x00\x00\x02\x00\x00', utils.SUBPROTOCOL_TAG_ACK,
       b'\x00\x00\x00\x00\x00\x02\x00\x00'),
      (b'\x00\x04\x00\x00\x00\x06\x99abcde', utils.SUBPROTOCOL_TAG_DATA,
       b'\x00\x00\x00\x06\x99abcde'),
      (b'\x00\x01\x00\x00\x00\x01z', utils.SUBPROTOCOL_TAG_CONNECT_SUCCESS_SID,
       b'\x00\x00\x00\x01z'),
      (b'\x10\x00\x00\x01z', 4096, b'\x00\x01z'),
  )
  def testExtractSubprotocolTag(self, binary_data, expected_tag,
                                expected_bytes_left):
    tag, bytes_left = utils.ExtractSubprotocolTag(binary_data)
    self.assertEqual(tag, expected_tag)
    self.assertEqual(bytes_left, expected_bytes_left)

  @parameterized.parameters(
      (b'', utils.IncompleteData),
      (b'\x00', utils.IncompleteData),
  )
  def testExtractSubprotocolTagIncompleteData(self, binary_data,
                                              expected_error):
    with self.AssertRaisesExceptionMatches(expected_error, ''):
      utils.ExtractSubprotocolTag(binary_data)


if __name__ == '__main__':
  cli_test_base.main()
