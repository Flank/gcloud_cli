# -*- coding: utf-8 -*- #
# This Python file uses the following encoding: utf-8
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Base class for the style tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core.console.style import ansi
from googlecloudsdk.core.console.style import mappings
from googlecloudsdk.core.console.style import text
from tests.lib import sdk_test_base


class TestTextTypes(text._TextTypes):  # pylint: disable=protected-access
  BLUE = 1
  BLUE_AND_BOLD = 2
  BLUE_AND_BRACKETS = 3
  BOLD = 4
  ITALICS = 5


STYLE_MAPPINGS_TESTING = mappings.StyleMapping({
    TestTextTypes.BLUE: text.TextAttributes(
        '{}', color=ansi.Colors.BLUE, attrs=[]),
    TestTextTypes.BLUE_AND_BOLD: text.TextAttributes(
        '{}', color=ansi.Colors.BLUE, attrs=[ansi.Attrs.BOLD]),
    TestTextTypes.BLUE_AND_BRACKETS: text.TextAttributes(
        '[{}]', color=ansi.Colors.BLUE, attrs=[]),
    TestTextTypes.BOLD: text.TextAttributes(
        '{}', color=None, attrs=[ansi.Attrs.BOLD]),
    TestTextTypes.ITALICS: text.TextAttributes(
        '{}', color=None, attrs=[ansi.Attrs.ITALICS]),
})


class StyleTestBase(sdk_test_base.WithLogCapture):
  """Save and restore console attributes state."""

  def SetUp(self):
    properties.VALUES.core.color_theme.Set('testing')
    self.blue = '\x1b[38;5;4m'
    self.italics = '\x1b[3m'
    self.bold = '\x1b[1m'
    self.blue_italics = '\x1b[3;38;5;4m'
    self.blue_bold = '\x1b[1;38;5;4m'
    self.blue_bold_italics = '\x1b[1;3;38;5;4m'
    self.bold_italics = '\x1b[1;3m'
    self.no_italics = '\x1b[23m'
    self.no_bold = '\x1b[21m'
    self.no_blue_italics = '\x1b[23;39;0m'
    self.no_blue_bold = '\x1b[21;39;0m'
    self.no_blue_bold_italics = '\x1b[21;23;39;0m'
    self.no_bold_italics = '\x1b[21;23m'
    self.reset = '\x1b[39;0m'
