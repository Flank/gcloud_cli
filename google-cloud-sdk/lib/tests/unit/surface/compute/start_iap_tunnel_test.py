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

"""Tests for the start_iap_tunnel subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools
import socket
import time

from googlecloudsdk.api_lib.compute import iap_tunnel_websocket
from googlecloudsdk.api_lib.compute import iap_tunnel_websocket_utils
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.credentials import store as c_store
from tests.lib import mock_matchers
from tests.lib import test_case
from tests.lib.surface.compute import test_base

import mock
import portpicker

MESSAGES = apis.GetMessagesModule('compute', 'v1')
MAX_ACCEPT_WAIT_TIME_SEC = 120

INSTANCE_WITH_EXTERNAL_ADDRESS = MESSAGES.Instance(
    id=11111,
    name='instance-1',
    networkInterfaces=[
        MESSAGES.NetworkInterface(
            accessConfigs=[
                MESSAGES.AccessConfig(
                    name='external-nat',
                    natIP='23.251.133.75'),
            ],
            name='nic0',
        ),
    ],
    status=MESSAGES.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-1'),
    zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-1'))


class StartIapTunnelTestBeta(test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.c_store_load = self.StartObjectPatch(
        c_store, 'LoadIfEnabled', autospec=True, return_value='an access token')
    self.c_store_refresh = self.StartObjectPatch(
        c_store, 'Refresh', autospec=True, return_value=None)

    # Mocks for incoming local socket connections.
    self.portpicker_mock = self.StartObjectPatch(
        portpicker, 'is_port_free', autospec=True, return_value=True)
    self.socket_getaddrinfo = self.StartObjectPatch(
        socket, 'getaddrinfo', autospec=True,
        return_value=[(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP,
                       'canonname', ('127.0.0.1', 22175))])
    self.socket_mock = mock.MagicMock()
    self.socket_init = self.StartObjectPatch(
        socket, 'socket', return_value=self.socket_mock)
    self.conn_mock = mock.MagicMock()
    self.conn_mock.recv.side_effect = iter(['data1', 'data2', None])

    def SocketAcceptGenerator():
      yield (self.conn_mock, ('127.0.0.1', 22176))
      max_wait_time = time.time() + MAX_ACCEPT_WAIT_TIME_SEC
      while (self.websocket_mock2.Close.call_count < 1 and
             time.time() < max_wait_time):
        time.sleep(0.001)
      raise KeyboardInterrupt()

    self.socket_mock.accept.side_effect = SocketAcceptGenerator()

    # WebSocket mocks.
    self.websocket_mock1 = mock.MagicMock()
    self.websocket_mock2 = mock.MagicMock()

    def WebSocketInitGenerator():
      yield self.websocket_mock1
      yield self.websocket_mock2
      raise RuntimeError('No more websocket mocks')

    self.websocket_cls_mock = self.StartObjectPatch(
        iap_tunnel_websocket, 'IapTunnelWebSocket', autospec=True,
        side_effect=WebSocketInitGenerator())

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.v1_messages.Project(name='my-project')],
    ])

    self.Run("""
        compute start-iap-tunnel instance-1 22 --zone zone-1
        --local-host-port localhost:22175
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          MESSAGES.ComputeInstancesGetRequest(
              instance='instance-1',
              project=str('my-project'),
              zone='zone-1'))],
    )

    self.assertEqual(self.c_store_load.call_count, 2)
    self.assertEqual(self.c_store_refresh.call_count, 0)
    self.assertEqual(self.portpicker_mock.call_count, 1)
    self.socket_getaddrinfo.assert_has_calls([
        mock.call('localhost', 22175, socket.AF_UNSPEC, socket.SOCK_STREAM, 0,
                  socket.AI_PASSIVE)])
    self.assertEqual(self.socket_getaddrinfo.call_count, 1)

    # Server socket is created then bind() and listen() followed by accept()
    # twice -- the first yielding the one connection and the second being
    # interrupted by a raised keyboard exception.
    self.socket_init.assert_has_calls([
        mock.call(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)])
    self.assertEqual(self.socket_init.call_count, 1)
    self.socket_mock.bind.assert_has_calls([mock.call(('127.0.0.1', 22175))])
    self.assertEqual(self.socket_mock.bind.call_count, 1)
    self.socket_mock.listen.assert_has_calls([mock.call(1)])
    self.assertEqual(self.socket_mock.listen.call_count, 1)
    self.socket_mock.accept.assert_has_calls([mock.call(), mock.call()])
    self.assertEqual(self.socket_mock.accept.call_count, 2)
    self.socket_mock.close.assert_has_calls([mock.call()])
    self.assertEqual(self.socket_mock.close.call_count, 1)

    # Calls for one connection that was accepted.  Three recv() calls that
    # result in two websocket Send().  The last results in no data and signals
    # closing of the connection.
    self.conn_mock.recv.assert_has_calls([
        mock.call(16384), mock.call(16384), mock.call(16384)])
    self.assertEqual(self.conn_mock.recv.call_count, 3)
    self.conn_mock.close.assert_has_calls([mock.call()])
    self.assertTrue(self.conn_mock.close.call_count >= 1)

    tunnel_target = iap_tunnel_websocket_utils.IapTunnelTargetInfo(
        project=str('my-project'), zone='zone-1', instance='instance-1',
        interface='nic0', port=22, url_override=None, proxy_info=None)
    partial_matcher = mock_matchers.TypeMatcher(functools.partial)
    self.websocket_cls_mock.assert_has_calls([
        mock.call(tunnel_target, partial_matcher, partial_matcher,
                  partial_matcher, ignore_certs=False),
        mock.call(tunnel_target, partial_matcher, partial_matcher,
                  partial_matcher, ignore_certs=False)])

    # Test connection to start.
    self.assertEqual(self.websocket_mock1.InitiateConnection.call_count, 1)
    self.assertEqual(self.websocket_mock1.Close.call_count, 1)
    # Calls resulting from one connection that was accepted.
    self.assertEqual(self.websocket_mock2.InitiateConnection.call_count, 1)
    self.websocket_mock2.Send.assert_has_calls([
        mock.call('data1'), mock.call('data2')])
    self.assertEqual(self.websocket_mock2.Send.call_count, 2)
    self.assertEqual(self.websocket_mock2.Close.call_count, 1)


class StartIapTunnelTestAlpha(StartIapTunnelTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
