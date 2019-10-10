# -*- coding: utf-8 -*- #
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
"""Tests for man_renderer.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib.core.document_renderers import test_base


class ManRendererTests(test_base.Style):

  def testStyle1(self):
    self.Run(__file__, [], 'man', '.1')

  def testStyle2(self):
    self.Run(__file__, ['markdown'], 'man', '.1')

  def testStyle3(self):
    self.Run(__file__, ['markdown', 'markdown-command'], 'man', '.1')

  def testStyle4(self):
    self.Run(__file__, ['hidden-group'], 'man', '.1')

  def testStyle5(self):
    self.Run(__file__, ['hidden-group', 'hidden-command'], 'man', '.1')

  def testStyle6(self):
    self.Run(__file__, ['README'], 'man', '.1')

  def testStyle7(self):
    self.Run(__file__, ['RELEASE_NOTES'], 'man', '.1')


class ManMarkdownTests(test_base.Markdown):

  def testManNullInput(self):
    markdown = self.NULL_MARKDOWN
    expected = ''
    self.Run('man', markdown, expected)

  def testManNewNotes(self):
    markdown = self.NEW_NOTES_MARKDOWN
    expected = textwrap.dedent("""\

        .TH "NOTES" ""

        .SH "Test Title"


        .SH "SECTION"

        Section prose.


        .SH "NOTES"
        New note.
        """)
    self.Run('man', markdown, expected, notes='New note.')

  def testManInsertNotes(self):
    markdown = self.INSERT_NOTES_MARKDOWN
    expected = textwrap.dedent("""\

        .TH "NOTES" ""

        .SH "Test Title"


        .SH "SECTION"

        Section prose.


        .SH "NOTES"
        New note.

        Original note.
       """)
    self.Run('man', markdown, expected, notes='New note.')

  def testManTitle(self):
    markdown = self.TITLE_MARKDOWN
    expected = textwrap.dedent("""\

        .TH "New Title" ""

        .SH "Test Title"


        .SH "SECTION"

        Section prose.
        """)
    self.Run('man', markdown, expected, title='New Title')

  def testManRoot(self):
    markdown = self.ROOT_MARKDOWN
    expected = textwrap.dedent(r"""
      .TH "GCLOUD COMPONENT" 1


      .SH "SYNOPSIS"
      .HP
      gcloud component [\ \fIflags\fR\ ] [\ \fIpositionals\fR\ ]


      .SH "SECTION"

      Section prose about the gcloud component command.


      .SH "GCLOUD WIDE FLAGS"

      These are available in all commands: \-\-foo, \-\-bar and \-\-verbosity.
      """)
    self.Run('man', markdown, expected)

  def testManSingleQuoteRune(self):
    markdown = textwrap.dedent("""\
        == DESCRIPTION ==

        'This' short line should have a leading escape.

        'This' long long long long long long long long long long long line starting with a single quoted word should have a leading "escaped" single quote.
        """)
    expected = textwrap.dedent("""\

        .TH "Leading Single Quote" ""

        .SH "DESCRIPTION"

        \\'This' short line should have a leading escape.

        \\'This' long long long long long long long long long long long line starting
        with a single quoted word should have a leading "escaped" single quote.
        """)
    self.Run('man', markdown, expected, title='Leading Single Quote')

  def testManExampleNotBullet(self):
    markdown = textwrap.dedent(r"""
        == EXAMPLE ==

        This example should not render as a partial bullet list:

          $ gcloud compute ssh --zone abc-east-1 --\
              -- -vvv

        == FLAGS ==

        *--zone* _ZONE_::

        The zone of the instance to connect to.
        """)
    expected = textwrap.dedent(r"""

        .TH "Example Not Bullet" ""

        .SH "EXAMPLE"

        This example should not render as a partial bullet list:

        .RS 2m
        $ gcloud compute ssh \-\-zone abc\-east\-1 \-\-\e
            \-\- \-vvv
        .RE


        .SH "FLAGS"

        .RS 2m
        .TP 2m
        \fB\-\-zone\fR \fIZONE\fR
        The zone of the instance to connect to.
        .RE
        .sp
        """)
    self.Run('man', markdown, expected, title='Example Not Bullet')

  def testManCodeBlock(self):
    markdown = self.CODE_BLOCK_MARKDOWN
    expected = textwrap.dedent(r"""
        .TH "NOTES" ""

        .SH "DESCRIPTION"

        The basic format of a YAML argument file is:

        .RS 2m
        arg\-group1:
          arg1: value1  # a comment
          arg2: value2
          ...
        .RE

        .RS 2m
        # Another comment
        arg\-group2:
          arg3: value3
          ...
        .RE

        and pretty printed as yaml:

        .RS 2m
        arg\-group1:
          arg1: value1  # a comment
          arg2: value2
          ...
        .RE

        .RS 2m
        # Another comment
        arg\-group2:
          arg3: value3
          ...
        .RE

        List arguments may be specified within square brackets:

        .RS 2m
        device\-ids: [Nexus5, Nexus6, Nexus9]
        .RE

        or by using the alternate YAML list notation with one dash per list item with an
        unindented code block:

        .RS 2m
        device\-ids:
          \- Nexus5
          \- Nexus6
          \- Nexus9
        .RE

        .RS 2m
        device\-numbers:
          \- 5
          \- 6
          \- 9
        .RE

        and some python code for coverage:

        .RS 2m
        class Xyz(object):
          '''Some class.'''
        .RE

        .RS 2m
          def __init__(self, value):
            self.value = value
        .RE

        If a list argument only contains a single value, you may omit the square
        brackets:

        .RS 2m
        device\-ids: Nexus9
        .RE


        .SH "Composition"

        A special \fBinclude: [\fIARG_GROUP1\fR, ...]\fR syntax allows merging or
        composition of argument groups (see \fBEXAMPLES\fR below). Included argument
        groups can \fBinclude:\fR other argument groups within the same YAML file, with
        unlimited nesting.
        """)
    self.maxDiff = None  # pylint: disable=invalid-name
    self.Run('man', markdown, expected)

  def testManExampleBlock(self):
    markdown = self.EXAMPLE_BLOCK_MARKDOWN
    expected = textwrap.dedent(r"""
        .TH "NOTES" ""

        .SH "DESCRIPTION"

        The basic example is:

        .RS 2m
        # Run first:
        gcloud foo bar
        .RE

        .RS 2m
        # Run last:
        gcloud bar foo
        .RE

        However, in non\-leap year months with a blue moon:

        .RS 2m
        # Run first:
        gcloud bar foo
        .RE

        .RS 2m
        # Run last:
        gcloud foo bar
        .RE

        .RS 2m
        # Run again
        gcloud foo foo
        .RE

        .RS 2m
        device\-ids: [Nexus5, Nexus6, Nexus9]
        .RE

        And that's it.
        """)
    self.maxDiff = None  # pylint: disable=invalid-name
    self.Run('man', markdown, expected)

  def testManQuotedFontEmphasis(self):
    markdown = self.FONT_EMPHASIS_MARKDOWN
    expected = textwrap.dedent("""\

        .TH "NOTES" ""

        .SH "Test Title"


        .SH "SECTION"

        Double air quotes ``+\\-*/'' on non\\-identifier chars or single identifier chars
        ``x'' and inline \\f5*code`_blocks\\fR should disable markdown in the quoted
        string with air quotes \\f5retained/\\fR and code block quotes consumed.
        """)
    self.Run('man', markdown, expected)

  def testManLink(self):
    markdown = self.LINK_MARKDOWN
    expected = r"""
.TH "New Title" ""

.SH "Test Title"


.SH "SECTION"

Here are the link styles:
.RS 2m
.IP "\(bu" 2m
Style 1 display[this] (http://foo.bar) target and text.
.IP "\(bu" 2m
Style 1 http://foo.bar target only.
.IP "\(bu" 2m
Style 2 display[this] (http://foo.bar) text and target.
.IP "\(bu" 2m
Style 2 display[this] text and local target.
.IP "\(bu" 2m
Style 2 http://foo.bar target only.
.IP "\(bu" 2m
Style 2 foo#bar local target only.
.IP "\(bu" 2m
Style 2 [display[this]]() text only.
.IP "\(bu" 2m
Style 2 []() empty text and target.
.RE
.sp
"""
    self.Run('man', markdown, expected, title='New Title')

  def testManDefinitionList(self):
    markdown = self.DEFINITION_LIST_MARKDOWN
    expected = r"""
.TH "New Title" ""

.SH "NESTED DEFINITION LISTS"

Intro text.
.RS 2m
.TP 2m
\fBfirst top definition name\fR
First top definition description.
.RS 2m
.TP 2m
\fBfirst nested definition name\fR
First nested definition description.
.TP 2m
\fBlast nested definition name\fR
Last nested definition description.
.RE
.sp
Nested summary text.
.TP 2m
\fBlast top definition name\fR
Last top definition description.
.RE
.sp
Top summary text.


.SH "NESTED DEFINITION LISTS WITH POP"

Intro text.
.RS 2m
.TP 2m
\fBfirst top definition name\fR
First top definition description.
.RS 2m
.TP 2m
\fBfirst nested definition name\fR
First nested definition description.
.TP 2m
\fBlast nested definition name\fR
Last nested definition description.
.RE
.RE
.sp
Top summary text.
"""
    self.Run('man', markdown, expected, title='New Title')

  def testManDefinitionListEmptyItem(self):
    markdown = self.DEFINITION_LIST_EMPTY_ITEM_MARKDOWN
    expected = r"""
.TH "New Title" ""

.SH "DEFINITION LIST EMPTY ITEM TESTS"


.SH "POSITIONAL ARGUMENTS"

.RS 2m
.TP 2m
SUPERFLUOUS
Superfluous definition to bump the list nesting level.
.RS 2m
.TP 2m

g2 group description. At least one of these must be specified:

.RS 2m
.TP 2m
\fIFILE\fR
The input file.

.TP 2m

g21 details. At most one of these may be specified:

.RS 2m
.TP 2m
\fB\-\-flag\-21\-a\fR=\fIFLAG_21_A\fR
Help 21 a.

.TP 2m
\fB\-\-flag\-21\-b\fR=\fIFLAG_21_B\fR
Help 21 b.

.RE
.sp
.TP 2m

g22 details. At most one of these may be specified:

.RS 2m
.TP 2m
\fB\-\-flag\-22\-a\fR=\fIFLAG_22_A\fR
Help 22 a.

.TP 2m
\fB\-\-flag\-22\-b\fR=\fIFLAG_22_B\fR
Help 22 b.

.RE
.RE
.sp
.TP 2m

And an extraneous paragraph.

.RE
.RE
.sp

.SH "REQUIRED FLAGS"

.RS 2m
.TP 2m

g1 group details. Exactly one of these must be specified:

.RS 2m
.TP 2m

g11 details.
.RS 2m
.TP 2m
\fB\-\-flag\-11\-a\fR=\fIFLAG_11_A\fR
Help 11 a. This is a modal flag. It must be specified if any of the other
arguments in the group are specified.

.TP 2m
\fB\-\-flag\-11\-b\fR=\fIFLAG_11_B\fR
Help 11 b.

.RE
.sp
.TP 2m

g12 details.
.RS 2m
.TP 2m
\fB\-\-flag\-12\-a\fR=\fIFLAG_12_A\fR
Help 12 a. This is a modal flag. It must be specified if any of the other
arguments in the group are specified.

.TP 2m
\fB\-\-flag\-12\-b\fR=\fIFLAG_12_B\fR
Help 12 b.
.RE
.RE
.RE
.sp
"""
    self.Run('man', markdown, expected, title='New Title')


if __name__ == '__main__':
  test_base.main()
