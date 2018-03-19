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
"""Integration test for 'category-manager taxonomies get-iam-policy' command."""

from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class GetIamPolicyIntegrationTest(e2e_base.WithServiceAuth):
  """Integration test for get-iam-policy command, with service acct."""

  # TODO(b/73498472): Remove skip e2e test decorator once production backend
  # is ready for v1alpha2 release.
  @test_case.Filters.skip('Failing', 'b/73498472')
  def testGetIamPolicy(self):
    """Test get iam policy."""
    self.Run('alpha category-manager stores get-iam-policy')
    # Check the content of output.
    self.AssertOutputContains('etag:')


if __name__ == '__main__':
  sdk_test_base.main()
