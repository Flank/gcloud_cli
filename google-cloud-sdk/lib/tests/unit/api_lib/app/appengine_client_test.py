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
"""Tests of the AppEngine Client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import appengine_client
from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import test_case

import mock
from oauth2client.contrib import gce as oauth2client_gce
import six


class AppengineClientTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.StartObjectPatch(
        store, 'LoadFreshCredential'
    ).return_value = oauth2client_gce.AppAssertionCredentials()

    self.mock_urlopen = self.StartObjectPatch(six.moves.urllib.request,
                                              'urlopen')
    self.mock_response = mock.MagicMock()
    self.mock_response.read.return_value = b'scope1 scope2'
    self.mock_urlopen.return_value = self.mock_response
    self.appengine_client = appengine_client.AppengineClient()

  def testIsGCEEnvironment_MissingScope(self):
    with self.AssertRaisesExceptionMatches(
        appengine_client.Error,
        'The account has the following scopes: [scope1, scope2]. It needs '
        '[https://www.googleapis.com/auth/cloud-platform] in order to succeed'):
      self.appengine_client._IsGceEnvironment()


if __name__ == '__main__':
  test_case.main()
