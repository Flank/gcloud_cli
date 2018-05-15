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
"""E2e test for 'category-manager assets search' command."""

from tests.lib import e2e_base
from tests.lib import sdk_test_base


class AssetSearchE2eTest(e2e_base.WithServiceAuth):
  """E2e test for search command, with service acct."""

  def SearchEnd2EndTest(self):
    """Test executing a search query."""
    self.Run('alpha category-manager assets search')

    # Check the content of output.
    self.AssertOutputContains('name:')


if __name__ == '__main__':
  sdk_test_base.main()
