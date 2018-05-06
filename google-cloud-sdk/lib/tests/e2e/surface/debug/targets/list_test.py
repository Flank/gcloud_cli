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

"""Integration test for the 'debug targets list' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.debug import base


class ListTest(base.DebugIntegrationTest):

  def testTargetList(self):
    self.RunDebug(['targets', 'list'])
    self.AssertOutputContains('NAME ID', normalize_space=True)
    self.AssertOutputContains(self.debuggee.target_id)

if __name__ == '__main__':
  test_case.main()
