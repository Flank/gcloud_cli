# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Tests for the core.util.keyboard_interrupt module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import subprocess
import sys

import googlecloudsdk
from googlecloudsdk.core.util import encoding
from tests.lib import cli_test_base
from tests.lib import test_case
from six.moves import range


@test_case.Filters.DoNotRunOnWindows(
    'Must be running in Windows console to test ^C.')
@test_case.Filters.RunOnlyInKokoro('see notes in b/72871055')
class KeyboardInterruptTests(cli_test_base.CliTestBase):

  def RunScenario(self, scenario):
    """Runs `gcloud meta test <scenario>`."""

    # First get the path of the python gcloud main module.
    # This could be different in unit and bundled tests.
    sdk_path = googlecloudsdk.__file__
    for _ in range(2):
      sdk_path = os.path.dirname(sdk_path)
      gcloud = os.path.join(sdk_path, 'gcloud.py')
      if os.path.exists(gcloud):
        break

    # Make sure the gcloud main imports are visible.
    env = os.environ.copy()
    encoding.SetEncodedValue(env, 'PYTHONPATH', os.pathsep.join(sys.path))

    # Subprocess stderr=X redirection requires file streams, not buffers.
    # stderr=subprocess.PIPE only works resliably with p=subprocess.Popen() and
    # p.communicate(), but that messes up meta test signal delivery by absorbing
    # it -- we would never see it here.
    try:
      stderr_path = os.path.join(self.temp_path, 'stderr')
      stderr = open(stderr_path, 'w')
      # Here we do not disable site packages, since these tests can run under
      # virtual env where not all packages are vendored.
      subprocess.check_call(
          [sys.executable, gcloud, 'meta', 'test', scenario],
          stderr=stderr, env=env)
    finally:
      stderr.close()
      stderr = open(stderr_path, 'r')
      # Write the subprocess stderr to the buffer stream used by the
      # WithOutputCapture mixin.
      sys.stderr.write(stderr.read())
      stderr.close()
      os.remove(stderr_path)

  def testKeyboardInterrupt(self):
    with self.AssertRaisesExceptionMatches(
        subprocess.CalledProcessError,
        'Command'):
      self.RunScenario('--interrupt')
    self.AssertErrContains('Command killed by keyboard interrupt')


if __name__ == '__main__':
  cli_test_base.main()
