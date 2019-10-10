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


class LevelsTest(test_case.TestCase):

  def SetUp(self):
    temp_dir = files.TemporaryDirectory()
    self.temp_path = temp_dir.path
    self.addCleanup(temp_dir.Close)
    self.messages = apis.GetMessagesModule('accesscontextmanager', 'v1')

  def _MakeFile(self, contents):
    filename = 'test.yaml'
    full_path = os.path.join(self.temp_path, filename)
    files.WriteFileContents(full_path, contents)
    return full_path

  def testParseMissingFile(self):
    with self.assertRaisesRegex(yaml.FileLoadError,
                                'Failed to load'):
      levels.ParseBasicLevelConditions('does-not-exist.yaml')

  def testParseInvalidYaml(self):
    path = self._MakeFile(':')
    with self.assertRaisesRegex(yaml.YAMLParseError,
                                'Failed to parse YAML'):
      levels.ParseBasicLevelConditions(path)

  def testParseEmpty(self):
    path = self._MakeFile('')
    with self.assertRaisesRegex(levels.ParseError, 'File is empty'):
      levels.ParseBasicLevelConditions(path)

  def testParseValidYamlInvalidObjectEncodeError(self):
    path = self._MakeFile('test')
    with self.assertRaisesRegex(levels.ParseError,
                                'Invalid format'):
      levels.ParseBasicLevelConditions(path)

  def testParseValidYamlInvalidObjectUnrecognizedField(self):
    path = self._MakeFile('[{"invalid-prop": "value"}]')
    with self.assertRaisesRegex(levels.ParseError,
                                r'Unrecognized fields: \[invalid-prop\]'):
      levels.ParseBasicLevelConditions(path)

  def testParseSuccess(self):
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

    conditions = levels.ParseBasicLevelConditions(path)

    self.assertEqual(
        conditions,
        [
            self.messages.Condition(
                ipSubnetworks=['192.168.100.14/24', '2001:db8::/48'],
                negate=True),
            self.messages.Condition(
                members=['user:user@example.com',
                         'serviceAccount:serviceacct@gservices.com']),
            self.messages.Condition(
                requiredAccessLevels=[
                    'accessPolicies/my_policy/accessLevels/other_level'])
        ])


if __name__ == '__main__':
  test_case.main()
