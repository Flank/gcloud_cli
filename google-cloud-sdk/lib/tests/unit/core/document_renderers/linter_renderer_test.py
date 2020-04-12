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
import six


class LinterRendererTests(test_base.Markdown, parameterized.TestCase):
  test_linter_renderer = linter_renderer.LinterRenderer()

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

  def testMultilineCommandNameExampleCheck(self):
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

  @parameterized.named_parameters(
      ('name too long',
       '# NAME\n\ngcloud info - display information about the current gcloud '
       'environment and this is making the name section description way too '
       'long and over the max length allowed',
       '# NAME_PRONOUN_CHECK SUCCESS\n# NAME_DESCRIPTION_CHECK SUCCESS\n'
       '# NAME_LENGTH_CHECK FAILED: Please shorten the name section description'
       ' to less than'
       ' ' + six.text_type(test_linter_renderer._NAME_WORD_LIMIT) + ' words.\n'
      ),
      ('no name explanation',
       '# NAME\ngcloud fake command -\n',
       '# NAME_PRONOUN_CHECK SUCCESS\n# NAME_DESCRIPTION_CHECK FAILED: Please '
       'add an explanation for the command.\n# NAME_LENGTH_CHECK SUCCESS\n')
  )
  def testNameSection(self, markdown, expected):
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
      gcloud fake command group - this is a brief summary

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
    """)
    meta_data = render_document.CommandMetaData(is_group=True)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)

  @parameterized.named_parameters(
      ('topic command no example',
       '# NAME\ngcloud topic fake topic to describe - short description for the'
       ' fake idea.\n',
       '# NAME_PRONOUN_CHECK SUCCESS\n# NAME_DESCRIPTION_CHECK'
       ' SUCCESS\n# NAME_LENGTH_CHECK SUCCESS\nThere are no errors for the NAME'
       ' section.\n',
       False),
      ('alpha no example',
       '# NAME\n\ngcloud alpha fake command - fake alpha command to test not '
       'throwing examples error',
       '# NAME_PRONOUN_CHECK SUCCESS\n# NAME_DESCRIPTION_CHECK SUCCESS\n'
       '# NAME_LENGTH_CHECK SUCCESS\nThere are no errors for the NAME '
       'section.\n',
       False),
      ('no sections', '',
       '# EXAMPLE_PRESENT_CHECK FAILED: You have not included an example in '
       'the Examples section.\n',
       False),
      ('GA no example',
       '# NAME\ngcloud fake command - fake command to test throwing examples '
       'error',
       '# NAME_PRONOUN_CHECK SUCCESS\n# NAME_DESCRIPTION_CHECK SUCCESS\n'
       '# NAME_LENGTH_CHECK SUCCESS\nThere are no errors for the NAME section.'
       '\n# EXAMPLE_PRESENT_CHECK FAILED: You have not included an example in '
       'the Examples section.\n',
       False),
      ('GA command group no example',
       '# NAME\ngcloud fake command group - short description of group.',
       '# NAME_PRONOUN_CHECK SUCCESS\n# NAME_DESCRIPTION_CHECK SUCCESS\n'
       '# NAME_LENGTH_CHECK SUCCESS\nThere are no errors for the NAME '
       'section.\n',
       True),
  )

  def testNoExamples(self, markdown, expected, is_group):
    meta_data = render_document.CommandMetaData(is_group=is_group)
    self.Run('linter', markdown, expected, notes='', command_metadata=meta_data)


if __name__ == '__main__':
  test_base.main()

