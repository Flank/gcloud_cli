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
    self.survey = survey.Survey('GeneralSurvey')
    mc_question = 'Overall, how satisfied are you with Cloud SDK?'
    mc_instruction = ('Please answer the question by typing the number that '
                      'corresponds to your answer: ')
    mc_instruction_on_rejection = ('Answer is invalid, please type a number '
                                   'from 1 to 5: ')
    mc_choices = ['Very satisfied', 'Somewhat satisfied',
                  'Neither satisfied nor dissatisfied', 'Somewhat dissatisfied',
                  'Very dissatisfied']

    nps_question = ('On a scale from 0-10, where 0 means "Not at all likely" '
                    'and 10 means "Extremely likely", how likely are you to '
                    'recommend Cloud SDK to a friend or colleague?')
    nps_instruction = ('Please answer the question by typing the number that '
                       'corresponds to your answer: ')
    nps_instruction_on_rejection = ('Answer is invalid, please type a number '
                                    'from 0 to 10: ')

    open_question_1 = (
        'What are the reasons for the rating you gave? [Please DO '
        'NOT enter personal info]')
    open_instruction_1 = 'Please type your answer: '

    open_question_2 = ('What could we do to improve your rating? [Please DO '
                       'NOT enter personal info]')
    open_instruction_2 = 'Please type your answer: '

    self.multi_choice_question = question.SatisfactionQuestion(
        question=mc_question,
        instruction=mc_instruction,
        instruction_on_rejection=mc_instruction_on_rejection,
        choices=mc_choices)

    self.nps_question = question.NPSQuestion(
        question=nps_question,
        instruction=nps_instruction,
        instruction_on_rejection=nps_instruction_on_rejection,
        min_answer=0,
        max_answer=10)

    self.free_text_question_1 = question.FreeTextQuestion(
        question=open_question_1,
        instruction=open_instruction_1,
        instruction_on_rejection=None)

    self.free_text_question_2 = question.FreeTextQuestion(
        question=open_question_2,
        instruction=open_instruction_2,
        instruction_on_rejection=None)

  def testPrintWelcome(self):
    self.survey.PrintWelcomeMsg()
    self.AssertErrMatches('Thank you for taking the survey.*')

  def testQuestions(self):
    expected_questions = [
        self.multi_choice_question, self.nps_question,
        self.free_text_question_1, self.free_text_question_2
    ]
    for survey_question, expected_question in zip(self.survey.questions,
                                                  expected_questions):
      self.assertEqual(survey_question, expected_question)

  def testSurveyNotDefinedException(self):
    with self.AssertRaisesExceptionRegexp(
        survey.SurveyContentNotDefinedError,
        'Cannot find survey SurveyNotExisting.yaml .*'):
      _ = survey.Survey('SurveyNotExisting')

  def testPrintSurveyInstruction(self):
    self.survey.PrintInstruction()
    self.AssertErrEquals(
        'To skip this question, type s; to exit the survey, type x.\n')

  def testQuestionServing(self):
    expected_questions = [
        self.multi_choice_question, self.nps_question,
        self.free_text_question_1, self.free_text_question_2
    ]
    for served_question, expected_question in zip(self.survey,
                                                  expected_questions):
      self.assertEqual(served_question, expected_question)


class GeneralSurveyTest(SurveyTest):

  def SetUp(self):
    super(GeneralSurveyTest, self).SetUp()
    self.survey = survey.GeneralSurvey()

  def testIsSatisfied(self):
    self.survey.questions[0].AnswerQuestion('5')
    self.assertTrue(self.survey.IsSatisfied())
    self.survey.questions[0].AnswerQuestion('1')
    self.assertFalse(self.survey.IsSatisfied())

  def testQuestionServing_Satisfied(self):
    expected_questions = [
        self.multi_choice_question, self.nps_question, self.free_text_question_1
    ]
    index = 0
    for served_question in self.survey:
      self.assertEqual(served_question, expected_questions[index])
      if isinstance(served_question, question.SatisfactionQuestion):
        served_question.AnswerQuestion('5')
      index += 1

  def testQuestionServing_Dissatisfied(self):
    expected_questions = [
        self.multi_choice_question, self.nps_question, self.free_text_question_2
    ]
    index = 0
    for served_question in self.survey:
      self.assertEqual(served_question, expected_questions[index])
      if isinstance(served_question, question.SatisfactionQuestion):
        served_question.AnswerQuestion('1')
      index += 1


if __name__ == '__main__':
  test_case.main()
