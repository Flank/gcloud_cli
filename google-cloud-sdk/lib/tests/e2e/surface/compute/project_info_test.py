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
"""e2e tests for compute project-info command group."""
import contextlib

from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


class ProjectInfoTests(e2e_base.WithServiceAuth):
  """E2E tests for compute project-info command group."""

  TEST_VALUE = 'test_value'

  @contextlib.contextmanager
  def _ProjectInfoMetadata(self, key, value):
    self.Run(
        'compute project-info add-metadata --metadata {}={}'.format(key, value))
    try:
      yield
    finally:
      self.Run('compute project-info remove-metadata --keys {}'.format(key))

  @test_case.Filters.skip('Flaky: race condition on project', 'b/72444489')
  def testAddRemoveMetadata(self):
    metadata_key = next(e2e_utils.GetResourceNameGenerator('metadata'))
    with self._ProjectInfoMetadata(metadata_key, self.TEST_VALUE):
      result = self.Run('compute project-info describe')
    for item in result.commonInstanceMetadata.items:
      if item.key == metadata_key:
        self.assertEqual(item.value, self.TEST_VALUE)
        break
    else:
      self.fail('Metadata key [{}] not found'.format(metadata_key))
