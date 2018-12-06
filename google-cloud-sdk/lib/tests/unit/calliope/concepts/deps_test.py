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

"""Tests for the deps module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope.concepts import concepts_test_base


class DepsTest(concepts_test_base.ConceptsTestBase,
               parameterized.TestCase):
  """Test for the calliope.concepts.deps module."""

  def Project(self):
    return 'fake-project'

  def SetUp(self):
    properties.VALUES.core.project.Set(self.Project())

  def testGenericFallthrough(self):
    """Test functionality of a generic fallthrough."""
    fallthrough = deps.Fallthrough(lambda: 'FOO', 'this is the hint')
    self.assertEqual('FOO', fallthrough.GetValue(self._GetMockNamespace()))
    self.assertEqual('this is the hint', fallthrough.hint)

  def testGenericFallthroughFails(self):
    """Test functionality of a generic fallthrough."""
    fallthrough = deps.Fallthrough(lambda: None, 'this is the hint')
    with self.assertRaises(deps.FallthroughNotFoundError):
      fallthrough.GetValue(self._GetMockNamespace())

  def testPropertyFallthrough(self):
    """Test functionality of a property fallthrough."""
    fallthrough = deps.PropertyFallthrough(properties.VALUES.core.project)
    self.assertEqual(self.Project(),
                     fallthrough.GetValue(self._GetMockNamespace()))

  def testPropertyFallthroughFails(self):
    """Test property fallthrough when the property is unset."""
    self.UnsetProject()
    fallthrough = deps.PropertyFallthrough(properties.VALUES.core.project)
    with self.assertRaises(deps.FallthroughNotFoundError):
      fallthrough.GetValue(self._GetMockNamespace())

  def testArgFallthrough(self):
    """Test functionality of a property fallthrough."""
    fallthrough = deps.ArgFallthrough('--a')
    self.assertEqual('foo',
                     fallthrough.GetValue(self._GetMockNamespace(a='foo')))

  @parameterized.named_parameters(
      ('Arg', deps.ArgFallthrough('--a'), True),
      ('Generic',
       deps.Fallthrough(lambda: 'projects/p/shelves/s/books/b', hint='h'),
       False),
      ('GenericActive',
       deps.Fallthrough(lambda: 'projects/p/shelves/s/books/b', hint='h',
                        active=True),
       True))
  def testAnchorFallthrough(self, orig_fallthrough, active):
    """Test the FullySpecifiedAnchorFallthrough gives other parameters."""
    proj_fallthrough = deps.FullySpecifiedAnchorFallthrough(
        orig_fallthrough,
        self.book_collection,
        'projectsId')
    shelf_fallthrough = deps.FullySpecifiedAnchorFallthrough(
        orig_fallthrough,
        self.book_collection,
        'shelvesId')
    parsed_args = self._GetMockNamespace(a='projects/p/shelves/s/books/b')

    self.assertEqual(
        'p',
        proj_fallthrough.GetValue(parsed_args))
    self.assertEqual(
        's',
        shelf_fallthrough.GetValue(parsed_args))
    self.assertEqual(active, proj_fallthrough.active)
    self.assertEqual(active, shelf_fallthrough.active)

  @parameterized.named_parameters(
      ('CantParse', 'projectsId', 'b'),
      ('WrongParam', 'project', 'projects/p/shelves/s/books/b'))
  def testAnchorFallthroughFails(self, proj_param, anchor_value):
    """Test failures with FullySpecifiedAnchorFallthrough."""
    proj_fallthrough = deps.FullySpecifiedAnchorFallthrough(
        deps.ArgFallthrough('--a'),
        self.book_collection,
        proj_param)
    parsed_args = self._GetMockNamespace(a=anchor_value)

    with self.assertRaises(deps.FallthroughNotFoundError):
      proj_fallthrough.GetValue(parsed_args)

  @parameterized.named_parameters(
      ('ArgFallthroughFlag',
       deps.ArgFallthrough('--resources', plural=True), ['xyz'], ['xyz']),
      ('ArgFallthroughSingle',
       deps.ArgFallthrough('--resources', plural=True), 'xyz', ['xyz']),
      ('Property',
       deps.PropertyFallthrough(properties.VALUES.compute.zone, plural=True),
       'xyz', ['xyz']),
      ('Fallthrough', deps.Fallthrough(lambda: 'xyz', hint='h', plural=True),
       None, ['xyz']))
  def testFallthroughsPlural(self, fallthrough, val, expected):
    properties.VALUES.compute.zone.Set(val)
    parsed_args = self._GetMockNamespace(resources=val)
    self.assertEqual(expected, fallthrough.GetValue(parsed_args=parsed_args))

  @parameterized.named_parameters(
      ('ArgFallthroughFlag',
       [deps.ArgFallthrough('--resources', plural=True)], ['xyz'], ['xyz']),
      ('ArgFallthroughSingle',
       [deps.ArgFallthrough('--resources', plural=True)], 'xyz', ['xyz']),
      ('Property',
       [deps.PropertyFallthrough(properties.VALUES.compute.zone, plural=True)],
       'xyz', ['xyz']),
      ('Fallthrough', [deps.Fallthrough(lambda: 'xyz', hint='h', plural=True)],
       None, ['xyz']))
  def testGet_Plural(self, fallthroughs, val, expected):
    properties.VALUES.compute.zone.Set(val)
    result = deps.Get(
        'resource',
        {'resource': fallthroughs},
        parsed_args=self._GetMockNamespace(
            resources=val))
    self.assertEqual(expected, result)

  def testGet_ArgsGiven(self):
    """Test the deps object can initialize attributes using ArgFallthrough."""
    fallthroughs_map = {
        'name': [deps.ArgFallthrough('--myresource-name')],
        'project': [deps.ArgFallthrough('--myresource-project'),
                    deps.ArgFallthrough('--project'),
                    deps.PropertyFallthrough(properties.VALUES.core.project)]}
    parsed_args = self._GetMockNamespace(
        myresource_name='example',
        myresource_project='exampleproject')
    self.assertEqual(
        'example',
        deps.Get('name', fallthroughs_map, parsed_args=parsed_args))
    self.assertEqual(
        'exampleproject',
        deps.Get('project', fallthroughs_map, parsed_args=parsed_args))

  def testGet_UseProperty(self):
    """Test the deps object can initialize attributes using PropertyFallthrough.
    """
    result = deps.Get(
        'project',
        {'project': [deps.ArgFallthrough('--myresource-project'),
                     deps.ArgFallthrough('--project'),
                     deps.PropertyFallthrough(properties.VALUES.core.project)]},
        parsed_args=self._GetMockNamespace(myresource_project=None))
    self.assertEqual(self.Project(), result)

  def testGet_BothFail(self):
    """Test the deps object raises an error if an attribute can't be found."""
    self.UnsetProject()
    fallthroughs_map = {
        'project': [deps.ArgFallthrough('--myresource-project'),
                    deps.ArgFallthrough('--project'),
                    deps.PropertyFallthrough(properties.VALUES.core.project)]}
    parsed_args = self._GetMockNamespace(myresource_project=None)
    regex = re.escape(
        'Failed to find attribute [project]. The attribute can be set in the '
        'following ways: \n'
        '- provide the argument [--myresource-project] on the command line\n'
        '- provide the argument [--project] on the command line\n'
        '- set the property [core/project]')
    with self.assertRaisesRegex(deps.AttributeNotFoundError, regex):
      deps.Get('project', fallthroughs_map, parsed_args=parsed_args)

  def testGet_AnotherProperty(self):
    """Test the deps object handles non-project property.
    """
    properties.VALUES.compute.zone.Set('us-east1b')
    result = deps.Get(
        'zone',
        {'zone': [deps.ArgFallthrough('--myresource-zone'),
                  deps.PropertyFallthrough(properties.VALUES.compute.zone)]},
        parsed_args=self._GetMockNamespace(myresource_zone=None))
    self.assertEqual('us-east1b', result)

  def testGet_BothFail_AnotherProperty(self):
    """Test the deps error has the correct message for non-project properties.
    """
    properties.VALUES.compute.zone.Set(None)
    fallthroughs_map = {
        'zone': [deps.ArgFallthrough('--myresource-zone'),
                 deps.PropertyFallthrough(properties.VALUES.compute.zone),
                 deps.Fallthrough(lambda: None, 'custom hint')]}
    parsed_args = self._GetMockNamespace(myresource_zone=None)
    regex = re.escape(
        'Failed to find attribute [zone]. The attribute can be set in the '
        'following ways: \n'
        '- provide the argument [--myresource-zone] on the command line\n'
        '- set the property [compute/zone]\n'
        '- custom hint')
    with self.assertRaisesRegex(deps.AttributeNotFoundError, regex):
      deps.Get('zone', fallthroughs_map, parsed_args=parsed_args)


if __name__ == '__main__':
  test_case.main()
