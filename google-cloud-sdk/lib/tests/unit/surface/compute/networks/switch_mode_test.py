# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for the networks switch-mode subcommand."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class NetworksSwitchModeTest(test_base.BaseTest,
                             completer_test_base.CompleterBase):
  api_version = 'alpha'
  messages = apis.GetMessagesModule('compute', 'alpha')

  def SetUp(self):
    self.SelectApi(self.api_version)

  def testSwitchToCustomMode(self):
    with self.assertRaisesRegex(
        calliope_base.DeprecationException,
        '`switch-mode` has been removed. '
        'Please use `--switch-to-custom-subnet-mode` with `gcloud compute '
        'networks update` instead.'):
      self._RunSwitchModeCommand(mode='custom', interactive=False)

  def _RunSwitchModeCommand(self, mode='custom', interactive=True):
    command = '%s compute networks switch-mode network-1 --mode=%s %s' % (
        self.api_version if self.api_version else '',
        mode,
        '' if interactive else '--quiet')
    self.Run(command.strip())

if __name__ == '__main__':
  test_case.main()
