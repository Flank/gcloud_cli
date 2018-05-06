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
from __future__ import unicode_literals
import re

from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case


class DepsTest(sdk_test_base.WithFakeAuth):
  """Test for the calliope.concepts.deps module."""

  def Project(self):
    return 'fake-project'

  def SetUp(self):
    properties.VALUES.core.project.Set(self.Project())

  def testGenericFallthrough(self):
    """Test functionality of a generic fallthrough."""
    fallthrough = deps.Fallthrough(lambda: 'FOO', 'this is the hint')
    self.assertEqual('FOO', fallthrough.GetValue())
    self.assertEqual('this is the hint', fallthrough.hint)

  def testGenericFallthroughFails(self):
    """Test functionality of a generic fallthrough."""
    fallthrough = deps.Fallthrough(lambda: None, 'this is the hint')
    with self.assertRaises(deps.FallthroughNotFoundError):
      fallthrough.GetValue()

  def testPropertyFallthrough(self):
    """Test functionality of a property fallthrough."""
    fallthrough = deps.PropertyFallthrough(properties.VALUES.core.project)
    self.assertEqual(self.Project(), fallthrough.GetValue())

  def testPropertyFallthroughFails(self):
    """Test property fallthrough when the property is unset."""
    properties.VALUES.core.project.Set(None)
    fallthrough = deps.PropertyFallthrough(properties.VALUES.core.project)
    with self.assertRaises(deps.FallthroughNotFoundError):
      fallthrough.GetValue()

  def testDeps_ArgsGiven(self):
    """Test the deps object can initialize attributes using ArgFallthrough."""
    deps_object = deps.Deps(
        {'name': [deps.ArgFallthrough('--myresource-name', 'example')],
         'project': [deps.ArgFallthrough('--myresource-project',
                                         'exampleproject'),
                     deps.PropertyFallthrough(properties.VALUES.core.project)]})
    self.assertEqual('example', deps_object.Get('name'))
    self.assertEqual('exampleproject', deps_object.Get('project'))

  def testDeps_UseProperty(self):
    """Test the deps object can initialize attributes using PropertyFallthrough.
    """
    deps_object = deps.Deps(
        {'project': [deps.ArgFallthrough('--myresource-project', None),
                     deps.PropertyFallthrough(properties.VALUES.core.project)]})
    self.assertEqual(self.Project(), deps_object.Get('project'))

  def testDeps_BothFail(self):
    """Test the deps object raises an error if an attribute can't be found."""
    properties.VALUES.core.project.Set(None)
    deps_object = deps.Deps(
        {'project': [deps.ArgFallthrough('--myresource-project', None),
                     deps.PropertyFallthrough(properties.VALUES.core.project)]})
    regex = re.escape(
        'Failed to find attribute [project]. The attribute can be set in the '
        'following ways: \n'
        '- Provide the flag [--myresource-project] on the command line\n'
        '- Set the property [core/project] or provide the flag [--project] '
        'on the command line')
    with self.assertRaisesRegex(deps.AttributeNotFoundError, regex):
      deps_object.Get('project')

  def testDeps_AnotherProperty(self):
    """Test the deps object handles non-project property.
    """
    properties.VALUES.compute.zone.Set('us-east1b')
    deps_object = deps.Deps(
        {'zone': [deps.ArgFallthrough('--myresource-zone', None),
                  deps.PropertyFallthrough(properties.VALUES.compute.zone)]})
    self.assertEqual('us-east1b', deps_object.Get('zone'))

  def testDeps_BothFail_AnotherProperty(self):
    """Test the deps error has the correct message for non-project properties.
    """
    properties.VALUES.compute.zone.Set(None)
    deps_object = deps.Deps(
        {'zone': [deps.ArgFallthrough('--myresource-zone', None),
                  deps.PropertyFallthrough(properties.VALUES.compute.zone),
                  deps.Fallthrough(lambda: None, 'Custom hint')]})
    regex = re.escape(
        'Failed to find attribute [zone]. The attribute can be set in the '
        'following ways: \n'
        '- Provide the flag [--myresource-zone] on the command line\n'
        '- Set the property [compute/zone]\n'
        '- Custom hint')
    with self.assertRaisesRegex(deps.AttributeNotFoundError, regex):
      deps_object.Get('zone')


if __name__ == '__main__':
  test_case.main()
