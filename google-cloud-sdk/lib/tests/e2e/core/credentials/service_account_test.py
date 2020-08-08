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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import e2e_base
from tests.lib import test_case


class TestServiceAccount(e2e_base.WithServiceAuth):
  """This class tests service account activated via google-auth.

  Activating service account via google-auth is the default behavior of the
  base class WithServiceAuth. The two test methods cover the cases of
  loading credentials of oauth2client and google-auth respectively.
  """

  # TODO(b/147255499): remove this test after everything is on google-auth.
  def testLoadOauth2client(self):
    self.Run('compute instances list')

  def testLoadGoogleAuth(self):
    # dns surface is on google-auth
    self.Run('dns managed-zones list')


class TestServiceAccountOauth2client(TestServiceAccount):
  """This class tests service account activated via oauth2client.

  Setting disable_activate_service_account_google_auth to True will cause
  the activation being executed against oauth2client. The two test cases of
  loading credentails of oauth2client and google-auth are inherented from
  TestServiceAccount.
  """

  def PreSetUp(self):
    self.disable_activate_service_account_google_auth = True


if __name__ == '__main__':
  test_case.main()
