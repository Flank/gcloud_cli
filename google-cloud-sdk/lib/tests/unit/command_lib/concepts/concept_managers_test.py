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
from googlecloudsdk.command_lib.concepts import dependency_managers
from tests.lib import test_case
from tests.lib.command_lib.concepts import concepts_test_base
from tests.lib.command_lib.concepts import test_concepts
from tests.lib.core import core_completer_test_base

import mock


class ConceptManagerTest(concepts_test_base.ConceptArgsTestBase):

  def testAddConcept(self):
    manager = concept_managers.ConceptManager()
    manager.AddConcept(self.string_concept)
    self.assertEqual([self.string_concept], manager.concepts)

  def testAddToParserRaises(self):
    manager = concept_managers.ConceptManager()
    manager.AddConcept(self.string_concept)
    # The presentation name of two top level concepts can't be equivalent.
    manager.AddConcept(test_concepts.FooBarArg(name='c',
                                               help_text='help'))
    with self.assertRaisesRegex(ValueError, 'c'):
      manager.AddToParser(self.parser)

  def testAddToParser(self):
    manager = concept_managers.ConceptManager()
    manager.AddToParser(self.parser)
    self.assertEqual(manager.runtime_parser, self.parser.concepts)

  def testAddToArgparse(self):
    parser = mock.Mock()
    parser.add_argument_group.return_value = parser
    manager = concept_managers.ConceptManager()
    manager.AddConcept(self.group_arg_concept)
    manager.AddToParser(parser)
    parser.add_argument.assert_has_calls(
        [mock.call('--first-foo', help='A foo', required=False, completer=None,
                   metavar=None, hidden=False, default=None, action=None,
                   choices=None),
         mock.call('--first-bar', help='A bar', required=False, completer=None,
                   metavar=None, hidden=False, default=None, action=None,
                   choices=None),
         mock.call('--second-foo', help='A foo', required=False, completer=None,
                   metavar=None, hidden=False, default=None, action=None,
                   choices=None),
         mock.call('--second-bar', help='A bar', required=False, completer=None,
                   metavar=None, hidden=False, default=None, action=None,
                   choices=None)],
        any_order=True)
    parser.add_argument_group.assert_has_calls(
        [mock.call('help This is a concept with two group concepts inside it!'),
         mock.call('the first foobar This is a foobar concept.'),
         mock.call('the second foobar This is a foobar concept.')],
        any_order=True)

  def testFinalParse(self):
    dependencies = dependency_managers.DependencyNode.FromAttribute(
        self.string_concept.Attribute())
    mock_namespace = core_completer_test_base.MockNamespace(
        args={'c': 'value'})
    arg_getter = lambda: mock_namespace

    result = concept_managers.FinalParse(dependencies, arg_getter)

    self.assertEqual('value', result)


if __name__ == '__main__':
  test_case.main()
