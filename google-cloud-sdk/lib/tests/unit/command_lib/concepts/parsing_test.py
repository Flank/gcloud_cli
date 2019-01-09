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
"""Tests for the concepts v2 library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope.concepts import deps as deps_lib
from googlecloudsdk.command_lib.concepts import concept_managers
from googlecloudsdk.command_lib.concepts import exceptions
from googlecloudsdk.command_lib.concepts.all_concepts import concepts
from tests.lib import calliope_test_base
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.command_lib.concepts import concepts_test_base
from tests.lib.command_lib.concepts import test_concepts


class ParsingTests(cli_test_base.CliTestBase,
                   concepts_test_base.ConceptArgsTestBase):

  def testParse(self):
    concept_manager = concept_managers.ConceptManager()
    concept_manager.AddConcept(self.string_concept)
    concept_manager.AddToParser(self.parser)
    args = self.parser.parser.parse_args(['--c', 'x'])
    args.CONCEPT_ARGS.ParseConcepts()
    self.assertEqual('x', args.c)

  def testParseFallback(self):
    manager = concept_managers.ConceptManager()
    manager.AddConcept(test_concepts.MakeFooBar('foo-bar', 'help 1'))
    manager.AddToParser(self.parser)
    args = self.parser.parser.parse_args(['--bar', 'y'])
    args.CONCEPT_ARGS.ParseConcepts()
    self.assertEqual('fake-project', args.foo_bar.foo)
    self.assertEqual('y', args.foo_bar.bar)

  def testParseRequiredMissing(self):
    foo = concepts.SimpleArg(name='foo', required=True, key='foo',
                             help_text='A foo')
    manager = concept_managers.ConceptManager()
    manager.AddConcept(foo)
    manager.AddToParser(self.parser)
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --foo: Must be specified'):
      args = self.parser.parser.parse_args()
      args.CONCEPT_ARGS.ParseConcepts()

  def testParseRequiredMissingWithFallback(self):
    foo = concepts.SimpleArg(name='foo', required=True, key='foo',
                             help_text='A foo',
                             fallthroughs=[deps_lib.ArgFallthrough('notfound')])
    manager = concept_managers.ConceptManager()
    manager.AddConcept(foo)
    manager.AddToParser(self.parser)
    with self.assertRaisesRegex(
        exceptions.MissingRequiredArgumentError, re.escape(
            'No value was provided for [--foo]: Failed to find attribute. '
            'The attribute can be set in the following ways: \n'
            '- provide the argument [--foo] on the command line\n'
            '- provide the argument [notfound] on the command line')):
      args = self.parser.parser.parse_args()
      args.CONCEPT_ARGS.ParseConcepts()

  def testParseGroupConcept(self):
    manager = concept_managers.ConceptManager()
    manager.AddConcept(test_concepts.MakeFooBar('foo-bar', 'help 1'))
    manager.AddToParser(self.parser)
    args = self.parser.parser.parse_args(['--foo', 'x', '--bar', 'y'])
    args.CONCEPT_ARGS.ParseConcepts()
    self.assertEqual('x', args.foo_bar.foo)
    self.assertEqual('y', args.foo_bar.bar)

  def testParseTwoLayerConceptGroup(self):
    manager = concept_managers.ConceptManager()
    manager.AddConcept(self.group_arg_concept)
    manager.AddToParser(self.parser)
    args = self.parser.parser.parse_args(['--first-foo', 'x',
                                          '--first-bar', 'y',
                                          '--second-foo', 'a',
                                          '--second-bar', 'b'])
    args.CONCEPT_ARGS.ParseConcepts()
    self.assertEqual('x', args.baz.first.foo)
    self.assertEqual('y', args.baz.first.bar)
    self.assertEqual('a', args.baz.second.foo)
    self.assertEqual('b', args.baz.second.bar)


class ModalGroupTests(cli_test_base.CliTestBase,
                      concepts_test_base.ConceptArgsTestBase):

  @staticmethod
  def MakeModalFooBar(name, help_text):
    """A modal group arg with two required and one optional attributes."""
    foo = concepts.SimpleArg(name='foo', required=True, key='foo',
                             help_text='A foo')
    bar = concepts.SimpleArg(name='bar', key='bar', help_text='A bar')
    baz = concepts.SimpleArg(name='baz', key='bar', required=True,
                             help_text='A bar')

    foobar = concepts.GroupArg(name, help_text=help_text)
    foobar.AddConcept(foo)
    foobar.AddConcept(bar)
    foobar.AddConcept(baz)
    return foobar

  @staticmethod
  def MakeModalFooBarWithInvalidFallthrough(name, help_text):
    """A modal group arg with an invalid fallthrough.

    Holds a required and an optional attribute.

    Args:
      name: str, name of the modal group.
      help_text: str, help text for the modal group.

    Returns:
      the modal group.
    """
    foo = concepts.SimpleArg(
        name='foo', required=True, key='foo',
        help_text='A foo',
        fallthroughs=[
            deps_lib.ArgFallthrough('notfound')
        ])
    bar = concepts.SimpleArg(name='bar', key='bar', help_text='A bar')

    foobar = concepts.GroupArg(name, help_text=help_text)
    foobar.AddConcept(foo)
    foobar.AddConcept(bar)
    return foobar

  def testParseModalGroupOnlyOptional(self):
    manager = concept_managers.ConceptManager()
    manager.AddConcept(self.MakeModalFooBar('foo-bar', 'help 1'))
    manager.AddToParser(self.parser)
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --bar: --baz --foo must be specified'):
      args = self.parser.parser.parse_args(['--bar', 'y'])
      args.CONCEPT_ARGS.ParseConcepts()

  def testParseModalGroupRequiredMissingWithOptional(self):
    manager = concept_managers.ConceptManager()
    manager.AddConcept(self.MakeModalFooBar('foo-bar', 'help 1'))
    manager.AddToParser(self.parser)
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        re.escape('argument [--foo : --bar]: --baz must be specified')):
      args = self.parser.parser.parse_args(['--foo', 'x', '--bar', 'y'])
      args.CONCEPT_ARGS.ParseConcepts()

  def testParseModalGroupRequiredMissingNoOptional(self):
    manager = concept_managers.ConceptManager()
    manager.AddConcept(self.MakeModalFooBar('foo-bar', 'help 1'))
    manager.AddToParser(self.parser)
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                'argument --foo: --baz must be specified'):
      args = self.parser.parser.parse_args(['--foo', 'x'])
      args.CONCEPT_ARGS.ParseConcepts()

  def testParseModalGroupNoneSpecified(self):
    manager = concept_managers.ConceptManager()
    manager.AddConcept(self.MakeModalFooBar('foo-bar', 'help 1'))
    manager.AddToParser(self.parser)
    args = self.parser.parser.parse_args()
    args.CONCEPT_ARGS.ParseConcepts()

  def testParseModalGroupAllRequiredOneSpecified(self):
    manager = concept_managers.ConceptManager()
    manager.AddConcept(self.MakeModalFooBar('foo-bar', 'help 1'))
    manager.AddToParser(self.parser)
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                'argument --foo: --baz must be specified'):
      args = self.parser.parser.parse_args(['--foo', 'x'])
      args.CONCEPT_ARGS.ParseConcepts()

  def testParseModalGroupAllRequiredAllSpecified(self):
    manager = concept_managers.ConceptManager()
    manager.AddConcept(self.MakeModalFooBar('foo-bar', 'help 1'))
    manager.AddToParser(self.parser)
    args = self.parser.parser.parse_args(['--foo', 'x', '--baz', 'z'])
    args.CONCEPT_ARGS.ParseConcepts()

  def testParseModalGroupWithInvalidFallthrough(self):
    manager = concept_managers.ConceptManager()
    manager.AddConcept(self.MakeModalFooBarWithInvalidFallthrough(
        'foo-bar', 'help 1'))
    manager.AddToParser(self.parser)
    with self.assertRaisesRegex(
        exceptions.ModalGroupError,
        re.escape('Failed to specify [foo-bar]: --bar: '
                  '--foo must be specified')):
      args = self.parser.parser.parse_args(['--bar', 'y'])
      args.CONCEPT_ARGS.ParseConcepts()


class MutexGroupTests(cli_test_base.CliTestBase,
                      concepts_test_base.ConceptArgsTestBase):

  @staticmethod
  def MakeMutexFooBar(name, help_text):
    """A mutex group arg with two attributes."""
    foo = concepts.SimpleArg(name='foo', key='foo', help_text='A foo')
    bar = concepts.SimpleArg(name='bar', key='bar', help_text='A bar')

    foobar = concepts.GroupArg(name, help_text=help_text, mutex=True)
    foobar.AddConcept(foo)
    foobar.AddConcept(bar)
    return foobar

  def testParseOptionalMutexGroup(self):
    foo = concepts.SimpleArg(name='foo', key='foo', help_text='A foo')
    bar = concepts.SimpleArg(name='bar', key='bar', help_text='A bar')
    foobar = concepts.GroupArg('foo-bar', help_text='help 1', mutex=True)
    foobar.AddConcept(foo)
    foobar.AddConcept(bar)

    manager = concept_managers.ConceptManager()
    manager.AddConcept(foobar)
    manager.AddToParser(self.parser)
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --bar: At most one of --bar | --foo may be specified.'):
      args = self.parser.parser.parse_args(['--foo', 'x', '--bar', 'y'])
      args.CONCEPT_ARGS.ParseConcepts()

  def testParseRequiredMutexGroup(self):
    foo = concepts.SimpleArg(name='foo', key='foo', help_text='A foo')
    bar = concepts.SimpleArg(name='bar', key='bar', help_text='A bar')
    foobar = concepts.GroupArg('foo-bar', required=True, help_text='help 1',
                               mutex=True)
    foobar.AddConcept(foo)
    foobar.AddConcept(bar)

    manager = concept_managers.ConceptManager()
    manager.AddConcept(foobar)
    manager.AddToParser(self.parser)
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        re.escape(
            'argument --bar: Exactly one of (--bar | --foo) must be specified.'
        )):
      args = self.parser.parser.parse_args(['--foo', 'x', '--bar', 'y'])
      args.CONCEPT_ARGS.ParseConcepts()

  def testParseOptionalMutexGroupFallthrough(self):
    foo = concepts.SimpleArg(name='foo', key='foo', help_text='A foo',
                             fallthroughs=[
                                 deps_lib.Fallthrough(lambda: 4, hint='none'),
                             ])
    bar = concepts.SimpleArg(name='bar', key='bar', help_text='A bar',
                             fallthroughs=[
                                 deps_lib.Fallthrough(lambda: 4, hint='none'),
                             ])
    foobar = concepts.GroupArg('foo-bar', help_text='help 1', mutex=True)
    foobar.AddConcept(foo)
    foobar.AddConcept(bar)

    manager = concept_managers.ConceptManager()
    manager.AddConcept(foobar)
    manager.AddToParser(self.parser)
    with self.assertRaisesRegex(
        exceptions.OptionalMutexGroupError,
        re.escape('Failed to specify [foo-bar]: '
                  'At most one of --foo | --bar may be specified.')):
      args = self.parser.parser.parse_args()
      args.CONCEPT_ARGS.ParseConcepts()

  def testParseRequiredMutexGroupFallthrough(self):
    foo = concepts.SimpleArg(name='foo', key='foo', help_text='A foo',
                             fallthroughs=[
                                 deps_lib.Fallthrough(lambda: 4, hint='none'),
                             ])
    bar = concepts.SimpleArg(name='bar', key='bar', help_text='A bar',
                             fallthroughs=[
                                 deps_lib.Fallthrough(lambda: 4, hint='none'),
                             ])
    foobar = concepts.GroupArg('foo-bar', required=True, help_text='help 1',
                               mutex=True)
    foobar.AddConcept(foo)
    foobar.AddConcept(bar)

    manager = concept_managers.ConceptManager()
    manager.AddConcept(foobar)
    manager.AddToParser(self.parser)
    with self.assertRaisesRegex(
        exceptions.RequiredMutexGroupError,
        re.escape('Failed to specify [foo-bar]: '
                  'Exactly one of (--foo | --bar) must be specified.')):
      args = self.parser.parser.parse_args()
      args.CONCEPT_ARGS.ParseConcepts()


class CLITest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.test_cli = self.LoadTestCli('sdk12')

  def testConceptManagerParsesDuringArgParse(self):
    return_value = self.test_cli.Execute(['sdk', 'concepts', '--a', 'x'])
    self.assertEqual('x', return_value)

  def testConceptManagerParsesEmpty(self):
    return_value = self.test_cli.Execute(['sdk', 'concepts'])
    self.assertEqual(None, return_value)

  def testConceptManagerParsesRequired(self):
    return_value = self.test_cli.Execute(['sdk', 'required', '--required',
                                          'value'])
    self.assertEqual('value', return_value)

  def testConceptManagerRequiredRaises(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.test_cli.Execute(['sdk', 'required'])


if __name__ == '__main__':
  test_case.main()
