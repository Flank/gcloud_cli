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
"""Integration test for the 'composer operations list' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import re
from tests.lib import test_case
from tests.lib.surface.composer import base


class ListOperationsIntegrationTest(base.ComposerE2ETestBase):
  """Integration test for the 'composer operations list' command.

  Composer gcloud e2e tests are run against a project with existing operations
  for reasons described in base.ComposerE2ETestBase. Therefore, no new
  operations are started before testing list.
  """

  def testListOperations(self):
    ops = list(
        self.Run(
            'composer operations list --locations=us-central1 --limit=2 '
            '--format=disable'))
    self.assertGreater(len(ops), 0)
    for op in ops:
      # operation name follows correct pattern
      match = re.match(
          'projects/' + self.Project() + '/locations/us-central1/operations/'
          '[0-9a-f][-0-9a-f]*[0-9a-f]', op.name)
      self.assertTrue(bool(match))


if __name__ == '__main__':
  test_case.main()
