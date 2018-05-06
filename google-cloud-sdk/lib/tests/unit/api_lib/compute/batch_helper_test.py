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
"""Unit tests for the batch_helper module."""

import textwrap

from apitools.base.py import http_wrapper
from googlecloudsdk.api_lib.compute import batch_helper
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
import mock


class MakeRequestsTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.compute_v1 = apis.GetClientInstance('compute', 'v1', no_http=True)
    self.messages = apis.GetMessagesModule('compute', 'v1')
    self.StartPatch('time.sleep')

    self.project = 'test_project'
    self.service = 'test_service'
    self.mock_http = self.StartPatch(
        'googlecloudsdk.core.credentials.http.Http', autospec=True)
    self.mock_http.request = None

    self.message = ('Access Not Configured. Compute Engine API has not been '
                    'used in project {project} before or it is disabled. '
                    'Enable it by visiting '
                    'https://console.developers.google.com/apis/api/'
                    '{service}/overview?project={project} then retry. If you '
                    'enabled this API recently, wait a few minutes for the '
                    'action to propagate to our systems and retry.').format(
                        project=self.project, service=self.service)

  def testBatchHelperMakeRequest(self):
    properties.VALUES.core.should_prompt_to_enable_api.Set(True)

    service_enablement = {'enabled': False}
    enable_mock = self.StartPatch(
        'googlecloudsdk.api_lib.services.enable_api.'
        'EnableServiceIfDisabled')
    def Enable(enable_project, enable_service):
      self.assertEqual(enable_project, self.project)
      self.assertEqual(enable_service, self.service)
      service_enablement['enabled'] = True
    enable_mock.side_effect = Enable

    with mock.patch.object(http_wrapper, 'MakeRequest',
                           autospec=True) as mock_request:
      # pylint: disable=unused-argument
      def Perform(http, request):
        # We ignore the inputs and just return what we expect
        if service_enablement['enabled']:
          return http_wrapper.Response({
              'status': '200',
              'content-type': 'multipart/mixed; boundary="boundary"',
          }, textwrap.dedent("""\
          --boundary
          content-type: application/json; charset=UTF-8
          content-id: <id+0>

          HTTP/1.1 200 OK
          {}
          --boundary--"""), None)
        else:
          return http_wrapper.Response({
              'status': '200',
              'content-type': 'multipart/mixed; boundary="boundary"',
          }, textwrap.dedent("""\
          --boundary
          content-type: application/json; charset=UTF-8
          content-id: <id+0>

          HTTP/1.1 403 Forbidden
          {{
           "error": {{
            "errors": [
             {{
              "domain": "usageLimits",
              "reason": "accessNotConfigured",
              "message": "{message}",
              "extendedHelp": ""
             }}
            ],
            "code": 403,
            "message": "{message}"
           }}
          }}
          --boundary--""".format(message=self.message)), None)

      mock_request.side_effect = Perform

      self.WriteInput('y')
      batch_helper.MakeRequests(
          requests=[(self.compute_v1.instances,
                     'Get',
                     self.messages.ComputeInstancesGetRequest(
                         instance='my-instance-1',
                         project='my-project',
                         zone='my-zone'))],
          http=self.mock_http,
          batch_url='https://www.googleapis.com/batch/compute')

      # This ensures that it was called twice (once for failure, once for
      # success)
      self.assertTrue(service_enablement['enabled'])
      self.assertEqual(2, mock_request.call_count)

    enable_mock.assert_called_once_with(self.project, self.service)

  def NoEnableApiBaseTest(self):
    with mock.patch.object(http_wrapper, 'MakeRequest',
                           autospec=True) as mock_request:
      # pylint: disable=unused-argument
      def Perform(http, request):
        return http_wrapper.Response({
            'status': '200',
            'content-type': 'multipart/mixed; boundary="boundary"',
        }, textwrap.dedent("""\
        --boundary
        content-type: application/json; charset=UTF-8
        content-id: <id+0>

        HTTP/1.1 403 Forbidden
        {{
         "error": {{
          "errors": [
           {{
            "domain": "usageLimits",
            "reason": "accessNotConfigured",
            "message": "{message}",
            "extendedHelp": ""
           }}
          ],
          "code": 403,
          "message": "{message}"
         }}
        }}
        --boundary--""".format(message=self.message)), None)

      mock_request.side_effect = Perform

      _, errors = batch_helper.MakeRequests(
          requests=[(self.compute_v1.instances,
                     'Get',
                     self.messages.ComputeInstancesGetRequest(
                         instance='my-instance-1',
                         project='my-project',
                         zone='my-zone'))],
          http=self.mock_http,
          batch_url='https://www.googleapis.com/batch/compute')

      error_code, error_msg = errors[0]
      # Errors are thrown in a layer above this one. It is sufficient to check
      # that the error matches what we expect and MakeRequest is only called
      # once (which means no retries).
      self.assertEqual(error_code, 403)
      self.assertEqual(error_msg, self.message)
      self.assertEqual(mock_request.call_count, 1)

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
