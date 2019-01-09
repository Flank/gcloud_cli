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

from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.concepts import dependency_managers
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.command_lib.concepts import concepts_test_base
from tests.lib.core import core_completer_test_base


class DependencyManagerTest(concepts_test_base.ConceptArgsTestBase):

  def testParse(self):
    dependency_manager = dependency_managers.DependencyManager(
        dependency_managers.DependencyNode.FromAttribute(
            self.string_concept.Attribute()))
    mock_namespace = core_completer_test_base.MockNamespace(
        args={'c': 'value'})

    result = dependency_manager.ParseConcept(mock_namespace)

    self.assertEqual('value', result)

  def testRecursiveParsing(self):
    dependency_manager = dependency_managers.DependencyManager(
        dependency_managers.DependencyNode.FromAttribute(
            self.group_arg_concept.Attribute()))
    mock_namespace = core_completer_test_base.MockNamespace(
        args={'first_foo': 'x',
              'first_bar': 'y',
              'second_foo': 'a',
              'second_bar': 'b'})

    result = dependency_manager.ParseConcept(mock_namespace)
    self.assertEqual('x', result.first.foo)
    self.assertEqual('y', result.first.bar)
    self.assertEqual('a', result.second.foo)
    self.assertEqual('b', result.second.bar)

  def testRecursiveParsingWithFallthroughs(self):
    properties.VALUES.core.project.Set('ft')
    dependency_manager = dependency_managers.DependencyManager(
        dependency_managers.DependencyNode.FromAttribute(
            self.group_arg_concept.Attribute()))
    mock_namespace = core_completer_test_base.MockNamespace(
        args={'first_bar': 'y',
              'second_bar': 'b'})

    result = dependency_manager.ParseConcept(mock_namespace)

    self.assertEqual('ft', result.first.foo)
    self.assertEqual('y', result.first.bar)
    self.assertEqual('ft', result.second.foo)
    self.assertEqual('b', result.second.bar)


class DependencyNodeTest(concepts_test_base.ConceptArgsTestBase):

  def testDependencyNode_Single(self):
    dependency_node = dependency_managers.DependencyNode.FromAttribute(
        self.fallthrough_concept.Attribute())
    self.assertEqual('c', dependency_node.name)
    self.assertEqual(self.fallthrough_concept, dependency_node.concept)
    self.assertIsNone(dependency_node.dependencies)
    self.assertEqual('--c', dependency_node.arg_name)
    self.assertEqual([self.fallthrough], dependency_node.fallthroughs)

  def testDependencyNode_Group(self):
    dependency_node = dependency_managers.DependencyNode.FromAttribute(
        self.group_arg_concept.Attribute())
    self.assertEqual('baz', dependency_node.name)
    self.assertEqual(self.group_arg_concept, dependency_node.concept)
    self.assertEqual(['first', 'second'],
                     sorted(dependency_node.dependencies.keys()))
    self.assertIsNone(dependency_node.arg_name)
    self.assertEqual([], dependency_node.fallthroughs)

    first = dependency_node.dependencies['first']
    self.assertEqual('first', first.concept.name)
    self.assertEqual(['bar', 'foo'],
                     sorted(first.dependencies.keys()))
    self.assertIsNone(first.arg_name)
    self.assertEqual([], first.fallthroughs)

    first_foo = first.dependencies['foo']
    self.assertEqual('first_foo', first_foo.concept.name)
    self.assertIsNone(first_foo.dependencies)
    self.assertEqual('--first-foo', first_foo.arg_name)
    self.assertEqual([deps.PropertyFallthrough(properties.VALUES.core.project)],
                     first_foo.fallthroughs)


class DependencyViewTest(concepts_test_base.ConceptArgsTestBase):

  def testDependencyViewFromValue(self):
    def Getter():
      return 'x'
    dependency_view = dependency_managers.DependencyViewFromValue(Getter)

    self.assertEqual('x', dependency_view.value)

  def testDependencyViewFromValue_Error(self):
    def Getter():
      raise deps.AttributeNotFoundError('not found')
    dependency_view = dependency_managers.DependencyViewFromValue(Getter)

    with self.assertRaisesRegex(deps.AttributeNotFoundError, 'not found'):
      dependency_view.value  # pylint:disable=pointless-statement

  def testDependencyViewGroup(self):
    dependency_view = dependency_managers.DependencyView(
        {'foo': 'x', 'bar': 'y'})
    self.assertEqual('x', dependency_view.foo)
    self.assertEqual('y', dependency_view.bar)


if __name__ == '__main__':
  test_case.main()
