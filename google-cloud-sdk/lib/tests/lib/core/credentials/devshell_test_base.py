# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Utilities used by devshell tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import socket
import threading

from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import devshell
from googlecloudsdk.core.credentials import store
from tests.lib import sdk_test_base


class _ServerTerminatedError(ValueError):
  pass


class AuthReferenceServer(threading.Thread):
  """Fake implementation of auth server."""

  def __init__(self, port, response=None):
    super(AuthReferenceServer, self).__init__(None)
    self.port = int(port)
    self.response = response or devshell.CredentialInfoResponse(
        user_email='joe@example.com',
        project_id='fooproj',
        access_token='sometoken',
        expires_in=1800)

  def __enter__(self):
    self.Start()

  def Start(self):
    if socket.has_ipv6:
      self._socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    else:
      self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    os.environ[devshell.DEVSHELL_ENV] = 'True'
    os.environ[devshell.DEVSHELL_CLIENT_PORT] = str(self.port)
    os.environ[devshell.DEVSHELL_ENV_IPV6_ENABLED] = str(self.port)
    self._socket.bind(('localhost', self.port))
    self._socket.listen(0)
    self._stopped = False
    self.start()
    return self

  def __exit__(self, e_type, value, traceback):
    self.Stop()

  def Stop(self):
    self._stopped = True
    del os.environ[devshell.DEVSHELL_ENV]
    del os.environ[devshell.DEVSHELL_CLIENT_PORT]
    del os.environ[devshell.DEVSHELL_ENV_IPV6_ENABLED]
    self._socket.close()

  def _AcceptOrCancel(self):
    """accept(), but watch for a Stop request and abort faster."""
    old_timeout = self._socket.gettimeout()
    timeout_step_sec = 0.2
    self._socket.settimeout(timeout_step_sec)
    for _ in range(int(old_timeout / timeout_step_sec)):
      try:
        s, unused_addr = self._socket.accept()
        break
      except socket.timeout:
        if self._stopped:
          raise _ServerTerminatedError()
    self._socket.settimeout(old_timeout)
    return s

  def run(self):
    s = None
    try:
      while True:
        try:
          self._socket.settimeout(15)
          s = self._AcceptOrCancel()
          resp_1 = s.recv(6).decode('utf-8')
          if '\n' not in resp_1:
            raise Exception('invalid request data')
          nstr, extra = resp_1.split('\n', 1)
          resp_buffer = extra
          n = int(nstr)
          to_read = n-len(extra)
          if to_read > 0:
            resp_buffer += s.recv(to_read, socket.MSG_WAITALL).decode('utf-8')
          if resp_buffer != '[]':
            raise Exception('bad request')
          msg = devshell.MessageToJSON(self.response)
          l = len(msg)
          s.sendall(('%d\n%s' % (l, msg)).encode('utf-8'))
        finally:
          if s:
            s.close()
    except (socket.error, _ServerTerminatedError):
      pass


class DevshellTestBase(sdk_test_base.SdkBase):
  """A base class for tests of Dev Shell.

  This class sets up the fake enviornment to test Dev Shell. Resources are
  cleaned up by the TearDown function at the end of each test.
  """

  @sdk_test_base.Retry(
      why='The port used by the proxy may be in use.',
      max_retrials=3,
      sleep_ms=300)
  def _CreateAndStartDevshellProxy(self):
    self.devshell_proxy = AuthReferenceServer(self.GetPort())
    try:
      self.devshell_proxy.Start()
    except Exception as e:  # pylint: disable=bare-except
      # Clean up environment variables set by Start().
      self.devshell_proxy.Stop()
      raise e

  def SetUp(self):
    self._devshell_provider = store.DevShellCredentialProvider()
    self._devshell_provider.Register()
    self.assertIsNone(properties.VALUES.core.project.Get())
    self._CreateAndStartDevshellProxy()
    self.assertEqual('fooproj', properties.VALUES.core.project.Get())

  def TearDown(self):
    self._devshell_provider.UnRegister()
    # Need to do this check while the dev shell proxy is still active.
    self.assertIsNone(properties.VALUES.core.project.Get())
    self.devshell_proxy.Stop()
