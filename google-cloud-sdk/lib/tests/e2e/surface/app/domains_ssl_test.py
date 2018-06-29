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
"""Tests for dev_app_server for java and python."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class DomainTests(sdk_test_base.BundledBase, e2e_base.WithServiceAuth):
  """Test we can get domain mappings for apps."""

  TIMEOUT = 60  # 1 minute

  def SetUp(self):
    pass

  def TearDown(self):
    pass

  def testListDomains(self):
    self.ExecuteScript(
        'gcloud',
        ['--verbosity=debug', 'app', 'domain-mappings', 'list'],
        timeout=DomainTests.TIMEOUT)


class SslTests(sdk_test_base.BundledBase, e2e_base.WithServiceAuth):
  """Test we can get ssl certificates for apps."""

  TIMEOUT = 60  # 1 minute

  def SetUp(self):
    pass

  def TearDown(self):
    pass

  def testListCertificates(self):
    self.ExecuteScript(
        'gcloud',
        ['--verbosity=debug', 'app', 'ssl-certificates', 'list'],
        timeout=SslTests.TIMEOUT)


if __name__ == '__main__':
  test_case.main()
