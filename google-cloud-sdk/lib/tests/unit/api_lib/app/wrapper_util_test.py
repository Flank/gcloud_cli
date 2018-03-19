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

"""Package containing unit tests for the wrapper_util module.
"""

import itertools
import os
from googlecloudsdk.api_lib.app import wrapper_util
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from tests.lib import test_case


class GetRuntimesTest(test_case.Base):

  def testEmpty(self):
    self.assertEqual(set([]), wrapper_util.GetRuntimes([]))

  def testInvalidArgs(self):
    with files.TemporaryDirectory(change_to=True):
      runtimes = wrapper_util.GetRuntimes(['--bad-args', 'foo', 'bar.yaml'])
      self.assertEqual(set([]), runtimes)

  def testBadYaml(self):
    with files.TemporaryDirectory(change_to=True) as tmp_dir:
      self.Touch(tmp_dir, 'app.yaml', contents='!/#{invalidYaml^$/')
      runtimes = wrapper_util.GetRuntimes(['app.yaml'])
      self.assertEqual(set([]), runtimes)

  def testGoodYaml(self):
    with files.TemporaryDirectory(change_to=True) as tmp_dir:
      self.Touch(tmp_dir, 'app.yaml', contents=yaml.dump({'runtime': 'foobar'}))
      runtimes = wrapper_util.GetRuntimes(['app.yaml'])
      self.assertEqual({'foobar'}, runtimes)

  def testGoodYamlAndBadArguments(self):
    with files.TemporaryDirectory(change_to=True) as tmp_dir:
      self.Touch(tmp_dir, 'app.yaml',
                 contents=yaml.dump({
                     'runtime': 'foobar',
                     'other_setting': 'othervalue'}))
      runtimes = wrapper_util.GetRuntimes(['lkjfa', 'app.yaml', '--bad-arg'])
      self.assertEqual({'foobar'}, runtimes)

  def testNoYamlInDirectory(self):
    dirname = 'app_dir'
    with files.TemporaryDirectory(change_to=True) as tmp_dir:
      self.Touch(os.path.join(tmp_dir, dirname), 'foo.yaml',
                 contents=yaml.dump({'runtime': 'foobar'}),
                 makedirs=True)
      runtimes = wrapper_util.GetRuntimes([dirname])
      self.assertEqual(set(), runtimes)

  def testValidYamlInDirectory(self):
    dirname = 'app_dir'
    with files.TemporaryDirectory(change_to=True) as tmp_dir:
      self.Touch(os.path.join(tmp_dir, dirname), 'app.yaml',
                 contents=yaml.dump({'runtime': 'foobar'}),
                 makedirs=True)
      runtimes = wrapper_util.GetRuntimes([dirname])
      self.assertEqual({'foobar'}, runtimes)

  def testYamlsInCurrentAndSubDirectory(self):
    yaml1_name = 'app.yaml'
    with files.TemporaryDirectory(change_to=True) as tmp_dir:
      self.Touch(tmp_dir, yaml1_name, yaml.dump({'runtime': 'foobar1'}))
      dirname = 'modules'
      yaml2_name = os.path.join(dirname, 'app.yaml')
      self.Touch(os.path.join(tmp_dir, dirname), 'app.yaml',
                 contents=yaml.dump({'runtime': 'foobar2'}),
                 makedirs=True)
      runtimes = wrapper_util.GetRuntimes([yaml1_name, yaml2_name])
      self.assertEqual({'foobar1', 'foobar2'}, runtimes)

  def testMultipleYamlsInDirectory(self):
    dirname = 'app_dir'
    with files.TemporaryDirectory(change_to=True) as tmp_dir:
      self.Touch(os.path.join(tmp_dir, dirname), 'app.yaml',
                 contents=yaml.dump({'runtime': 'foobar'}),
                 makedirs=True)
      self.Touch(os.path.join(tmp_dir, dirname), 'app.yml',
                 contents=yaml.dump({'runtime': 'foobar'}),
                 makedirs=True)
      with self.assertRaises(wrapper_util.MultipleAppYamlError):
        wrapper_util.GetRuntimes([dirname])

  def testMultipleYamlsAndBadArguments(self):
    with files.TemporaryDirectory(change_to=True) as tmp_dir:
      self.Touch(tmp_dir, 'app.yaml', contents=yaml.dump({'runtime': 'foobar'}))
      self.Touch(tmp_dir, 'foo.yaml', contents=yaml.dump({'runtime': 'baz'}))
      runtimes = wrapper_util.GetRuntimes(['foo.yaml', 'app.yaml', '--bad-arg'])
      self.assertEqual({'foobar', 'baz'}, runtimes)

  def testRuntimeNotString(self):
    with files.TemporaryDirectory(change_to=True) as tmp_dir:
      self.Touch(tmp_dir, 'app.yaml',
                 contents=yaml.dump({'runtime': {'key': 'value'}}))
      runtimes = wrapper_util.GetRuntimes(['app.yaml'])
      self.assertEqual(set(), runtimes)

  def testYamlNotDict(self):
    with files.TemporaryDirectory(change_to=True) as tmp_dir:
      self.Touch(tmp_dir, 'app.yaml',
                 contents=yaml.dump(['myfield', 'otherfield']))
      runtimes = wrapper_util.GetRuntimes(['app.yaml'])
      self.assertEqual(set([]), runtimes)

  def testPythonWithoutLibs(self):
    """Python27 without libraries are just python27."""
    with files.TemporaryDirectory(change_to=True) as tmp_dir:
      self.Touch(tmp_dir, 'app.yaml', contents=yaml.dump(
          {'runtime': 'python27'}))
      runtimes = wrapper_util.GetRuntimes(['app.yaml'])
      self.assertEqual({'python27'}, runtimes)

  def testPythonWithLibs(self):
    """Python27 with libraries generate an extra fake runtime."""
    with files.TemporaryDirectory(change_to=True) as tmp_dir:
      self.Touch(tmp_dir, 'app.yaml', contents=yaml.dump(
          {'runtime': 'python27', 'libraries': 'dummy'}))
      runtimes = wrapper_util.GetRuntimes(['app.yaml'])
      self.assertEqual({'python27', 'python27-libs'}, runtimes)

  def testOtherWithLibs(self):
    """Runtime other than python27 with libraries do not yield it."""
    with files.TemporaryDirectory(change_to=True) as tmp_dir:
      self.Touch(tmp_dir, 'app.yaml', contents=yaml.dump(
          {'runtime': 'foobar', 'libraries': 'dummy'}))
      runtimes = wrapper_util.GetRuntimes(['app.yaml'])
      self.assertEqual({'foobar'}, runtimes)


class GetComponentsTest(test_case.TestCase):

  def testDefaultComponents(self):
    self.assertEqual(wrapper_util.GetComponents([]), ['app-engine-python'])

  def testJava(self):
    self.assertEqual(
        wrapper_util.GetComponents(['java7']),
        ['app-engine-python', 'app-engine-java'])

  def testPhp(self):
    self.assertEqual(
        wrapper_util.GetComponents(['php55']),
        ['app-engine-python', 'app-engine-php'])

  def testPython(self):
    self.assertEqual(
        wrapper_util.GetComponents(['python27']),
        ['app-engine-python'])

  def testMulti(self):
    self.assertEqual(
        wrapper_util.GetComponents(['php55', 'java7']),
        ['app-engine-python', 'app-engine-php', 'app-engine-java'])

  def testPythonExtras(self):
    self.assertEqual(
        wrapper_util.GetComponents(['python27', 'python27-libs']),
        ['app-engine-python', 'app-engine-python-extras'])


class _ParseBooleanTest(test_case.TestCase):
  """Test parsing boolean flags of dev_appserver."""

  def testBooleanTrue(self):
    self.assertTrue(wrapper_util._ParseBoolean(True))

  def testBooleanFalse(self):
    self.assertFalse(wrapper_util._ParseBoolean(False))

  def testTrue(self):
    for value in itertools.product('Tt', 'Rr', 'Uu', 'Ee'):
      self.assertTrue(wrapper_util._ParseBoolean(''.join(value)))

  def testYes(self):
    self.assertTrue(wrapper_util._ParseBoolean('YES'))

  def testOne(self):
    self.assertTrue(wrapper_util._ParseBoolean('1'))

  def testFalse(self):
    for value in itertools.product('Ff', 'Aa', 'Ll', 'Ss', 'Ee'):
      self.assertFalse(wrapper_util._ParseBoolean(''.join(value)))

  def testNo(self):
    self.assertFalse(wrapper_util._ParseBoolean('NO'))

  def testZero(self):
    self.assertFalse(wrapper_util._ParseBoolean('0'))

  def testBad(self):
    self.assertRaisesRegexp(ValueError, "known booleans are 'true', 'yes'",
                            wrapper_util._ParseBoolean, 'bad')


if __name__ == '__main__':
  test_case.main()
