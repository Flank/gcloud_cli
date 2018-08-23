# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Unit tests for api_lib.cloudbuild.build."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
import time

from apitools.base.py import encoding
from apitools.base.py import extra_types
from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.cloudbuild import build
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import build_base
from tests.lib.apitools import http_error
from six.moves import range  # pylint: disable=redefined-builtin


class CloudBuildClientTest(e2e_base.WithMockHttp, sdk_test_base.WithLogCapture,
                           build_base.BuildBase):

  _PROJECT_NAME = 'operations/build/my-project/1234567890'
  _TYPE_STRING = 'type.googleapis.com/google.devtools.cloudbuild.v1.Build'
  _LOG_URL = ('https://www.googleapis.com/'
              'storage/v1/b/logs-bucket/o/log-build-id.txt')

  def SetUp(self):
    self.mock_client = api_mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = core_apis.GetMessagesModule('cloudbuild', 'v1')
    # Intercept logging output.
    self.mock_log_content = ''
    mock_log_print = self.StartPatch(
        'googlecloudsdk.api_lib.cloudbuild.logs.LogTailer._PrintLogLine')
    mock_log_print.side_effect = self._MockPrintLogLine
    self.StartPatch('googlecloudsdk.core.console.console_attr_os.GetTermSize',
                    return_value=(40, 100))
    self.client = build.CloudBuildClient(self.mock_client, self.messages)
    self.build = self.messages.Build(images=['gcr.io/my-project/output-tag'])
    self.StartObjectPatch(time, 'sleep')

  def _MockPrintLogLine(self, text):
    self.mock_log_content += text + '\n'

  def _ExpectCreateBuild(self,
                         logs_bucket=None,
                         exception=None,
                         retries=0,
                         response_error=None,
                         success=True,
                         stream_log=True):
    # Common data (for both initial create call and polling
    type_msg = self.messages.Operation.ResponseValue.AdditionalProperty(
        key='@type',
        value=extra_types.JsonValue(
            string_value=self._TYPE_STRING
        ),
    )
    build_properties = [
        extra_types.JsonObject.Property(
            key='id',
            value=extra_types.JsonValue(string_value='build-id'),
        )
    ]
    if logs_bucket:
      build_properties.append(
          extra_types.JsonObject.Property(
              key='logsBucket',
              value=extra_types.JsonValue(string_value=logs_bucket)))
    build_meta = self.messages.Operation.MetadataValue.AdditionalProperty(
        key='build',
        value=extra_types.JsonValue(
            object_value=extra_types.JsonObject(properties=build_properties,),),
    )
    type_meta = self.messages.Operation.MetadataValue.AdditionalProperty(
        key='@type',
        value=extra_types.JsonValue(
            string_value=self._TYPE_STRING
        ),
    )

    # Data for just the initial create call
    if exception:
      response = None
    else:
      response = self.messages.Operation(
          name=self._PROJECT_NAME,
          metadata=self.messages.Operation.MetadataValue(
              additionalProperties=[
                  type_meta,
                  build_meta,
              ],
          ),
          response=self.messages.Operation.ResponseValue(
              additionalProperties=[
                  type_msg,
              ],
          ),
      )
    self.mock_client.projects_builds.Create.Expect(
        self.messages.CloudbuildProjectsBuildsCreateRequest(
            projectId='my-project',
            build=self.messages.Build(
                images=['gcr.io/my-project/output-tag'],
                logsBucket=logs_bucket
            ),
        ),
        response=response,
        exception=exception
    )

    if not exception:
      # Data for just polling
      success_msg = self.messages.Operation.ResponseValue.AdditionalProperty(
          key='status',
          value=extra_types.JsonValue(
              string_value='SUCCESS'
          ),
      )
      # Intermediate responses.
      for _ in range(retries):
        self.mock_client.operations.Get.Expect(
            self.messages.Operation(
                name=self._PROJECT_NAME,
            ),
            self.messages.Operation(
                name=self._PROJECT_NAME,
                done=False))
      # Final response.
      final_response = self.messages.Operation(
          name=self._PROJECT_NAME,
          metadata=self.messages.Operation.MetadataValue(
              additionalProperties=[
                  type_meta,
                  build_meta
              ],
          )
      )
      # Update the final response depending on the desired results.
      # If success is False and response_error is None, then the final response
      # will be an unfinished operation.
      if success:
        if response_error:
          raise ValueError(
              'A test is attempting to create a mock Operation response with '
              'both a successful response and an error.')
        final_response.response = self.messages.Operation.ResponseValue(
            additionalProperties=[
                type_msg,
                success_msg,
            ],
        )
        final_response.done = True
      elif response_error:
        final_response.error = response_error
        final_response.done = True

      if stream_log:
        self.mock_client.operations.Get.Expect(
            self.messages.Operation(name=self._PROJECT_NAME,), final_response)

  def _ExpectLogRequest(self, b=0):
    self.AddHTTPResponse(
        self._LOG_URL,
        expected_params={'alt': 'media'},
        request_headers={'Range': 'bytes={}-'.format(b)},
        body='Some log text\n',
        headers={'status': 206})

  def testBuild(self):
    self._ExpectCreateBuild(logs_bucket='logs-bucket')
    self._ExpectLogRequest()
    self.build.logsBucket = 'logs-bucket'

    self.client.ExecuteCloudBuild(self.build, project='my-project')

    expected = ('--------- REMOTE BUILD OUTPUT ----------\n'
                'Some log text\n'
                '----------------------------------------\n\n')
    self.assertEqual(self.mock_log_content, expected)

  def testBuildAsync(self):
    self._ExpectCreateBuild(logs_bucket='logs-bucket', stream_log=False)
    self.build.logsBucket = 'logs-bucket'
    result = self.client.ExecuteCloudBuildAsync(
        self.build, project='my-project')
    result_build_id = build.GetBuildProp(result, 'id')
    self.assertEqual(result_build_id, 'build-id')

  def testBuild_TailLogs(self):
    self._ExpectCreateBuild(logs_bucket='logs-bucket', retries=2)
    for i in range(3):
      self._ExpectLogRequest(b=i * len('Some log text\n'))
    self.build.logsBucket = 'logs-bucket'

    self.client.ExecuteCloudBuild(self.build, project='my-project')

  def testBuild_ProjectFromProperties(self):
    properties.VALUES.core.project.Set('my-project')
    self.addCleanup(properties.VALUES.core.project.Set, None)

    self._ExpectCreateBuild(logs_bucket='logs-bucket')
    self._ExpectLogRequest()
    self.build.logsBucket = 'logs-bucket'

    self.client.ExecuteCloudBuild(self.build)

    expected = ('--------- REMOTE BUILD OUTPUT ----------\n'
                'Some log text\n'
                '----------------------------------------\n\n')
    self.assertEqual(self.mock_log_content, expected)

  def testBuild_NoLogs(self):
    self._ExpectCreateBuild()

    self.client.ExecuteCloudBuild(self.build, project='my-project')

    self.assertEqual(self.mock_log_content, '')

  def testBuildCreateFailure(self):
    error_msg = ('The cloudbuild API is not enabled for project ID '
                 '"my-project": to enable it, visit '
                 'https://console.cloud.google.com/apis/api/'
                 'cloudbuild.googleapis.com/overview?project=my-project')
    error_url = ('https://cloudbuild.googleapis.com/v1/projects/my-project/'
                 'builds?alt=json')
    self._ExpectCreateBuild(exception=http_error.MakeHttpError(404, error_msg,
                                                               url=error_url))

    with self.AssertRaisesHttpErrorMatchesAsHttpException(
        'Project [my-project] not found: ' + error_msg):
      self.client.ExecuteCloudBuild(self.build, project='my-project')

    self.assertEqual(self.mock_log_content, '')

  def testBuild_CreateOperationError(self):
    error_msg = 'Build failed; check build logs for details'
    error_code = 2
    response_error = self.messages.Status(
        code=error_code,
        message=error_msg)
    self._ExpectCreateBuild(response_error=response_error, success=False)

    expected = ('Cloud build failed. Check logs in the Cloud Console.'
                ' Failure status: UNKNOWN: Error Response: [2] Build failed; '
                'check build logs for details')

    with self.AssertRaisesExceptionMatches(build.BuildFailedError, expected):
      self.client.ExecuteCloudBuild(self.build, project='my-project')

  def testBuild_CreateOperationErrorDetails(self):
    error_msg = 'Build failed; check build logs for details'
    error_code = 2
    response_error = self.messages.Status(
        code=error_code,
        message=error_msg,
        details=[
            encoding.PyValueToMessage(
                self.messages.Status.DetailsValueListEntry,
                {'Detail': 'This is a detail about the failure'}),
            encoding.PyValueToMessage(
                self.messages.Status.DetailsValueListEntry,
                {'Detail2': 'This is another detail'})
        ]
    )
    self._ExpectCreateBuild(response_error=response_error, success=False)

    expected = textwrap.dedent("""\
        Cloud build failed. Check logs in the Cloud Console. Failure status: UNKNOWN: Error Response: [2] Build failed; check build logs for details

        Details: [
          [
            {
              "Detail": "This is a detail about the failure"
            },
            {
              "Detail2": "This is another detail"
            }
          ]
        ]
    """)

    with self.AssertRaisesExceptionMatches(build.BuildFailedError, expected):
      self.client.ExecuteCloudBuild(self.build, project='my-project')

  def testBuild_CreateOperationTimesOut(self):
    self._ExpectCreateBuild(retries=60 * 60 - 1, success=False)
    expr = ('Operation [{}] timed out. This operation may still be underway.'
            .format(self._PROJECT_NAME))
    expected = 'Cloud build timed out.'
    with self.AssertRaisesExceptionMatches(build.BuildFailedError, expected):
      self.client.ExecuteCloudBuild(self.build, project='my-project')
    self.AssertLogContains(expr)

  def testBuild_TimeoutWithLogs(self):
    self.build.logsBucket = 'logs-bucket'
    for i in range(60 * 60):
      self._ExpectLogRequest(b=i * len('Some log text\n'))
    self._ExpectCreateBuild(
        retries=60 * 60 - 1, success=False, logs_bucket=self.build.logsBucket)
    expr = ('Operation [{}] timed out. This operation may still be underway.'
            .format(self._PROJECT_NAME))
    expected = 'Cloud build timed out.'
    with self.AssertRaisesExceptionMatches(build.BuildFailedError, expected):
      self.client.ExecuteCloudBuild(self.build, project='my-project')
    self.AssertLogContains(expr)


if __name__ == '__main__':
  test_case.main()
