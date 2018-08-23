# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Base class for list_verified domains tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class DomainsListCommandTest(sdk_test_base.WithFakeAuth,
                             cli_test_base.CliTestBase):
  """Tests using the AuthorizedDomains service."""

  APPENGINE_API = 'appengine'
  APPENGINE_API_VERSION = 'v1'
  exp_messages = core_apis.GetMessagesModule(APPENGINE_API,
                                             APPENGINE_API_VERSION)

  def _FormatApp(self):
    return 'apps/{0}'.format(self.Project())

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.messages = core_apis.GetMessagesModule(self.APPENGINE_API,
                                                self.APPENGINE_API_VERSION)
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass(self.APPENGINE_API,
                                 self.APPENGINE_API_VERSION),
        real_client=core_apis.GetClientInstance(
            self.APPENGINE_API, self.APPENGINE_API_VERSION, no_http=True))
    self.mock_client.Mock()
    # If any API calls were made but weren't expected, this will throw an error
    self.addCleanup(self.mock_client.Unmock)

  def ExpectListVerifiedDomains(self, domains):
    """Adds expected list-user-verified request and response.

    Args:
      domains: messages.AuthorizedDomain[], list of domains to expect.
    """
    request = self.messages.AppengineAppsAuthorizedDomainsListRequest(
        parent=self._FormatApp())
    response = self.messages.ListAuthorizedDomainsResponse(domains=domains)
    self.mock_client.AppsAuthorizedDomainsService.List.Expect(
        request, response=response)

  def testListDomainMappings(self):
    domains = [
        self.messages.AuthorizedDomain(id='example.com'),
        self.messages.AuthorizedDomain(id='example2.com')
    ]

    self.ExpectListVerifiedDomains(domains)
    self.Run('domains list-user-verified')
    self.AssertOutputEquals(
        """\
          ID
          example.com
          example2.com
        """,
        normalize_space=True)
