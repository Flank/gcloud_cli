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

  def testGoodName(self):
    markdown = textwrap.dedent("""\
    # NAME

    gcloud info - display information about the current gcloud environment

    # EXAMPLES

    filler examples section
    """)

    expected = textwrap.dedent("""There are no errors for the NAME section.\n
There are no errors for the EXAMPLES section.\n\n""")
    self.Run('linter', markdown, expected, notes='')

  def testNameTooLong(self):
    test_linter_renderer = linter_renderer.LinterRenderer()
    markdown = textwrap.dedent("""\
    # NAME

    gcloud info - display information about the current gcloud environment and
    this is making the line too long

    # EXAMPLES

    filler examples section
    """)
    expected = textwrap.dedent("""\
Refer to the detailed style guide: go/cloud-sdk-help-guide#name
This is the analysis for NAME:\nPlease shorten the NAME section to less than """
                               + str(test_linter_renderer._NAME_WORD_LIMIT) +
                               """ words.\n
There are no errors for the EXAMPLES section.\n\n""")
    self.Run('linter', markdown, expected, notes='')

  def testGoodExampleSection(self):
    markdown = textwrap.dedent("""\
    # EXAMPLES

    filler example section
    """)
    expected = textwrap.dedent("""\
    There are no errors for the EXAMPLES section.\n\n""")
    self.Run('linter', markdown, expected, notes='')

  def testNoExamplesSection(self):
    markdown = textwrap.dedent("""\
    """)
    expected = textwrap.dedent("""\
Refer to the detailed style guide: go/cloud-sdk-help-guide#examples
This is the analysis for EXAMPLES:\nYou have not included an example.\n\n""")
    self.Run('linter', markdown, expected, notes='')

if __name__ == '__main__':
  test_base.main()
