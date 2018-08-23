# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import division
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
  event.completion_requested = True
  return event


def Tuples(choices):
  return [(choice.text, choice.start_position) for choice in choices]


class GetCompletionsTest(subtests.Base):

  @classmethod
  def SetUpClass(cls):
    path = os.path.join(os.path.dirname(testdata.__file__), 'gcloud.json')
    cls.tree = {
        'commands': {
            'gcloud': cli_tree.Load(path=path),
            'ls': {
                'commands': {},
                'is_group': False,
                'positionals': [],
            },
            'uls': {
                'commands': {},
                'is_group': False,
                'positionals': [],
            },
        },
        'positionals': [],
    }

  def SetUp(self):
    self.StartObjectPatch(
        generate_cli_trees.CliTreeGenerator,
        'MemoizeFailures',
        return_value=None)

  def Choices(self, text, completions=None):
    cosh = mock.MagicMock()
    self.get_completions_arg = None

    def _GetCompletions(x):
      self.get_completions_arg = x
      return completions or []

    cosh.GetCompletions = _GetCompletions
    interactive_completer = completer.InteractiveCliCompleter(
        interactive_parser=parser.Parser(self.tree), cosh=cosh)
    return list(interactive_completer.get_completions(
        MockDocument(text), MockEvent()))

  def testCommandNameFirstArgGcloud(self):
    choices = self.Choices('g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandNameFirstArgAfterSemiColonGcloud(self):
    choices = self.Choices('echo hello; g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandNameFirstArgAfterPipeGcloud(self):
    choices = self.Choices('echo hello | g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandNameFirstArgAfterPipe2Gcloud(self):
    choices = self.Choices('echo hello || g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandNameFirstArgAfterAmpersandGcloud(self):
    choices = self.Choices('echo hello & g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandNameFirstArgAfterAmpersand2Gcloud(self):
    choices = self.Choices('echo hello && g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandNameFirstArgAfterCloseGcloud(self):
    choices = self.Choices('value=$(g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandNameFirstArgLs(self):
    choices = self.Choices('l')
    self.assertEqual([('ls', -1)], Tuples(choices))

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

  def testCompletedTextStartPositionIsCorrectExplicitFlagEqualsNoValue(self):
    choices = self.Choices('gcloud alpha compute instances create --verbosity=')
    self.assertEqual(
        [('critical', 0),
         ('debug', 0),
         ('error', 0),
         ('info', 0),
         ('none', 0),
         ('warning', 0)],
        Tuples(choices))

  def testCompletedTextStartPositionIsCorrectExplicitFlagNoEqualsNoValue(self):
    choices = self.Choices('gcloud alpha compute instances create --verbosity')
    self.assertEqual(
        [(' critical', 0),
         (' debug', 0),
         (' error', 0),
         (' info', 0),
         (' none', 0),
         (' warning', 0)],
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

  def testCompletionFallback(self):
    self.Choices('gcloud info ')
    self.assertEqual(['gcloud', 'info', ''], self.get_completions_arg)

  def testCompletionFilePathMarkOneDir(self):
    if os.path.isdir('/bin'):
      completions = self.Choices('ls /bi', completions=['/bin'])
      self.assertEqual(['ls', '/bi'], self.get_completions_arg)
      self.assertEqual(
          [('/bin/', '/bin/')],
          [(c.text, c.display) for c in completions])

  def testCompletionFilePathMarkManyDirsAndFiles(self):
    if (os.path.isdir('/bin') and
        os.path.isdir('/lib') and
        os.path.isdir('/tmp')):
      completions = self.Choices(
          'ls /', completions=['/bin', '/lib', '/tmp', '/unix'])
      self.assertEqual(['ls', '/'], self.get_completions_arg)
      self.assertEqual(
          [('/bin', 'bin/'), ('/lib', 'lib/'), ('/tmp', 'tmp/'),
           ('/unix', 'unix')],
          [(c.text, c.display) for c in completions])

  def testCompletionUriPathMarkOneFile(self):
    completions = self.Choices(
        'uls ', completions=['gs://abc'])
    self.assertEqual(['uls', ''], self.get_completions_arg)
    self.assertEqual(
        [('gs://abc', 'gs://abc')],
        [(c.text, c.display) for c in completions])

  def testCompletionUriPathMarkOneDir(self):
    completions = self.Choices(
        'uls ', completions=['gs://abc/'])
    self.assertEqual(['uls', ''], self.get_completions_arg)
    self.assertEqual(
        [('gs://abc/', 'gs://abc/')],
        [(c.text, c.display) for c in completions])

  def testCompletionUriPathMarkManyDirs(self):
    completions = self.Choices(
        'uls gs://a', completions=['gs://abc/', 'gs://axyz/'])
    self.assertEqual(['uls', 'gs://a'], self.get_completions_arg)
    self.assertEqual(
        [('gs://abc', 'abc/'), ('gs://axyz', 'axyz/')],
        [(c.text, c.display) for c in completions])

  def testCompletionUriPathMarkManyDirsAndFiles(self):
    completions = self.Choices(
        'uls gs://a', completions=['gs://abc/', 'gs://ax'])
    self.assertEqual(['uls', 'gs://a'], self.get_completions_arg)
    self.assertEqual(
        [('gs://abc', 'abc/'), ('gs://ax', 'ax')],
        [(c.text, c.display) for c in completions])
