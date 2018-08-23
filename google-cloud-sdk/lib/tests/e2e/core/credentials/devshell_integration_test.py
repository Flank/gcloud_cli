# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Integration tests for devshell credentials."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import devshell
from googlecloudsdk.core.credentials import store as c_store
from tests.lib import e2e_base
from tests.lib import test_case
from tests.lib.core.credentials import devshell_test_base


@test_case.Filters.RunOnlyOnLinux
class ProxiedAuthIntegration(e2e_base.WithServiceAuth):

  def SetUp(self):
    # get some real credentials so we can feed tests something that works.
    real_creds = c_store.Load()
    c_store.Refresh(real_creds)
    self.devshell_proxy = devshell_test_base.AuthReferenceServer(
        self.GetPort(),
        response=devshell.CredentialInfoResponse(
            user_email='joe@example.com',
            project_id='fooproj',
            access_token=real_creds.access_token))
    self.devshell_proxy.Start()
    self._devshell_provider = c_store.DevShellCredentialProvider()
    self._devshell_provider.Register()
    properties.VALUES.core.account.Set('joe@example.com')

  def TearDown(self):
    self.devshell_proxy.Stop()
    self._devshell_provider.UnRegister()

  def testSimpleIntegration(self):
    creds = c_store.Load()
    self.assertEqual(type(creds), devshell.DevshellCredentials)
    self.Run('sql flags list')


if __name__ == '__main__':
  test_case.main()
