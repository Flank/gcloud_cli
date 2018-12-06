# -*- coding: utf-8 -*- #
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
"""Integration tests for the emulators pubsub commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import tempfile
from googlecloudsdk.command_lib.util import java
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.emulators import proxy_util


# TODO(b/36895967) It would be nice to get rid of the dependency on
# BundledBase, which in practice is a bit too coarse. Ideally, it would
# depend on things like it depends on java -- check if they are there,
# fail if they aren't. For extra credit, it would be possible to configure
# the location of the dependency for it can easily be run in different ways.
@test_case.Filters.SkipOnPy3('They are broken', 'b/116340294')
class StartTests(sdk_test_base.BundledBase, cli_test_base.CliTestBase):

  def SetUp(self):
    # Verify that Java is installed or skip these tests
    with self.SkipTestIfRaises(java.JavaError):
      java.RequireJavaInstalled('test')

  @test_case.Filters.SkipOnWindows('Subprocess and windows not playing nicely',
                                   'b/34811745')
  def testStart(self):
    port = self.GetPort()
    test_call_out = None
    # We wrap the execution for error handling purposes. We do not want to
    # interleave the emulator stdout with the grpc call's standard out, but if
    # there is an error it useful to have both. When the test catches the
    # TimeoutError it will print the emulator's stdout, so we need to print the
    # grpc calling process's.
    try:
      with self.ExecuteScriptAsync(
          'gcloud', ['alpha', 'emulators', 'start', '--emulators=pubsub',
                     '--proxy-port=' + port],
          match_strings=['Logging pubsub to:',
                         'Executing:',
                         'routes configuration written to file:',
                         'proxy configuration written to file:',
                         ('INFO: proxying to gcp disabled and local emulator '
                          'not found, no route for service: datastore'),
                         ('INFO: creating handler for service [pubsub] to '
                          'local port ['),
                         'com.google.cloudsdk.emulators.EmulatorProxy main',
                         'INFO: Starting server on port: {}'.format(port)],
          timeout=30):
        test_call_env = dict(os.environ,
                             PUBSUB_EMULATOR_HOST='localhost:{}'.format(port),
                             GOOGLE_CLOUD_PROJECT='cloudsdktest')
        test_call_out_no, test_call_out = tempfile.mkstemp()
        with proxy_util.RunEmulatorProxyClient(
            log_file=test_call_out_no, env=test_call_env) as proc:
          proc.wait()
          output = files.ReadFileContents(test_call_out)
          self.assertIn('Created with target localhost:' + port, output)
          self.assertIn('topic created', output)
          self.assertIn('topic deleted', output)
          self.assertIn('it all checks out!', output)
          self.assertIn('Terminated', output)
    finally:
      if test_call_out is not None:
        log.status.Print(
            ('had exception, printing out subprocess '
             'stdout and stderr\n{line}\n{content}\n{line}').format(
                 line='='*80,
                 content=files.ReadFileContents(test_call_out)))


if __name__ == '__main__':
  test_case.main()
