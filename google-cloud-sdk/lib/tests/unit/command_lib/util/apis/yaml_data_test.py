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
"""Tests for the yaml_data file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from googlecloudsdk.command_lib.util.apis import yaml_data
from tests.lib import parameterized
from tests.lib import sdk_test_base


class ResourceYAMLDataTest(sdk_test_base.WithOutputCapture,
                           parameterized.TestCase):

  def testCreateResourceYAMLDataFromPath(self):
    resource_yaml_data = yaml_data.ResourceYAMLData.FromPath('iot.region')
    region_data = {
        'attributes': [{
            'parameter_name': 'locationsId',
            'help': 'The name of the Cloud IoT region.',
            'attribute_name': 'region'
        }],
        'collection':
            'cloudiot.projects.locations',
        'name':
            'region',
        'disable_auto_completers':
            False
    }
    self.assertEqual(region_data, resource_yaml_data.GetData())
    self.assertEqual('region', resource_yaml_data.GetArgName())

  def testCreateResourceYAMLDataFromPathWithUnderscore(self):
    resource_yaml_data = yaml_data.ResourceYAMLData.FromPath(
        'ml_engine.project')
    project_data = {
        'name':
            'project',
        'collection':
            'ml.projects',
        'attributes': [{
            'attribute_name': 'project',
            'parameter_name': 'projectsId',
            'help': 'The name of the Google Cloud ML Engine project.'
        }]
    }
    self.assertEqual(project_data, resource_yaml_data.GetData())
    self.assertEqual('project', resource_yaml_data.GetArgName())

  @parameterized.parameters('', 'a', 'abc.', 'a.b.c')
  def testInvalidResourcePath(self, invalid_path):
    error_msg = re.escape('Invalid resource_path: [{}].'.format(invalid_path))
    with self.assertRaisesRegex(yaml_data.InvalidResourcePathError, error_msg):
      yaml_data.ResourceYAMLData.FromPath(invalid_path)
