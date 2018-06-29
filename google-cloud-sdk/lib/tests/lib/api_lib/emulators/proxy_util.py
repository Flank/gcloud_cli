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
"""Useful code for running emulator proxies."""

from __future__ import absolute_import
from __future__ import unicode_literals

import contextlib
import subprocess
from googlecloudsdk.command_lib.emulators import proxy_util
from googlecloudsdk.core.util import files


@contextlib.contextmanager
def RunEmulatorProxyClient(log_file=None, env=None):
  """Runs proxy client to test running emulator reverse proxy.

  Args:
    log_file: int, a file to reroute stdout and stderr to.
    env: dict, the env for the subprocess.

  Yields:
    the calling subprocess
  """
  reverse_proxy_jar = proxy_util.ReverseProxyJar()
  java_path = files.FindExecutableOnPath('java')
  classname = 'com.google.cloudsdk.emulators.Testing$ProtoClient'
  stdout = log_file if log_file is not None else subprocess.PIPE
  stderr = log_file if log_file is not None else subprocess.PIPE
  proc = subprocess.Popen(
      [java_path, '-cp', reverse_proxy_jar, classname],
      stdout=stdout, stderr=stderr, env=env)
  yield proc
  try:
    proc.kill()
  except OSError:
    # The caller did our dirty work for us
    pass
