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
#
"""Tests for the grpc_util module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import gapic_util
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

AUTH_HEADERS = {'authorization': 'Bearer fake-access-token'}
PROJECT_HEADER = {'x-goog-user-project': 'fake-project'}
AUTH_HEADERS_WITH_PROJECT = AUTH_HEADERS.copy()
AUTH_HEADERS_WITH_PROJECT.update(PROJECT_HEADER)


class GapicUtilTest(sdk_test_base.WithFakeAuth, parameterized.TestCase):

  def Project(self):
    return 'fake-project'

  def FakeAuthAccessToken(self):
    return 'fake-access-token'

  def SetUp(self):
    super(GapicUtilTest, self).SetUp()
    properties.VALUES.core.project.Set(self.Project())

  # these are the meaningfully distinct cases with respect the code under test
  @parameterized.parameters((True, True, AUTH_HEADERS_WITH_PROJECT),
                            (True, False, AUTH_HEADERS_WITH_PROJECT),
                            (False, True, AUTH_HEADERS),
                            (False, False, AUTH_HEADERS))
  def testGetStoredCredentials(self, enable_resource_quota, use_google_auth,
                               expected_headers):
    credentials = gapic_util.StoredCredentials(
        enable_resource_quota=enable_resource_quota,
        force_resource_quota=False,
        allow_account_impersonation=True,
        use_google_auth=use_google_auth)
    headers = {}
    credentials.apply(headers)
    self.assertEqual(expected_headers, headers)


if __name__ == '__main__':
  test_case.main()
