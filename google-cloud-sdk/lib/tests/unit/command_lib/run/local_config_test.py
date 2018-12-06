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
"""Tests for local_config.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import tempfile
from googlecloudsdk.command_lib.run import local_config
from tests.lib import test_case


class LocalConfigTest(test_case.TestCase):

  def SetUp(self):
    self._filename = tempfile.NamedTemporaryFile().name

  def testParseSucceed_WithAllFields(self):
    with open(self._filename, 'w') as f:
      f.write('service: foo\nregion: bar')
    config = local_config.LocalConfig.ParseFrom(self._filename)
    self.assertEqual(config.service, 'foo')
    self.assertEqual(config.region, 'bar')

  def testParseSucceed_WithMissingField(self):
    with open(self._filename, 'w') as f:
      f.write('service: foo\n')
    config = local_config.LocalConfig.ParseFrom(self._filename)
    self.assertEqual(config.service, 'foo')
    self.assertEqual(config.region, None)

    with open(self._filename, 'w') as f:
      f.write('region: bar\n')
    config = local_config.LocalConfig.ParseFrom(self._filename)
    self.assertEqual(config.service, None)
    self.assertEqual(config.region, 'bar')

  def testParseFail_InvalidField(self):
    with open(self._filename, 'w') as f:
      f.write('foo: s1\nregion: us-central1\nservice: foo\n')
    with self.assertRaises(local_config.ConfigError) as ctx:
      local_config.LocalConfig.ParseFrom(self._filename)
    self.assertEqual(
        'Invalid field {} in {}'.format('foo', self._filename),
        str(ctx.exception))
