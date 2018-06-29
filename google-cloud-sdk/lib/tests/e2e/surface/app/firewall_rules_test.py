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
"""End-to-end tests for firewall-rules."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class FirewallRulesTests(sdk_test_base.BundledBase, e2e_base.WithServiceAuth):
  """Test we can get firewall-rules apps."""

  TIMEOUT = 60  # 1 minute

  def testListDomains(self):
    self.ExecuteScript(
        'gcloud',
        ['--verbosity=debug', 'app', 'firewall-rules', 'list'],
        timeout=FirewallRulesTests.TIMEOUT)

if __name__ == '__main__':
  test_case.main()
