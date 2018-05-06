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
"""Tests for googlecloudsdk.api_lib.cloudbuild.logs."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py import exceptions as api_exceptions

from googlecloudsdk.api_lib.cloudbuild import logs as cloudbuild_logs
from tests.lib import e2e_base

TEST_ID = '17c228a2-501d-458e-904e-2f3001ee429f'
LOG_URL_PATTEN = 'https://storage.googleapis.com/{bucket}/log-{obj}.txt'


class TailingTest(e2e_base.WithMockHttp):
  """Test cloud_storage.LogTailer."""

  _LOG_URL = 'https://www.googleapis.com/storage/v1/b/bucket/o/log-build-id.txt'

  def SetUp(self):
    self.mock_log_content = ''
    mock_log_print = self.StartPatch(
        'googlecloudsdk.api_lib.cloudbuild.logs.LogTailer._PrintLogLine')
    mock_log_print.side_effect = self._MockPrintLogLine

    mock_term = self.StartPatch(
        'googlecloudsdk.core.console.console_attr_os.GetTermSize')
    mock_term.side_effect = self._MockTermSize

  def _MockPrintLogLine(self, text):
    self.mock_log_content += text + '\n'

  def _MockTermSize(self):
    return 40, 100

  def testPoll(self):
    # This test covers the happy path flow ...
    # 1) logfile hasn't started yet and returns 404's
    self.AddHTTPResponse(
        self._LOG_URL,
        expected_params={'alt': 'media'},
        request_headers={'Range': 'bytes=0-'},
        body='not found here',
        headers={'status': 404})
    self.AddHTTPResponse(
        self._LOG_URL,
        expected_params={'alt': 'media'},
        request_headers={'Range': 'bytes=0-'},
        body='not found yet',
        headers={'status': 404})
    self.AddHTTPResponse(
        self._LOG_URL,
        expected_params={'alt': 'media'},
        request_headers={'Range': 'bytes=0-'},
        body='Some log text\n',
        headers={'status': 206})
    self.AddHTTPResponse(
        self._LOG_URL,
        expected_params={'alt': 'media'},
        request_headers={'Range': 'bytes=14-'},
        body='couldnt do the range you asked me for.',
        headers={'status': 416})
    self.AddHTTPResponse(
        self._LOG_URL,
        expected_params={'alt': 'media'},
        request_headers={'Range': 'bytes=14-'},
        body='Some more text\nAnd another line\n',
        headers={'status': 206})

    tailer = cloudbuild_logs.LogTailer('bucket', 'log-build-id.txt')
    tailer.Poll()  # 404
    tailer.Poll()  # 404
    # The log separator line doesn't print until the log starts.
    self.assertEqual(self.mock_log_content, '')
    tailer.Poll()  # 206 (content)
    tailer.Poll()  # 416
    tailer.Poll(True)  # 206 (content)
    expected = ('--------- REMOTE BUILD OUTPUT ----------\n'
                'Some log text\n'
                'Some more text\nAnd another line\n'
                '----------------------------------------\n\n')
    self.assertEqual(self.mock_log_content, expected)

  def testPoll429(self):
    # If the service is pushing back (err 429), we do best effort polling and
    # then move on without finishing the log.
    self.AddHTTPResponse(
        self._LOG_URL,
        expected_params={'alt': 'media'},
        request_headers={'Range': 'bytes=0-'},
        body='Some log text\n',
        headers={'status': 206})
    self.AddHTTPResponse(
        self._LOG_URL,
        expected_params={'alt': 'media'},
        request_headers={'Range': 'bytes=14-'},
        body='stop calling me so often!',
        headers={'status': 429})
    self.AddHTTPResponse(
        self._LOG_URL,
        expected_params={'alt': 'media'},
        request_headers={'Range': 'bytes=14-'},
        body='too much! server is pushing back with 429',
        headers={'status': 429})

    tailer = cloudbuild_logs.LogTailer('bucket', 'log-build-id.txt')
    tailer.Poll()  # 206 (content)
    tailer.Poll()  # 429
    tailer.Poll(True)  # 429
    expected = ('--------- REMOTE BUILD OUTPUT ----------\n'
                'Some log text\n'
                '-------- (possibly incomplete) ---------\n\n')
    self.assertEqual(self.mock_log_content, expected)

  def testPoll503(self):
    # If the service is unavailable (err 503), we do best effort polling and
    # then move on without finishing the log.
    self.AddHTTPResponse(
        self._LOG_URL,
        expected_params={'alt': 'media'},
        request_headers={'Range': 'bytes=0-'},
        body='Some log text\n',
        headers={'status': 206})
    self.AddHTTPResponse(
        self._LOG_URL,
        expected_params={'alt': 'media'},
        request_headers={'Range': 'bytes=14-'},
        body='I am a server and Im really overloaded',
        headers={'status': 503})
    self.AddHTTPResponse(
        self._LOG_URL,
        expected_params={'alt': 'media'},
        request_headers={'Range': 'bytes=14-'},
        body='So much load. So service unavailable.',
        headers={'status': 503})

    tailer = cloudbuild_logs.LogTailer('bucket', 'log-build-id.txt')
    tailer.Poll()  # 206 (content)
    tailer.Poll()  # 503
    tailer.Poll(True)  # 503
    expected = ('--------- REMOTE BUILD OUTPUT ----------\n'
                'Some log text\n'
                '-------- (possibly incomplete) ---------\n\n')
    self.assertEqual(self.mock_log_content, expected)

  def testPollError(self):
    # Any other errors will result in hard failure.
    self.AddHTTPResponse(
        self._LOG_URL,
        expected_params={'alt': 'media'},
        request_headers={'Range': 'bytes=0-'},
        body='you got no permission',
        headers={'status': 403})

    tailer = cloudbuild_logs.LogTailer('bucket', 'log-build-id.txt')
    try:
      tailer.Poll()  # 403
    except api_exceptions.HttpError:
      # Success.
      return
    self.fail('Expected a HttpError')


class MakeLogTailerTest(e2e_base.WithMockHttp):
  """Test class for _MakeBuildClient's bucket and log object generation."""

  def SetUp(self):
    self.build_client = cloudbuild_logs.CloudBuildClient(client=object(),
                                                         messages=object())

  def _AssertLogTailer(self, build):
    expected_url = LOG_URL_PATTEN.format(bucket=build.bucket, obj=build.id)
    tailer = cloudbuild_logs.LogTailer.FromBuild(build)

    if tailer.url != expected_url:
      self.fail('LogTailer.url {} did not match expected {}'
                .format(tailer.url, expected_url))

  def _makeMockBuildResource(self, bucket):
    bucket += '_cloudbuild/logs'
    return type(str(''), (), dict(id=TEST_ID, bucket=bucket,
                                  logsBucket='gs://' + bucket + ''))()

  # Test for b/35934834 where lstrip() would remove "s", "g" from bucket name 2
  def testMakeLogTailer(self):

    # Test with non leading g,s bucket
    self._AssertLogTailer(self._makeMockBuildResource('example-bucket'))

    # Test with leading g,s bucket
    self._AssertLogTailer(self._makeMockBuildResource('sg-bucket'))

    # Test with gs:// in bucket. Should not be possible with a URL
    self._AssertLogTailer(self._makeMockBuildResource('sg-bucketgs://'))

