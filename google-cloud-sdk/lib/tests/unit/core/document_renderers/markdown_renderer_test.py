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
"""Tests for markdown_renderer.py."""

from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from tests.lib.core.document_renderers import test_base


class MarkdownRendererTests(test_base.Style):

  def testStyle1(self):
    self.Run(__file__, [], 'markdown', '.md')

  def testStyle2(self):
    self.Run(__file__, ['markdown'], 'markdown', '.md')

  def testStyle3(self):
    self.Run(__file__, ['markdown', 'markdown-command'], 'markdown', '.md')

  def testStyle4(self):
    self.Run(__file__, ['hidden-group'], 'markdown', '.md')

  def testStyle5(self):
    self.Run(__file__, ['hidden-group', 'hidden-command'], 'markdown', '.md')

  def testStyle6(self):
    self.Run(__file__, ['README'], 'markdown', '.md')

  def testStyle7(self):
    self.Run(__file__, ['RELEASE_NOTES'], 'markdown', '.md')


class MarkdownMarkdownTests(test_base.Markdown):

  def testMarkdownNullInput(self):
    markdown = self.NULL_MARKDOWN
    expected = ''
    self.Run('markdown', markdown, expected)

  def testMarkdownNewNotes(self):
    markdown = self.NEW_NOTES_MARKDOWN
    expected = textwrap.dedent("""\
        # Test Title

        ## SECTION

        Section prose.


        ## NOTES

        New note.
        """)
    self.Run('markdown', markdown, expected, notes='New note.')

  def testMarkdownInsertNotes(self):
    markdown = self.INSERT_NOTES_MARKDOWN
    expected = textwrap.dedent("""\
        # Test Title

        ## SECTION

        Section prose.

        ## NOTES

        New note.

        Original note.
       """)
    self.Run('markdown', markdown, expected, notes='New note.')

  def testMarkdownTitle(self):
    markdown = self.TITLE_MARKDOWN
    expected = textwrap.dedent("""\
        # Test Title

        ## SECTION

        Section prose.
        """)
    self.Run('markdown', markdown, expected, title='New Title')


if __name__ == '__main__':
  test_base.main()
