# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for survey module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.survey import question
from googlecloudsdk.command_lib.survey import survey
from tests.lib import cli_test_base
from tests.lib import test_case


class SurveyTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.survey = survey.Survey('TwoQuestionGeneralSurvey')
    mc_question = 'Overall, how satisfied are you with Cloud SDK?'
    mc_instruction = ('Please answer the question by typing the number that '
                      'corresponds to your answer: ')
    mc_instruction_on_rejection = ('Answer is invalid, please type a number '
                                   'from 1 to 5: ')
    mc_choices = ['Very satisfied', 'Somewhat satisfied',
                  'Neither satisfied nor dissatisfied', 'Somewhat dissatisfied',
                  'Very dissatisfied']
    open_question = ('What are the reasons for the rating you gave? [Please DO '
                     'NOT enter personal info]')
    open_instruction = 'Please type your answer: '

    self.multi_choice_question = question.MultiChoiceQuestion(
        question=mc_question,
        instruction=mc_instruction,
        instruction_on_rejection=mc_instruction_on_rejection,
        choices=mc_choices)
    self.free_text_question = question.FreeTextQuestion(
        question=open_question,
        instruction=open_instruction,
        instruction_on_rejection=None)

  def testPrintWelcome(self):
    self.survey.PrintWelcomeMsg()
    self.AssertErrMatches('Thank you for taking the survey.*')

  def testQuestions(self):
    expected_questions = [self.multi_choice_question, self.free_text_question]
    for q, expected_q in zip(self.survey.questions, expected_questions):
      self.assertEqual(q, expected_q)

  def testLen(self):
    self.assertEqual(len(self.survey), 2)

  def testSurveyNotDefinedException(self):
    with self.AssertRaisesExceptionRegexp(
        survey.SurveyContentNotDefinedError,
        'Cannot find survey SurveyNotExisting.yaml .*'):
      _ = survey.Survey('SurveyNotExisting')

  def testPrintSurveyInstruction(self):
    self.survey.PrintInstruction()
    self.AssertErrEquals(
        'To skip this question, type s; to exit the survey, type x.\n')


if __name__ == '__main__':
  test_case.main()
