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

import io
import os
import subprocess
import sys

import googlecloudsdk
from googlecloudsdk.core.util import encoding
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

from six.moves import range  # pylint: disable=redefined-builtin


@test_case.Filters.DoNotRunOnWindows(
    'Cannot test tty behavior from a shell script.')
@test_case.Filters.DoNotRunOnMac(
    'pty not working on some mac installations.')
@sdk_test_base.Filters.RunOnlyInBundle
class IsInteractiveBundle(cli_test_base.CliTestBase):

  def ptyRequired(self):
    try:
      import pty   # pylint: disable=g-import-not-at-top, unused-variable
    except ImportError:
      self.SkipTest('Needs import pty')

  def SetUp(self):
    self.prog_dir = os.path.join(os.path.dirname(__file__), 'testdata')
    self.ptyshell = os.path.join(self.prog_dir, 'run_pty_shell')

  def RunScenario(self, scenario):
    """Runs `gcloud meta test <scenario>`."""

    self.ptyRequired()
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
    python_path = encoding.GetEncodedValue(env, 'PYTHONPATH')
    python_path = os.pathsep.join(
        ([python_path] if python_path else []) + [sdk_path])
    encoding.SetEncodedValue(env, 'PYTHONPATH', python_path)
    # Prevent gcloud wrapper script fallback to a python different from the one
    # running this test.
    encoding.SetEncodedValue(env, 'CLOUDSDK_PYTHON', sys.executable)

    # Subprocess stderr=X redirection requires file streams, not buffers.
    # stderr=subprocess.PIPE only works reliably with p=subprocess.Popen() and
    # p.communicate(), but that messes up meta test signal delivery by absorbing
    # it -- we would never see it here.
    try:
      stderr_path = os.path.join(self.temp_path, 'stderr')
      stderr = io.open(stderr_path, 'w')
      command_args = ['/bin/bash', self.ptyshell, scenario]
      subprocess.check_call(command_args, stderr=stderr, env=env)
    finally:
      stderr.close()
      stderr = io.open(stderr_path, 'r')
      # Write the subprocess stderr to the buffer stream used by the
      # WithOutputCapture mixin.
      sys.stderr.write(stderr.read())
      stderr.close()
      os.remove(stderr_path)

  def testInteractive1(self):
    testfile = os.path.join(self.prog_dir, 'interactive_bash_test1.sh')
    self.RunScenario(testfile)
    self.AssertErrContains('TRUE')

  def testInteractive2(self):
    testfile = os.path.join(self.prog_dir, 'interactive_bash_test2.sh')
    self.RunScenario(testfile)
    self.AssertErrContains('TRUE')

  def testInteractive3(self):
    testfile = 'for i in 1 2; do gcloud meta test --is-interactive;done'
    self.RunScenario(testfile)
    self.AssertErrContains('TRUE')


if __name__ == '__main__':
  cli_test_base.main()
