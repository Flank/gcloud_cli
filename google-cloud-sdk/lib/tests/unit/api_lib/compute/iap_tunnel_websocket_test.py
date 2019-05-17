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

import collections
import functools
import threading
import time

from googlecloudsdk.api_lib.compute import iap_tunnel_websocket
from googlecloudsdk.api_lib.compute import iap_tunnel_websocket_helper
from googlecloudsdk.api_lib.compute import iap_tunnel_websocket_utils as utils
from googlecloudsdk.core import http
from tests.lib import cli_test_base
from tests.lib import parameterized

import mock


def GetAccessToken():
  return 'one-access-token'


class IapTunnelWebSocketTest(cli_test_base.CliTestBase, parameterized.TestCase):

  def SetUp(self):
    self._received_data = []
    self._close_received = False
    self.tunnel_target = utils.IapTunnelTargetInfo(
        project='project-a', zone='zone-b', instance='instance-c',
        interface='nic0', port=22, url_override=None, proxy_info=None)
    self.iap_tunnel_websocket = iap_tunnel_websocket.IapTunnelWebSocket(
        self.tunnel_target, GetAccessToken, self.DataCallback,
        self.CloseCallback, ignore_certs=True)
    self.iap_tunnel_websocket._websocket_helper = mock.MagicMock()
    self.iap_tunnel_websocket._connect_msg_received = True

  def DataCallback(self, data):
    self._received_data.append(data)

  def CloseCallback(self):
    self._close_received = True

  def testInit(self):
    self.assertIs(self.iap_tunnel_websocket._tunnel_target, self.tunnel_target)
    self.assertEqual(self.iap_tunnel_websocket._get_access_token_callback,
                     GetAccessToken)
    self.iap_tunnel_websocket._data_handler_callback('test 1')
    self.assertListEqual(self._received_data, ['test 1'])
    self.assertTrue(self.iap_tunnel_websocket._ignore_certs)

    second_socket = iap_tunnel_websocket.IapTunnelWebSocket(
        self.tunnel_target, GetAccessToken, self.DataCallback,
        self.CloseCallback)
    self.assertFalse(second_socket._ignore_certs)

  def testClose(self):
    self.iap_tunnel_websocket.Close()
    self.assertTrue(self._close_received)
    self.assertEqual(
        self.iap_tunnel_websocket._websocket_helper.SendClose.call_count, 1)
    self.assertEqual(
        self.iap_tunnel_websocket._websocket_helper.Close.call_count, 1)

    self.iap_tunnel_websocket.Close()
    self.assertEqual(
        self.iap_tunnel_websocket._websocket_helper.SendClose.call_count, 1)
    self.assertEqual(
        self.iap_tunnel_websocket._websocket_helper.Close.call_count, 2)

  def testAttemptReconnect(self):
    counts = {'reconnect': 0}

    def Reconnect(raise_exception_on_first):
      counts['reconnect'] += 1
      if counts['reconnect'] == 1 and raise_exception_on_first:
        raise Exception

    self.iap_tunnel_websocket._AttemptReconnect(
        functools.partial(Reconnect, False))
    self.assertEqual(counts['reconnect'], 1)

    counts['reconnect'] = 0
    self.iap_tunnel_websocket._AttemptReconnect(
        functools.partial(Reconnect, True))
    self.assertEqual(counts['reconnect'], 2)

  @mock.patch.object(http, 'MakeUserAgentString', autospec=True)
  @mock.patch.object(iap_tunnel_websocket_helper, 'IapTunnelWebSocketHelper',
                     autospec=True)
  def testStartNewWebSocket(self, websocket_helper_cls_mock,
                            make_user_agent_mock):
    new_socket = iap_tunnel_websocket.IapTunnelWebSocket(
        self.tunnel_target, GetAccessToken, self.DataCallback,
        self.CloseCallback, ignore_certs=True)
    websocket_helper_mock = mock.MagicMock()
    websocket_helper_cls_mock.return_value = websocket_helper_mock
    make_user_agent_mock.return_value = 'my-user-agent/1234'

    new_socket._StartNewWebSocket()

    url = utils.CreateWebSocketConnectUrl(self.tunnel_target)
    headers = ['User-Agent: my-user-agent/1234',
               'Authorization: Bearer one-access-token']
    websocket_helper_cls_mock.assert_called_once()
    websocket_helper_cls_mock.assert_called_with(
        url, headers, True, None, new_socket._OnData, new_socket._OnClose)
    self.assertIs(new_socket._websocket_helper, websocket_helper_mock)
    websocket_helper_mock.StartReceivingThread.assert_called_once()

  @mock.patch.object(http, 'MakeUserAgentString', autospec=True)
  @mock.patch.object(iap_tunnel_websocket_helper, 'IapTunnelWebSocketHelper',
                     autospec=True)
  def testStartNewWebSocketReconnect(self, websocket_helper_cls_mock,
                                     make_user_agent_mock):
    new_socket = iap_tunnel_websocket.IapTunnelWebSocket(
        self.tunnel_target, GetAccessToken, self.DataCallback,
        self.CloseCallback, ignore_certs=True)
    websocket_helper_mock = mock.MagicMock()
    websocket_helper_cls_mock.return_value = websocket_helper_mock
    make_user_agent_mock.return_value = 'my-user-agent/1234'

    new_socket._connection_sid = 'I am a SID'
    new_socket._total_bytes_received = 4567
    new_socket._connect_msg_received = True
    new_socket._StartNewWebSocket()

    self.assertFalse(new_socket._connect_msg_received)
    url = utils.CreateWebSocketReconnectUrl(
        self.tunnel_target, 'I am a SID', 4567)
    headers = ['User-Agent: my-user-agent/1234',
               'Authorization: Bearer one-access-token']
    websocket_helper_cls_mock.assert_called_once()
    websocket_helper_cls_mock.assert_called_with(
        url, headers, True, None, new_socket._OnData, new_socket._OnClose)
    self.assertIs(new_socket._websocket_helper, websocket_helper_mock)
    websocket_helper_mock.StartReceivingThread.assert_called_once()

  def testSendAck(self):
    self.iap_tunnel_websocket._total_bytes_received = 4096
    self.iap_tunnel_websocket._SendAck()
    self.assertEqual(
        self.iap_tunnel_websocket._websocket_helper.Send.call_count, 1)
    self.iap_tunnel_websocket._websocket_helper.Send.assert_has_calls(
        [mock.call(b'\x00\x07\x00\x00\x00\x00\x00\x00\x10\x00')])

  def testSendQueuedData(self):
    self.iap_tunnel_websocket._unsent_data.extend([b'testing', b'again'])
    self.iap_tunnel_websocket._SendQueuedData()
    self.assertEqual(
        self.iap_tunnel_websocket._websocket_helper.Send.call_count, 2)
    # The data being sent is a custom binary subprotocol that identifies the
    # type with the first two bytes and then the rest is specific to that
    # message type.
    self.iap_tunnel_websocket._websocket_helper.Send.assert_has_calls(
        [mock.call(b'\x00\x04\x00\x00\x00\x07testing'),
         mock.call(b'\x00\x04\x00\x00\x00\x05again')])

  def testWaitForOpenOrRaiseErrorWithSuccess(self):
    # Should exit if _connect_msg_received gets set to True
    self.iap_tunnel_websocket._connect_msg_received = False
    self.iap_tunnel_websocket._websocket_helper.IsClosed.return_value = False
    # This is a hack to circumvent the logic that stops waiting if the recv
    # thread itself has stopped
    self.iap_tunnel_websocket._send_and_reconnect_thread = threading.Thread(
        target=self.iap_tunnel_websocket._WaitForOpenOrRaiseError)
    self.iap_tunnel_websocket._send_and_reconnect_thread.daemon = True
    self.iap_tunnel_websocket._send_and_reconnect_thread.start()
    time.sleep(0.1)
    self.assertTrue(
        self.iap_tunnel_websocket._send_and_reconnect_thread.isAlive())
    self.iap_tunnel_websocket._connect_msg_received = True
    self.iap_tunnel_websocket._send_and_reconnect_thread.join(0.2)
    self.assertFalse(
        self.iap_tunnel_websocket._send_and_reconnect_thread.isAlive())

  def testWaitForOpenOrRaiseErrorWithError(self):
    self.iap_tunnel_websocket._connect_msg_received = False
    self.iap_tunnel_websocket._websocket_helper.IsClosed.return_value = True
    self.iap_tunnel_websocket._websocket_helper.ErrorMsg.return_value = ''
    with self.assertRaisesRegexp(iap_tunnel_websocket.ConnectionCreationError,
                                 r'Unexpected error while connecting'):
      self.iap_tunnel_websocket._WaitForOpenOrRaiseError()

  def testWaitForOpenOrRaiseErrorWithErrorMsg(self):
    self.iap_tunnel_websocket._connect_msg_received = False
    self.iap_tunnel_websocket._websocket_helper.IsClosed.return_value = True
    self.iap_tunnel_websocket._websocket_helper.ErrorMsg.return_value = (
        'Handshake status 500')
    error_regexp = r'^Error while connecting \[Handshake status 500\]\.$'
    with self.assertRaisesRegexp(iap_tunnel_websocket.ConnectionCreationError,
                                 error_regexp):
      self.iap_tunnel_websocket._WaitForOpenOrRaiseError()

  def testWaitForOpenOrRaiseErrorWith400ErrorMsg(self):
    self.iap_tunnel_websocket._connect_msg_received = False
    self.iap_tunnel_websocket._websocket_helper.IsClosed.return_value = True
    self.iap_tunnel_websocket._websocket_helper.ErrorMsg.return_value = (
        'Handshake status 400')
    error_regexp = (r'^Error while connecting \[Handshake status 400\]\. '
                    r'\(May be due to missing permissions\)$')
    with self.assertRaisesRegexp(iap_tunnel_websocket.ConnectionCreationError,
                                 error_regexp):
      self.iap_tunnel_websocket._WaitForOpenOrRaiseError()

  def testSendOneDataFrame(self):
    self.iap_tunnel_websocket.Send(b'testing')
    self.assertListEqual(list(self.iap_tunnel_websocket._unsent_data),
                         [b'testing'])
    self.iap_tunnel_websocket.Send(b'again')
    self.assertListEqual(list(self.iap_tunnel_websocket._unsent_data),
                         [b'testing', b'again'])

  def testSendSkipIfEmpty(self):
    self.iap_tunnel_websocket.Send(b'')
    self.assertFalse(self.iap_tunnel_websocket._unsent_data)

  def testSendSplitIntoFrames(self):
    large_data = b'\x03' * utils.SUBPROTOCOL_MAX_DATA_FRAME_SIZE
    self.iap_tunnel_websocket.Send(large_data + b'testing')
    self.assertListEqual(list(self.iap_tunnel_websocket._unsent_data),
                         [large_data, b'testing'])

  def testOnDataSubprotocolAck(self):
    self.iap_tunnel_websocket._total_bytes_confirmed = 5
    self.iap_tunnel_websocket._unconfirmed_data = collections.deque()
    self.iap_tunnel_websocket._unconfirmed_data.append(b'12')
    self.iap_tunnel_websocket._OnData(
        b'\x00\x07\x00\x00\x00\x00\x00\x00\x00\x07')
    self.assertEqual(self.iap_tunnel_websocket._total_bytes_confirmed, 7)

  def testOnDataSubprotocolConnectSuccessSid(self):
    self.iap_tunnel_websocket._connect_msg_received = False
    self.iap_tunnel_websocket._OnData(b'\x00\x01\x00\x00\x00\x07testing')
    self.assertFalse(self._received_data)
    self.assertEqual(self.iap_tunnel_websocket._connection_sid, b'testing')
    self.assertTrue(self.iap_tunnel_websocket._connect_msg_received)

  def testOnDataSubprotocolReconnectSuccessAck(self):
    self.iap_tunnel_websocket._connect_msg_received = False
    self.iap_tunnel_websocket._total_bytes_confirmed = 7
    self.iap_tunnel_websocket._unconfirmed_data = collections.deque()
    self.iap_tunnel_websocket._unconfirmed_data.append(b'123')
    self.iap_tunnel_websocket._OnData(
        b'\x00\x02\x00\x00\x00\x00\x00\x00\x00\x0a')
    self.assertTrue(self.iap_tunnel_websocket._connect_msg_received)
    self.assertEqual(self.iap_tunnel_websocket._total_bytes_confirmed, 10)

  def testOnDataSubprotocolData(self):
    # The data being received is a custom binary subprotocol that identifies the
    # type with the first two bytes and then the rest is specific to that
    # message type.
    self.iap_tunnel_websocket._OnData(b'\x00\x04\x00\x00\x00\x07testing')
    self.assertListEqual(self._received_data, [b'testing'])

    self.iap_tunnel_websocket._OnData(b'\x00\x04\x00\x00\x00\x05again')
    self.assertListEqual(self._received_data, [b'testing', b'again'])

  @parameterized.parameters(
      (b'\x00\x01\x00\x00\x00\x03SID', True,
       iap_tunnel_websocket.SubprotocolExtraConnectSuccessSid),
      (b'\x00\x01', False, utils.IncompleteData),
      (b'\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01', True,
       iap_tunnel_websocket.SubprotocolExtraReconnectSuccessAck),
      (b'\x00\x02', False, utils.IncompleteData),
      (b'\x00\x04', True, utils.IncompleteData),
      (b'\x00\x04\x00\x00\x00\x03DATA', False,
       iap_tunnel_websocket.SubprotocolEarlyDataError),
      (b'\x00\x07', True, utils.IncompleteData),
      (b'\x00\x07\x00\x00\x00\x00\x00\x00\x00\x02', False,
       iap_tunnel_websocket.SubprotocolEarlyAckError),
  )
  def testOnDataRaisesError(self, binary_data, is_connected, expected_error):
    self.iap_tunnel_websocket._connect_msg_received = is_connected
    self.iap_tunnel_websocket._unconfirmed_data.extend([b'a', b'c'])
    with self.AssertRaisesExceptionMatches(expected_error, ''):
      self.iap_tunnel_websocket._OnData(binary_data)

  @parameterized.parameters(
      (0, [], 0, 0, []),
      (4096, [b'1234'], 4100, 4100, []),
      (4100, [b'56789', b'abc'], 4108, 4108, []),
      (4108, [b'defghi', b'jk'], 4111, 4111, [b'ghi', b'jk']),
      (4111, [b'ghi', b'jk'], 4115, 4115, [b'k']),
  )
  def testConfirmData(self, start_bytes_confirmed, unconfirmed_data,
                      confirm_data_size, resulting_bytes_confirmed,
                      remaining_unconfirmed_data):
    self.iap_tunnel_websocket._total_bytes_confirmed = start_bytes_confirmed
    self.iap_tunnel_websocket._unconfirmed_data = collections.deque()
    self.iap_tunnel_websocket._unconfirmed_data.extend(unconfirmed_data)
    self.iap_tunnel_websocket._ConfirmData(confirm_data_size)
    self.assertEqual(self.iap_tunnel_websocket._total_bytes_confirmed,
                     resulting_bytes_confirmed)
    self.assertListEqual(list(self.iap_tunnel_websocket._unconfirmed_data),
                         remaining_unconfirmed_data)

  @parameterized.parameters(
      (4115, [], 4113, iap_tunnel_websocket.SubprotocolOutOfOrderAckError,
       'Received out-of-order Ack for [4113] bytes'),
      (4115, [], 4118, iap_tunnel_websocket.SubprotocolInvalidAckError,
       'Bytes confirmed [4118] were larger than bytes sent [4115]'),
      (4115, [b'lmnop'], 4121,
       iap_tunnel_websocket.SubprotocolInvalidAckError,
       'Bytes confirmed [4121] were larger than bytes sent [4120]'),
  )
  def testConfirmDataRaisesError(self, start_bytes_confirmed, unconfirmed_data,
                                 confirm_data_size, expected_error,
                                 expected_msg):
    self.iap_tunnel_websocket._total_bytes_confirmed = start_bytes_confirmed
    self.iap_tunnel_websocket._unconfirmed_data = collections.deque()
    self.iap_tunnel_websocket._unconfirmed_data.extend(unconfirmed_data)
    with self.AssertRaisesExceptionMatches(expected_error, expected_msg):
      self.iap_tunnel_websocket._ConfirmData(confirm_data_size)


if __name__ == '__main__':
  cli_test_base.main()
