# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Validate that all scenerio tests follow scenario test schema."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import pkg_resources
from tests.lib import cli_test_base
from tests.lib.scenario import schema as scenario_schema


TEMPLATE_ROOT = (os.path.join(os.path.dirname(__file__), 'templates'))
SCENARIO_TEAMPLATE_FILE_NAME = 'test_template.scenario.yaml'
SCENARIO_TEMPLATE_PATH = os.path.join(TEMPLATE_ROOT,
                                      SCENARIO_TEAMPLATE_FILE_NAME)

DESCRIBE_EXAMPLE_FILE_NAME = 'describe_test.scenario.yaml'
DESCRIBE_EXAMPLE_PATH = os.path.join(TEMPLATE_ROOT, DESCRIBE_EXAMPLE_FILE_NAME)

CREATE_EXAMPLE_FILE_NAME = 'create_test.scenario.yaml'
CREATE_EXAMPLE_PATH = os.path.join(TEMPLATE_ROOT, CREATE_EXAMPLE_FILE_NAME)


class ValidateScenarioTests(cli_test_base.CliTestBase):

  def testValidateTemplate(self):
    val = pkg_resources.GetResourceFromFile(SCENARIO_TEMPLATE_PATH)
    template = yaml.load(val, version=yaml.VERSION_1_2)
    validator = scenario_schema.Validator(template)
    try:
      validator.Validate()
    except scenario_schema.ValidationError as e:
      self.fail(e)

  def testValidateDescribeExample(self):
    example = yaml.load(
        pkg_resources.GetResourceFromFile(DESCRIBE_EXAMPLE_PATH),
        version=yaml.VERSION_1_2)
    validator = scenario_schema.Validator(example)
    try:
      validator.Validate()
    except scenario_schema.ValidationError as e:
      self.fail(e)

  def testValidateCreateExample(self):
    example = yaml.load(
        pkg_resources.GetResourceFromFile(CREATE_EXAMPLE_PATH),
        version=yaml.VERSION_1_2)
    validator = scenario_schema.Validator(example)
    try:
      validator.Validate()
    except scenario_schema.ValidationError as e:
      self.fail(e)

if __name__ == '__main__':
  cli_test_base.main()
