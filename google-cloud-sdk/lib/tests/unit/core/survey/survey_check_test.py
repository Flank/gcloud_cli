# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for survey_check module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core import config
from googlecloudsdk.core.survey import survey_check
from tests.lib import sdk_test_base
from tests.lib import test_case


class PromptRecordTest(sdk_test_base.WithOutputCapture, sdk_test_base.SdkBase):

  def SetUp(self):
    self.tempdir = self.CreateTempDir()
    self.StartPatch(
        'googlecloudsdk.core.config.Paths.survey_prompting_cache_path',
        new=os.path.join(self.tempdir, 'survey_prompt_file'))
    self.last_prompt_time = 1544643641
    self.last_answer_survey_time = 1544643689
    self.new_last_prompt_time = 1544645421

  def testReadSavePromptRecord(self):
    record = survey_check.PromptRecord()
    self.assertEqual(record.last_prompt_time, None)
    self.assertEqual(record.last_answer_survey_time, None)
    self.assertFalse(record.dirty)
    with record as r:
      r.last_prompt_time = self.last_prompt_time
      r.last_answer_survey_time = self.last_answer_survey_time
      self.assertTrue(record.dirty)
    self.assertFalse(record.dirty)

    new_record = survey_check.PromptRecord()
    self.assertEqual(new_record.last_prompt_time, self.last_prompt_time)
    self.assertEqual(new_record.last_answer_survey_time,
                     self.last_answer_survey_time)
    with new_record as r:
      r.last_prompt_time = self.new_last_prompt_time
    self.assertEqual(new_record.last_prompt_time, self.new_last_prompt_time)
    self.assertEqual(new_record.last_answer_survey_time,
                     self.last_answer_survey_time)

  def testReadSavePromptRecord_LastPromptTimeOnly(self):
    record = survey_check.PromptRecord()
    with record as r:
      r.last_prompt_time = self.last_prompt_time
    new_record = survey_check.PromptRecord()
    self.assertEqual(new_record.last_prompt_time, self.last_prompt_time)
    self.assertEqual(new_record.last_answer_survey_time, None)

  def testReadSavePromptRecord_LastAnswerSurveyTimeOnly(self):
    record = survey_check.PromptRecord()
    with record as r:
      r.last_answer_survey_time = self.last_answer_survey_time
    new_record = survey_check.PromptRecord()
    self.assertEqual(new_record.last_prompt_time, None)
    self.assertEqual(new_record.last_answer_survey_time,
                     self.last_answer_survey_time)

  def testReadPromptRecord_BadFile(self):
    with open(config.Paths().survey_prompting_cache_path, 'w') as f:
      f.write('junk data')
    record = survey_check.PromptRecord()
    self.assertEqual(record.last_prompt_time, None)
    self.assertEqual(record.last_answer_survey_time, None)


class SurveyPrompterTest(sdk_test_base.WithOutputCapture,
                         sdk_test_base.SdkBase):

  def SetUp(self):
    self.tempdir = self.CreateTempDir()
    self.StartPatch(
        'googlecloudsdk.core.config.Paths.survey_prompting_cache_path',
        new=os.path.join(self.tempdir, 'survey_prompt_file'))
    self.current_time = 1544651979
    # pylint: disable=line-too-long
    self.last_prompt_time_expired = self.current_time - survey_check.SURVEY_PROMPT_INTERVAL - 10
    self.last_prompt_time_unexpired = self.current_time - survey_check.SURVEY_PROMPT_INTERVAL + 10
    self.last_answer_survey_time_expired = self.current_time - survey_check.SURVEY_PROMPT_INTERVAL_AFTER_ANSWERED - 10
    self.last_answer_survey_time_unexpired = self.current_time - survey_check.SURVEY_PROMPT_INTERVAL_AFTER_ANSWERED + 10
    # pylint: enable=line-too-long
    self.StartPatch('time.time', return_value=self.current_time)
    self.StartPatch('googlecloudsdk.core.log.out.isatty', return_value=True)
    self.StartPatch('googlecloudsdk.core.log.err.isatty', return_value=True)

  def testShouldPrompt_EmptyCache(self):
    prompter = survey_check.SurveyPrompter()
    self.assertTrue(prompter.ShouldPrompt())

  def testShouldPrompt_NotPromptedYet_AnswerNotExpired(self):
    with survey_check.PromptRecord() as pr:
      pr.last_answer_survey_time = self.last_answer_survey_time_unexpired
    prompter = survey_check.SurveyPrompter()
    self.assertFalse(prompter.ShouldPrompt())

  def testShouldPrompt_NotPromptedYet_AnswerExpired(self):
    with survey_check.PromptRecord() as pr:
      pr.last_answer_survey_time = self.last_answer_survey_time_expired
    prompter = survey_check.SurveyPrompter()
    self.assertTrue(prompter.ShouldPrompt())

  def testShouldPrompt_LastPromptExpired_NotAnswered(self):
    with survey_check.PromptRecord() as pr:
      pr.last_prompt_time = self.last_prompt_time_expired
    prompter = survey_check.SurveyPrompter()
    self.assertTrue(prompter.ShouldPrompt())

  def testShouldPrompt_LastPromptNotExpired_NotAnswered(self):
    with survey_check.PromptRecord() as pr:
      pr.last_prompt_time = self.last_prompt_time_unexpired
    prompter = survey_check.SurveyPrompter()
    self.assertFalse(prompter.ShouldPrompt())

  def testShouldPrompt_LastPromptExpired_AnswerNotExpired(self):
    with survey_check.PromptRecord() as pr:
      pr.last_prompt_time = self.last_prompt_time_expired
      pr.last_answer_survey_time = self.last_answer_survey_time_unexpired
    prompter = survey_check.SurveyPrompter()
    self.assertFalse(prompter.ShouldPrompt())

  def testShouldPrompt_LastPromptExpired_AnswerExpired(self):
    with survey_check.PromptRecord() as pr:
      pr.last_prompt_time = self.last_prompt_time_expired
      pr.last_answer_survey_time = self.last_answer_survey_time_expired
    prompter = survey_check.SurveyPrompter()
    self.assertTrue(prompter.ShouldPrompt())

  def testShouldPrompt_LastPromptNotExpired_AnswerNotExpired(self):
    with survey_check.PromptRecord() as pr:
      pr.last_prompt_time = self.last_prompt_time_unexpired
      pr.last_answer_survey_time = self.last_answer_survey_time_unexpired
    prompter = survey_check.SurveyPrompter()
    self.assertFalse(prompter.ShouldPrompt())

  def testShouldPrompt_LastPromptNotExpired_AnswerExpired(self):
    with survey_check.PromptRecord() as pr:
      pr.last_prompt_time = self.last_prompt_time_unexpired
      pr.last_answer_survey_time = self.last_answer_survey_time_expired
    prompter = survey_check.SurveyPrompter()
    self.assertFalse(prompter.ShouldPrompt())

  def testShouldPrompt_NotIsatty(self):
    self.StartPatch('googlecloudsdk.core.log.out.isatty', return_value=False)
    self.StartPatch('googlecloudsdk.core.log.err.isatty', return_value=False)
    prompter = survey_check.SurveyPrompter()
    self.assertFalse(prompter.ShouldPrompt())

  def testPromptForSurvey_NoCacheFile(self):
    prompter = survey_check.SurveyPrompter()
    prompter.Prompt()
    self.AssertErrEquals('')
    with survey_check.PromptRecord() as pr:
      self.assertEqual(pr.last_prompt_time, 1544651979)
      self.assertEqual(pr.last_answer_survey_time, None)

  def testPromptForSurvey(self):
    with survey_check.PromptRecord() as pr:
      pr.last_prompt_time = 0
    prompter = survey_check.SurveyPrompter()
    prompter.Prompt()
    self.AssertErrEquals(
        '\n\nTo take a quick anonymous survey, run:\n'
        '  $ gcloud survey\n\n'
    )
    with survey_check.PromptRecord() as pr:
      self.assertEqual(pr.last_prompt_time, 1544651979)
      self.assertEqual(pr.last_answer_survey_time, None)


if __name__ == '__main__':
  test_case.main()
