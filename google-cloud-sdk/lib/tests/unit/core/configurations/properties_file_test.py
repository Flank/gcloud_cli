# -*- coding: utf-8 -*- #
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
"""Tests for googlecloudsdk.core.configurations.properties_file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core.configurations import properties_file
from tests.lib import sdk_test_base
from tests.lib import test_case


class PropertiesFileTest(sdk_test_base.SdkBase):

  def SetUp(self):
    self.properties_dir = self.Resource(
        'tests', 'unit', 'core', 'test_data', 'properties_files')
    self.properties1_file = os.path.join(self.properties_dir, 'properties1')
    self.properties2_file = os.path.join(self.properties_dir, 'properties2')
    self.properties3_file = os.path.join(self.properties_dir, 'properties3')
    self.bad_properties1_file = os.path.join(self.properties_dir,
                                             'bad_properties1')

  def testBasicParse(self):
    properties1 = properties_file.PropertiesFile([self.properties1_file])
    self.assertEqual(properties1.Get('core', 'john'), 'cool')

  def testDefaultWhenNotSet(self):
    properties1 = properties_file.PropertiesFile([self.properties1_file])
    self.assertEqual(
        properties1.Get('core', 'notjohn'), None)

  def testBasicParseFailure(self):
    with self.assertRaises(properties_file.PropertiesParseError):
      properties_file.PropertiesFile([self.bad_properties1_file])

  def testOverride(self):
    properties12 = properties_file.PropertiesFile(
        [self.properties1_file, self.properties2_file])
    self.assertEqual(properties12.Get('core', 'funtimes'), 'are here')
    self.assertEqual(properties12.Get('core', 'john'), 'meh')
    self.assertEqual(properties12.Get('core', 'mark'), 'so so')
    self.assertEqual(properties12.Get('core', 'rajeev'), 'awesome')

  def testMissing(self):
    properties1 = properties_file.PropertiesFile([self.properties1_file])
    self.assertEqual(properties1.Get('nothing', 'nowhere'), None)

  def testMultiSection(self):
    properties123 = properties_file.PropertiesFile(
        [self.properties1_file, self.properties2_file, self.properties3_file])
    self.assertEqual(properties123.Get('core', 'mark'), "ok you're cool too")
    self.assertEqual(properties123.Get('compute', 'project'),
                     'no specific properties')
    self.assertEqual(properties123.Get('nothing', 'project'), None)


if __name__ == '__main__':
  test_case.main()
