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
"""Unit tests for api_lib/compute/iap_websocket_tunnel module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging
import ssl
import threading
import time

from googlecloudsdk.api_lib.compute import iap_tunnel_websocket_helper
from googlecloudsdk.api_lib.compute import iap_tunnel_websocket_utils as utils
from googlecloudsdk.core import log
from tests.lib import cli_test_base
from tests.lib import parameterized

import httplib2
import mock
import socks
import websocket

TEST_URL = (
    'wss://tunnel.cloudproxy.app/v4/connect?project=iap-test-admin-proxy&'
    'instance=instance-1&zone=us-west1-b&interface=nic0&port=22')
TEST_HEADERS = ['User-Agent: test-agent',
                'Sec-WebSocket-Protocol: 13']


class IapTunnelWebSocketHelperTest(cli_test_base.CliTestBase,
                                   parameterized.TestCase):

  def SetUp(self):
    self._received_data = []
    self._close_received = False
    self.helper = iap_tunnel_websocket_helper.IapTunnelWebSocketHelper(
        TEST_URL, TEST_HEADERS, True, None, self.DataCallback,
        self.CloseCallback)
    self.helper._websocket = mock.MagicMock()
    self.helper._websocket.sock.connected = True

  def DataCallback(self, data):
    self._received_data.append(data)

  def CloseCallback(self):
    self._close_received = True

  def testInit(self):
    self.assertEqual(self.helper._on_data, self.DataCallback,
                     self.CloseCallback)
    self.assertListEqual(sorted(self.helper._sslopt.keys()),
                         ['ca_certs', 'cert_reqs', 'check_hostname'])
    self.assertTrue(self.helper._sslopt['ca_certs'].endswith('cacerts.txt'))
    self.assertEqual(self.helper._sslopt['cert_reqs'], ssl.CERT_OPTIONAL)
    self.assertFalse(self.helper._sslopt['check_hostname'])
    self.assertFalse(self.helper._is_closed)

    second_helper = iap_tunnel_websocket_helper.IapTunnelWebSocketHelper(
        TEST_URL, TEST_HEADERS, False, None, self.DataCallback,
        self.CloseCallback)
    self.assertListEqual(sorted(second_helper._sslopt.keys()),
                         ['ca_certs', 'cert_reqs'])
    self.assertTrue(second_helper._sslopt['ca_certs'].endswith('cacerts.txt'))
    self.assertEqual(second_helper._sslopt['cert_reqs'], ssl.CERT_REQUIRED)

  def testClose(self):
    self.assertFalse(self.helper._is_closed)
    self.helper.Close()
    self.assertTrue(self.helper._is_closed)
    self.assertEqual(self.helper._websocket.close.call_count, 1)
    # Skip close() call if already marked as closed
    self.helper.Close()
    self.assertTrue(self.helper._is_closed)
    self.assertEqual(self.helper._websocket.close.call_count, 1)
    # Check exception on close() still results in being marked as closed
    self.helper._is_closed = False
    self.helper._websocket.close.side_effect = EnvironmentError
    self.helper.Close()
    self.assertTrue(self.helper._is_closed)
    self.assertEqual(self.helper._websocket.close.call_count, 2)

  def testIsClosed(self):
    self.assertFalse(self.helper.IsClosed())
    self.helper.Close()
    self.assertTrue(self.helper.IsClosed())
    self.helper._is_closed = False
    self.helper._receiving_thread = threading.Thread(target=lambda: True)
    self.helper._receiving_thread.start()
    while self.helper._receiving_thread.isAlive():
      time.sleep(0.001)
    self.assertFalse(self.helper._is_closed)
    self.assertTrue(self.helper.IsClosed())

  @mock.patch.object(log, 'debug', autospec=True)
  def testSend(self, log_debug_mock):
    log_debug_mock.side_effect = lambda *args, **kwargs: args[0] % args[1:]
    log.SetVerbosity(logging.DEBUG)
    self.helper.Send(b'123')
    self.assertEqual(self.helper._websocket.send.call_count, 1)
    self.helper._websocket.send.assert_has_calls([mock.call(b'123', opcode=2)])
    self.assertFalse(self.helper.IsClosed())
    self.assertEqual(log_debug_mock.call_count, 1)
    log_debug_mock.assert_has_calls(
        [mock.call(u'SEND data_len [%d] send_data[:20] %r', 3, b'123')])

    log.SetVerbosity(logging.WARNING)
    self.helper._websocket.send.side_effect = EnvironmentError
    self.assertRaises(EnvironmentError, self.helper.Send, b'xyz')
    self.assertEqual(self.helper._websocket.send.call_count, 2)
    self.helper._websocket.send.assert_has_calls([mock.call(b'xyz', opcode=2)])
    self.assertTrue(self.helper.IsClosed())

    self.helper._websocket.send.side_effect = (
        websocket.WebSocketConnectionClosedException)
    self.assertRaises(iap_tunnel_websocket_helper.WebSocketConnectionClosed,
                      self.helper.Send, b'wer')
    self.assertEqual(self.helper._websocket.send.call_count, 3)
    self.helper._websocket.send.assert_has_calls([mock.call(b'wer', opcode=2)])

    self.helper._websocket.send.side_effect = RuntimeError
    self.assertRaises(iap_tunnel_websocket_helper.WebSocketSendError,
                      self.helper.Send, b'qwf')
    self.assertEqual(self.helper._websocket.send.call_count, 4)
    self.helper._websocket.send.assert_has_calls([mock.call(b'qwf', opcode=2)])

  @mock.patch.object(log, 'info', autospec=True)
  @mock.patch.object(log, 'debug', autospec=True)
  def testSendClose(self, log_debug_mock, log_info_mock):
    log_debug_mock.side_effect = lambda *args, **kwargs: args[0] % args[1:]
    log.SetVerbosity(logging.DEBUG)
    self.helper.SendClose()
    self.assertEqual(self.helper._websocket.sock.send_close.call_count, 1)
    self.helper._websocket.sock.send_close.assert_has_calls([mock.call()])
    self.assertFalse(self.helper.IsClosed())
    self.assertEqual(log_debug_mock.call_count, 1)
    self.assertEqual(log_info_mock.call_count, 0)
    log_debug_mock.assert_has_calls([mock.call(u'CLOSE')])

    log.SetVerbosity(logging.WARNING)
    self.helper._websocket.sock.send_close.side_effect = RuntimeError
    self.helper.SendClose()
    self.assertEqual(self.helper._websocket.sock.send_close.call_count, 2)
    self.assertTrue(self.helper.IsClosed())
    self.assertEqual(log_info_mock.call_count, 1)
    log_info_mock.assert_has_calls(
        [mock.call(u'Error during WebSocket send of Close message.',
                   exc_info=True)])

    self.helper._websocket.sock.send_close.side_effect = (
        websocket.WebSocketConnectionClosedException)
    self.helper.SendClose()
    self.assertEqual(self.helper._websocket.sock.send_close.call_count, 3)
    self.helper._websocket.sock.send_close.assert_has_calls([mock.call()])
    self.assertEqual(log_info_mock.call_count, 2)
    log_info_mock.assert_has_calls(
        [mock.call(u'Unable to send WebSocket Close message [%s].', '')])

  @mock.patch.object(utils, 'CheckCACertsFile', autospec=True)
  @mock.patch.object(threading, 'Thread')
  @mock.patch.object(websocket, 'WebSocketApp', autospec=True)
  def testStartReceivingThread(self, websocket_app_cls_mock, thread_cls_mock,
                               check_ca_certs_mock):
    websocket_app_mock = mock.MagicMock()
    websocket_app_cls_mock.return_value = websocket_app_mock
    thread_mock = mock.MagicMock()
    thread_cls_mock.return_value = thread_mock
    check_ca_certs_mock.return_value = 'ca certs'
    new_helper = iap_tunnel_websocket_helper.IapTunnelWebSocketHelper(
        TEST_URL, TEST_HEADERS, True, None, self.DataCallback,
        self.CloseCallback)

    check_ca_certs_mock.assert_called_once()
    check_ca_certs_mock.assert_called_with(True)

    websocket_app_cls_mock.assert_called_once()
    websocket_app_cls_mock.assert_called_with(
        TEST_URL, header=TEST_HEADERS, on_error=new_helper._OnError,
        on_close=new_helper._OnClose, on_data=new_helper._OnData)
    self.assertIs(new_helper._websocket, websocket_app_mock)

    new_helper.StartReceivingThread()
    thread_cls_mock.assert_called_once()
    thread_cls_mock.assert_called_with(target=new_helper._ReceiveFromWebSocket)
    self.assertIs(new_helper._receiving_thread, thread_mock)
    self.assertTrue(thread_mock.daemon)
    thread_mock.start.assert_called_once()

  @mock.patch.object(log, 'info', autospec=True)
  def testOnClose(self, log_info_mock):
    log_info_mock.side_effect = lambda *args, **kwargs: args[0] % args[1:]
    self.helper._OnClose(None)
    self.assertTrue(self.helper.IsClosed())
    self.assertEqual(log_info_mock.call_count, 0)

    self.helper._OnClose(None, 'close message from server')
    self.assertTrue(self.helper.IsClosed())
    self.assertEqual(log_info_mock.call_count, 1)
    log_info_mock.assert_has_calls(
        [mock.call(u'Received WebSocket Close message [%r].',
                   u'close message from server')])
    self.assertTrue(self._close_received)

  @mock.patch.object(log, 'info', autospec=True)
  @mock.patch.object(log, 'debug', autospec=True)
  def testOnData(self, log_debug_mock, log_info_mock):
    log.SetVerbosity(logging.DEBUG)
    log_debug_mock.side_effect = lambda *args, **kwargs: args[0] % args[1:]
    self.helper._OnData(None, b'456', 2, True)
    self.assertListEqual(self._received_data, [b'456'])
    self.assertEqual(log_debug_mock.call_count, 1)
    self.assertEqual(log_info_mock.call_count, 0)
    log_debug_mock.assert_has_calls(
        [mock.call(u'RECV opcode [%r] data_len [%d] binary_data[:20] [%r]', 2,
                   3, b'456')])
    self.assertFalse(self.helper.IsClosed())

    log.SetVerbosity(logging.WARNING)
    self.assertRaises(iap_tunnel_websocket_helper.WebSocketInvalidOpcodeError,
                      self.helper._OnData, None, b'789', 1, None)
    self.assertEqual(log_debug_mock.call_count, 2)
    self.assertEqual(log_info_mock.call_count, 1)
    self.assertEqual(log_info_mock.call_args[0][0],
                     'Error while processing Data message.')
    self.assertTrue(self.helper.IsClosed())

    self.helper._is_closed = False
    self.helper._OnData(None, b'abcd', 0, True)
    self.assertListEqual(self._received_data, [b'456', b'abcd'])
    self.assertEqual(log_debug_mock.call_count, 3)
    self.assertEqual(log_info_mock.call_count, 1)
    self.assertFalse(self.helper.IsClosed())

  @mock.patch.object(log, 'info', autospec=True)
  def testOnError(self, log_info_mock):
    log_info_mock.side_effect = lambda *args, **kwargs: args[0] % args[1:]
    self.helper._OnError(None, Exception('some error'))
    self.assertEqual(log_info_mock.call_count, 1)
    log_info_mock.assert_has_calls(
        [mock.call('Error during WebSocket processing\n'
                   'Exception: some error\n')])

  @mock.patch.object(log, 'info', autospec=True)
  def testReceiveFromWebSocket(self, log_info_mock):
    log_info_mock.side_effect = lambda *args, **kwargs: args[0] % args[1:]
    self.helper._ReceiveFromWebSocket()
    self.assertEqual(self.helper._websocket.run_forever.call_count, 1)
    self.helper._websocket.run_forever.assert_has_calls(
        [mock.call(origin=u'bot:iap-tunneler', sslopt=self.helper._sslopt)])
    self.assertEqual(log_info_mock.call_count, 0)
    self.assertTrue(self.helper.IsClosed())

    self.helper._is_closed = False
    self.helper._proxy_info = httplib2.ProxyInfo(
        socks.PROXY_TYPE_HTTP, '10.4.3.2', '80', '', 'userA', 'passB')
    self.helper._websocket.run_forever.side_effect = EnvironmentError
    self.helper._ReceiveFromWebSocket()
    self.assertEqual(self.helper._websocket.run_forever.call_count, 2)
    self.helper._websocket.run_forever.assert_has_calls(
        [mock.call(origin='bot:iap-tunneler', sslopt=self.helper._sslopt,
                   http_proxy_host='10.4.3.2', http_proxy_port='80',
                   http_proxy_auth=('userA', 'passB'))])
    self.assertEqual(log_info_mock.call_count, 1)
    self.assertEqual(log_info_mock.call_args[0][0],
                     'Error while receiving from WebSocket.')
    self.assertTrue(self.helper.IsClosed())


if __name__ == '__main__':
  cli_test_base.main()
