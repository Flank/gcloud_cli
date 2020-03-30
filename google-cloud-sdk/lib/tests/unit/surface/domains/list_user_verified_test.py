# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

from apitools.base.py import exceptions as api_exceptions
from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base


class DomainsListCommandTest(sdk_test_base.WithFakeAuth,
                             cli_test_base.CliTestBase,
                             parameterized.TestCase):
  """Tests using the AuthorizedDomains service."""

  APPENGINE_API = 'appengine'
  APPENGINE_API_VERSION = 'v1'

  RUN_API = 'run'
  RUN_API_VERSION = 'v1'

  exp_messages = core_apis.GetMessagesModule(APPENGINE_API,
                                             APPENGINE_API_VERSION)

  def _FormatApp(self):
    return 'apps/{0}'.format(self.Project())

  def _FormatRunProject(self, location):
    return 'projects/{0}/locations/{1}'.format(self.Project(), location)

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.gae_messages = core_apis.GetMessagesModule(self.APPENGINE_API,
                                                    self.APPENGINE_API_VERSION)
    self.gae_mock_client = apitools_mock.Client(
        core_apis.GetClientClass(self.APPENGINE_API,
                                 self.APPENGINE_API_VERSION),
        real_client=core_apis.GetClientInstance(
            self.APPENGINE_API, self.APPENGINE_API_VERSION, no_http=True))
    self.gae_mock_client.Mock()
    # If any API calls were made but weren't expected, this will throw an error
    self.addCleanup(self.gae_mock_client.Unmock)
    self.run_messages = core_apis.GetMessagesModule(self.RUN_API,
                                                    self.RUN_API_VERSION)
    self.run_mock_client = apitools_mock.Client(
        core_apis.GetClientClass(self.RUN_API,
                                 self.RUN_API_VERSION),
        real_client=core_apis.GetClientInstance(
            self.RUN_API, self.RUN_API_VERSION, no_http=True))
    self.run_mock_client.Mock()
    # If any API calls were made but weren't expected, this will throw an error
    self.addCleanup(self.run_mock_client.Unmock)

  def ExpectListVerifiedDomains(self, domains):
    """Adds expected list-user-verified request and response.

    Args:
      domains: messages.AuthorizedDomain[], list of domains to expect.
    """
    request = self.gae_messages.AppengineAppsAuthorizedDomainsListRequest(
        parent=self._FormatApp())
    response = self.gae_messages.ListAuthorizedDomainsResponse(domains=domains)
    self.gae_mock_client.AppsAuthorizedDomainsService.List.Expect(
        request, response=response)

  def ExpectListVerifiedDomainsRun(self, domains, gae_exception):
    """Adds expected list-user-verified request and response.

    Args:
      domains: messages.AuthorizedDomain[], list of domains to expect.
      gae_exception: exception for the GAE api to raise to get to use Cloud Run.
    """
    gae_request = self.gae_messages.AppengineAppsAuthorizedDomainsListRequest(
        parent=self._FormatApp())
    self.gae_mock_client.AppsAuthorizedDomainsService.List.Expect(
        gae_request, exception=gae_exception)
    run_request = (self.run_messages.
                   RunProjectsLocationsAuthorizeddomainsListRequest(
                       parent=self._FormatRunProject('-')))
    response = self.run_messages.ListAuthorizedDomainsResponse(domains=domains)
    self.run_mock_client.projects_locations_authorizeddomains.List.Expect(
        run_request, response=response)

  def testListDomainMappings(self):
    domains = [
        self.gae_messages.AuthorizedDomain(id='example.com'),
        self.gae_messages.AuthorizedDomain(id='example2.com')
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

  @parameterized.parameters(api_exceptions.HttpNotFoundError(None, None, None),
                            api_exceptions.HttpForbiddenError(None, None, None))
  def testListDomainCloudRun(self, gae_exception):
    domains = [
        self.run_messages.AuthorizedDomain(id='example.com'),
        self.run_messages.AuthorizedDomain(id='example2.com')
    ]
    self.ExpectListVerifiedDomainsRun(domains, gae_exception)
    self.Run('domains list-user-verified')
    self.AssertOutputEquals(
        """\
          ID
          example.com
          example2.com
        """,
        normalize_space=True)

  def testListDomainBoth404(self):

    gae_request = self.gae_messages.AppengineAppsAuthorizedDomainsListRequest(
        parent=self._FormatApp())
    self.gae_mock_client.AppsAuthorizedDomainsService.List.Expect(
        gae_request,
        exception=api_exceptions.HttpNotFoundError(None, None, None))
    run_request = (self.run_messages.
                   RunProjectsLocationsAuthorizeddomainsListRequest(
                       parent=self._FormatRunProject('-')))
    self.run_mock_client.projects_locations_authorizeddomains.List.Expect(
        run_request,
        exception=api_exceptions.HttpNotFoundError(None, None, None))
    with self.assertRaises(calliope_exceptions.HttpException):
      self.Run('domains list-user-verified')
    self.AssertErrContains(
        'you must activate either the App Engine or Cloud Run API',
        normalize_space=True)
