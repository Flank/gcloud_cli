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

from googlecloudsdk.command_lib.concepts import concept_managers
from tests.lib import calliope_test_base
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.command_lib.concepts import concepts_test_base
from tests.lib.command_lib.concepts import test_concepts


class FullParsingTests(concepts_test_base.ConceptArgsTestBase):

  def testParse(self):
    concept_manager = concept_managers.ConceptManager()
    concept_manager.AddConcept(self.string_concept)
    concept_manager.AddToParser(self.parser)
    args = self.parser.parser.parse_args(['--c', 'x'])
    args.CONCEPT_ARGS.ParseConcepts()
    self.assertEqual('x', args.c)

  def testParseCompoundConcepts(self):
    manager = concept_managers.ConceptManager()
    manager.AddConcept(test_concepts.FooBarArg(help_text='help 1'))
    manager.AddToParser(self.parser)
    args = self.parser.parser.parse_args(['--foo', 'x', '--bar', 'y'])
    args.CONCEPT_ARGS.ParseConcepts()
    self.assertEqual('x', args.foo_bar.foo)
    self.assertEqual('y', args.foo_bar.bar)

  def testParseTwoLayerCompoundConcepts(self):
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
