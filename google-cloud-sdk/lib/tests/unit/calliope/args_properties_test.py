# Copyright 2015 Google Inc. All Rights Reserved.
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
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.calliope import util


class ArgsPropertiesTest(util.WithTestTool):

  def testPersistAndLoad(self):
    self.assertEqual(self.cli.Execute(['command1', '--trace-email=foo']),
                     'foo')
    properties.PersistProperty(properties.VALUES.core.trace_email, 'bar')
    self.assertEqual(self.cli.Execute(['command1']), 'bar')

  def testProjectIsSet(self):
    # Test that the arg is recognized.
    self.assertEqual(self.cli.Execute(['command1', '--trace-email=foo']),
                     'foo')
    # Test that if the arg is not set, we read the workspace properties.
    properties.PersistProperty(properties.VALUES.core.trace_email, 'bar')
    self.assertEqual(self.cli.Execute(['command1']), 'bar')

  def testNonPersistence(self):
    self.assertEqual(self.cli.Execute(['command1', '--trace-email=foo']),
                     'foo')
    self.assertEqual(self.cli.Execute(['command1']), None)

  def testSetOverride(self):
    properties.VALUES.core.trace_email.Set('bar')
    self.assertEqual(self.cli.Execute(['command1', '--trace-email=foo']),
                     'foo')

  def testFlagOverridesWorkspace(self):
    properties.PersistProperty(properties.VALUES.core.trace_email, 'bar')
    self.assertEqual(self.cli.Execute(['command1', '--trace-email=foo']),
                     'foo')

  def testProjectIsSetByAction(self):
    self.cli.Execute('command1 --trace-email foo'.split())
    self.AssertOutputContains('trace_email is foo')

  def testPropNotSetByAnything(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('unsetprop'.split())
    self.AssertErrContains('re-running your command with the [--foo] flag')


if __name__ == '__main__':
  test_case.main()
