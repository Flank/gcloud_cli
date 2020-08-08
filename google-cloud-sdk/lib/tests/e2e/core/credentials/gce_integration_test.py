# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Integration tests for gce properties."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import gce
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case
import oauth2client
import google.auth.compute_engine as google_auth_gce


class GCEIntegrationTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self._gce_provider = store.GceCredentialProvider()
    self._gce_provider.Register()

  def TearDown(self):
    self._gce_provider.UnRegister()

  @sdk_test_base.Filters.RunOnlyOnGCE
  def testRemoteServiceAccountExistsOnGCE(self):
    properties.VALUES.core.check_gce_metadata.Set(True)
    self.ClearOutput()
    self.Run(['config', 'list', 'account'])
    self.AssertOutputNotContains('unset')

  @sdk_test_base.Filters.RunOnlyOnGCE
  def testMetadataServer(self):
    metadata = gce._GCEMetadata()
    self.assertNotEqual(metadata.DefaultAccount() or None, None)
    self.assertNotEqual(metadata.Project() or None, None)
    self.assertNotEqual(metadata.Accounts() or None, None)

    self.assertNotEqual(re.match(r'\w*?-\w*?-\w', metadata.Zone()), None)
    self.assertNotEqual(re.match(r'\w*?-\w*?', metadata.Region()), None)

  @sdk_test_base.Filters.RunOnlyOnGCE
  def testGCECredentials(self):
    cred = store.AcquireFromGCE()
    self.assertIsInstance(
        cred, oauth2client.contrib.gce.AppAssertionCredentials)
    self.assertIsNotNone(cred.access_token)
    self.assertFalse(cred.access_token_expired)

    cred = store.AcquireFromGCE(use_google_auth=True)
    self.assertIsInstance(cred, google_auth_gce.Credentials)
    self.assertIsNotNone(cred.token)
    self.assertFalse(cred.expired)

  @sdk_test_base.Filters.RunOnlyOnGCE
  def testGCEIdTokenMinting(self):
    cred = store.AcquireFromGCE()
    self.assertIsInstance(
        cred, oauth2client.contrib.gce.AppAssertionCredentials)
    self.assertIsNotNone(cred.access_token)
    self.assertFalse(cred.access_token_expired)
    self.assertIsNotNone(cred.id_tokenb64)

    cred = store.AcquireFromGCE(use_google_auth=True)
    self.assertIsInstance(cred, google_auth_gce.Credentials)
    self.assertIsNotNone(cred.token)
    self.assertFalse(cred.expired)
    self.assertIsNotNone(cred._id_token)
    self.assertIsNotNone(cred.id_tokenb64)


class GCEIntegrationTestGCPServices(cli_test_base.CliTestBase):

  @sdk_test_base.Filters.RunOnlyOnGCE
  def testGoogleAuth(self):
    with e2e_base.GceServiceAccount() as auth:
      # dns surface is on google-auth
      self.Run('dns managed-zones list --project {} --account={}'.format(
          auth.Project(), auth.Account()))

  # TODO(b/147255499): remove this test after everything is on google-auth.
  @sdk_test_base.Filters.RunOnlyOnGCE
  def testOauth2client(self):
    with e2e_base.GceServiceAccount() as auth:
      self.Run('compute instances list --project {} --account={}'.format(
          auth.Project(), auth.Account()))


if __name__ == '__main__':
  test_case.main()
