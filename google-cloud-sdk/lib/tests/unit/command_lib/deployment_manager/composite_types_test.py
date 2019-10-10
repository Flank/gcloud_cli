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

"""Tests for DM composite_types command_lib."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.deployment_manager import composite_types
from tests.lib import test_case
from tests.lib.surface.deployment_manager import unit_test_base


class CompositeTypeCommandTest(unit_test_base.CompositeTypesUnitTestBase):

  def FinalTestDataDir(self):
    return 'simple_configs'

  def SetUp(self):
    self.TargetingV2BetaApi()

  def testTemplateContentsFor(self):
    template_path = self.GetTestFilePath('simple.jinja')
    actual_template = composite_types.TemplateContentsFor(self.messages,
                                                          template_path)
    self.assertEqual(self.GetExpectedSimpleTemplate(), actual_template)

  def testTemplateContentsFor_NotTemplate(self):
    with self.assertRaisesRegex(exceptions.Error,
                                'No path or name for a config, template, or '
                                'composite type was specified.'):
      composite_types.TemplateContentsFor(self.messages, '')

  def testTemplateFlagFileTypeSuccess(self):
    for value in ['boo.py', '123.jinja']:
      self.assertEqual(composite_types.template_flag_arg_type(value), value)

  def testTemplateFlagFileTypeFailure(self):
    for value in ['boo.pi', '123.jnja']:
      with self.assertRaisesRegex(
          arg_parsers.ArgumentTypeError,
          re.escape('Bad value [{0}]: must be a python (".py") or jinja '
                    '(".jinja") file'.format(value))):
        composite_types.template_flag_arg_type(value)


if __name__ == '__main__':
  test_case.main()
