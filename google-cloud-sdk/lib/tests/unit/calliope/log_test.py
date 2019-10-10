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
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.calliope import util


class LoggingConfigTest(util.Base, sdk_test_base.WithOutputCapture):
  """Tests basic configuration of the python logger under calliope."""

  def SetUp(self):
    log.Reset()
    log.SetUserOutputEnabled(True)

  def TearDown(self):
    log.Reset()

  def testCLIMode(self):
    """Makes sure INFO goes to stdout when executing from the command line."""
    cli = self.GetCLI()
    cli.Execute(['loggingcommand'])

    self._DoCommonLogCheck()
    self.AssertOutputContains('INFO message3')
    self.AssertErrNotContains('INFO message3')
    self.AssertOutputNotContains('INFO message4')
    self.AssertErrContains('INFO message4')
    self.assertIn('INFO message3', self.GetLogFileContents())
    self.assertIn('INFO message4', self.GetLogFileContents())

  def testCLIModeNoOutput(self):
    """Make sure we can suppress INFO if we want."""
    cli = self.GetCLI()
    cli.Execute(['--no-user-output-enabled', 'loggingcommand'])

    self._DoCommonLogCheck()
    self.AssertOutputNotContains('INFO message3')
    self.AssertErrNotContains('INFO message3')
    self.AssertOutputNotContains('INFO message4')
    self.AssertErrNotContains('INFO message4')
    self.assertIn('INFO message3', self.GetLogFileContents())
    self.assertIn('INFO message4', self.GetLogFileContents())

  def testCLIModeNoOutputDeprecatedExplicitFalse(self):
    """Make sure we can suppress INFO if we want."""
    cli = self.GetCLI()
    cli.Execute(['--user-output-enabled=false', 'loggingcommand'])

    self._DoCommonLogCheck()
    self.AssertOutputNotContains('INFO message3')
    self.AssertErrNotContains('INFO message3')
    self.AssertOutputNotContains('INFO message4')
    self.AssertErrNotContains('INFO message4')
    self.assertIn('INFO message3', self.GetLogFileContents())
    self.assertIn('INFO message4', self.GetLogFileContents())

  def testCLIModeNoOutputDeprecatedExplicitTrue(self):
    """Make sure we can enable INFO if we want."""
    cli = self.GetCLI()
    cli.Execute(['--user-output-enabled=true', 'loggingcommand'])

    self._DoCommonLogCheck()
    self.AssertOutputContains('INFO message3')
    self.AssertErrNotContains('INFO message3')
    self.AssertOutputNotContains('INFO message4')
    self.AssertErrContains('INFO message4')
    self.assertIn('INFO message3', self.GetLogFileContents())
    self.assertIn('INFO message4', self.GetLogFileContents())

  def testCLIModeVerbosity(self):
    """Make sure we can suppress INFO if we want."""
    cli = self.GetCLI()
    cli.Execute(['--verbosity=info', 'loggingcommand'])

    # Still get stdout and stderr
    self.AssertOutputContains('INFO message3')
    self.AssertErrContains('INFO message4')

    # Now we get info too.
    self.AssertErrContains('INFO message1')
    self.AssertErrContains('INFO message2')
    self.assertIn('INFO message1', self.GetLogFileContents())
    self.assertIn('INFO message2', self.GetLogFileContents())

  def testCLIModeLowVerbosity(self):
    """Make sure we can suppress INFO if we want."""
    cli = self.GetCLI()
    cli.Execute(['--verbosity=critical', 'loggingcommand'])

    # Still get stdout and stderr
    self.AssertOutputContains('INFO message3')
    self.AssertErrContains('INFO message4')

    # No logging comes out.
    self.AssertErrNotContains('INFO message1')
    self.AssertErrNotContains('INFO message2')
    self.AssertErrNotContains('WARNING message1')
    self.AssertErrNotContains('WARNING message2')
    self.AssertErrNotContains('ERROR message1')
    self.AssertErrNotContains('ERROR message2')

    # Still log to file.
    self.assertIn('INFO message1', self.GetLogFileContents())
    self.assertIn('INFO message2', self.GetLogFileContents())
    self.assertIn('WARNING message1', self.GetLogFileContents())
    self.assertIn('WARNING message2', self.GetLogFileContents())
    self.assertIn('ERROR message1', self.GetLogFileContents())
    self.assertIn('ERROR message2', self.GetLogFileContents())

  def testFileLoggingDisabled(self):
    properties.VALUES.core.disable_file_logging.Set(True)
    cli = self.GetCLI()

    cli.Execute(['loggingcommand'])

    # No logging file gets created.
    self.assertEqual([], os.listdir(self.logs_dir))

    # Still get console logging.
    self.AssertOutputContains('INFO message3')
    self.AssertErrContains('INFO message4')
    self.AssertErrContains('WARNING: WARNING message1')
    self.AssertErrContains('WARNING: WARNING message2')
    self.AssertErrContains('ERROR: ERROR message1')
    self.AssertErrContains('ERROR: ERROR message2')

  def testMultipleFiles(self):
    cli = self.GetCLI()
    logs_dir2 = self.CreateTempDir()
    log.AddFileLogging(logs_dir2)
    cli.Execute(['loggingcommand'])

    self._DoCommonLogCheck()
    self._DoCommonLogCheck(logs_dir2)

  def testDirReregistration(self):
    cli = self.GetCLI()
    log.AddFileLogging(self.logs_dir)
    cli.Execute(['loggingcommand'])
    self._DoCommonLogCheck()

  def _DoCommonLogCheck(self, logs_dir=None):
    """Check the common things between CLI and API mode.

    Args:
      logs_dir: str, The path to the logs dir to check.  If None, the standard
        one will be used.
    """
    for suffix in ['1', '2']:
      self.AssertOutputNotContains('INFO message' + suffix)
      self.AssertOutputNotContains('WARNING message' + suffix)
      self.AssertOutputNotContains('ERROR message' + suffix)

      self.AssertErrNotContains('INFO: INFO message' + suffix)
      self.AssertErrContains('WARNING: WARNING message' + suffix)
      self.AssertErrContains('ERROR: ERROR message' + suffix)

      contents = self.GetLogFileContents()
      self.assertIn('INFO message' + suffix, contents)
      self.assertIn('WARNING message' + suffix, contents)
      self.assertIn('ERROR message' + suffix, contents)


if __name__ == '__main__':
  test_case.main()
