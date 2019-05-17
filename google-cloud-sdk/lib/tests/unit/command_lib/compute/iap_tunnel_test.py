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

"""Tests for iap_tunnel command lib."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ctypes
import errno
import io
import os
import socket
import sys
import time

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import iap_tunnel
from surface.compute import ssh as ssh_surface
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope import util
from tests.lib.surface.compute import test_base as compute_test_base
from tests.lib.surface.compute import utils as compute_tests_utils

import mock
import six


class StdinSocketRecvWindowsTest(test_case.Base):

  STDIN_HANDLE = 42

  def SetUp(self):
    self.StartPatch('ctypes.windll.kernel32.GetStdHandle', autospec=True)
    self.StartPatch('ctypes.windll.kernel32.ReadFile', autospec=True)

    ctypes.windll.kernel32.GetStdHandle.return_value = self.STDIN_HANDLE
    self.sock = iap_tunnel._StdinSocket()

  @test_case.Filters.RunOnlyOnWindows
  def testNormal(self):
    read_data = [b'data1', b'data2', b'a\na\0a\xffa', b'']

    def ReadFile(unused_h, buf, bufsize, number_of_bytes_read, unused_overlap):
      self.assertEqual(bufsize, len(buf.raw))
      b = read_data.pop(0)
      number_of_bytes_read._obj.value = len(b)
      buf.raw = b
      return 1

    ctypes.windll.kernel32.ReadFile.side_effect = ReadFile

    self.assertEqual(self.sock.recv(1024), b'data1')
    self.assertEqual(self.sock.recv(5), b'data2')
    self.assertEqual(self.sock.recv(1024), b'a\na\0a\xffa')
    self.assertEqual(self.sock.recv(1024), b'')

    self.assertEqual(ctypes.windll.kernel32.GetStdHandle.call_count, 4)
    ctypes.windll.kernel32.GetStdHandle.assert_has_calls([mock.call(-10)]*4)
    self.assertEqual(ctypes.windll.kernel32.ReadFile.call_count, 4)
    ctypes.windll.kernel32.ReadFile.assert_has_calls([
        mock.call(self.STDIN_HANDLE, mock.ANY, 1024, mock.ANY, None),
        mock.call(self.STDIN_HANDLE, mock.ANY, 5, mock.ANY, None),
        mock.call(self.STDIN_HANDLE, mock.ANY, 1024, mock.ANY, None),
        mock.call(self.STDIN_HANDLE, mock.ANY, 1024, mock.ANY, None)])

  @test_case.Filters.RunOnlyOnWindows
  def testFail(self):
    ctypes.windll.kernel32.ReadFile.return_value = 0
    with self.assertRaises(socket.error):
      self.sock.recv(1024)


class StdinSocketRecvUnixTest(test_case.Base):
  # pylint: disable=g-import-not-at-top

  def SetUp(self):
    self.StartPatch('fcntl.fcntl', autospec=True)
    self.StartPatch('sys.stdin', autospec=True)
    self.StartPatch('time.sleep', autospec=True)
    if six.PY2:
      self.stdin_mock = sys.stdin
    else:
      self.stdin_mock = sys.stdin.buffer

    self.sock = iap_tunnel._StdinSocket()

  @test_case.Filters.DoNotRunOnWindows
  def testNormal(self):
    import fcntl

    self.stdin_mock.read.side_effect = [b'data1', b'a\na\0a\xffa', b'']
    fcntl.fcntl.side_effect = [0x8002, 0, 0]*3

    self.assertEqual(self.sock.recv(1024), b'data1')
    self.assertEqual(self.sock.recv(1024), b'a\na\0a\xffa')
    self.assertEqual(self.sock.recv(1024), b'')

    self.assertEqual(self.stdin_mock.read.call_count, 3)
    self.stdin_mock.read.assert_has_calls(
        [mock.call(1024)]*3)
    self.assertEqual(fcntl.fcntl.call_count, 9)
    fcntl.fcntl.assert_has_calls(
        [mock.call(sys.stdin, fcntl.F_GETFL),
         mock.call(sys.stdin, fcntl.F_SETFL, 0x8002 | os.O_NONBLOCK),
         mock.call(sys.stdin, fcntl.F_SETFL, 0x8002)]*3)
    self.assertEqual(time.sleep.call_count, 0)

  @test_case.Filters.DoNotRunOnWindows
  def testBufsizeOne(self):
    import fcntl
    self.stdin_mock.read.return_value = b'd'
    self.assertEqual(self.sock.recv(1), b'd')
    self.assertEqual(self.stdin_mock.read.call_count, 1)
    self.assertEqual(fcntl.fcntl.call_count, 3)

  @test_case.Filters.DoNotRunOnWindows
  def testNoDataAvailableAtFirst(self):
    import fcntl

    # events is Exceptions to throw or data to return
    if six.PY2:
      # The EAGAIN error indicates no data is available
      events = [IOError(errno.EAGAIN, 'Resource temporarily unavailable'), b'd']
    else:
      # The None return value indicates no data is available
      events = [None, b'd']

    def Read(unused_bufsize):
      v = events.pop(0)
      if isinstance(v, Exception):
        raise v
      return v

    self.stdin_mock.read.side_effect = Read

    self.assertEqual(self.sock.recv(1024), b'd')

    self.assertEqual(self.stdin_mock.read.call_count, 2)
    self.assertEqual(fcntl.fcntl.call_count, 6)
    self.assertEqual(time.sleep.call_count, 1)

  @test_case.Filters.DoNotRunOnWindows
  def testEofInNonblocking(self):
    import fcntl

    self.stdin_mock.read.side_effect = [b'd', b'']

    self.assertEqual(self.sock.recv(1024), b'd')
    self.assertEqual(self.sock.recv(1024), b'')
    # Subsequent read calls will immediately return an empty string without
    # actually trying to read from stdin.
    self.assertEqual(self.sock.recv(1024), b'')

    self.assertEqual(self.stdin_mock.read.call_count, 2)
    self.assertEqual(fcntl.fcntl.call_count, 6)
    self.assertEqual(time.sleep.call_count, 0)


class StdinSocketSendTest(test_case.Base, test_case.WithOutputCapture):

  def testSend(self):
    sock = iap_tunnel._StdinSocket()
    self.assertEqual(sock.send(b'data1'), 5)
    self.assertEqual(sock.send(b'a\na\0a\xffa'), 7)
    self.assertEqual(self.GetOutputBytes(), b'data1a\na\0a\xffa')

  def testClose(self):
    sock = iap_tunnel._StdinSocket()
    sock.close()


# WithOutputCapture makes it hard to mock flush.
class StdinSocketSendFlushTest(test_case.Base):

  def testFlush(self):
    # Autospeccing sys.stdout should work, but Kokoro sets --capture=fd which
    # causes sys.stdout to be replaced with something that autospec can't handle
    # correctly.
    # This autospec makes sys.stdout look like python3, but that still works
    # well enough in python2 for the purpose of this test.
    self.StartPatch('sys.stdout',
                    autospec=io.TextIOWrapper(io.BufferedIOBase()))
    sock = iap_tunnel._StdinSocket()
    sock.send(b'data1')
    sock.send(b'a\na\0a\xffa')
    if six.PY2:
      self.assertEqual(sys.stdout.flush.call_count, 2)
    else:
      self.assertEqual(sys.stdout.buffer.flush.call_count, 2)


class SSHTunnelArgsTest(compute_test_base.BaseTest, parameterized.TestCase):

  API_VERSION = 'v1'

  def SetUp(self):
    self.parser = util.ArgumentParser()
    self.SelectApi(self.API_VERSION)
    self.api_mock = compute_tests_utils.ComputeApiMock(
        self.API_VERSION, project=self.Project(), zone='zone-1').Start()
    self.addCleanup(self.api_mock.Stop)

    self.instance_ref = self.api_mock.resources.Parse(
        'instance-2',
        params={'project': self.Project(), 'zone': 'zone-1'},
        collection='compute.instances')
    m = self.api_mock.messages
    self.external_nic = m.NetworkInterface(
        accessConfigs=[m.AccessConfig(natIP='10.0.0.0')])
    self.internal_nic = m.NetworkInterface(networkIP='10.0.0.1', name='nic0')

  def _FromArgs(self, cmd_line, include_external_nic=True):
    return iap_tunnel.SshTunnelArgs.FromArgs(
        self.parser.parse_args(cmd_line), base.ReleaseTrack.BETA,
        self.instance_ref, self.internal_nic,
        self.external_nic if include_external_nic else None)

  def _GenExpectedTunnelArgs(self):
    expected_tunnel_args = iap_tunnel.SshTunnelArgs()
    expected_tunnel_args.track = base.ReleaseTrack.BETA.prefix
    expected_tunnel_args.project = 'my-project'
    expected_tunnel_args.zone = 'zone-1'
    expected_tunnel_args.instance = 'instance-2'
    expected_tunnel_args.interface = 'nic0'
    return expected_tunnel_args

  @parameterized.parameters((False, False), (False, True),
                            (True, False), (True, True))
  def testFromArgsWithIapTunnelingEnabled(self, internal_ip_flag_available,
                                          iap_tunneling_flag_available):
    if internal_ip_flag_available:
      ssh_surface.AddInternalIPArg(self.parser)
    if iap_tunneling_flag_available:
      iap_tunnel.AddSshTunnelArgs(self.parser, self.parser)
    expected_tunnel_args = self._GenExpectedTunnelArgs()

    if iap_tunneling_flag_available:
      # Implicit enabled cases
      self.assertEqual(self._FromArgs([], include_external_nic=False),
                       expected_tunnel_args)
      # Explicit enabled cases
      self.assertEqual(self._FromArgs(['--tunnel-through-iap']),
                       expected_tunnel_args)
      self.assertEqual(self._FromArgs(['--tunnel-through-iap'],
                                      include_external_nic=False),
                       expected_tunnel_args)

    if internal_ip_flag_available and iap_tunneling_flag_available:
      # Implicit enabled cases
      self.assertEqual(self._FromArgs(['--no-internal-ip'],
                                      include_external_nic=False),
                       expected_tunnel_args)
      # Explicit enabled cases
      self.assertEqual(self._FromArgs(['--no-internal-ip',
                                       '--tunnel-through-iap']),
                       expected_tunnel_args)
      self.assertEqual(self._FromArgs(['--no-internal-ip',
                                       '--tunnel-through-iap'],
                                      include_external_nic=False),
                       expected_tunnel_args)

  @parameterized.parameters((False, False), (False, True),
                            (True, False), (True, True))
  def testFromArgsWithIapTunnelingDisabled(self, internal_ip_flag_available,
                                           iap_tunneling_flag_available):
    if internal_ip_flag_available:
      ssh_surface.AddInternalIPArg(self.parser)
    if iap_tunneling_flag_available:
      iap_tunnel.AddSshTunnelArgs(self.parser, self.parser)

    # Implicit disabled cases
    self.assertIsNone(self._FromArgs([]))
    if not iap_tunneling_flag_available:
      self.assertIsNone(self._FromArgs([], include_external_nic=False))

    if iap_tunneling_flag_available:
      # Explicit disabled cases
      self.assertIsNone(self._FromArgs(['--no-tunnel-through-iap']))
      self.assertIsNone(self._FromArgs(['--no-tunnel-through-iap'],
                                       include_external_nic=False))

    if internal_ip_flag_available:
      # Implicit disabled cases
      self.assertIsNone(self._FromArgs(['--internal-ip']))
      self.assertIsNone(self._FromArgs(['--internal-ip'],
                                       include_external_nic=False))
      self.assertIsNone(self._FromArgs(['--no-internal-ip']))

    if internal_ip_flag_available and iap_tunneling_flag_available:
      # Not allowed to use both --internal-ip and --tunnel-through-iap flags,
      # but --internal-ip trumps --tunnel-through-iap and IAP tunneling is
      # disabled.
      self.assertIsNone(self._FromArgs(['--internal-ip',
                                        '--tunnel-through-iap']))
      self.assertIsNone(self._FromArgs(['--internal-ip',
                                        '--tunnel-through-iap'],
                                       include_external_nic=False))
      # For completeness, other combinations with IAP tunneling explicitly
      # disabled.
      self.assertIsNone(self._FromArgs(['--internal-ip',
                                        '--no-tunnel-through-iap']))
      self.assertIsNone(self._FromArgs(['--internal-ip',
                                        '--no-tunnel-through-iap'],
                                       include_external_nic=False))
      self.assertIsNone(self._FromArgs(['--no-internal-ip',
                                        '--no-tunnel-through-iap']))
      self.assertIsNone(self._FromArgs(['--no-internal-ip',
                                        '--no-tunnel-through-iap'],
                                       include_external_nic=False))

  def testFromArgsWithPassThroughArgs(self):
    ssh_surface.AddInternalIPArg(self.parser)
    iap_tunnel.AddSshTunnelArgs(self.parser, self.parser)

    expected_tunnel_args = self._GenExpectedTunnelArgs()
    expected_tunnel_args.pass_through_args = [
        '--iap-tunnel-url-override=https://none']
    self.assertEqual(
        self._FromArgs(['--tunnel-through-iap',
                        '--iap-tunnel-url-override=https://none']),
        expected_tunnel_args)

    expected_tunnel_args.pass_through_args = [
        '--iap-tunnel-insecure-disable-websocket-cert-check']
    self.assertEqual(
        self._FromArgs(['--tunnel-through-iap',
                        '--iap-tunnel-insecure-disable-websocket-cert-check']),
        expected_tunnel_args)

    expected_tunnel_args.pass_through_args = [
        '--iap-tunnel-url-override=https://none',
        '--iap-tunnel-insecure-disable-websocket-cert-check']
    self.assertEqual(
        self._FromArgs(['--tunnel-through-iap',
                        '--iap-tunnel-url-override=https://none',
                        '--iap-tunnel-insecure-disable-websocket-cert-check']),
        expected_tunnel_args)

    expected_tunnel_args.pass_through_args = []
    self.assertEqual(
        self._FromArgs(
            ['--tunnel-through-iap',
             '--no-iap-tunnel-insecure-disable-websocket-cert-check']),
        expected_tunnel_args)


if __name__ == '__main__':
  test_case.main()
