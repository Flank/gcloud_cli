# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for concord_util module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os

from googlecloudsdk.api_lib.survey import concord_util
from googlecloudsdk.command_lib.survey import survey
from googlecloudsdk.core import metrics
from googlecloudsdk.core.survey import survey_check
from googlecloudsdk.core.util import platforms
from tests.lib import cli_test_base
from tests.lib import test_case

import httplib2
import mock


class ConcordUtilTest(cli_test_base.CliTestBase):

  def SetUp(self):
    # prepare test survey
    self.survey_instances = survey.Survey('TwoQuestionGeneralSurvey')
    q1, q2 = self.survey_instances.questions
    q1.AnswerQuestion('1')
    q2.AnswerQuestion('Love Cloud SDK!')

    self.mock_client = mock.create_autospec(httplib2.Http)
    self.StartPatch(
        'googlecloudsdk.core.http.Http', return_value=self.mock_client)

    self.StartObjectPatch(
        metrics, 'GetTimeMillis', autospec=True, return_value=100)
    self.StartObjectPatch(
        metrics, 'GetUserAgent', autospec=True, return_value='cloudsdk')
    self.StartObjectPatch(metrics, 'GetCID', autospec=True, return_value='111')

    os_attrs = {'id': 'os_id'}
    self.mock_os = mock.create_autospec(platforms.OperatingSystem, **os_attrs)
    platform_attrs = {'operating_system': self.mock_os}
    self.mock_platform = mock.create_autospec(platforms.Platform,
                                              **platform_attrs)
    self.StartObjectPatch(
        platforms.Platform, 'Current', return_value=self.mock_platform)

    self.StartPatch(
        'googlecloudsdk.api_lib.survey.concord_util._SurveyEnvironment',
        return_value=[{
            'env': 'env'
        }])

    self.tempdir = self.CreateTempDir()
    self.StartPatch(
        'googlecloudsdk.core.config.Paths.survey_prompting_cache_path',
        new=os.path.join(self.tempdir, 'survey_prompt_file'))
    self.StartPatch('time.time', return_value=200)

  def testLogSurveyAnswers_Success(self):
    self.mock_client.request.return_value = ({'status': '200'}, '')
    concord_util.LogSurveyAnswers(self.survey_instances)
    expected_headers = {'user-agent': 'cloudsdk'}
    expected_hats_response = {
        'hats_metadata': {
            'site_id': 'CloudSDK',
            'site_name': 'googlecloudsdk',
            'survey_id': 'TwoQuestionGeneralSurvey'
        },
        'multiple_choice_response': [{
            'question_number': 0,
            'answer_text': ['Very satisfied'],
            'answer_index': [1],
            'order_index': [1],
            'order': [1, 2, 3, 4, 5]
        }],
        'open_text_response': [{
            'question_number': 1,
            'answer_text': 'Love Cloud SDK!'
        }]
    }
    expected_concord_event = {
        'event_metadata': [{
            'env': 'env'
        }],
        'console_type': 'CloudSDK',
        'event_type': 'hatsSurvey',
        'hats_response': expected_hats_response
    }
    expected_log_events = [{
        'event_time_ms':
            100,
        'source_extension_json':
            json.dumps(expected_concord_event, sort_keys=True)
    }]

    expected_body = json.dumps({
        'client_info': {
            'client_type': 'DESKTOP',
            'desktop_client_info': {
                'os': 'os_id'
            }
        },
        'log_source_name': 'CONCORD',
        'zwieback_cookie': '111',
        'request_time_ms': 100,
        'log_event': expected_log_events
    },
                               sort_keys=True)

    self.mock_client.request.assert_called_once_with(
        'https://play.googleapis.com/log',
        method='POST',
        body=expected_body,
        headers=expected_headers)
    with survey_check.PromptRecord() as pr:
      self.assertEqual(pr.last_answer_survey_time, 200)
    self.AssertErrEquals('Your response is submitted.\n')

  def testLongSurveyAnswersTest_Failed(self):
    self.mock_client.request.return_value = ({'status': '400'}, '')
    with self.AssertRaisesExceptionMatches(
        concord_util.SurveyNotRecordedError,
        'We cannot record your feedback at this time, please try again later.'):
      concord_util.LogSurveyAnswers(self.survey_instances)


if __name__ == '__main__':
  test_case.main()
