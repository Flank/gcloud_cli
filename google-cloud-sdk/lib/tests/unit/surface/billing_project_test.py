# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Test the global --billing-project flag."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import google_auth_credentials
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.core.credentials import credentials_test_base

import httplib2


def _SetUp(self):
  properties.VALUES.core.account.Set('fakeuser')
  fake_creds = self.MakeUserAccountCredentialsGoogleAuth()
  fake_creds.token = 'access-token'
  store.Store(fake_creds)

  self.refresh_mock = self.StartObjectPatch(
      google_auth_credentials.UserCredWithReauth, 'refresh')
  self.request_mock = self.StartObjectPatch(
      httplib2.Http, 'request', autospec=True)
  self.request_mock.return_value = (httplib2.Response({'status': 200}),
                                    b'{"projects": []}')


# Use asset surface as an example, asset API supports project override
class BillingProjectAPISupportsProjectOverride(
    cli_test_base.CliTestBase, credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    _SetUp(self)

  def testDifferentProjectForBilling_UnsetProperty(self):

    self.Run('asset export --project fake-project '
             '--output-path=gs://my-bucket/my-object '
             '--billing-project billing_project_in_flag')
    project_override_header = self.request_mock.call_args[1]['headers'][
        b'X-Goog-User-Project']
    self.assertEqual(project_override_header, b'billing_project_in_flag')

  def testDifferentProjectForBilling_SetProperty(self):

    properties.PersistProperty(properties.VALUES.billing.quota_project,
                               'billing_project_in_property',
                               properties.Scope.USER)
    try:
      self.Run('asset export --project fake-project '
               '--output-path=gs://my-bucket/my-object '
               '--billing-project billing_project_in_flag')
    finally:
      properties.PersistProperty(properties.VALUES.billing.quota_project, None,
                                 properties.Scope.USER)

    project_override_header = self.request_mock.call_args[1]['headers'][
        b'X-Goog-User-Project']
    self.assertEqual(project_override_header, b'billing_project_in_flag')


# Use iot surface as an example, iot API does not support project override
class BillingProjectAPIDoesNotSupportsProjectOverride(
    cli_test_base.CliTestBase, credentials_test_base.CredentialsTestBase):

  def SetUp(self):
    _SetUp(self)

  def testDifferentProjectForBilling_UnsetProperty(self):

    self.Run('iot registries list --region=us-central1 --project fake-project '
             '--billing-project billing_project_in_flag')
    project_override_header = self.request_mock.call_args[1]['headers'][
        b'X-Goog-User-Project']
    self.assertEqual(project_override_header, b'billing_project_in_flag')

  def testDifferentProjectForBilling_SetProperty(self):

    properties.PersistProperty(properties.VALUES.billing.quota_project,
                               'billing_project_in_property',
                               properties.Scope.USER)
    try:
      self.Run('iot registries list --region=us-central1 --project fake-project'
               ' --billing-project billing_project_in_flag')
    finally:
      properties.PersistProperty(properties.VALUES.billing.quota_project, None,
                                 properties.Scope.USER)

    project_override_header = self.request_mock.call_args[1]['headers'][
        b'X-Goog-User-Project']
    self.assertEqual(project_override_header, b'billing_project_in_flag')


if __name__ == '__main__':
  test_case.main()
