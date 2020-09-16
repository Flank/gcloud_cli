# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Integration tests to roll out the google auth."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store as c_store
from tests.lib import e2e_base
from tests.lib import test_case


# TODO(b/147255499): remove this test after google-auth rollout is done.
class TestUseGoogleAuth(e2e_base.WithServiceAuth):
  """Tests to make sure surfaces are on google-auth."""

  def MockLoadIfEnabledBuilder(self, expected_use_google_auth):
    orig_load_if_enabled = c_store.LoadIfEnabled

    def MockLoadIfEnabled(allow_account_impersonation=True,
                          use_google_auth=False):
      self.assertIs(use_google_auth, expected_use_google_auth)
      return orig_load_if_enabled(
          allow_account_impersonation=allow_account_impersonation,
          use_google_auth=use_google_auth)

    return MockLoadIfEnabled

  def SetUp(self):
    properties.VALUES.auth.opt_out_google_auth.Set(False)
    self.StartObjectPatch(
        c_store,
        'LoadIfEnabled').side_effect = self.MockLoadIfEnabledBuilder(True)

  def testDns(self):
    self.Run('dns managed-zones list')

  def testKms(self):
    self.Run('kms locations list')

  def testPubsub(self):
    self.Run('pubsub topics list')

  def testDataflow(self):
    self.Run('dataflow jobs list')

  def testCompute(self):
    self.Run('compute instances list')

  def testFunctions(self):
    self.Run('functions list')

  def testIam(self):
    self.Run('iam service-accounts list')

  def testRedis(self):
    self.Run('redis instances list --region=us-central1')

  def testContainer(self):
    self.Run('container clusters list')

  def testServices(self):
    self.Run('services list')


if __name__ == '__main__':
  test_case.main()
