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

"""Tests for tests.unit.api_lib.util.enablement."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import http_wrapper
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import http
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
import mock


class EnablementTest(cli_test_base.CliTestBase, parameterized.TestCase):

  def SetUp(self):
    self.project = 'test_project'
    self.service = 'test_service'

    self.message = ('Access Not Configured. Compute Engine API has not been '
                    'used in project {project} before or it is disabled. '
                    'Enable it by visiting '
                    'https://console.developers.google.com/apis/api/'
                    '{service}/overview?project={project} then retry. If you '
                    'enabled this API recently, wait a few minutes for the '
                    'action to propagate to our systems and retry.').format(
                        project=self.project, service=self.service)

  @parameterized.parameters(('google.com:cloudsdktool', False),
                            ('test-project', True))
  def testShouldEnable(self, project, answer):
    self.assertEqual(apis.ShouldAttemptProjectEnable(project), answer)

  def testSingleRequestEnablement(self):
    properties.VALUES.core.should_prompt_to_enable_api.Set(True)

    service_enablement = {'enabled': False}
    service_enabled_mock = self.StartPatch(
        'googlecloudsdk.api_lib.services.enable_api.'
        'IsServiceEnabled')
    def IsServiceEnabled(enable_project, enable_service):
      self.assertEqual(enable_project, self.project)
      self.assertEqual(enable_service, self.service)
      return service_enablement['enabled']
    service_enabled_mock.side_effect = IsServiceEnabled
    enable_mock = self.StartPatch(
        'googlecloudsdk.api_lib.services.enable_api.'
        'EnableService')
    def Enable(enable_project, enable_service):
      self.assertEqual(enable_project, self.project)
      self.assertEqual(enable_service, self.service)
      service_enablement['enabled'] = True
    enable_mock.side_effect = Enable

    # pylint: disable=unused-argument
    def Perform(arg, method, body, headers, redirections, connection_type):
      # We ignore the inputs and just return what we expect
      # Since we are mocking at the core.http level, the contents here are
      # text instead of bytes as core.http.Http handles this decoding usually.
      if service_enablement['enabled']:
        return ({'status': '200'}, '{"field": "abc"}')
      else:
        return ({'status': '403'}, textwrap.dedent("""\
          {{
           "error": {{
            "code": 403,
            "message": "{message}",
            "status": "PERMISSION_DENIED"
           }}
          }}""").format(message=self.message))

    mock_http_methods = mock.Mock()
    mock_http_methods.redirect_codes = []
    self.StartObjectPatch(http, 'Http', autospec=True,
                          return_value=mock_http_methods)
    mock_http_methods.request.side_effect = Perform
    mock_http_methods.connections = None

    client = apis.GetClientInstance('dataproc', 'v1')
    messages = client.MESSAGES_MODULE

    self.WriteInput('y')
    client.projects_regions_jobs.Get(
        messages.DataprocProjectsRegionsJobsGetRequest(
            projectId=self.project,
            region='global',
            jobId='testjobid'))
    # This ensures that it was called twice (once for failure, once for
    # success)
    self.assertTrue(service_enablement['enabled'])
    self.assertEqual(mock_http_methods.request.call_count, 2)

    enable_mock.assert_called_once_with(self.project, self.service)

  def testRequestEnablementPromptsOnlyOnce(self):
    properties.VALUES.core.should_prompt_to_enable_api.Set(True)

    prompt_to_enable_mock = self.StartPatch(
        'googlecloudsdk.api_lib.util.apis.'
        'PromptToEnableApi')

    service_enabled_response = http_wrapper.Response({'status': '200'},
                                                     '{"field": "abc"}', '')
    service_disabled_response = http_wrapper.Response({'status': '403'},
                                                      textwrap.dedent("""\
      {{
       "error": {{
        "code": 403,
        "message": "{message}",
        "status": "PERMISSION_DENIED"
       }}
      }}""").format(message=self.message), '')

    callback = apis.CheckResponseForApiEnablement()
    callback(service_disabled_response)
    # Catch two retries while we wait for enablement propagation
    with self.AssertRaisesExceptionMatches(apitools_exceptions.RequestError,
                                           'Retry'):
      callback(service_disabled_response)
      callback(service_disabled_response)
    callback(service_enabled_response)
    prompt_to_enable_mock.assert_called_once_with(self.project, self.service,
                                                  mock.ANY)

  def NoEnableApiBaseTest(self):
    # pylint: disable=unused-argument
    def Perform(arg, method, body, headers, redirections, connection_type):
      # We ignore the inputs and just return what we expect
      return ({'status': '403'}, textwrap.dedent("""\
        {{
         "error": {{
          "code": 403,
          "message": "{message}",
          "status": "PERMISSION_DENIED"
         }}
        }}""").format(message=self.message))

    mock_http_methods = mock.Mock()
    mock_http_methods.redirect_codes = []
    self.StartObjectPatch(http, 'Http', autospec=True,
                          return_value=mock_http_methods)
    mock_http_methods.request.side_effect = Perform
    mock_http_methods.connections = None

    client = apis.GetClientInstance('dataproc', 'v1')
    messages = client.MESSAGES_MODULE

    with self.AssertRaisesExceptionMatches(apitools_exceptions.HttpError,
                                           self.message):
      client.projects_regions_jobs.Get(
          messages.DataprocProjectsRegionsJobsGetRequest(
              projectId=self.project,
              region='global',
              jobId='testjobid'))
    self.assertEqual(mock_http_methods.request.call_count, 1)

  def testBatchHelperMakeRequest_DisableApiPrompts(self):
    properties.VALUES.core.should_prompt_to_enable_api.Set(False)
    self.NoEnableApiBaseTest()

  def testBatchHelperMakeRequest_DisablePrompts(self):
    properties.VALUES.core.disable_prompts.Set(False)
    self.NoEnableApiBaseTest()

  def testBatchHelperMakeRequest_Cancel(self):
    self.WriteInput('n')
    self.NoEnableApiBaseTest()


if __name__ == '__main__':
  test_case.main()
