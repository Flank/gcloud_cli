# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

import ctypes
import functools
import io
import select
import socket
import sys
import time

from googlecloudsdk.api_lib.compute import iap_tunnel_websocket
from googlecloudsdk.api_lib.compute import iap_tunnel_websocket_utils
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.util import platforms
from tests.lib import mock_matchers
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base

import mock
import portpicker
import six

MESSAGES = apis.GetMessagesModule('compute', 'v1')
MAX_SELECT_WAIT_TIME_SEC = 120

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
    selfLink=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1/instances/instance-1'),
    zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
          'zones/zone-1'))


class StartIapTunnelTestGA(test_base.BaseTest, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    # test_base.BaseTest replaces sleep with a mock, but we need it.
    self.real_sleep = time.sleep

  def SetUp(self):
    self.SelectApi('v1' if self.track.prefix is None else self.track.prefix)

    self.c_store_load = self.StartObjectPatch(
        c_store, 'LoadIfEnabled', autospec=True, return_value='an access token')
    self.c_store_refresh = self.StartObjectPatch(
        c_store, 'Refresh', autospec=True, return_value=None)

    # Mocks for incoming local socket connections.
    self.portpicker_mock = self.StartObjectPatch(
        portpicker, 'is_port_free', autospec=True, return_value=True)
    self.socket_getaddrinfo = self.StartObjectPatch(
        socket, 'getaddrinfo', autospec=True,
        return_value=[(socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP,
                       'canonname', ('::1', 22175, 0, 0)),
                      (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP,
                       'canonname', ('127.0.0.1', 22175))])
    self.socket_mock = mock.MagicMock()
    self.socket_mock.fileno.return_value = 10
    self.socket_mock2 = mock.MagicMock()
    self.socket_mock2.fileno.return_value = 11
    self.socket_init = self.StartObjectPatch(socket, 'socket')
    self.socket_init.side_effect = [self.socket_mock, self.socket_mock2]
    self.conn_mock = mock.MagicMock()
    self.conn_mock.recv.side_effect = [b'data1', b'data2', b'']
    self.socket_mock.accept.return_value = (self.conn_mock, ('::1', 22176))

    def SelectGenerator():
      yield [[self.socket_mock], [], []]
      max_wait_time = time.time() + MAX_SELECT_WAIT_TIME_SEC
      while (self.websocket_mock2.Close.call_count < 1 and
             time.time() < max_wait_time):
        self.real_sleep(0.2)
        yield [[], [], []]
      raise KeyboardInterrupt()

    self.select_mock = self.StartObjectPatch(select, 'select', autospec=True)
    self.select_mock.side_effect = SelectGenerator()

    # WebSocket mocks.
    self.websocket_mock1 = mock.MagicMock()
    self.websocket_mock2 = mock.MagicMock()

    # These mocks lazily create member objects. We force the Close member mock
    # object to be allocated here. Otherwise there's a race condition where 2
    # Close objects could be created simultaneously in 2 threads causing flakes.
    self.websocket_mock2.Close  # pylint: disable=pointless-statement

    def WebSocketInitGenerator():
      yield self.websocket_mock1
      yield self.websocket_mock2
      raise RuntimeError('No more websocket mocks')

    self.websocket_cls_mock = self.StartObjectPatch(
        iap_tunnel_websocket, 'IapTunnelWebSocket', autospec=True,
        side_effect=WebSocketInitGenerator())

  @parameterized.parameters(
      ('compute start-iap-tunnel instance-1 22 --zone zone-1 '
       '--local-host-port localhost:22175',),
      ('compute start-iap-tunnel instance-1 22 --zone zone-1 '
       '--local-host-port :22175',))
  def testSimpleCase(self, gcloud_cmd):
    self.make_requests.side_effect = [
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.v1_messages.Project(name='my-project')],
    ]

    self.Run(gcloud_cmd)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

    self.assertEqual(self.c_store_load.call_count, 2)
    self.assertEqual(self.c_store_refresh.call_count, 0)
    self.assertEqual(self.portpicker_mock.call_count, 1)
    self.socket_getaddrinfo.assert_has_calls([
        mock.call('localhost', 22175, socket.AF_UNSPEC, socket.SOCK_STREAM, 0,
                  socket.AI_PASSIVE)])
    self.assertEqual(self.socket_getaddrinfo.call_count, 1)

    # Server socket is created then bind() and listen() followed by select()
    # at least twice -- the first yielding the one connection from accept() call
    # and a later one being interrupted by a raised keyboard exception.
    self.socket_init.assert_has_calls([
        mock.call(socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP),
        mock.call(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)])
    self.assertEqual(self.socket_init.call_count, 2)
    self.socket_mock.bind.assert_has_calls([mock.call(('::1', 22175, 0, 0))])
    self.assertEqual(self.socket_mock.bind.call_count, 1)
    self.socket_mock.listen.assert_has_calls([mock.call(1)])
    self.assertEqual(self.socket_mock.listen.call_count, 1)

    self.socket_mock2.bind.assert_has_calls([mock.call(('127.0.0.1', 22175))])
    self.assertEqual(self.socket_mock2.bind.call_count, 1)
    self.socket_mock2.listen.assert_has_calls([mock.call(1)])
    self.assertEqual(self.socket_mock2.listen.call_count, 1)

    self.select_mock.assert_called_with([self.socket_mock, self.socket_mock2],
                                        (), (), 0.2)
    self.assertTrue(self.select_mock.call_count >= 2)  # pylint:disable=g-generic-assert
    self.socket_mock.accept.assert_has_calls([mock.call()])
    self.assertEqual(self.socket_mock.accept.call_count, 1)
    self.socket_mock.close.assert_has_calls([mock.call()])
    self.assertEqual(self.socket_mock.close.call_count, 1)
    self.assertEqual(self.socket_mock2.accept.call_count, 0)
    self.socket_mock2.close.assert_has_calls([mock.call()])
    self.assertEqual(self.socket_mock2.close.call_count, 1)

    # Calls for one connection that was accepted.  Three recv() calls that
    # result in two websocket Send().  The last results in no data and signals
    # closing of the connection.
    self.conn_mock.recv.assert_has_calls([mock.call(16384)]*3)
    self.assertEqual(self.conn_mock.recv.call_count, 3)
    self.conn_mock.close.assert_has_calls([mock.call()])
    self.assertTrue(self.conn_mock.close.call_count >= 1)  # pylint:disable=g-generic-assert

    tunnel_target = iap_tunnel_websocket_utils.IapTunnelTargetInfo(
        project='my-project', zone='zone-1', instance='instance-1',
        interface='nic0', port=22, url_override=None, proxy_info=None)
    partial_matcher = mock_matchers.TypeMatcher(functools.partial)
    self.websocket_cls_mock.assert_has_calls([
        mock.call(tunnel_target, partial_matcher, partial_matcher,
                  partial_matcher, ignore_certs=False)]*2)
    self.assertEqual(self.websocket_cls_mock.call_count, 2)

    # Test connection to start.
    self.assertEqual(self.websocket_mock1.InitiateConnection.call_count, 1)
    self.assertEqual(self.websocket_mock1.Send.call_count, 0)
    self.assertEqual(self.websocket_mock1.LocalEOF.call_count, 0)
    self.assertEqual(self.websocket_mock1.WaitForAllSent.call_count, 0)
    self.assertEqual(self.websocket_mock1.Close.call_count, 1)
    # Calls resulting from one connection that was accepted.
    self.assertEqual(self.websocket_mock2.InitiateConnection.call_count, 1)
    self.websocket_mock2.Send.assert_has_calls([
        mock.call(b'data1'), mock.call(b'data2')])
    self.assertEqual(self.websocket_mock2.Send.call_count, 2)
    self.assertEqual(self.websocket_mock2.LocalEOF.call_count, 1)
    self.assertEqual(self.websocket_mock2.WaitForAllSent.call_count, 1)
    self.assertEqual(self.websocket_mock2.Close.call_count, 1)


class StartIapTunnelTestBeta(StartIapTunnelTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class StartIapTunnelTestAlpha(StartIapTunnelTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class StartIapTunnelStdinTestGA(test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi('v1' if self.track.prefix is None else self.track.prefix)

    self.c_store_load = self.StartObjectPatch(
        c_store, 'LoadIfEnabled', autospec=True, return_value='an access token')
    self.c_store_refresh = self.StartObjectPatch(
        c_store, 'Refresh', autospec=True, return_value=None)

    # Mock how StdinSocket accesses stdin.
    if platforms.OperatingSystem.IsWindows():
      self.StartPatch('ctypes.windll.kernel32.GetStdHandle', autospec=True)
      self.StartPatch('ctypes.windll.kernel32.ReadFile', autospec=True)

      read_data = [b'data1', b'data2', b'']

      def ReadFile(unused_h, buf, unused_bufsize, number_of_bytes_read,
                   unused_overlapped):
        b = read_data.pop(0)
        number_of_bytes_read._obj.value = len(b)
        buf.raw = b
        return 1

      ctypes.windll.kernel32.ReadFile.side_effect = ReadFile

    else:
      self.StartPatch('fcntl.fcntl', autospec=True)
      if six.PY2:
        self.StartPatch('sys.stdin', autospec=True)
        self.stdin_mock = sys.stdin
      else:
        # Manually create an autospec object because sys.stdin has already been
        # replaced by FakeStd which autospec can't handle buffer correctly.
        self.StartPatch('sys.stdin',
                        autospec=io.TextIOWrapper(io.BufferedIOBase()))
        self.stdin_mock = sys.stdin.buffer
      self.stdin_mock.read.side_effect = [b'data1', b'data2', b'']

    # WebSocket mock.
    self.websocket_mock = mock.MagicMock()

    def WebSocketInitGenerator():
      yield self.websocket_mock
      raise RuntimeError('No more websocket mocks')

    self.websocket_cls_mock = self.StartObjectPatch(
        iap_tunnel_websocket, 'IapTunnelWebSocket', autospec=True,
        side_effect=WebSocketInitGenerator())

  @test_case.Filters.SkipOnWindowsAndPy3('failing', 'b/143145077')
  def testSimpleCase(self):
    self.make_requests.side_effect = [
        [INSTANCE_WITH_EXTERNAL_ADDRESS],
        [self.v1_messages.Project(name='my-project')],
    ]

    self.Run('compute start-iap-tunnel instance-1 22 --zone zone-1 '
             '--listen-on-stdin')

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1',
              project='my-project',
              zone='zone-1'))],
    )

    self.assertEqual(self.c_store_load.call_count, 1)
    self.assertEqual(self.c_store_refresh.call_count, 0)

    # The last call results in no data and signals closing of the connection.
    if platforms.OperatingSystem.IsWindows():
      # Three ReadFile() calls that result in two websocket Send().
      ctypes.windll.kernel32.ReadFile.assert_has_calls(
          [mock.call(mock.ANY, mock.ANY, 16384, mock.ANY, None)]*3)
      self.assertEqual(ctypes.windll.kernel32.ReadFile.call_count, 3)
    else:
      # Three read() calls that result in two websocket Send().
      self.stdin_mock.read.assert_has_calls([mock.call(16384)]*3)
      self.assertEqual(self.stdin_mock.read.call_count, 3)

    tunnel_target = iap_tunnel_websocket_utils.IapTunnelTargetInfo(
        project='my-project', zone='zone-1', instance='instance-1',
        interface='nic0', port=22, url_override=None, proxy_info=None)
    partial_matcher = mock_matchers.TypeMatcher(functools.partial)
    self.websocket_cls_mock.assert_called_once_with(
        tunnel_target, partial_matcher, partial_matcher, partial_matcher,
        ignore_certs=False)

    self.assertEqual(self.websocket_mock.InitiateConnection.call_count, 1)
    self.websocket_mock.Send.assert_has_calls([
        mock.call(b'data1'), mock.call(b'data2')])
    self.assertEqual(self.websocket_mock.Send.call_count, 2)
    self.assertEqual(self.websocket_mock.LocalEOF.call_count, 1)
    self.assertEqual(self.websocket_mock.WaitForAllSent.call_count, 1)
    self.assertEqual(self.websocket_mock.Close.call_count, 1)


class StartIapTunnelStdinTestBeta(StartIapTunnelStdinTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class StartIapTunnelStdinTestAlpha(StartIapTunnelStdinTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
