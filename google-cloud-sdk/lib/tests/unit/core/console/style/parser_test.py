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
"""Tests for the console style parser."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core.console.style import parser
from googlecloudsdk.core.console.style import text
from googlecloudsdk.core.util import platforms
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.core.console.style import style_test_base


class ParserText(style_test_base.StyleTestBase, parameterized.TestCase):
  """Tests basic configuration of core logger."""

  def SetUp(self):
    # Bypass parser.GetTypedTextParser as this isn't a platform specific test.
    self.parser = parser.TypedTextParser(
        style_test_base.STYLE_MAPPINGS_TESTING, True)

  def testBasicColoring(self):
    blue_text = text.TypedText('blue', style_test_base.TestTextTypes.BLUE)
    parsed_text = self.parser.ParseTypedTextToString(blue_text)
    self.assertEquals(self.blue + 'blue' + self.reset, parsed_text)

  def testStringFormatting(self):
    blue_text = text.TypedText('blue',
                               style_test_base.TestTextTypes.BLUE_AND_BRACKETS)
    parsed_text = self.parser.ParseTypedTextToString(blue_text)
    self.assertEquals(self.blue + '[blue]' + self.reset, parsed_text)

  def testAttributes(self):
    bold_text = text.TypedText('bold',
                               style_test_base.TestTextTypes.BOLD)
    parsed_text = self.parser.ParseTypedTextToString(bold_text)
    self.assertEquals(self.bold + 'bold' + self.reset, parsed_text)

  def testNestedText(self):
    blue_text = text.TypedText('blue', style_test_base.TestTextTypes.BLUE)
    text_with_nested_text = text.TypedText(['Text: ', blue_text, '.'])
    parsed_text = self.parser.ParseTypedTextToString(text_with_nested_text)
    self.assertEquals(
        'Text: {blue}blue{reset}.'.format(
            blue=self.blue, reset=self.reset),
        parsed_text)

  def testNestedTextAttributesReset(self):
    project_name = style_test_base.TestTextTypes.BOLD('cool-project')
    instance_name = style_test_base.TestTextTypes.BOLD('my-instance')
    resource_path = style_test_base.TestTextTypes.BLUE_AND_BRACKETS(
        'projects/', project_name, '/instance/', instance_name)
    success_message = style_test_base.TestTextTypes.ITALICS('Success!')
    message = text.TypedText(
        ['Created instance ', resource_path, '. ', success_message])
    parsed_text = self.parser.ParseTypedTextToString(message)
    self.assertEquals(
        'Created instance {blue}[projects/{blue_bold}cool-project{reset}'
        '{blue}/instance/{blue_bold}my-instance{reset}{blue}]{reset}. '
        '{italics}Success!{reset}'.format(
            blue=self.blue, reset=self.reset, blue_bold=self.blue_bold,
            italics=self.italics),
        parsed_text)

  def testNestedTextParentAttributesPropagate(self):
    project_name = style_test_base.TestTextTypes.BOLD('cool-project')
    instance_name = style_test_base.TestTextTypes.BOLD('my-instance')
    resource_path = style_test_base.TestTextTypes.BLUE_AND_BRACKETS(
        'projects/', project_name, '/instance/', instance_name)
    message = style_test_base.TestTextTypes.ITALICS(
        'Created instance ', resource_path, '.')
    parsed_text = self.parser.ParseTypedTextToString(message)
    self.assertEquals(
        '{italics}Created instance {blue_italics}[projects/{bold_italics}'
        'cool-project{reset}{blue_italics}/instance/{bold_italics}my-instance'
        '{reset}{blue_italics}]{reset}{italics}.{reset}'.format(
            blue_italics=self.blue_italics, reset=self.reset,
            bold_italics=self.blue_bold_italics, italics=self.italics),
        parsed_text)

  def testParentAttributeIsSame(self):
    bold_text = style_test_base.TestTextTypes.BOLD('bold')
    nested_bold_text = style_test_base.TestTextTypes.BOLD(
        'outer_bold ', bold_text)
    parsed_text = self.parser.ParseTypedTextToString(nested_bold_text)
    # The double bold is not great. Would need to support knowing how many
    # levels above in the rescursive stack the attribute came from.
    self.assertEquals(
        '{bold}outer_bold {bold}bold{reset}{bold}{reset}'.format(
            bold=self.bold, reset=self.reset),
        parsed_text)

  @parameterized.named_parameters(
      ('RequestEnabled', None, None, None, False, True, True),
      ('RequestDisabled', None, None, None, False, False, False),
      ('WindowsDisabled', platforms.OperatingSystem.WINDOWS, None, None, False,
       True, False),
      ('InteractiveUxDisabled', None, 'OFF', None, False, True, False),
      ('StructuredErrorsAlways', None, None, 'always', False, True, False),
      ('StructuredErrorsLog', None, None, 'log', False, True, False),
      ('StructuredErrorsTerminal', None, None, 'terminal', False, True, False),
      ('ColorDisabled', None, None, None, True, True, False),
  )
  def testGetParser(self, platform, interactive_ux, show_structured_logs,
                    disable_color, enabled, expected_enabled):
    self.StartObjectPatch(platforms.OperatingSystem, 'Current').return_value = (
        platform or platforms.OperatingSystem.LINUX)
    properties.VALUES.core.interactive_ux_style.Set(interactive_ux or 'NORMAL')
    properties.VALUES.core.show_structured_logs.Set(
        show_structured_logs or 'never')
    properties.VALUES.core.disable_color.Set(disable_color)
    style_parser = parser.GetTypedTextParser(enabled=enabled)
    self.assertEqual(expected_enabled, style_parser.style_enabled)


if __name__ == '__main__':
  test_case.main()
