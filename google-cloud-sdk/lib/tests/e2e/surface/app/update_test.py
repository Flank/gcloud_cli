# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Tests for Feature settings."""

from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class UpdateTests(sdk_test_base.BundledBase, e2e_base.WithServiceAuth):
  """Test we can update feature settings for apps."""

  @test_case.Filters.skip('Failing', 'b/72860381')
  def testAppUpdate(self):
    # Run these commands in sequence otherwise there may be operation conflict
    # errors.
    # Enable split-health-checks.
    self.ExecuteScript(
        'gcloud',
        ['--verbosity=debug', 'app', 'update', '--split-health-checks'])
    # Disable split-health-checks.
    self.ExecuteScript(
        'gcloud',
        ['--verbosity=debug', 'app', 'update', '--no-split-health-checks'])
    # Disable container-optimized-os.
    self.ExecuteScript(
        'gcloud',
        ['alpha', '--verbosity=debug', 'app', 'update',
         '--no-use-container-optimized-os'])
    # Update multiple features.
    self.ExecuteScript(
        'gcloud',
        ['beta', '--verbosity=debug', 'app', 'update',
         '--split-health-checks', '--no-use-container-optimized-os'])


if __name__ == '__main__':
  test_case.main()
