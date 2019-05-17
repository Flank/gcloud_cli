# -*- coding: utf-8 -*- #
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
from __future__ import division
from __future__ import unicode_literals

from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case

# The gcloud App Engine e2e test service account is specifically IRDB
# authorized for this domain. See
# https://g3doc.corp.google.com/apphosting/admin/g3doc/guides/ssl.md for more
# context.
#
# Contact appengine-admin-api@ to have a new user whitelisted in the event these
# tests are run with a new calling credential.
DOMAIN = 'testappeng19.com'


class DomainTests(sdk_test_base.BundledBase, e2e_base.WithServiceAuth):
  """Test we can get domain mappings for apps."""

  def SetUp(self):
    # Clean up any bad state.
    self.DeleteMapping()

  def TearDown(self):
    # Clean up any bad state.
    self.DeleteMapping()

  def DeleteMapping(self):
    self.Run(['--verbosity=debug', 'app', 'domain-mappings', 'delete', DOMAIN])

  def ListMappings(self):
    results = self.Run(['--verbosity=debug', 'app', 'domain-mappings', 'list'])
    return [result.id for result in results]

  @test_case.Filters.skip('Failing', 'b/112431513')
  def testCreateAndDelete(self):
    list_result = self.ListMappings()

    self.assertNotIn(DOMAIN, list_result)

    self.Run(['--verbosity=debug', 'app', 'domain-mappings', 'create', DOMAIN])

    list_result = self.ListMappings()

    self.assertIn(DOMAIN, list_result)

    get_result = self.Run(
        ['--verbosity=debug', 'app', 'domain-mappings', 'describe', DOMAIN])

    self.assertEqual(get_result.id, DOMAIN)

    self.DeleteMapping()

    list_result = self.ListMappings()

    self.assertNotIn(DOMAIN, list_result)


class SslTests(sdk_test_base.BundledBase, e2e_base.WithServiceAuth):
  """Test we can get ssl certificates for apps."""

  TIMEOUT = 60  # 1 minute

  def SetUp(self):
    pass

  def TearDown(self):
    pass

  def testListCertificates(self):
    self.Run(['--verbosity=debug', 'app', 'ssl-certificates', 'list'])


if __name__ == '__main__':
  test_case.main()
