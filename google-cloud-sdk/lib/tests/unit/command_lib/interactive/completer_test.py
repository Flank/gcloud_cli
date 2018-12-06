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
import time

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.interactive import application
from googlecloudsdk.command_lib.interactive import completer
from googlecloudsdk.command_lib.interactive import debug
from googlecloudsdk.command_lib.interactive import parser
from googlecloudsdk.command_lib.interactive.completer import Spinner
from googlecloudsdk.command_lib.meta import generate_cli_trees
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import resource_projector
from tests.lib import test_case
from tests.unit.command_lib.interactive import testdata

import mock


class MockCLI(object):

  def __init__(self):
    self.command_count = 0
    self.debug = debug.Debug()


class MockCompleter(object):

  def __init__(self):
    self.cli = MockCLI()
    self.debug = self.cli.debug


def MockDocument(text=''):
  doc = mock.MagicMock()
  doc.text_before_cursor = text
  doc.cursor_position = len(text)
  return doc


def MockEvent(requested=False):
  event = mock.MagicMock()
  event.completion_requested = requested
  return event


def Tuples(choices):
  return [(choice.text, choice.start_position) for choice in choices]


class SpinnerTest(test_case.WithOutputCapture):

  def MockSleep(self, secs):
    millisecs = int(secs * 1000.0)
    if millisecs == Spinner._TICKER_INTERVAL:
      self._spin_count -= 1
    if millisecs == Spinner._TICKER_WAIT_CHECK_INTERVAL:
      self._wait_count -= 1
    if self._wait_count <= 0 and self._spin_count <= 0:
      self._spinner._done_loading = True

  def SetUpSleep(self, secs):
    millisecs = int(secs * 1000.0)
    self._wait_count = (min(millisecs, Spinner._TICKER_WAIT) //
                        Spinner._TICKER_WAIT_CHECK_INTERVAL)
    millisecs -= Spinner._TICKER_WAIT
    self._spin_count = millisecs // Spinner._TICKER_INTERVAL
    self.StartObjectPatch(time, 'sleep', side_effect=self.MockSleep)

  def Wait(self):
    while not self._spinner._done_loading:
      pass

  @classmethod
  def SetUpClass(cls):
    pass

  def SetUp(self):
    self._spinner = None
    self.SetEncoding('utf8')
    self.spin_marks = (
        console_attr.GetConsoleAttr().GetProgressTrackerSymbols().spin_marks)

  def SetTestSpinner(self, spinner):
    self._spinner = spinner

  def testFastCompletionSpinner(self):
    time_to_sleep = 0.19
    self.SetUpSleep(time_to_sleep)
    with completer.Spinner(self.SetTestSpinner):
      self.Wait()
    self.AssertOutputContains(self.spin_marks[0], success=False)

  def testSlowCompletionSpinner(self):
    time_to_sleep = 2
    self.SetUpSleep(time_to_sleep)
    with completer.Spinner(self.SetTestSpinner):
      self.Wait()
    expected_output = ''
    for c in self.spin_marks:
      expected_output += c + '\b'
    self.AssertOutputContains(expected_output)

  def testMultipleSpinners(self):
    time_to_sleep = 0.5
    self.SetUpSleep(time_to_sleep)
    with completer.Spinner(self.SetTestSpinner):
      self.Wait()
    self.SetUpSleep(time_to_sleep)
    with completer.Spinner(self.SetTestSpinner):
      self.Wait()
    expected_output = ''
    for c in self.spin_marks[:3]:
      expected_output += c + '\b'
    expected_output += ' \b' + expected_output
    self.AssertOutputContains(expected_output)

  def testSpinnerState(self):
    time_to_sleep = 0.5
    self.SetUpSleep(time_to_sleep)
    with completer.Spinner(self.SetTestSpinner) as spinner:
      self.Wait()
      self.assertEqual(self._spinner, spinner)
    self.assertEqual(self._spinner, None)


class GetCompletionsTest(test_case.TestCase):

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
            'pre': {
                'commands': {},
                'flags': {
                    '--bar': {
                        'is_hidden': False,
                        'name': '--bar',
                        'type': 'bool',
                    },
                    '--foo': {
                        'is_hidden': False,
                        'name': '--foo',
                        'type': 'bool',
                    },
                    '--foobar': {
                        'is_hidden': False,
                        'name': '--foobar',
                        'type': 'bool',
                    },
                    '--foohidden': {
                        'is_hidden': True,
                        'name': '--foobar',
                        'type': 'bool',
                    },
                    '--val': {
                        'choices': ['abc', 'abcxyz'],
                        'is_hidden': False,
                        'name': '--val',
                        'type': 'string',
                    },
                    '--value': {
                        'choices': ['pdq', 'pdqzzz'],
                        'is_hidden': False,
                        'name': '--value',
                        'type': 'string',
                    },
                },
                'is_group': False,
                'positionals': [],
            },
            'prefix': {
                'commands': {},
                'is_group': False,
                'positionals': [],
            },
            'sub': {
                'commands': {
                    'foo': {
                        'commands': {},
                        'is_group': False,
                        'positionals': [],
                    },
                },
                'is_group': True,
                'positionals': [],
            },
            'subber': {
                'commands': {
                    'bar': {
                        'commands': {},
                        'is_group': False,
                        'positionals': [],
                    },
                },
                'is_group': True,
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
    application._AddCliTreeKeywordsAndBuiltins(cls.tree)  # pylint: disable=protected-access

  def SetUp(self):
    self.StartObjectPatch(
        generate_cli_trees.CliTreeGenerator,
        'MemoizeFailures',
        return_value=None)

  def Choices(self, text, completions=None, requested=False):
    coshell = mock.MagicMock()
    self.get_completions_arg = None
    self.get_completions_prefix = None

    def _GetCompletions(x, prefix=False):
      self.get_completions_arg = x
      self.get_completions_prefix = prefix
      return completions or []

    coshell.GetCompletions = _GetCompletions
    interactive_completer = completer.InteractiveCliCompleter(
        interactive_parser=parser.Parser(self.tree),
        coshell=coshell, debug=debug.Debug())
    interactive_completer.cli = MockCLI()
    return list(interactive_completer.get_completions(
        MockDocument(text), MockEvent(requested=requested)))

  def testCommandNameFirstArgGcloud(self):
    choices = self.Choices('g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandNameFirstExtension(self):
    # The space in 'foo.sh ' ensures that LoadOrGenerate is called.
    # No exception should be thrown in interactive mode because extensions
    # are allowed.
    choices = self.Choices('foo.sh ')
    self.assertEqual([], Tuples(choices))

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

  def testCommandAfterNot(self):
    choices = self.Choices('! g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandAfterOpenCurly(self):
    choices = self.Choices('{ g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandAfterDo(self):
    choices = self.Choices('do g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandAfterElif(self):
    choices = self.Choices('elif g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandAfterElse(self):
    choices = self.Choices('else g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandAfterIf(self):
    choices = self.Choices('if g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandAfterThen(self):
    choices = self.Choices('then g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandAfterTime(self):
    choices = self.Choices('time g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandAfterUntil(self):
    choices = self.Choices('until g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandAfterWhile(self):
    choices = self.Choices('while g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandAfterWhileNotTime(self):
    choices = self.Choices('while ! time g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandAfterIfKeyword(self):
    choices = self.Choices('if g')
    self.assertEqual([('gcloud', -1)], Tuples(choices))

  def testCommandAfterExport(self):
    choices = self.Choices('name=value g')
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

  def testCompletedTextStartPositionIsCorrectExplicitFlagPartialValue(self):
    choices = self.Choices(
        'gcloud alpha compute instances create --verbosity=w')
    self.assertEqual(
        [('warning', -1)],
        Tuples(choices))

  def testCompletedTextStartPositionIsCorrectImplicitFlagPartialValue(self):
    choices = self.Choices(
        'gcloud alpha compute instances create --verbosity w')
    self.assertEqual([('warning', -1)], Tuples(choices))

  def testCompletionPrefixCommandOne(self):
    completions = self.Choices('pref', completions=['pre', 'prefix'])
    self.assertEqual(
        [('prefix', 'prefix')],
        [(c.text, c.display) for c in completions])

  def testCompletionPrefixCommandTwo(self):
    completions = self.Choices('pre', completions=['pre', 'prefix'])
    self.assertEqual(
        [('pre', 'pre'), ('prefix', 'prefix')],
        [(c.text, c.display) for c in completions])

  def testCompletionPrefixBoolFlagPartial(self):
    completions = self.Choices('pre --f', completions=['--foo', '--foobar'])
    self.assertEqual(
        [('--foo', '--foo'), ('--foobar', '--foobar')],
        [(c.text, c.display) for c in completions])

  def testCompletionPrefixBoolFlagOne(self):
    completions = self.Choices('pre --foo', completions=['--foo', '--foobar'])
    self.assertEqual(
        [('--foo', '--foo'), ('--foobar', '--foobar')],
        [(c.text, c.display) for c in completions])

  def testCompletionPrefixStringFlagPartial(self):
    completions = self.Choices('pre --v', completions=['--val', '--value'])
    self.assertEqual(
        [('--val', '--val'), ('--value', '--value')],
        [(c.text, c.display) for c in completions])

  def testCompletionPrefixStringFlagOne(self):
    completions = self.Choices('pre --val', completions=['--foo', '--value'])
    self.assertEqual(
        [('--val', '--val'), ('--value', '--value')],
        [(c.text, c.display) for c in completions])

  def testCompletionPrefixStringFlagSpacePartialValue(self):
    completions = self.Choices('pre --val a', completions=['abc', 'abcxyz'])
    self.assertEqual(
        [('abc', 'abc'), ('abcxyz', 'abcxyz')],
        [(c.text, c.display) for c in completions])

  def testCompletionPrefixStringFlagEqualPartialValue(self):
    completions = self.Choices('pre --val=a', completions=['abc', 'abcxyz'])
    self.assertEqual(
        [('abc', 'abc'), ('abcxyz', 'abcxyz')],
        [(c.text, c.display) for c in completions])

  def testCompletionPrefixStringFlagEqualPrefixValue(self):
    completions = self.Choices('pre --val=abc', completions=['abc', 'abcxyz'])
    self.assertEqual(
        [('abc', 'abc'), ('abcxyz', 'abcxyz')],
        [(c.text, c.display) for c in completions])

  def testCompletionPrefixStringFlagEqualDisambiguatingValue(self):
    completions = self.Choices('pre --val=abcx', completions=['abcxyz'])
    self.assertEqual(
        [('abcxyz', 'abcxyz')],
        [(c.text, c.display) for c in completions])

  def testCompletionPrefixGroupTwo(self):
    completions = self.Choices('sub', completions=['sub', 'subber'])
    self.assertEqual(
        [('sub', 'sub'), ('subber', 'subber')],
        [(c.text, c.display) for c in completions])

  def testCompletionExactShortGroupCommand(self):
    completions = self.Choices('sub f', completions=['foo'])
    self.assertEqual(
        [('foo', 'foo')],
        [(c.text, c.display) for c in completions])

  def testCompletionExactLongGroupCommand(self):
    completions = self.Choices('subber b', completions=['bar'])
    self.assertEqual(
        [('bar', 'bar')],
        [(c.text, c.display) for c in completions])

  def testCompletionFallback(self):
    self.Choices('gcloud info ', requested=True)
    self.assertEqual(['gcloud', 'info', ''], self.get_completions_arg)

  def testCompletionFilePathMarkOneDir(self):
    completions = self.Choices(
        'ls /bi', completions=['/bin/'], requested=True)
    self.assertEqual(['ls', '/bi'], self.get_completions_arg)
    self.assertEqual(
        [('/bin/', 'bin/')],
        [(c.text, c.display) for c in completions])

  def testCompletionFilePathMarkManyDirsAndFiles(self):
    completions = self.Choices(
        'ls /',
        completions=['/bin/', '/lib/', '/tmp/', '/unix'],
        requested=True)
    self.assertEqual(['ls', '/'], self.get_completions_arg)
    self.assertEqual(
        [('/bin', 'bin/'), ('/lib', 'lib/'), ('/tmp', 'tmp/'),
         ('/unix', 'unix')],
        [(c.text, c.display) for c in completions])

  def testCompletionUriPathMarkOneFile(self):
    completions = self.Choices(
        'uls ', completions=['gs://abc'], requested=True)
    self.assertEqual(['uls', ''], self.get_completions_arg)
    self.assertEqual(
        [('gs://abc', 'abc')],
        [(c.text, c.display) for c in completions])

  def testCompletionUriPathMarkOneDir(self):
    completions = self.Choices(
        'uls ', completions=['gs://abc/'], requested=True)
    self.assertEqual(['uls', ''], self.get_completions_arg)
    self.assertEqual(
        [('gs://abc/', 'abc/')],
        [(c.text, c.display) for c in completions])

  def testCompletionUriPathMarkManyDirs(self):
    completions = self.Choices(
        'uls gs://a', completions=['gs://abc/', 'gs://ace/'], requested=True)
    self.assertEqual(['uls', 'gs://a'], self.get_completions_arg)
    self.assertEqual(
        [('gs://abc', 'abc/'), ('gs://ace', 'ace/')],
        [(c.text, c.display) for c in completions])

  def testCompletionUriPathMarkManyDirsAndFiles(self):
    completions = self.Choices(
        'uls gs://a', completions=['gs://abc/', 'gs://ac'], requested=True)
    self.assertEqual(['uls', 'gs://a'], self.get_completions_arg)
    self.assertEqual(
        [('gs://abc', 'abc/'), ('gs://ac', 'ac')],
        [(c.text, c.display) for c in completions])


class ExecutableCompletionTest(test_case.TestCase):

  def MockCommandCompleter(self, args):
    self.called.append('command')
    return None, 0

  def MockFlagCompleter(self, args):
    self.called.append('flag')
    return None, 0

  def MockPositionalCompleter(self, args):
    self.called.append('positional')
    return None, 0

  def MockInteractiveCompleter(self, args):
    self.called.append('interactive')
    return None, 0

  def SetUp(self):
    self.StartObjectPatch(
        generate_cli_trees.CliTreeGenerator,
        'MemoizeFailures',
        return_value=None)
    self.called = []
    self.StartObjectPatch(
        completer.InteractiveCliCompleter,
        'CommandCompleter',
        side_effect=self.MockCommandCompleter)
    self.StartObjectPatch(
        completer.InteractiveCliCompleter,
        'FlagCompleter',
        side_effect=self.MockFlagCompleter)
    self.StartObjectPatch(
        completer.InteractiveCliCompleter,
        'PositionalCompleter',
        side_effect=self.MockPositionalCompleter)
    self.StartObjectPatch(
        completer.InteractiveCliCompleter,
        'InteractiveCompleter',
        side_effect=self.MockInteractiveCompleter)
    self.completer = completer.InteractiveCliCompleter(
        interactive_parser=parser.Parser({'commands': {}, 'positionals': []}),
        coshell=mock.MagicMock(), debug=debug.Debug())
    self.completer.cli = MockCLI()

  def GetCompletions(self, text='', requested=False):
    list(self.completer.get_completions(
        MockDocument(text), MockEvent(requested)))

  def testTabs_000(self):
    self.GetCompletions(text='', requested=False)
    self.assertEqual([], self.called)
    self.GetCompletions(text='a', requested=False)
    self.assertEqual(['command', 'flag', 'positional', 'interactive'],
                     self.called)
    self.GetCompletions(text='z', requested=False)
    self.assertEqual(['command', 'flag', 'positional', 'interactive',
                      'command', 'flag', 'positional', 'interactive'],
                     self.called)

  def testTabs_001(self):
    self.GetCompletions(text='', requested=False)
    self.assertEqual([], self.called)
    self.GetCompletions(text='a', requested=False)
    self.assertEqual(['command', 'flag', 'positional', 'interactive'],
                     self.called)
    self.GetCompletions(text='z', requested=True)
    self.assertEqual(['command', 'flag', 'positional', 'interactive',
                      'interactive'],
                     self.called)

  def testTabs_010(self):
    self.GetCompletions(text='', requested=False)
    self.assertEqual([], self.called)
    self.GetCompletions(text='a', requested=True)
    self.assertEqual(['interactive'], self.called)
    self.GetCompletions(text='z', requested=False)
    self.assertEqual(['interactive',
                      'command', 'flag', 'positional', 'interactive'],
                     self.called)

  def testTabs_011(self):
    self.GetCompletions(text='', requested=False)
    self.assertEqual([], self.called)
    self.GetCompletions(text='a', requested=True)
    self.assertEqual(['interactive'], self.called)
    self.GetCompletions(text='z', requested=True)
    self.assertEqual(['interactive', 'interactive'], self.called)

  def testTabs_100(self):
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.GetCompletions(text='a', requested=False)
    self.assertEqual(['interactive'], self.called)
    self.GetCompletions(text='z', requested=False)
    self.assertEqual(['interactive', 'interactive'], self.called)

  def testTabs_101(self):
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.GetCompletions(text='a', requested=False)
    self.assertEqual(['interactive'], self.called)
    self.GetCompletions(text='z', requested=True)
    self.assertEqual(['interactive', 'interactive'], self.called)

  def testTabs_110(self):
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.GetCompletions(text='a', requested=True)
    self.assertEqual(['interactive'], self.called)
    self.GetCompletions(text='z', requested=False)
    self.assertEqual(['interactive', 'interactive'], self.called)

  def testTabs_111(self):
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.GetCompletions(text='a', requested=True)
    self.assertEqual(['interactive'], self.called)
    self.GetCompletions(text='z', requested=True)
    self.assertEqual(['interactive', 'interactive'], self.called)

  def testTabs_200(self):
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.GetCompletions(text='a', requested=False)
    self.assertEqual(['command', 'flag', 'positional', 'interactive'],
                     self.called)
    self.GetCompletions(text='z', requested=False)
    self.assertEqual(['command', 'flag', 'positional', 'interactive',
                      'command', 'flag', 'positional', 'interactive'],
                     self.called)

  def testTabs_201(self):
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.GetCompletions(text='a', requested=False)
    self.assertEqual(['command', 'flag', 'positional', 'interactive'],
                     self.called)
    self.GetCompletions(text='z', requested=True)
    self.assertEqual(['command', 'flag', 'positional', 'interactive',
                      'interactive'],
                     self.called)

  def testTabs_210(self):
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.GetCompletions(text='a', requested=True)
    self.assertEqual(['interactive'], self.called)
    self.GetCompletions(text='z', requested=False)
    self.assertEqual(['interactive',
                      'command', 'flag', 'positional', 'interactive'],
                     self.called)

  def testTabs_211(self):
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.GetCompletions(text='a', requested=True)
    self.assertEqual(['interactive'], self.called)
    self.GetCompletions(text='az', requested=True)
    self.assertEqual(['interactive', 'interactive'], self.called)

  def testTabsReset_00(self):
    self.GetCompletions(text='', requested=False)
    self.assertEqual([], self.called)
    self.completer.reset()
    self.GetCompletions(text='a', requested=False)
    self.assertEqual(['command', 'flag', 'positional', 'interactive'],
                     self.called)

  def testTabsReset_01(self):
    self.GetCompletions(text='', requested=False)
    self.assertEqual([], self.called)
    self.completer.reset()
    self.GetCompletions(text='a', requested=True)
    self.assertEqual(['interactive'], self.called)

  def testTabsReset_10(self):
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.completer.reset()
    self.GetCompletions(text='a', requested=False)
    self.assertEqual(['command', 'flag', 'positional', 'interactive'],
                     self.called)

  def testTabsReset_11(self):
    self.GetCompletions(text='', requested=True)
    self.assertEqual([], self.called)
    self.completer.reset()
    self.GetCompletions(text='a', requested=True)
    self.assertEqual(['interactive'], self.called)


class InteractiveCompletionCacheTest(test_case.TestCase):

  def SetUp(self):
    self.maxDiff = None  # pylint:disable=invalid-name

  def MakeArgs(self, args=None):
    """Make a completer args list from a list of arg strings."""
    return [parser.ArgToken(a) for a in args or []]

  def testEmptyCacheLookup(self):
    cache = completer.CompletionCache(MockCompleter())
    self.assertIsNone(cache.Lookup(self.MakeArgs()))
    self.assertIsNone(cache.Lookup(self.MakeArgs(['ls'])))
    self.assertIsNone(cache.Lookup(self.MakeArgs(['ls', ''])))

  def testCompletionSequenceCacheLookup(self):
    cache = completer.CompletionCache(MockCompleter())
    # First arg 'ls' completion.
    cache.Update(self.MakeArgs(['ls']), ['ls'])
    self.assertIsNone(cache.Lookup(self.MakeArgs()))
    self.assertEqual(['ls'], cache.Lookup(self.MakeArgs(['ls'])))
    self.assertIsNone(cache.Lookup(self.MakeArgs(['ls', ''])))
    # Second arg completion.
    cache.Update(self.MakeArgs(['ls', '']), ['abc', 'xyz'])
    self.assertEqual(['abc', 'xyz'], cache.Lookup(self.MakeArgs(['ls', ''])))
    self.assertEqual(['abc'], cache.Lookup(self.MakeArgs(['ls', 'a'])))
    self.assertEqual(['xyz'], cache.Lookup(self.MakeArgs(['ls', 'x'])))
    # First arg 'grep' completion.
    cache.Update(self.MakeArgs(['grep']), ['grep'])
    self.assertEqual(['grep'], cache.Lookup(self.MakeArgs(['grep'])))
    self.assertIsNone(cache.Lookup(self.MakeArgs(['ls'])))
    # First arg 'ls' completion. Second arg cache should be dirty.
    cache.Update(self.MakeArgs(['ls']), ['ls'])
    self.assertEqual(['ls'], cache.Lookup(self.MakeArgs(['ls'])))
    self.assertIsNone(cache.Lookup(self.MakeArgs(['ls', ''])))
    # New second arg completion.
    cache.Update(self.MakeArgs(['ls', '']), ['abc', 'xyz'])
    self.assertEqual(['abc', 'xyz'], cache.Lookup(self.MakeArgs(['ls', ''])))
    self.assertEqual(['abc'], cache.Lookup(self.MakeArgs(['ls', 'a'])))
    self.assertEqual(['xyz'], cache.Lookup(self.MakeArgs(['ls', 'x'])))
    # Third arg completion.
    cache.Update(self.MakeArgs(['ls', 'abc', '']), ['etc', 'pdq'])
    self.assertEqual(['etc'], cache.Lookup(self.MakeArgs(['ls', 'abc', 'e'])))
    # Old second arg completion should be clean.
    self.assertEqual(['xyz'], cache.Lookup(self.MakeArgs(['ls', 'x'])))
    # Third arg completion should still be clean.
    self.assertEqual(['pdq'], cache.Lookup(self.MakeArgs(['ls', 'abc', 'p'])))
    # Executing the command should invalidate the cache.
    cache.completer.cli.command_count += 1
    self.assertIsNone(cache.Lookup(self.MakeArgs(['ls', 'abc', 'p'])))

  def testCompletionSequenceWithDirsCacheLookup(self):
    cache = completer.CompletionCache(MockCompleter())

    # First arg completion.

    self.assertEqual(
        [],
        resource_projector.MakeSerializable(cache.args))

    cache.Update(
        self.MakeArgs(['']),
        ['df', 'ls', 'wc'])

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['df', 'ls', 'wc'],
        cache.Lookup(self.MakeArgs([''])))
    self.assertEqual(
        ['ls'],
        cache.Lookup(self.MakeArgs(['l'])))
    self.assertEqual(
        ['ls'],
        cache.Lookup(self.MakeArgs(['ls'])))
    self.assertEqual(
        None,
        cache.Lookup(self.MakeArgs(['ls', ''])))

    # Second arg first dir completion.

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    cache.Update(
        self.MakeArgs(['ls', '']),
        ['abc/', 'ace', 'xyz/'])

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': '',
                'completions': ['abc/', 'ace', 'xyz/'],
                'dirs': {},
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['abc/', 'ace', 'xyz/'],
        cache.Lookup(self.MakeArgs(['ls', ''])))
    self.assertEqual(
        ['abc/', 'ace'],
        cache.Lookup(self.MakeArgs(['ls', 'a'])))
    self.assertEqual(
        ['abc/', 'ace'],
        cache.Lookup(self.MakeArgs(['ls', 'a'])))
    self.assertEqual(
        ['xyz/'],
        cache.Lookup(self.MakeArgs(['ls', 'x'])))
    self.assertEqual(
        [],
        cache.Lookup(self.MakeArgs(['ls', 'z'])))
    self.assertEqual(
        ['ace'],
        cache.Lookup(self.MakeArgs(['ls', 'ac'])))
    self.assertEqual(
        ['abc/'],
        cache.Lookup(self.MakeArgs(['ls', 'abc'])))

    # Second arg second dir completion.

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': '',
                'completions': ['abc/', 'ace', 'xyz/'],
                'dirs': {},
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        None,
        cache.Lookup(self.MakeArgs(['ls', 'abc/'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': '',
                'completions': ['abc/', 'ace', 'xyz/'],
                'dirs': {},
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    cache.Update(
        self.MakeArgs(['ls', 'abc/']),
        ['abc/etc/', 'abc/exp/', 'abc/log'])

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': 'abc/',
                'completions': ['abc/etc/', 'abc/exp/', 'abc/log'],
                'dirs': {
                    '': ['', ['abc/', 'ace', 'xyz/']],
                    'abc': ['abc/', ['abc/etc/', 'abc/exp/', 'abc/log']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['abc/etc/', 'abc/exp/', 'abc/log'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': 'abc/',
                'completions': ['abc/etc/', 'abc/exp/', 'abc/log'],
                'dirs': {
                    '': ['', ['abc/', 'ace', 'xyz/']],
                    'abc': ['abc/', ['abc/etc/', 'abc/exp/', 'abc/log']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['abc/etc/', 'abc/exp/'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/e'])))
    self.assertEqual(
        ['abc/log'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/l'])))
    self.assertEqual(
        [],
        cache.Lookup(self.MakeArgs(['ls', 'abc/z'])))
    self.assertEqual(
        ['abc/exp/'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/ex'])))
    self.assertEqual(
        ['abc/exp/'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/exp'])))
    self.assertEqual(
        [],
        cache.Lookup(self.MakeArgs(['ls', 'abc/exz'])))
    self.assertEqual(
        ['abc/exp/'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/exp'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': 'abc/',
                'completions': ['abc/etc/', 'abc/exp/', 'abc/log'],
                'dirs': {
                    '': ['', ['abc/', 'ace', 'xyz/']],
                    'abc': ['abc/', ['abc/etc/', 'abc/exp/', 'abc/log']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        None,
        cache.Lookup(self.MakeArgs(['ls', 'abc/exp/'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': 'abc/',
                'completions': ['abc/etc/', 'abc/exp/', 'abc/log'],
                'dirs': {
                    '': ['', ['abc/', 'ace', 'xyz/']],
                    'abc': ['abc/', ['abc/etc/', 'abc/exp/', 'abc/log']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    cache.Update(
        self.MakeArgs(['ls', 'abc/exp/']),
        ['abc/exp/ascii', 'abc/exp/Ṳᾔḯ¢◎ⅾℯ'])

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': 'abc/exp/',
                'completions': ['abc/exp/ascii', 'abc/exp/Ṳᾔḯ¢◎ⅾℯ'],
                'dirs': {
                    '': ['', ['abc/', 'ace', 'xyz/']],
                    'abc': ['abc/', ['abc/etc/', 'abc/exp/', 'abc/log']],
                    'abc/exp': ['abc/exp/',
                                ['abc/exp/ascii', 'abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['abc/exp/ascii', 'abc/exp/Ṳᾔḯ¢◎ⅾℯ'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/exp/'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': 'abc/exp/',
                'completions': ['abc/exp/ascii', 'abc/exp/Ṳᾔḯ¢◎ⅾℯ'],
                'dirs': {
                    '': ['', ['abc/', 'ace', 'xyz/']],
                    'abc': ['abc/', ['abc/etc/', 'abc/exp/', 'abc/log']],
                    'abc/exp': ['abc/exp/',
                                ['abc/exp/ascii', 'abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['abc/exp/'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/exp'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': 'abc/',
                'completions': ['abc/etc/', 'abc/exp/', 'abc/log'],
                'dirs': {
                    '': ['', ['abc/', 'ace', 'xyz/']],
                    'abc': ['abc/', ['abc/etc/', 'abc/exp/', 'abc/log']],
                    'abc/exp': ['abc/exp/',
                                ['abc/exp/ascii', 'abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['abc/exp/'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/ex'])))
    self.assertEqual(
        ['abc/etc/', 'abc/exp/'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/e'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': 'abc/',
                'completions': ['abc/etc/', 'abc/exp/', 'abc/log'],
                'dirs': {
                    '': ['', ['abc/', 'ace', 'xyz/']],
                    'abc': ['abc/', ['abc/etc/', 'abc/exp/', 'abc/log']],
                    'abc/exp': ['abc/exp/',
                                ['abc/exp/ascii', 'abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['abc/etc/', 'abc/exp/', 'abc/log'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': 'abc/',
                'completions': ['abc/etc/', 'abc/exp/', 'abc/log'],
                'dirs': {
                    '': ['', ['abc/', 'ace', 'xyz/']],
                    'abc': ['abc/', ['abc/etc/', 'abc/exp/', 'abc/log']],
                    'abc/exp': ['abc/exp/',
                                ['abc/exp/ascii', 'abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['abc/etc/'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/etc'])))

    self.assertEqual(
        None,
        cache.Lookup(self.MakeArgs(['ls', 'abc/etc/'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': 'abc/',
                'completions': ['abc/etc/', 'abc/exp/', 'abc/log'],
                'dirs': {
                    '': ['', ['abc/', 'ace', 'xyz/']],
                    'abc': ['abc/', ['abc/etc/', 'abc/exp/', 'abc/log']],
                    'abc/exp': ['abc/exp/',
                                ['abc/exp/ascii', 'abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    cache.Update(
        self.MakeArgs(['ls', 'abc/etc/']),
        ['abc/etc/data'])

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': 'abc/etc/',
                'completions': ['abc/etc/data'],
                'dirs': {
                    '': ['', ['abc/', 'ace', 'xyz/']],
                    'abc': ['abc/', ['abc/etc/', 'abc/exp/', 'abc/log']],
                    'abc/etc': ['abc/etc/', ['abc/etc/data']],
                    'abc/exp': ['abc/exp/',
                                ['abc/exp/ascii', 'abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['abc/etc/data'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/etc/'])))

    self.assertEqual(
        ['abc/etc/', 'abc/exp/', 'abc/log'],
        cache.Lookup(self.MakeArgs(['ls', 'abc/'])))

    self.assertEqual(
        ['abc/'],
        cache.Lookup(self.MakeArgs(['ls', 'abc'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': '',
                'completions': ['abc/', 'ace', 'xyz/'],
                'dirs': {
                    '': ['', ['abc/', 'ace', 'xyz/']],
                    'abc': ['abc/', ['abc/etc/', 'abc/exp/', 'abc/log']],
                    'abc/etc': ['abc/etc/', ['abc/etc/data']],
                    'abc/exp': ['abc/exp/',
                                ['abc/exp/ascii', 'abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['ace'],
        cache.Lookup(self.MakeArgs(['ls', 'ac'])))
    self.assertEqual(
        [],
        cache.Lookup(self.MakeArgs(['ls', 'z'])))
    self.assertEqual(
        ['xyz/'],
        cache.Lookup(self.MakeArgs(['ls', 'x'])))
    self.assertEqual(
        ['abc/', 'ace'],
        cache.Lookup(self.MakeArgs(['ls', 'a'])))
    self.assertEqual(
        ['abc/', 'ace'],
        cache.Lookup(self.MakeArgs(['ls', 'a'])))
    self.assertEqual(
        ['abc/', 'ace', 'xyz/'],
        cache.Lookup(self.MakeArgs(['ls', ''])))
    self.assertEqual(
        ['ls'],
        cache.Lookup(self.MakeArgs(['ls'])))
    self.assertEqual(
        ['ls'],
        cache.Lookup(self.MakeArgs(['l'])))
    self.assertEqual(
        ['df', 'ls', 'wc'],
        cache.Lookup(self.MakeArgs([''])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['df', 'ls', 'wc'],
                'dirs': {},
            },
            {
                'prefix': '',
                'completions': ['abc/', 'ace', 'xyz/'],
                'dirs': {
                    '': ['', ['abc/', 'ace', 'xyz/']],
                    'abc': ['abc/', ['abc/etc/', 'abc/exp/', 'abc/log']],
                    'abc/etc': ['abc/etc/', ['abc/etc/data']],
                    'abc/exp': ['abc/exp/',
                                ['abc/exp/ascii', 'abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

  def testCompletionSequenceWithUriDirsCacheLookup(self):
    cache = completer.CompletionCache(MockCompleter())

    # First arg completion.

    self.assertEqual(
        [],
        resource_projector.MakeSerializable(cache.args))

    cache.Update(
        self.MakeArgs(['']),
        ['uls'])

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['uls'],
        cache.Lookup(self.MakeArgs([''])))
    self.assertEqual(
        ['uls'],
        cache.Lookup(self.MakeArgs(['u'])))
    self.assertEqual(
        ['uls'],
        cache.Lookup(self.MakeArgs(['ul'])))
    self.assertEqual(
        ['uls'],
        cache.Lookup(self.MakeArgs(['uls'])))
    self.assertEqual(
        None,
        cache.Lookup(self.MakeArgs(['uls', ''])))

    # Second arg first dir completion.

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    cache.Update(
        self.MakeArgs(['uls', '']),
        ['gs://'])

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': '',
                'completions': ['gs://'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    cache.Update(
        self.MakeArgs(['uls', 'gs://']),
        ['gs://abc/', 'gs://ace', 'gs://xyz/'])

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://',
                'completions': ['gs://abc/', 'gs://ace', 'gs://xyz/'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['gs:'],
        cache.Lookup(self.MakeArgs(['uls', ''])))
    self.assertEqual(
        ['gs:'],
        cache.Lookup(self.MakeArgs(['uls', 'g'])))
    self.assertEqual(
        ['gs:'],
        cache.Lookup(self.MakeArgs(['uls', 'gs'])))
    self.assertEqual(
        ['gs:'],  # ['gs:/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs:'])))
    self.assertEqual(
        ['gs://'],  # ['gs:/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs:/'])))
    self.assertEqual(
        ['gs://abc/', 'gs://ace', 'gs://xyz/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://'])))
    self.assertEqual(
        ['gs://abc/', 'gs://ace'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://a'])))
    self.assertEqual(
        ['gs://abc/', 'gs://ace'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://a'])))
    self.assertEqual(
        ['gs://xyz/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://x'])))
    self.assertEqual(
        [],
        cache.Lookup(self.MakeArgs(['uls', 'gs://z'])))
    self.assertEqual(
        ['gs://ace'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://ac'])))
    self.assertEqual(
        ['gs://abc/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc'])))

    # Second arg second dir completion.

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://',
                'completions': ['gs://abc/', 'gs://ace', 'gs://xyz/'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        None,
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://',
                'completions': ['gs://abc/', 'gs://ace', 'gs://xyz/'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    cache.Update(
        self.MakeArgs(['uls', 'gs://abc/']),
        ['gs://abc/etc/', 'gs://abc/exp/', 'gs://abc/log'])

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://abc/',
                'completions': ['gs://abc/etc/', 'gs://abc/exp/',
                                'gs://abc/log'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['gs://abc/etc/', 'gs://abc/exp/', 'gs://abc/log'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://abc/',
                'completions': ['gs://abc/etc/', 'gs://abc/exp/',
                                'gs://abc/log'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['gs://abc/etc/', 'gs://abc/exp/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/e'])))
    self.assertEqual(
        ['gs://abc/log'],
        cache.Lookup(self.MakeArgs(['gs://uls', 'gs://abc/l'])))
    self.assertEqual(
        [],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/z'])))
    self.assertEqual(
        ['gs://abc/exp/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/ex'])))
    self.assertEqual(
        ['gs://abc/exp/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/exp'])))
    self.assertEqual(
        [],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/exz'])))
    self.assertEqual(
        ['gs://abc/exp/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/exp'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://abc/',
                'completions': ['gs://abc/etc/', 'gs://abc/exp/',
                                'gs://abc/log'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        None,
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/exp/'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://abc/',
                'completions': ['gs://abc/etc/', 'gs://abc/exp/',
                                'gs://abc/log'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    cache.Update(
        self.MakeArgs(['uls', 'gs://abc/exp/']),
        ['gs://abc/exp/ascii', 'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ'])

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://abc/exp/',
                'completions': ['gs://abc/exp/ascii', 'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                    'gs://abc/exp': ['gs://abc/exp/', ['gs://abc/exp/ascii',
                                                       'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['gs://abc/exp/ascii', 'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/exp/'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://abc/exp/',
                'completions': ['gs://abc/exp/ascii', 'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                    'gs://abc/exp': ['gs://abc/exp/', ['gs://abc/exp/ascii',
                                                       'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['gs://abc/exp/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/exp'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://abc/',
                'completions': ['gs://abc/etc/',
                                'gs://abc/exp/',
                                'gs://abc/log'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                    'gs://abc/exp': ['gs://abc/exp/', ['gs://abc/exp/ascii',
                                                       'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['gs://abc/exp/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/ex'])))
    self.assertEqual(
        ['gs://abc/etc/', 'gs://abc/exp/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/e'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://abc/',
                'completions': ['gs://abc/etc/',
                                'gs://abc/exp/',
                                'gs://abc/log'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                    'gs://abc/exp': ['gs://abc/exp/', ['gs://abc/exp/ascii',
                                                       'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['gs://abc/etc/', 'gs://abc/exp/', 'gs://abc/log'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://abc/',
                'completions': ['gs://abc/etc/',
                                'gs://abc/exp/',
                                'gs://abc/log'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                    'gs://abc/exp': ['gs://abc/exp/', ['gs://abc/exp/ascii',
                                                       'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['gs://abc/etc/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/etc'])))

    self.assertEqual(
        None,
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/etc/'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://abc/',
                'completions': ['gs://abc/etc/',
                                'gs://abc/exp/',
                                'gs://abc/log'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                    'gs://abc/exp': ['gs://abc/exp/', ['gs://abc/exp/ascii',
                                                       'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    cache.Update(
        self.MakeArgs(['uls', 'gs://abc/etc/']),
        ['gs://abc/etc/data'])

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://abc/etc/',
                'completions': ['gs://abc/etc/data'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                    'gs://abc/etc': ['gs://abc/etc/', ['gs://abc/etc/data']],
                    'gs://abc/exp': ['gs://abc/exp/', ['gs://abc/exp/ascii',
                                                       'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['gs://abc/etc/data'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/etc/'])))

    self.assertEqual(
        ['gs://abc/etc/', 'gs://abc/exp/', 'gs://abc/log'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc/'])))

    self.assertEqual(
        ['gs://abc/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://abc'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://',
                'completions': ['gs://abc/', 'gs://ace', 'gs://xyz/'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                    'gs://abc/etc': ['gs://abc/etc/', ['gs://abc/etc/data']],
                    'gs://abc/exp': ['gs://abc/exp/', ['gs://abc/exp/ascii',
                                                       'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['gs://ace'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://ac'])))
    self.assertEqual(
        [],
        cache.Lookup(self.MakeArgs(['uls', 'gs://z'])))
    self.assertEqual(
        ['gs://xyz/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://x'])))
    self.assertEqual(
        ['gs://abc/', 'gs://ace'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://a'])))
    self.assertEqual(
        ['gs://abc/', 'gs://ace'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://a'])))
    self.assertEqual(
        ['gs://abc/', 'gs://ace', 'gs://xyz/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://'])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': 'gs://',
                'completions': [u'gs://abc/', u'gs://ace', u'gs://xyz/'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                    'gs://abc/etc': ['gs://abc/etc/', ['gs://abc/etc/data']],
                    'gs://abc/exp': ['gs://abc/exp/', ['gs://abc/exp/ascii',
                                                       'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['gs:'],
        cache.Lookup(self.MakeArgs(['uls', ''])))
    self.assertEqual(
        ['uls'],
        cache.Lookup(self.MakeArgs(['uls'])))
    self.assertEqual(
        ['uls'],
        cache.Lookup(self.MakeArgs(['u'])))
    self.assertEqual(
        ['uls'],
        cache.Lookup(self.MakeArgs([''])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': '',
                'completions': ['gs:'],
                'dirs': {
                    '': ['', ['gs:']],
                    'gs:': ['gs:', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                    'gs://abc': ['gs://abc/', ['gs://abc/etc/',
                                               'gs://abc/exp/',
                                               'gs://abc/log']],
                    'gs://abc/etc': ['gs://abc/etc/', ['gs://abc/etc/data']],
                    'gs://abc/exp': ['gs://abc/exp/', ['gs://abc/exp/ascii',
                                                       'gs://abc/exp/Ṳᾔḯ¢◎ⅾℯ']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

  def testCompletionSequenceWithUriDirsCacheLookupBackSpace(self):
    cache = completer.CompletionCache(MockCompleter())

    # First arg completion.

    self.assertEqual(
        [],
        resource_projector.MakeSerializable(cache.args))

    cache.Update(
        self.MakeArgs(['']),
        ['uls'])

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['uls'],
        cache.Lookup(self.MakeArgs([''])))
    self.assertEqual(
        ['uls'],
        cache.Lookup(self.MakeArgs(['u'])))
    self.assertEqual(
        ['uls'],
        cache.Lookup(self.MakeArgs(['ul'])))
    self.assertEqual(
        ['uls'],
        cache.Lookup(self.MakeArgs(['uls'])))

    # Second arg first dir completion.

    self.assertEqual(
        None,
        cache.Lookup(self.MakeArgs(['uls', ''])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    cache.Update(
        self.MakeArgs(['uls', '']),
        ['gs://abc/', 'gs://ace', 'gs://xyz/'])

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': '',
                'completions': ['gs://abc/', 'gs://ace', 'gs://xyz/'],
                'dirs': {
                    '': ['', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))

    self.assertEqual(
        ['gs://'],
        cache.Lookup(self.MakeArgs(['uls', ''])))
    self.assertEqual(
        ['gs://abc/', 'gs://ace', 'gs://xyz/'],
        cache.Lookup(self.MakeArgs(['uls', 'gs://'])))
    self.assertEqual(
        None,
        cache.Lookup(self.MakeArgs(['uls', 'gs:/'])))
    self.assertEqual(
        None,
        cache.Lookup(self.MakeArgs(['uls', 'gs:'])))
    self.assertEqual(
        None,
        cache.Lookup(self.MakeArgs(['uls', 'gs'])))
    self.assertEqual(
        None,
        cache.Lookup(self.MakeArgs(['uls', 'g'])))
    self.assertEqual(
        ['gs://'],
        cache.Lookup(self.MakeArgs(['uls', ''])))

    self.assertEqual(
        [
            {
                'prefix': '',
                'completions': ['uls'],
                'dirs': {},
            },
            {
                'prefix': '',
                'completions': ['gs://'],
                'dirs': {
                    '': ['', ['gs://']],
                    'gs:/': ['gs://', ['gs://abc/', 'gs://ace', 'gs://xyz/']],
                },
            },
        ],
        resource_projector.MakeSerializable(cache.args))
