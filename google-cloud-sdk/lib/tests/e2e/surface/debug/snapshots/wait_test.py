# -*- coding: utf-8 -*- #
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

"""Integration test for the 'debug snapshots wait' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.debug import base


class WaitTest(base.DebugIntegrationTestWithTargetArg):

  def testSnapshotWaitWithTimeout(self):
    self.RunDebug(['snapshots', 'create', 'wait_dummy_file:123'])
    self.AssertOutputContains('id: ', normalize_space=True)
    self.AssertOutputContains('location: wait_dummy_file:123',
                              normalize_space=True)
    self.ClearOutput()
    self.RunDebug(['snapshots', 'create', 'wait_dummy_file:345'])
    self.AssertOutputContains('id: ', normalize_space=True)
    self.AssertOutputContains('location: wait_dummy_file:345',
                              normalize_space=True)
    self.ClearOutput()
    self.RunDebug(['snapshots', 'wait', '--timeout=1',
                   '--location=wait_dummy.*'])
    self.AssertErrContains('No snapshot', normalize_space=True)

if __name__ == '__main__':
  test_case.main()
