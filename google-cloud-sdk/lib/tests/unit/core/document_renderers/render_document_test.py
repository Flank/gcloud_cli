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
"""Tests for render_document.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib.core.document_renderers import test_base


class BadStyleMarkdownTests(test_base.Markdown):

  def testBadStyle(self):
    markdown = self.NULL_MARKDOWN
    self.Run('bad', markdown=markdown, expected=markdown,
             exception='Unknown markdown document style [bad]'
             ' -- must be one of: devsite, html, linter, man, markdown, text.')


class MarkdownCommandTests(test_base.Command):

  def testMarkdownCommandBadStyle(self):
    argv = ['render_document', '--style=bad']
    markdown = self.COMMAND_MARKDOWN
    with self.assertRaises(SystemExit):
      self.Run(argv, markdown)

  def testMarkdownCommandAllFlags(self):
    argv = ['render_document', '--style=markdown', '--title=Command Test',
            '--notes=render_document command test.']
    markdown = self.COMMAND_MARKDOWN
    expected = textwrap.dedent("""\
        # document command test

        ## NAME

        gcloud compute instances - read and manipulate Google Compute Engine virtual machine instances

        ## SYNOPSIS

        `gcloud compute instances` _COMMAND_ [*--format* _FORMAT_] [*--help*] [*--project* _PROJECT_ID_] [*--quiet*, *-q*] [*--trace-token* _TRACE_TOKEN_] [*-h*]

        ## DESCRIPTION

        Read and manipulate Google Compute Engine virtual machine instances.


        ## NOTES

        render_document command test.
        """)
    self.Run(argv, markdown, expected)


if __name__ == '__main__':
  test_base.main()
