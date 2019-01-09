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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.core.document_renderers import linter_renderer
from tests.lib.core.document_renderers import test_base


class LinterRendererTests(test_base.Markdown):

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
There are no errors for the NAME section.

There are no errors for the DESCRIPTION section.

There are no errors for the EXAMPLES section.

    """)
    self.Run('linter', markdown, expected, notes='')

  def testNameTooLong(self):
    test_linter_renderer = linter_renderer.LinterRenderer()
    markdown = textwrap.dedent("""\
# NAME

gcloud info - display information about the current gcloud environment and
this is making the line too long

# EXAMPLES
To run the fake command, run:

  $ link:gcloud/info[gcloud info]
    """)
    expected = textwrap.dedent("""\
Refer to the detailed style guide: go/cloud-sdk-help-guide#name
This is the analysis for NAME:
Please shorten the name section to less than """ +
                               str(test_linter_renderer._NAME_WORD_LIMIT) +
                               """ words.\n
There are no errors for the EXAMPLES section.\n\n""")
    self.Run('linter', markdown, expected, notes='')

  def testNoNameExplanation(self):
    markdown = textwrap.dedent("""\
# NAME
gcloud fake command -

# EXAMPLES

To run the fake command, run:

  $ link:gcloud/fake/command/[gcloud fake command]
    """)
    expected = textwrap.dedent("""\
Refer to the detailed style guide: go/cloud-sdk-help-guide#name
This is the analysis for NAME:
Please add an explanation for the command.

There are no errors for the EXAMPLES section.\n\n""")
    self.Run('linter', markdown, expected, notes='')

  def testNoSections(self):
    markdown = textwrap.dedent("""\
    """)
    expected = textwrap.dedent("""\
Refer to the detailed style guide: go/cloud-sdk-help-guide#examples
This is the analysis for EXAMPLES:
You have not included an example in the Examples section.\n\n""")
    self.Run('linter', markdown, expected, notes='')

  def testPersonalPronoun(self):
    markdown = textwrap.dedent("""\
# NAME
gcloud fake command - this is a brief summary

# EXAMPLES

To run the fake command, run:

  $ link:gcloud/fake/command/[gcloud fake command]
this is the examples section that has personal pronouns... me you us we bla
    """)
    expected = textwrap.dedent("""\
There are no errors for the NAME section.

Refer to the detailed style guide: go/cloud-sdk-help-guide#examples
This is the analysis for EXAMPLES:\nPlease remove personal pronouns.\n\n""")
    self.Run('linter', markdown, expected, notes='')

  def testNotHeadingToLint(self):
    markdown = textwrap.dedent("""\
# NAME
gcloud fake command - this is a brief summary

# EXAMPLES

To run the fake command, run:

  $ link:gcloud/fake/command/[gcloud fake command]

# NOT A HEADING TO KEEP

this is the filler text for the section not being kept
    """)
    expected = textwrap.dedent("""\
    There are no errors for the NAME section.

    There are no errors for the EXAMPLES section.\n\n""")
    self.Run('linter', markdown, expected, notes='')

# This test runs successfully when _analyze_example_flags_equals() is called.
# However this method is not invoked until b/121254697 is fixed.

#   def testNoEqualsInFlag(self):
#     markdown = textwrap.dedent("""\
# # NAME
# gcloud fake command - this is a brief summary
#
# # EXAMPLES
#
# To run the fake command, run:
#
#   $ link:gcloud/fake/command/[gcloud fake command] \
#     --good=value --bad bad_value
#
#     """)
#
#     expected = textwrap.dedent("""\
#     There are no errors for the NAME section.\n
#     Refer to the detailed style guide: go/cloud-sdk-help-guide#examples
#     This is the analysis for EXAMPLES:
#     There should be a `=` between the flag name and the value.
#     The following flags are not formatted properly:
#     bad\n
#     """)
#     self.Run('linter', markdown, expected, notes='')

if __name__ == '__main__':
  test_base.main()

