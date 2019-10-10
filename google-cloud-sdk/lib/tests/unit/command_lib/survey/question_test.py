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
"""Tests for question module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.survey import question
from tests.lib import cli_test_base
from tests.lib import test_case


class MultiChoiceQuestionTest(cli_test_base.CliTestBase):

  def SetUp(self):
    question_msg = 'How do you like Cloud SDK?'
    instruction = 'Please answer by entering a number: '
    instruction_on_rejection = ('Answer is invalid, please type a number from '
                                '1-2: ')
    choices = ['I like it', "I don't like it"]
    self.correct_content_dict = {
        'question': question_msg,
        'instruction': instruction,
        'instruction_on_rejection': instruction_on_rejection,
        'choices': choices
    }
    self.wrong_content_dict = {
        'question': question_msg,
        'choices': choices,
    }
    self.question = question.MultiChoiceQuestion(question_msg, instruction,
                                                 instruction_on_rejection,
                                                 choices)

  def testIsAnswered(self):
    self.assertFalse(self.question.IsAnswered())
    self.question.AnswerQuestion('1')
    self.assertTrue(self.question.IsAnswered())

  def testRetrieveAnswerFromUnansweredQuestion(self):
    with self.AssertRaisesExceptionMatches(
        question.RetrieveAnswerOfUnansweredQuestion,
        'No answer for this question.'):
      _ = self.question.answer

  def testAcceptAnswer(self):
    self.assertFalse(self.question.AcceptAnswer('0'))
    self.assertTrue(self.question.AcceptAnswer('1'))
    self.assertTrue(self.question.AcceptAnswer('2'))
    self.assertFalse(self.question.AcceptAnswer('3'))

  def testRejectAnswer(self):
    with self.AssertRaisesExceptionMatches(question.AnswerRejectedError,
                                           'Answer is invalid.'):
      self.question.AnswerQuestion('3')

  def testPrintQuestion(self):
    self.question.PrintQuestion()
    output_msg = """\
  How do you like Cloud SDK?
    [1] I like it
    [2] I don't like it
"""
    self.AssertOutputEquals(output_msg)

  def testPrintInstruction(self):
    self.question.PrintInstruction()
    err_msg = """\
Please answer by entering a number: """
    self.AssertErrEquals(err_msg)

  def testPrintInstructionOnRejection(self):
    self.question.PrintInstructionOnRejection()
    err_msg = """\
Answer is invalid, please type a number from 1-2: """
    self.AssertErrEquals(err_msg)

  def testFromDictionary(self):
    q = question.MultiChoiceQuestion.FromDictionary(self.correct_content_dict)
    self.assertEqual(q, self.question)

  def testFromDictionary_Exception(self):
    with self.AssertRaisesExceptionMatches(
        question.QuestionCreationError,
        'Question cannot be created because either some required field is '
        'missing or there are redundant fields. Required fields are question, '
        'instruction, instruction_on_rejection, choices.'):
      _ = question.MultiChoiceQuestion.FromDictionary(self.wrong_content_dict)

  def testEq(self):
    question_copy = question.MultiChoiceQuestion(
        self.question.question, self.question.instruction,
        self.question.instruction_on_rejection, self.question._choices)
    different_question_msg = self.question.question + ' Be honest'
    different_question = question.MultiChoiceQuestion(
        different_question_msg, self.question.instruction,
        self.question.instruction_on_rejection, self.question._choices)
    self.assertEqual(self.question, question_copy)
    self.assertNotEqual(self.question, different_question)

  def testChoice(self):
    self.assertEqual(self.question.Choice(1), 'I like it')
    self.assertEqual(self.question.Choice(2), "I don't like it")


class SatisfactionQuestionTest(cli_test_base.CliTestBase):

  def SetUp(self):
    question_msg = 'How do you like Cloud SDK?'
    instruction = 'Please answer by entering a number: '
    instruction_on_rejection = ('Answer is invalid, please type a number from '
                                '1-5: ')
    choices = [
        'Very satisfied', 'Somewhat satisfied',
        'Neither satisfied nor dissatisfied', 'Somewhat dissatisfied',
        'Very dissatisfied'
    ]
    indexes = [5, 4, 3, 2, 1]
    self.question = question.SatisfactionQuestion(question_msg, instruction,
                                                  instruction_on_rejection,
                                                  choices, indexes)

  def testPrintQuestion(self):
    self.question.PrintQuestion()
    output_msg = """\
  How do you like Cloud SDK?
    [5] Very satisfied
    [4] Somewhat satisfied
    [3] Neither satisfied nor dissatisfied
    [2] Somewhat dissatisfied
    [1] Very dissatisfied
"""
    self.AssertOutputEquals(output_msg)

  def testChoice(self):
    self.assertEqual(self.question.Choice(5), 'Very satisfied')
    self.assertEqual(self.question.Choice(4), 'Somewhat satisfied')
    self.assertEqual(
        self.question.Choice(3), 'Neither satisfied nor dissatisfied')
    self.assertEqual(self.question.Choice(2), 'Somewhat dissatisfied')
    self.assertEqual(self.question.Choice(1), 'Very dissatisfied')

  def testIsSatisfied(self):
    self.question.AnswerQuestion(1)
    self.assertFalse(self.question.IsSatisfied())
    self.question.AnswerQuestion(2)
    self.assertFalse(self.question.IsSatisfied())
    self.question.AnswerQuestion(3)
    self.assertFalse(self.question.IsSatisfied())
    self.question.AnswerQuestion(4)
    self.assertTrue(self.question.IsSatisfied())
    self.question.AnswerQuestion(5)
    self.assertTrue(self.question.IsSatisfied())


class RatingQuestionTest(cli_test_base.CliTestBase):

  def SetUp(self):
    question_msg = 'How likely will you recommend Cloud SDK to friends?'
    instruction = ('0 means extremely unlikely, 10 means extremely likely, '
                   'please answer a number in 0-10')
    instruction_on_rejection = ('Answer is invalid, please type a number from '
                                '0-10: ')
    self.question = question.RatingQuestion(question_msg, instruction,
                                            instruction_on_rejection, 0, 10)

  def testPrintQuestion(self):
    self.question.PrintQuestion()
    output_msg = """\
  How likely will you recommend Cloud SDK to friends?
"""
    self.AssertOutputEquals(output_msg)

  def testAcceptAnswer(self):
    self.assertFalse(self.question.AcceptAnswer('h'))
    self.assertFalse(self.question.AcceptAnswer('-1'))
    self.assertFalse(self.question.AcceptAnswer('11'))
    self.assertTrue(self.question.AcceptAnswer('0'))
    self.assertTrue(self.question.AcceptAnswer('10'))


class FreeTextQuestionTest(cli_test_base.CliTestBase):

  def SetUp(self):
    question_msg = 'Do you have feedback?'
    instruction = 'Please type your answer here: '
    self.correct_content_dict = {
        'question': question_msg,
        'instruction': instruction,
    }
    self.wrong_content_dict = {
        'question': question_msg,
    }
    self.question = question.FreeTextQuestion(
        question=question_msg,
        instruction=instruction)

  def testIsAnswered(self):
    self.assertFalse(self.question.IsAnswered())
    self.question.AnswerQuestion('random thing')
    self.assertTrue(self.question.IsAnswered())

  def testAcceptAnswer(self):
    self.assertTrue(self.question.AcceptAnswer(''))
    self.assertTrue(self.question.AcceptAnswer('random thing'))

  def testPrintQuestion(self):
    self.question.PrintQuestion()
    out_msg = """\
  Do you have feedback?
"""
    self.AssertOutputEquals(out_msg)

  def testPrintInstruction(self):
    self.question.PrintInstruction()
    err_msg = """\
Please type your answer here: """
    self.AssertErrEquals(err_msg)

  def testFromDictionary(self):
    q = question.FreeTextQuestion.FromDictionary(self.correct_content_dict)
    self.assertEqual(q, self.question)

  def testFromDictionary_Exception(self):
    with self.AssertRaisesExceptionMatches(
        question.QuestionCreationError,
        'Question cannot be created because either some required field is '
        'missing or there are redundant fields. Required fields are '
        'question, instruction.'):
      _ = question.FreeTextQuestion.FromDictionary(self.wrong_content_dict)

  def testEq(self):
    question_copy = question.FreeTextQuestion(
        self.question.question, self.question.instruction,
        self.question.instruction_on_rejection)
    different_question_msg = self.question.question + ' Be honest'
    different_question = question.FreeTextQuestion(
        different_question_msg, self.question.instruction,
        self.question.instruction_on_rejection)
    self.assertEqual(self.question, question_copy)
    self.assertNotEqual(self.question, different_question)


if __name__ == '__main__':
  test_case.main()
