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

"""Base for all Dataproc tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
import logging
import os
import sys

from googlecloudsdk.calliope import base
from tests.lib import cli_test_base


def _CreateLogger(name, log_level=None):
  """Create logger that does not interact with test_base.WithOutputCapture."""
  log = logging.getLogger(name)
  # sys.stderr is mocked by test_base.WithOutputCapture
  test_log_handler = logging.StreamHandler(sys.__stderr__)
  formatter = logging.Formatter(
      '%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
  test_log_handler.setFormatter(formatter)
  log.addHandler(test_log_handler)
  # Prevent log from propagating into test case output.
  log.propagate = False
  if log_level:
    log.setLevel(log_level.upper())
  return log


class DataprocTestBase(cli_test_base.CliTestBase):
  """Base class for all Dataproc tests."""

  @classmethod
  def SetUpClass(cls):
    log_level = os.getenv('CLOUDSDK_TEST_LOG_LEVEL', 'INFO')
    cls.log = _CreateLogger('dataproc-test', log_level)

  def SetUp(self):
    # Show captured output and error on debug and finer.
    if self.log.getEffectiveLevel() <= logging.DEBUG:
      self._show_test_output = True

  def RunDataproc(self, command, output_format='disable'):
    """Wrapper around test_base.Run to abstract out common args."""
    cmd = '--format={format} dataproc {command}'.format(
        format=output_format, command=command)
    return self.Run(cmd)


class DataprocTestBaseBeta(DataprocTestBase):
  """Base class for all Dataproc beta tests."""

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
