# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Integration tests for the 'runtime-config' commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
from googlecloudsdk.core.util import retry
from tests.lib import test_case
from tests.lib.surface.runtime_config import base


class ConfigTest(base.RuntimeConfigIntegrationTest):

  def _checkList(self, name1, name2):
    res = set(x['name'] for x in self.RunRuntimeConfig('list --format=disable'))
    return name1 in res and name2 in res

  def testList(self):
    with self._RuntimeConfig('rtc-configs', 'foo1') as name1:
      with self._RuntimeConfig('rtc-configs', 'foo2') as name2:
        r = retry.Retryer(max_retrials=10, exponential_sleep_multiplier=2.0)
        try:
          r.RetryOnResult(
              self._checkList,
              args=[name1, name2],
              sleep_ms=500,
              should_retry_if=False)
        except retry.MaxRetrialsException:
          self.fail('Could not setup the data properly')

        self.ClearOutput()
        self.RunRuntimeConfig('list')
        # Check each list output line individually since the integration
        # test project is shared and the list might contain unrelated
        # configurations created by other test instances.
        self.AssertOutputContains('NAME DESCRIPTION', normalize_space=True)
        self.AssertOutputContains(
            '{0} foo1'.format(name1), normalize_space=True)
        self.AssertOutputContains(
            '{0} foo2'.format(name2), normalize_space=True)

  def testDescribe(self):
    with self._RuntimeConfig('rtc-configs', 'foo1') as name:
      self.ClearOutput()
      self.RunRuntimeConfig('describe {0}'.format(name))
      self.AssertOutputContains("""\
atomicName: projects/{0}/configs/{1}
description: foo1
name: {1}
""".format(self.Project(), name))

  def testUpdate(self):
    with self._RuntimeConfig('rtc-configs', 'foo1') as name:
      self.RunRuntimeConfig('update {0} --description=updated'.format(name))
      self.ClearOutput()
      self.RunRuntimeConfig('describe {0}'.format(name))
      self.AssertOutputContains("""\
atomicName: projects/{0}/configs/{1}
description: updated
name: {1}
""".format(self.Project(), name))

      # Reset back to original description
      self.RunRuntimeConfig('update {0} --description=foo1'.format(name))


class VariableTest(base.RuntimeConfigIntegrationTest):

  def _CheckValue(self, cb, name, value, text):
    res = cb('get-value {0} --format=disable'.format(name))
    return value and res.value == value or text and res.text == text

  def _WaitForValue(self, cb, name, value='', text=''):
    r = retry.Retryer(max_retrials=10, exponential_sleep_multiplier=2.0)
    try:
      r.RetryOnResult(
          self._CheckValue,
          args=[cb, name, value, text],
          sleep_ms=500,
          should_retry_if=False)
    except retry.MaxRetrialsException:
      self.fail('Could not retrieve value for {0} in time'.format(name))

  FIRST_VAL = 'foo'
  SECOND_VAL = 'bar!'
  TEXT_VAL = 'Text!'

  def testSetGetUnset(self):
    with self._RuntimeConfig('rtc-vars') as config_name:
      def RunVariables(command):
        return self.RunRuntimeConfig(
            'variables {0} --config-name {1}'.format(command, config_name))

      # Test --fail-if-absent
      self.ClearErr()
      with self.AssertRaisesHttpExceptionMatches(
          'NOT_FOUND: Requested entity was not found.'):
        RunVariables('set a/var1 {0} --fail-if-absent'.format(self.FIRST_VAL))

      # Test set
      RunVariables('set a/var1 foo')
      self.ClearOutput()
      self._WaitForValue(
          RunVariables,
          name='a/var1',
          value=base64.b64encode(self.FIRST_VAL.encode()).strip())
      RunVariables('describe a/var1')
      self.AssertOutputMatches("""\
atomicName: projects/{0}/configs/{1}/variables/a/var1
name: a/var1
updateTime: [^\n]+
value: {2}
""".format(self.Project(), config_name, self.FIRST_VAL.strip()))

      # Test set with text.
      RunVariables('set a/var2 {0} --is-text'.format(self.TEXT_VAL))
      self.ClearOutput()
      self._WaitForValue(RunVariables, name='a/var2', text=self.TEXT_VAL)
      RunVariables('describe a/var2')
      self.AssertOutputMatches("""\
atomicName: projects/{0}/configs/{1}/variables/a/var2
name: a/var2
text: {2}
updateTime: [^\n]+
""".format(self.Project(), config_name, self.TEXT_VAL))

      # Test get-value
      self.ClearOutput()
      RunVariables('get-value a/var1')
      self.AssertOutputEquals(self.FIRST_VAL)

      self.ClearOutput()
      RunVariables('get-value a/var2')
      self.AssertOutputEquals(self.TEXT_VAL)

      # Test --fail-if-present
      self.ClearErr()
      with self.AssertRaisesHttpExceptionMatches(
          'ALREADY_EXISTS: Requested entity already exists'):
        RunVariables('set a/var1 {0} --fail-if-present'.format(self.SECOND_VAL))

      # Test update, with changing value type from binary to text.
      RunVariables('set a/var1 {0} --is-text'.format(self.SECOND_VAL))
      self.ClearOutput()
      self._WaitForValue(RunVariables, name='a/var1', text=self.SECOND_VAL)
      RunVariables('describe a/var1')
      self.AssertOutputMatches("""\
atomicName: projects/{0}/configs/{1}/variables/a/var1
name: a/var1
text: {2}
updateTime: [^\n]+
""".format(self.Project(), config_name, self.SECOND_VAL))
      self.ClearOutput()
      RunVariables('get-value a/var1')
      self.AssertOutputEquals(self.SECOND_VAL)
      self.ClearOutput()

      # Test update, with changing value type from text to binary.
      RunVariables('set a/var2 {0}'.format(self.SECOND_VAL))
      self.ClearOutput()
      self._WaitForValue(
          RunVariables,
          name='a/var2',
          value=base64.b64encode(self.SECOND_VAL.encode()).strip())
      RunVariables('describe a/var2')
      self.AssertOutputMatches("""\
atomicName: projects/{0}/configs/{1}/variables/a/var2
name: a/var2
updateTime: [^\n]+
value: {2}
""".format(self.Project(), config_name, self.SECOND_VAL.strip()))
      self.ClearOutput()
      RunVariables('get-value a/var2')
      self.AssertOutputEquals(self.SECOND_VAL)

      # Test unset
      RunVariables('unset a/var1')
      RunVariables('unset a/var2')

      # A subsequent describe should fail
      self.ClearErr()
      with self.AssertRaisesHttpExceptionMatches(
          'NOT_FOUND: Requested entity was not found.'):
        RunVariables('describe a/var1')

      # Unset without --fail-if-absent fails silently.
      RunVariables('unset a/var1')

      # --fail-if-absent causes unset to fail with an error message.
      self.ClearErr()
      with self.AssertRaisesHttpExceptionMatches(
          'NOT_FOUND: Requested entity was not found.'):
        RunVariables('unset a/var1 --fail-if-absent')

  def testList(self):
    with self._RuntimeConfig('rtc-vars') as config_name:

      def RunVariables(command):
        return self.RunRuntimeConfig(
            'variables {0} --config-name {1}'.format(command, config_name))

      RunVariables('set a/var1 foo')
      RunVariables('set b/var2 bar')
      RunVariables('set b/var3 baz --is-text')

      # Wait only for the last one to arrive.
      self._WaitForValue(RunVariables, name='b/var3', text='baz')

      self.ClearOutput()
      RunVariables('list')
      self.AssertOutputMatches(
          """\
NAME    UPDATE_TIME
a/var1  [^\n]+
b/var2  [^\n]+
b/var3  [^\n]+
  """,
          normalize_space=True)

      RunVariables('unset a/var1')
      RunVariables('unset b/var2')
      RunVariables('unset b/var3')


if __name__ == '__main__':
  test_case.main()
