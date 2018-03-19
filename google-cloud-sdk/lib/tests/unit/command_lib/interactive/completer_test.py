# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Tests for the parser used by gcloud interactive."""

from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.interactive import completer
from googlecloudsdk.command_lib.interactive import parser
from googlecloudsdk.command_lib.meta import generate_cli_trees
from tests.lib import subtests
from tests.unit.command_lib.interactive import testdata

import mock


def MockDocument(text):
  doc = mock.MagicMock()
  doc.text_before_cursor = text
  doc.cursor_position = len(text)
  return doc


def MockEvent():
  event = mock.MagicMock()
  event.completion_requested = False
  return event


def Tuples(choices):
  return [(choice.text, choice.start_position) for choice in choices]


class GetCompletionsTest(subtests.Base):

  @classmethod
  def SetUpClass(cls):
    path = os.path.join(os.path.dirname(testdata.__file__), 'gcloud.json')
    cls.tree = {'commands': {'gcloud': cli_tree.Load(path=path)}}

  def SetUp(self):
    self.StartObjectPatch(
        generate_cli_trees.CliTreeGenerator,
        'MemoizeFailures',
        return_value=None)

  def Choices(self, text):
    cosh = mock.MagicMock()
    cosh.GetCompletions = lambda x: []
    interactive_completer = completer.InteractiveCliCompleter(
        interactive_parser=parser.Parser(self.tree), cosh=cosh)
    return list(interactive_completer.get_completions(
        MockDocument(text), MockEvent()))

  def testNoChoicesAfterEmptyFlagArgWithoutChoices(self):
    choices = self.Choices('gcloud --account= ')
    self.assertEqual([], Tuples(choices))

  def testCompletedTextIsCorrectForNonFlags(self):
    choices = self.Choices('gcloud compute instances add')
    self.assertEqual(
        [('add-access-config', -3),
         ('add-labels', -3),
         ('add-metadata', -3),
         ('add-tags', -3)],
        Tuples(choices))

  def testCompletedTextStartPositionIsCorrectFlag(self):
    choices = self.Choices('gcloud --acc')
    self.assertEqual(
        [('--account', -5)],
        Tuples(choices))

  def testCompletedTextStartPositionIsCorrectExplicitFlagEmptyValue(self):
    choices = self.Choices('gcloud alpha compute instances create --verbosity=')
    self.assertEqual(
        [('critical', 0),
         ('debug', 0),
         ('error', 0),
         ('info', 0),
         ('none', 0),
         ('warning', 0)],
        Tuples(choices))

  def testCompletedTextStartPositionIsCorrectExplicitFlagPartialValue(self):
    choices = self.Choices(
        'gcloud alpha compute instances create --verbosity=w')
    self.assertEqual(
        [('warning', -1)],
        Tuples(choices))

  def testCompletedTextStartPositionIsCorrectImplicitFlagEmptyValue(self):
    choices = self.Choices('gcloud alpha compute instances create --verbosity ')
    self.assertEqual(
        [('critical', 0),
         ('debug', 0),
         ('error', 0),
         ('info', 0),
         ('none', 0),
         ('warning', 0)],
        Tuples(choices))

  def testCompletedTextStartPositionIsCorrectImplicitFlagPartialValue(self):
    choices = self.Choices(
        'gcloud alpha compute instances create --verbosity w')
    self.assertEqual([('warning', -1)], Tuples(choices))
