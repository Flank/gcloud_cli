# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for googlecloudsdk.command_lib.accesscontextmanager.levels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.accesscontextmanager import levels
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from tests.lib import test_case


class LevelsTestGA(test_case.TestCase):

  def PreSetUp(self):
    self.api_version = 'v1'

  def SetUp(self):
    temp_dir = files.TemporaryDirectory()
    self.temp_path = temp_dir.path
    self.addCleanup(temp_dir.Close)
    self.messages = apis.GetMessagesModule('accesscontextmanager',
                                           self.api_version)

  def _MakeFile(self, contents):
    filename = 'test.yaml'
    full_path = os.path.join(self.temp_path, filename)
    files.WriteFileContents(full_path, contents)
    return full_path

  def testBasicParseMissingFile(self):
    with self.assertRaisesRegex(yaml.FileLoadError, 'Failed to load'):
      levels.ParseBasicLevelConditions(self.api_version)('does-not-exist.yaml')

  def testBasicParseInvalidYaml(self):
    path = self._MakeFile(':')
    with self.assertRaisesRegex(yaml.YAMLParseError, 'Failed to parse YAML'):
      levels.ParseBasicLevelConditions(self.api_version)(path)

  def testBasicParseEmpty(self):
    path = self._MakeFile('')
    with self.assertRaisesRegex(levels.ParseError, 'File is empty'):
      levels.ParseBasicLevelConditions(self.api_version)(path)

  def testBasicParseValidYamlInvalidObjectEncodeError(self):
    path = self._MakeFile('test')
    with self.assertRaisesRegex(levels.ParseError, 'Invalid format'):
      levels.ParseBasicLevelConditions(self.api_version)(path)

  def testBasicParseValidYamlInvalidObjectUnrecognizedField(self):
    path = self._MakeFile('[{"invalid-prop": "value"}]')
    with self.assertRaisesRegex(levels.ParseError,
                                r'Unrecognized fields: \[invalid-prop\]'):
      levels.ParseBasicLevelConditions(self.api_version)(path)

  def testBasicParseSuccess(self):
    path = self._MakeFile("""\
        - ipSubnetworks:
          - 192.168.100.14/24
          - 2001:db8::/48
          negate: true
        - members:
          - user:user@example.com
          - serviceAccount:serviceacct@gservices.com
        - requiredAccessLevels:
          - accessPolicies/my_policy/accessLevels/other_level
        """)

    conditions = levels.ParseBasicLevelConditions(self.api_version)(path)

    self.assertEqual(conditions, [
        self.messages.Condition(
            ipSubnetworks=['192.168.100.14/24', '2001:db8::/48'], negate=True),
        self.messages.Condition(members=[
            'user:user@example.com', 'serviceAccount:serviceacct@gservices.com'
        ]),
        self.messages.Condition(requiredAccessLevels=[
            'accessPolicies/my_policy/accessLevels/other_level'
        ])
    ])

  def testLevelsParseMissingFile(self):
    with self.assertRaisesRegex(yaml.FileLoadError, 'Failed to load'):
      levels.ParseAccessLevels(self.api_version)('does-not-exist.yaml')

  def testLevelsParseInvalidYaml(self):
    path = self._MakeFile(':')
    with self.assertRaisesRegex(yaml.YAMLParseError, 'Failed to parse YAML'):
      levels.ParseAccessLevels(self.api_version)(path)

  def testLevelsParseEmpty(self):
    path = self._MakeFile('')
    with self.assertRaisesRegex(levels.ParseError, 'File is empty'):
      levels.ParseAccessLevels(self.api_version)(path)

  def testLevelsParseValidYamlInvalidObjectEncodeError(self):
    path = self._MakeFile('test')
    with self.assertRaisesRegex(levels.ParseError, 'Invalid format'):
      levels.ParseAccessLevels(self.api_version)(path)

  def testLevelsParseValidYamlInvalidObjectUnrecognizedField(self):
    path = self._MakeFile('[{"invalid-prop": "value"}]')
    with self.assertRaisesRegex(levels.ParseError,
                                r'Unrecognized fields: \[invalid-prop\]'):
      levels.ParseAccessLevels(self.api_version)(path)

  def testLevelsParseSuccess(self):
    path = self._MakeFile("""\
      - name: accessPolicies/my_policy/accessLevels/my_level
        title: My Basic Level
        description: Basic level for foo.
        basic:
          combiningFunction: AND
          conditions:
            - ipSubnetworks:
              - 192.168.100.14/24
              negate: true
            - members:
              - user:user@example.com
      - name: accessPolicies/my_policy/accessLevels/my_other_level
        title: My Other Basic Level
        description: Basic level for bar.
        basic:
          combiningFunction: OR
          conditions:
            - ipSubnetworks:
              - 2001:db8::/48
        """)

    access_levels = levels.ParseAccessLevels(self.api_version)(path)

    self.assertEqual(access_levels, [
        self.messages.AccessLevel(
            basic=self.messages.BasicLevel(
                combiningFunction=self.messages.BasicLevel
                .CombiningFunctionValueValuesEnum('AND'),
                conditions=[
                    self.messages.Condition(
                        ipSubnetworks=['192.168.100.14/24'], negate=True),
                    self.messages.Condition(members=['user:user@example.com']),
                ]),
            name='accessPolicies/my_policy/accessLevels/my_level',
            title='My Basic Level',
            description='Basic level for foo.'),
        self.messages.AccessLevel(
            basic=self.messages.BasicLevel(
                combiningFunction=self.messages.BasicLevel
                .CombiningFunctionValueValuesEnum('OR'),
                conditions=[
                    self.messages.Condition(ipSubnetworks=['2001:db8::/48']),
                ]),
            name='accessPolicies/my_policy/accessLevels/my_other_level',
            title='My Other Basic Level',
            description='Basic level for bar.')
    ])

  def testCustomParseMissingFile(self):
    with self.assertRaisesRegex(yaml.FileLoadError, 'Failed to load'):
      levels.ParseCustomLevel(self.api_version)('does-not-exist.yaml')

  def testCustomParseInvalidYaml(self):
    path = self._MakeFile(':')
    with self.assertRaisesRegex(yaml.YAMLParseError, 'Failed to parse YAML'):
      levels.ParseCustomLevel(self.api_version)(path)

  def testCustomParseEmpty(self):
    path = self._MakeFile('')
    with self.assertRaisesRegex(levels.ParseError, 'File is empty'):
      levels.ParseCustomLevel(self.api_version)(path)

  def testCustomParseValidYamlInvalidObjectEncodeError(self):
    path = self._MakeFile('test')
    with self.assertRaisesRegex(levels.ParseError, 'Invalid format'):
      levels.ParseCustomLevel(self.api_version)(path)

  def testCustomParseValidYamlInvalidObjectUnrecognizedField(self):
    path = self._MakeFile('invalid-expression: "value"')
    with self.assertRaisesRegex(levels.ParseError,
                                r'Unrecognized fields: \[invalid-expression\]'):
      levels.ParseCustomLevel(self.api_version)(path)

  def testParseSuccess(self):
    path = self._MakeFile("""\
        expression: "inIpRange(origin.ip, ['127.0.0.1/24']"
        """)

    expr = levels.ParseCustomLevel(self.api_version)(path)

    self.assertEqual(
        expr,
        self.messages.Expr(expression="inIpRange(origin.ip, ['127.0.0.1/24']"))


class LevelsTestBeta(LevelsTestGA):

  def PreSetUp(self):
    self.api_version = 'v1'


class LevelsTestAlpha(LevelsTestGA):

  def PreSetUp(self):
    self.api_version = 'v1alpha'


if __name__ == '__main__':
  test_case.main()
