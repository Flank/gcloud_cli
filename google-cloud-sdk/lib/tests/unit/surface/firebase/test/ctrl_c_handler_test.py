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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import signal

from googlecloudsdk.api_lib.firebase.test import ctrl_c_handler
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test.android import unit_base


MATRIX_ID = 'matrix99'


class CancellableTestSectionTests(unit_base.AndroidMockClientTest):

  @test_case.Filters.DoNotRunOnWindows
  def testCancellableTestSectionWithSigint(self):
    monitor = self.CreateMatrixMonitor(MATRIX_ID, self.args)
    self.ExpectMatrixCancel()
    # The code under test should work on Windows. However, Python does not
    # support sending POSIX signals on Windows. The Windows shell catches
    # CTRL-C and converts it into a SIGINT (which is why the code works).
    # Also, sending a CTRL_C_EVENT does not actually trigger the SIGINT handler.
    with self.assertRaises(exceptions.ExitCodeNoError):
      with ctrl_c_handler.CancellableTestSection(monitor):
        os.kill(os.getpid(), signal.SIGINT)
    self.AssertErrContains('Cancelling test [matrix99]')
    self.AssertErrContains('cancelled')

  @test_case.Filters.DoNotRunOnWindows
  def testCancellableTestSectionWithSigterm(self):
    monitor = self.CreateMatrixMonitor(MATRIX_ID, self.args)
    self.ExpectMatrixCancel()
    with self.assertRaises(exceptions.ExitCodeNoError):
      with ctrl_c_handler.CancellableTestSection(monitor):
        os.kill(os.getpid(), signal.SIGTERM)
    self.AssertErrContains('Cancelling test [matrix99]')
    self.AssertErrContains('cancelled')

  def testCancellableTestSection_RestoresSignalHandlers(self):
    monitor = self.CreateMatrixMonitor(MATRIX_ID, self.args)
    real_sigint_handler = signal.getsignal(signal.SIGINT)
    real_sigterm_handler = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGINT, FakeSigintHandler)
    signal.signal(signal.SIGTERM, FakeSigtermHandler)
    with ctrl_c_handler.CancellableTestSection(monitor):
      pass
    self.assertEqual(signal.getsignal(signal.SIGINT), FakeSigintHandler)
    self.assertEqual(signal.getsignal(signal.SIGTERM), FakeSigtermHandler)
    signal.signal(signal.SIGINT, real_sigint_handler)
    signal.signal(signal.SIGTERM, real_sigterm_handler)

  def ExpectMatrixCancel(self):
    self.testing_client.projects_testMatrices.Cancel.Expect(
        request=self.testing_msgs.TestingProjectsTestMatricesCancelRequest(
            projectId=self.PROJECT_ID, testMatrixId=MATRIX_ID),
        response=self.testing_msgs.CancelTestMatrixResponse(testState=None))


def FakeSigintHandler(unused_signal, unused_frame):
  pass


def FakeSigtermHandler(unused_signal, unused_frame):
  pass


if __name__ == '__main__':
  test_case.main()
