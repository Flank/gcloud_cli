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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.core.document_renderers import linter_renderer
from googlecloudsdk.core.document_renderers import render_document
from tests.lib import parameterized
from tests.lib.core.document_renderers import test_base


class LinterRendererTests(test_base.Markdown, parameterized.TestCase):

  def testGoodCommand(self):
    markdown = textwrap.dedent("""\
      # NAME
      gcloud fake command - this is a brief summary with no personal pronouns.

      # DESCRIPTION

      gcloud fake command is a filler command that does not exist. There are no
      personal pronouns in this description.

      # EXAMPLES

      To run the fake command, run:

        $ link:gcloud/fake/command/[gcloud fake command] positional

      This also has no personal pronouns and the example command starts with the
      command name.
    """)
    expected = textwrap.dedent("""\
      # NAME_PRONOUN_CHECK SUCCESS
      # NAME_DESCRIPTION_CHECK SUCCESS
      # NAME_LENGTH_CHECK SUCCESS
      There are no errors for the NAME section.
      # DESCRIPTION_PRONOUN_CHECK SUCCESS
      There are no errors for the DESCRIPTION section.
      # EXAMPLE_PRESENT_CHECK SUCCESS
      # EXAMPLES_PRONOUN_CHECK SUCCESS
      # EXAMPLE_FLAG_EQUALS_CHECK SUCCESS
      # EXAMPLE_NONEXISTENT_FLAG_CHECK SUCCESS
      There are no errors for the EXAMPLES section.
    """)
    meta_data = render_document.CommandMetaData(is_group=False)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  def testNoSections(self):
    markdown = textwrap.dedent("""\
    """)
    expected = textwrap.dedent("""\
      # EXAMPLE_PRESENT_CHECK FAILED: You have not included an example in the"""
                               """ Examples section.
    """)
    meta_data = render_document.CommandMetaData(is_group=False)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  def testNoExampleAlpha(self):
    markdown = textwrap.dedent("""\
      # NAME

      gcloud alpha fake command - fake alpha command to test not throwing """
                               """examples error
    """)
    expected = textwrap.dedent("""\
      # NAME_PRONOUN_CHECK SUCCESS
      # NAME_DESCRIPTION_CHECK SUCCESS
      # NAME_LENGTH_CHECK SUCCESS
      There are no errors for the NAME section.
    """)
    meta_data = render_document.CommandMetaData(is_group=False)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  def testNoExampleNotAlpha(self):
    markdown = textwrap.dedent("""\
      # NAME

      gcloud fake command - fake command to test throwing examples error
    """)
    expected = textwrap.dedent("""\
      # NAME_PRONOUN_CHECK SUCCESS
      # NAME_DESCRIPTION_CHECK SUCCESS
      # NAME_LENGTH_CHECK SUCCESS
      There are no errors for the NAME section.
      # EXAMPLE_PRESENT_CHECK FAILED: You have not included an example in the"""
                               """ Examples section.
    """)
    meta_data = render_document.CommandMetaData(is_group=False)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  def testExampleCheckNotAlphaMultilineCommandName(self):
    markdown = textwrap.dedent("""\
      # NAME

      gcloud long fake command with-subcommands subcommand-one subcommand-2 -
      fake command to test throwing examples error

      # EXAMPLES

      Example where the name of the command does not fit in one line and is
      thus broken down into many lines:

          $ gcloud long fake command with-subcommands subcommand-one \\
            subcommand-2 \\
                command-arg --command-flag=flag-value
    """)
    expected = textwrap.dedent("""\
      # NAME_PRONOUN_CHECK SUCCESS
      # NAME_DESCRIPTION_CHECK SUCCESS
      # NAME_LENGTH_CHECK SUCCESS
      There are no errors for the NAME section.
      # EXAMPLE_PRESENT_CHECK SUCCESS
      # EXAMPLES_PRONOUN_CHECK SUCCESS
      # EXAMPLE_FLAG_EQUALS_CHECK SUCCESS
      # EXAMPLE_NONEXISTENT_FLAG_CHECK SUCCESS
      There are no errors for the EXAMPLES section.
    """)
    meta_data = render_document.CommandMetaData(is_group=False)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  def testNameTooLong(self):
    test_linter_renderer = linter_renderer.LinterRenderer()
    markdown = textwrap.dedent("""\
      # NAME

      gcloud info - display information about the current gcloud environment and
      this is making the name section description way too long and over the """
                               """max length allowed
    """)
    expected = textwrap.dedent("""\
      # NAME_PRONOUN_CHECK SUCCESS
      # NAME_DESCRIPTION_CHECK SUCCESS
      # NAME_LENGTH_CHECK FAILED: Please shorten the name section description"""
                               ' to less than ' +
                               str(test_linter_renderer._NAME_WORD_LIMIT) +
                               """ words.
    """)
    meta_data = render_document.CommandMetaData(is_group=True)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  def testNoNameExplanation(self):
    markdown = textwrap.dedent("""\
      # NAME
      gcloud fake command -
    """)
    expected = textwrap.dedent("""\
      # NAME_PRONOUN_CHECK SUCCESS
      # NAME_DESCRIPTION_CHECK FAILED: Please add an explanation for the """
                               """command.
      # NAME_LENGTH_CHECK SUCCESS
    """)
    meta_data = render_document.CommandMetaData(is_group=True)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  @parameterized.named_parameters(
      ('Capital', 'She', 'she'),
      ('Repeated', 'he he', 'he'),
      ('Newline', 'Me\n', 'me'),
      ('Multiple pronouns', 'me he we', 'he\nme\nwe')
      )
  def testPersonalPronoun(self, help_text, pronouns):
    markdown = textwrap.dedent("""\
      # NAME
      gcloud fake command - this is a brief summary

      # DESCRIPTION
      this is the description section that has personal pronouns..."""
                               + help_text + '\n')
    expected = textwrap.dedent("""\
      # NAME_PRONOUN_CHECK SUCCESS
      # NAME_DESCRIPTION_CHECK SUCCESS
      # NAME_LENGTH_CHECK SUCCESS
      There are no errors for the NAME section.
      # DESCRIPTION_PRONOUN_CHECK FAILED: Please remove the following """
                               """personal pronouns in the DESCRIPTION section:
      """)
    expected += pronouns + '\n'
    meta_data = render_document.CommandMetaData(is_group=True)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  def testNotHeadingToLint(self):
    markdown = textwrap.dedent("""\
      # NAME
      gcloud fake command - this is a brief summary

      # NOT A HEADING TO KEEP

      this is the filler text for the section not being kept
    """)
    expected = textwrap.dedent("""\
      # NAME_PRONOUN_CHECK SUCCESS
      # NAME_DESCRIPTION_CHECK SUCCESS
      # NAME_LENGTH_CHECK SUCCESS
      There are no errors for the NAME section.
    """)
    meta_data = render_document.CommandMetaData(is_group=True)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  def testNotValidFlagForCommandNotEmptyFlag(self):
    markdown = textwrap.dedent("""\
      # NAME

      gcloud fake command - this is a brief summary

      # EXAMPLES
      To run the fake command, run:

        $ link:gcloud/fake/command/[gcloud fake command] \
        positional --good-flag-name=GOOD --bad-flag-name=BAD_VALUE

    """)
    expected = textwrap.dedent("""\
      # NAME_PRONOUN_CHECK SUCCESS
      # NAME_DESCRIPTION_CHECK SUCCESS
      # NAME_LENGTH_CHECK SUCCESS
      There are no errors for the NAME section.
      # EXAMPLE_PRESENT_CHECK SUCCESS
      # EXAMPLES_PRONOUN_CHECK SUCCESS
      # EXAMPLE_FLAG_EQUALS_CHECK SUCCESS
      # EXAMPLE_NONEXISTENT_FLAG_CHECK FAILED: The following flags are not """
                               """valid for the command: --bad-flag-name
    """)
    meta_data = render_document.CommandMetaData(flags=['--good-flag-name'],
                                                is_group=False)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  def testNotValidFlagForCommandEmptyFlag(self):
    markdown = textwrap.dedent("""\
      # NAME

      gcloud fake command - this is a brief summary

      # EXAMPLES
      To run the fake command, run:

        $ link:gcloud/fake/command/[gcloud fake command] \
        positional -- other things for command args

    """)
    expected = textwrap.dedent("""\
      # NAME_PRONOUN_CHECK SUCCESS
      # NAME_DESCRIPTION_CHECK SUCCESS
      # NAME_LENGTH_CHECK SUCCESS
      There are no errors for the NAME section.
      # EXAMPLE_PRESENT_CHECK SUCCESS
      # EXAMPLES_PRONOUN_CHECK SUCCESS
      # EXAMPLE_FLAG_EQUALS_CHECK SUCCESS
      # EXAMPLE_NONEXISTENT_FLAG_CHECK SUCCESS
      There are no errors for the EXAMPLES section.
    """)
    meta_data = render_document.CommandMetaData(flags=['--good-flag-name'],
                                                is_group=False)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  def testCatchNoEqualsInNonBoolFlag(self):
    markdown = textwrap.dedent("""\
      # NAME
      gcloud fake command - this is a brief summary

      # EXAMPLES

      To run the fake command, run:

        $ link:gcloud/fake/command/[gcloud fake command] \
          --good=value --bad bad_value

    """)
    expected = textwrap.dedent("""\
      # NAME_PRONOUN_CHECK SUCCESS
      # NAME_DESCRIPTION_CHECK SUCCESS
      # NAME_LENGTH_CHECK SUCCESS
      There are no errors for the NAME section.
      # EXAMPLE_PRESENT_CHECK SUCCESS
      # EXAMPLES_PRONOUN_CHECK SUCCESS
      # EXAMPLE_FLAG_EQUALS_CHECK FAILED: There should be an `=` between the """
                               """flag name and the value for the following """
                               """flags: --bad
      # EXAMPLE_NONEXISTENT_FLAG_CHECK SUCCESS
    """)
    meta_data = render_document.CommandMetaData(flags=['--good', '--bad'],
                                                is_group=False)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  def testIgnoreNoEqualsInBoolFlag(self):
    markdown = textwrap.dedent("""\
      # NAME
      gcloud fake command - this is a brief summary

      # EXAMPLES
      To run the fake command, run:

        $ link:gcloud/fake/command/[gcloud fake command] positional \
          --non-bool value --bool positional

    """)
    expected = textwrap.dedent("""\
      # NAME_PRONOUN_CHECK SUCCESS
      # NAME_DESCRIPTION_CHECK SUCCESS
      # NAME_LENGTH_CHECK SUCCESS
      There are no errors for the NAME section.
      # EXAMPLE_PRESENT_CHECK SUCCESS
      # EXAMPLES_PRONOUN_CHECK SUCCESS
      # EXAMPLE_FLAG_EQUALS_CHECK FAILED: There should be an `=` between the """
                               """flag name and the value for the following """
                               """flags: --non-bool
      # EXAMPLE_NONEXISTENT_FLAG_CHECK SUCCESS
    """)
    meta_data = render_document.CommandMetaData(flags=['--bool', '--non-bool'],
                                                bool_flags=['--bool'],
                                                is_group=False)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  def testLongCommandWithDescription(self):
    markdown = textwrap.dedent("""\
      # NAME
      gcloud fake command that is very long and takes up the whole line blah -
      this is a brief summary with no personal pronouns.

      # DESCRIPTION

      gcloud fake command is a filler command that does not exist. There are no
      personal pronouns in this description.
    """)
    expected = textwrap.dedent("""\
      # NAME_PRONOUN_CHECK SUCCESS
      # NAME_DESCRIPTION_CHECK SUCCESS
      # NAME_LENGTH_CHECK SUCCESS
      There are no errors for the NAME section.
      # DESCRIPTION_PRONOUN_CHECK SUCCESS
      There are no errors for the DESCRIPTION section.
      # EXAMPLE_PRESENT_CHECK FAILED: You have not included an example in the"""
                               """ Examples section.
    """)
    meta_data = render_document.CommandMetaData(is_group=False)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)


if __name__ == '__main__':
  test_base.main()

