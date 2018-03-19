# Copyright 2015 Google Inc. All Rights Reserved.
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
import os
import socket
import threading

from googlecloudsdk.core.credentials import devshell


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

    os.environ[devshell.DEVSHELL_ENV] = str(self.port)
    os.environ[devshell.DEVSHELL_ENV_IPV6_ENABLED] = str(self.port)
    self._socket.bind(('localhost', self.port))
    self._socket.listen(0)
    self.start()
    return self

  def __exit__(self, e_type, value, traceback):
    self.Stop()

  def Stop(self):
    del os.environ[devshell.DEVSHELL_ENV]
    del os.environ[devshell.DEVSHELL_ENV_IPV6_ENABLED]
    self._socket.close()

  def run(self):
    s = None
    try:
      while True:
        try:
          self._socket.settimeout(15)
          s, unused_addr = self._socket.accept()
          resp_buffer = ''
          resp_1 = s.recv(6)
          if '\n' not in resp_1:
            raise Exception('invalid request data')
          nstr, extra = resp_1.split('\n', 1)
          resp_buffer = extra
          n = int(nstr)
          to_read = n-len(extra)
          if to_read > 0:
            resp_buffer += s.recv(to_read, socket.MSG_WAITALL)
          if resp_buffer != '[]':
            raise Exception('bad request')
          msg = devshell.MessageToJSON(self.response)
          l = len(msg)
          s.sendall('%d\n%s' % (l, msg))
        finally:
          if s:
            s.close()
    except socket.error:
      pass
