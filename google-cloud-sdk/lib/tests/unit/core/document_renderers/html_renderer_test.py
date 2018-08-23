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
"""Tests for html_renderer.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib.core.document_renderers import test_base


class HTMLRendererTests(test_base.Style):

  def testStyle1(self):
    self.Run(__file__, [], 'html', '.html')

  def testStyle2(self):
    self.Run(__file__, ['markdown'], 'html', '.html')

  def testStyle3(self):
    self.Run(__file__, ['markdown', 'markdown-command'], 'html', '.html')

  def testStyle4(self):
    self.Run(__file__, ['hidden-group'], 'html', '.html')

  def testStyle5(self):
    self.Run(__file__, ['hidden-group', 'hidden-command'], 'html', '.html')

  def testStyle6(self):
    self.Run(__file__, ['README'], 'html', '.html')

  def testStyle7(self):
    self.Run(__file__, ['RELEASE_NOTES'], 'html', '.html')


class HTMLMarkdownTests(test_base.Markdown):

  def testHTMLNullInput(self):
    markdown = self.NULL_MARKDOWN
    expected = textwrap.dedent("""\
        <html>
        <head>
        <style>
          code { color: green; }
        </style>
        <script>
          window.onload = function() {
            if (parent.navigation.navigate) {
              parent.navigation.navigate(document.location.href);
            }
          }
        </script>
        <!--
                THIS DOC IS GENERATED.  DO NOT EDIT.
          -->
        <style>
          dd {
            margin-bottom: 1ex;
          }
          li {
            margin-top: 1ex; margin-bottom: 1ex;
          }
          .hangingindent {
            padding-left: 1.5em;
            text-indent: -1.5em;
          }
          .normalfont {
            font-weight: normal;
          }
          .notopmargin {
            margin-top: 0em;
          }
          .sectionbody {
            margin-top: .2em;
          }
        </style>
        </head>
        <body>
        <dl>

        </dl>
        </body>
        </html>
       """)
    self.Run('html', markdown, expected)

  def testHTMLNewNotes(self):
    markdown = self.NEW_NOTES_MARKDOWN
    expected = textwrap.dedent("""\
        <html>
        <head>
        <style>
          code { color: green; }
        </style>
        <script>
          window.onload = function() {
            if (parent.navigation.navigate) {
              parent.navigation.navigate(document.location.href);
            }
          }
        </script>
        <!--
                THIS DOC IS GENERATED.  DO NOT EDIT.
          -->
        <style>
          dd {
            margin-bottom: 1ex;
          }
          li {
            margin-top: 1ex; margin-bottom: 1ex;
          }
          .hangingindent {
            padding-left: 1.5em;
            text-indent: -1.5em;
          }
          .normalfont {
            font-weight: normal;
          }
          .notopmargin {
            margin-top: 0em;
          }
          .sectionbody {
            margin-top: .2em;
          }
        </style>
        </head>
        <body>
        <dl>

        <dt><h3>Test Title</h3></dt>
        <dd class="sectionbody">
        </dd>

        <dt><h4>SECTION</h4></dt>
        <dd class="sectionbody">
        Section prose.
        </dd>

        <dt><h4>NOTES</h4></dt>
        <dd class="sectionbody">
        New note.
        </dd>

        </dl>
        </body>
        </html>
       """)
    self.Run('html', markdown, expected, notes='New note.')

  def testHTMLInsertNotes(self):
    markdown = self.INSERT_NOTES_MARKDOWN
    expected = textwrap.dedent("""\
        <html>
        <head>
        <style>
          code { color: green; }
        </style>
        <script>
          window.onload = function() {
            if (parent.navigation.navigate) {
              parent.navigation.navigate(document.location.href);
            }
          }
        </script>
        <!--
                THIS DOC IS GENERATED.  DO NOT EDIT.
          -->
        <style>
          dd {
            margin-bottom: 1ex;
          }
          li {
            margin-top: 1ex; margin-bottom: 1ex;
          }
          .hangingindent {
            padding-left: 1.5em;
            text-indent: -1.5em;
          }
          .normalfont {
            font-weight: normal;
          }
          .notopmargin {
            margin-top: 0em;
          }
          .sectionbody {
            margin-top: .2em;
          }
        </style>
        </head>
        <body>
        <dl>

        <dt><h3>Test Title</h3></dt>
        <dd class="sectionbody">
        </dd>

        <dt><h4>SECTION</h4></dt>
        <dd class="sectionbody">
        Section prose.
        </dd>

        <dt><h4>NOTES</h4></dt>
        <dd class="sectionbody">
        New note.
        <p>
        Original note.
        </dd>

        </dl>
        </body>
        </html>
       """)
    self.Run('html', markdown, expected, notes='New note.')

  def testHTMLTitle(self):
    markdown = self.TITLE_MARKDOWN
    expected = textwrap.dedent("""\
        <html>
        <head>
        <title>New Title</title>
        <style>
          code { color: green; }
        </style>
        <script>
          window.onload = function() {
            if (parent.navigation.navigate) {
              parent.navigation.navigate(document.location.href);
            }
          }
        </script>
        <!--
                THIS DOC IS GENERATED.  DO NOT EDIT.
          -->
        <style>
          dd {
            margin-bottom: 1ex;
          }
          li {
            margin-top: 1ex; margin-bottom: 1ex;
          }
          .hangingindent {
            padding-left: 1.5em;
            text-indent: -1.5em;
          }
          .normalfont {
            font-weight: normal;
          }
          .notopmargin {
            margin-top: 0em;
          }
          .sectionbody {
            margin-top: .2em;
          }
        </style>
        </head>
        <body>
        <dl>

        <dt><h3>Test Title</h3></dt>
        <dd class="sectionbody">
        </dd>

        <dt><h4>SECTION</h4></dt>
        <dd class="sectionbody">
        Section prose.
        </dd>

        </dl>
        </body>
        </html>
       """)
    self.Run('html', markdown, expected, title='New Title')

  def testHTMLDeepList(self):
    markdown = self.DEEP_BULLET_MARKDOWN
    expected = textwrap.dedent("""\
      <html>
      <head>
      <style>
        code { color: green; }
      </style>
      <script>
        window.onload = function() {
          if (parent.navigation.navigate) {
            parent.navigation.navigate(document.location.href);
          }
        }
      </script>
      <!--
              THIS DOC IS GENERATED.  DO NOT EDIT.
        -->
      <style>
        dd {
          margin-bottom: 1ex;
        }
        li {
          margin-top: 1ex; margin-bottom: 1ex;
        }
        .hangingindent {
          padding-left: 1.5em;
          text-indent: -1.5em;
        }
        .normalfont {
          font-weight: normal;
        }
        .notopmargin {
          margin-top: 0em;
        }
        .sectionbody {
          margin-top: .2em;
        }
      </style>
      </head>
      <body>
      <dl>

      <dt><h3>Deep Bullet Test</h3></dt>
      <dd class="sectionbody">
      </dd>

      <dt><h4>SECTION</h4></dt>
      <dd class="sectionbody">
      <ul style="list-style-type:disc">
      <li>
      Level 1 bullet.
      <ul style="list-style-type:circle">
      <li>
      Level 2 bullet.
      <ul style="list-style-type:square">
      <li>
      Level 3 bullet.
      <ul style="list-style-type:disc">
      <li>
      Level 4 bullet.
      <ul style="list-style-type:circle">
      <li>
      Level 5 bullet.
      <ul style="list-style-type:square">
      <li>
      Level 6 bullet.
      <ul style="list-style-type:disc">
      <li>
      Level 7 bullet.
      <ul style="list-style-type:circle">
      <li>
      Level 8 bullet.
      <ul style="list-style-type:square">
      <li>
      Level 9 bullet.
      </li>
      </ul>
      </li>
      <li>
      Level 8 bullet.
      </li>
      </ul>
      </li>
      <li>
      Level 7 bullet.
      </li>
      </ul>
      </li>
      <li>
      Level 6 bullet.
      </li>
      </ul>
      </li>
      <li>
      Level 5 bullet.
      </li>
      </ul>
      </li>
      <li>
      Level 4 bullet.
      </li>
      </ul>
      </li>
      <li>
      Level 3 bullet.
      </li>
      </ul>
      </li>
      <li>
      Level 2 bullet.
      </li>
      </ul>
      </li>
      <li>
      Level 1 bullet.
      </li>
      </ul>
      <p>
      Post-list prose.
      </dd>

      </dl>
      </body>
      </html>
       """)
    self.Run('html', markdown, expected)

  def testHTMLDeepHeading(self):
    expected = textwrap.dedent("""\
      <html>
      <head>
      <title>New Title</title>
      <style>
        code { color: green; }
      </style>
      <script>
        window.onload = function() {
          if (parent.navigation.navigate) {
            parent.navigation.navigate(document.location.href);
          }
        }
      </script>
      <!--
              THIS DOC IS GENERATED.  DO NOT EDIT.
        -->
      <style>
        dd {
          margin-bottom: 1ex;
        }
        li {
          margin-top: 1ex; margin-bottom: 1ex;
        }
        .hangingindent {
          padding-left: 1.5em;
          text-indent: -1.5em;
        }
        .normalfont {
          font-weight: normal;
        }
        .notopmargin {
          margin-top: 0em;
        }
        .sectionbody {
          margin-top: .2em;
        }
      </style>
      </head>
      <body>
      <dl>

      <dt><h3>Deep Heading Test</h3></dt>
      <dd class="sectionbody">
      </dd>

      <dt><h4>SECTION</h4></dt>
      <dd class="sectionbody">
      Section prose.
      </dd>

      <dt><h5>Level 3 heading.</h5></dt>
      <dd class="sectionbody">
      Level 3 heading prose.
      </dd>

      <dt><h6>Level 4 heading.</h6></dt>
      <dd class="sectionbody">
      Level 4 heading prose.
      </dd>

      <dt><h7>Level 5 heading.</h7></dt>
      <dd class="sectionbody">
      Level 5 heading prose.
      </dd>

      <dt><h8>Level 6 heading.</h8></dt>
      <dd class="sectionbody">
      Level 6 heading prose.
      </dd>

      <dt><h9>Level 7 heading.</h9></dt>
      <dd class="sectionbody">
      Level 7 heading prose.
      </dd>

      <dt><h9>Level 8 heading.</h9></dt>
      <dd class="sectionbody">
      Level 8 heading prose.
      </dd>

      <dt><h9>Level 9 heading.</h9></dt>
      <dd class="sectionbody">
      Level 9 heading prose.
      </dd>

      <dt><h9>Level 8 heading.</h9></dt>
      <dd class="sectionbody">
      Level 8 heading prose.
      </dd>

      <dt><h9>Level 7 heading.</h9></dt>
      <dd class="sectionbody">
      Level 7 heading prose.
      </dd>

      <dt><h8>Level 6 heading.</h8></dt>
      <dd class="sectionbody">
      Level 6 heading prose.
      </dd>

      <dt><h7>Level 5 heading.</h7></dt>
      <dd class="sectionbody">
      Level 5 heading prose.
      </dd>

      <dt><h6>Level 4 heading.</h6></dt>
      <dd class="sectionbody">
      Level 4 heading prose.
      </dd>

      <dt><h5>Level 3 heading.</h5></dt>
      <dd class="sectionbody">
      Level 3 heading prose.
      </dd>

      <dt><h4>ANOTHER SECTION</h4></dt>
      <dd class="sectionbody">
      Another section prose.
      </dd>

      </dl>
      </body>
      </html>
       """)
    self.Run('html', self.DEEP_HEADING_MARKDOWN,
             expected, title='New Title')
    self.Run('html', self.DEEP_HEADING_MARKDOWN_NO_TAIL,
             expected, title='New Title')
    self.Run('html', self.DEEP_HEADING_MARKDOWN_HASH,
             expected, title='New Title')
    self.Run('html', self.DEEP_HEADING_MARKDOWN_HASH_NO_TAIL,
             expected, title='New Title')

  def testHTMLQuotedFontEmphasis(self):
    markdown = self.FONT_EMPHASIS_MARKDOWN
    expected = textwrap.dedent("""\
        <html>
        <head>
        <title>Test Title</title>
        <style>
          code { color: green; }
        </style>
        <script>
          window.onload = function() {
            if (parent.navigation.navigate) {
              parent.navigation.navigate(document.location.href);
            }
          }
        </script>
        <!--
                THIS DOC IS GENERATED.  DO NOT EDIT.
          -->
        <style>
          dd {
            margin-bottom: 1ex;
          }
          li {
            margin-top: 1ex; margin-bottom: 1ex;
          }
          .hangingindent {
            padding-left: 1.5em;
            text-indent: -1.5em;
          }
          .normalfont {
            font-weight: normal;
          }
          .notopmargin {
            margin-top: 0em;
          }
          .sectionbody {
            margin-top: .2em;
          }
        </style>
        </head>
        <body>
        <dl>

        <dt><h3>Test Title</h3></dt>
        <dd class="sectionbody">
        </dd>

        <dt><h4>SECTION</h4></dt>
        <dd class="sectionbody">
        Double air quotes ``+-*/&acute;&acute; on non-identifier chars or single
        identifier chars ``x&acute;&acute; and inline <code>*code`_blocks</code> should
        disable markdown in the quoted string with air quotes <code>retained/</code> and
        code block quotes consumed.
        </dd>

        </dl>
        </body>
        </html>
        """)
    self.Run('html', markdown, expected, title='Test Title')

  def testHTMLCodeBlock(self):
    markdown = self.CODE_BLOCK_MARKDOWN
    expected = textwrap.dedent("""\
        <html>
        <head>
        <title>New Title</title>
        <style>
          code { color: green; }
        </style>
        <script>
          window.onload = function() {
            if (parent.navigation.navigate) {
              parent.navigation.navigate(document.location.href);
            }
          }
        </script>
        <!--
                THIS DOC IS GENERATED.  DO NOT EDIT.
          -->
        <style>
          dd {
            margin-bottom: 1ex;
          }
          li {
            margin-top: 1ex; margin-bottom: 1ex;
          }
          .hangingindent {
            padding-left: 1.5em;
            text-indent: -1.5em;
          }
          .normalfont {
            font-weight: normal;
          }
          .notopmargin {
            margin-top: 0em;
          }
          .sectionbody {
            margin-top: .2em;
          }
        </style>
        </head>
        <body>
        <dl>

        <dt><h4>DESCRIPTION</h4></dt>
        <dd class="sectionbody">
        The basic format of a YAML argument file is:
        <p><code>
        &nbsp;&nbsp;arg-group1:<br>
        &nbsp;&nbsp;&nbsp;&nbsp;arg1: value1  # a comment<br>
        &nbsp;&nbsp;&nbsp;&nbsp;arg2: value2<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&hellip;<br>
        </code>

        <p><code>
        &nbsp;&nbsp;# Another comment<br>
        &nbsp;&nbsp;arg-group2:<br>
        &nbsp;&nbsp;&nbsp;&nbsp;arg3: value3<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&hellip;<br>
        </code>

        <p>
        and pretty printed as yaml:
        <p><code>
        &nbsp;&nbsp;arg-group1:<br>
        &nbsp;&nbsp;&nbsp;&nbsp;arg1: value1  # a comment<br>
        &nbsp;&nbsp;&nbsp;&nbsp;arg2: value2<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&hellip;<br>
        </code>

        <p><code>
        &nbsp;&nbsp;# Another comment<br>
        &nbsp;&nbsp;arg-group2:<br>
        &nbsp;&nbsp;&nbsp;&nbsp;arg3: value3<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&hellip;<br>
        </code>

        <p>
        List arguments may be specified within square brackets:
        <p><code>
        &nbsp;&nbsp;device-ids: [Nexus5, Nexus6, Nexus9]<br>
        </code>

        <p>
        or by using the alternate YAML list notation with one dash per list item with an
        unindented code block:
        <p><code>
        &nbsp;&nbsp;device-ids:<br>
        &nbsp;&nbsp;&nbsp;&nbsp;- Nexus5<br>
        &nbsp;&nbsp;&nbsp;&nbsp;- Nexus6<br>
        &nbsp;&nbsp;&nbsp;&nbsp;- Nexus9<br>
        </code>

        <p><code>
        &nbsp;&nbsp;device-numbers:<br>
        &nbsp;&nbsp;&nbsp;&nbsp;- 5<br>
        &nbsp;&nbsp;&nbsp;&nbsp;- 6<br>
        &nbsp;&nbsp;&nbsp;&nbsp;- 9<br>
        </code>

        <p>
        and some python code for coverage:
        <p><code>
        &nbsp;&nbsp;class Xyz(object):<br>
        &nbsp;&nbsp;&nbsp;&nbsp;'''Some class.'''<br>
        </code>

        <p><code>
        &nbsp;&nbsp;&nbsp;&nbsp;def __init__(self, value):<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;self.value = value<br>
        </code>

        <p>
        If a list argument only contains a single value, you may omit the square
        brackets:
        <p><code>
        &nbsp;&nbsp;device-ids: Nexus9<br>
        </code>

        </dd>

        <dt><h5>Composition</h5></dt>
        <dd class="sectionbody">
        A special <code>include: [<code><var>ARG_GROUP1</var></code>, &hellip;]</code>
        syntax allows merging or composition of argument groups (see
        <code>EXAMPLES</code> below). Included argument groups can <code>include:</code>
        other argument groups within the same YAML file, with unlimited nesting.
        </dd>

        </dl>
        </body>
        </html>
       """)
    self.maxDiff = 4096
    self.Run('html', markdown, expected, title='New Title')

  def testHTMLExampleBlock(self):
    markdown = self.EXAMPLE_BLOCK_MARKDOWN
    expected = textwrap.dedent("""\
        <html>
        <head>
        <title>New Title</title>
        <style>
          code { color: green; }
        </style>
        <script>
          window.onload = function() {
            if (parent.navigation.navigate) {
              parent.navigation.navigate(document.location.href);
            }
          }
        </script>
        <!--
                THIS DOC IS GENERATED.  DO NOT EDIT.
          -->
        <style>
          dd {
            margin-bottom: 1ex;
          }
          li {
            margin-top: 1ex; margin-bottom: 1ex;
          }
          .hangingindent {
            padding-left: 1.5em;
            text-indent: -1.5em;
          }
          .normalfont {
            font-weight: normal;
          }
          .notopmargin {
            margin-top: 0em;
          }
          .sectionbody {
            margin-top: .2em;
          }
        </style>
        </head>
        <body>
        <dl>

        <dt><h4>DESCRIPTION</h4></dt>
        <dd class="sectionbody">
        The basic example is:
        <p><code>
        &nbsp;&nbsp;# Run first:<br>
        &nbsp;&nbsp;gcloud foo bar<br>
        </code>

        <p><code>
        &nbsp;&nbsp;# Run last:<br>
        &nbsp;&nbsp;gcloud bar foo<br>
        </code>

        <p>
        However, in non-leap year months with a blue moon:
        <p><code>
        &nbsp;&nbsp;# Run first:<br>
        &nbsp;&nbsp;gcloud bar foo<br>
        </code>

        <p><code>
        &nbsp;&nbsp;# Run last:<br>
        &nbsp;&nbsp;gcloud foo bar<br>
        </code>

        <p><code>
        &nbsp;&nbsp;# Run again<br>
        &nbsp;&nbsp;gcloud foo foo<br>
        </code>

        <p><code>
        &nbsp;&nbsp;device-ids: [Nexus5, Nexus6, Nexus9]<br>
        </code>

        <p>
        And that's it.
        </dd>

        </dl>
        </body>
        </html>
       """)
    self.Run('html', markdown, expected, title='New Title')

  def testHTMLLink(self):
    markdown = self.LINK_MARKDOWN
    expected = textwrap.dedent("""\
        <html>
        <head>
        <title>New Title</title>
        <style>
          code { color: green; }
        </style>
        <script>
          window.onload = function() {
            if (parent.navigation.navigate) {
              parent.navigation.navigate(document.location.href);
            }
          }
        </script>
        <!--
                THIS DOC IS GENERATED.  DO NOT EDIT.
          -->
        <style>
          dd {
            margin-bottom: 1ex;
          }
          li {
            margin-top: 1ex; margin-bottom: 1ex;
          }
          .hangingindent {
            padding-left: 1.5em;
            text-indent: -1.5em;
          }
          .normalfont {
            font-weight: normal;
          }
          .notopmargin {
            margin-top: 0em;
          }
          .sectionbody {
            margin-top: .2em;
          }
        </style>
        </head>
        <body>
        <dl>

        <dt><h3>Test Title</h3></dt>
        <dd class="sectionbody">
        </dd>

        <dt><h4>SECTION</h4></dt>
        <dd class="sectionbody">
        Here are the link styles:
        <ul style="list-style-type:disc">
        <li>
        Style 1 <a href="http://foo.bar" target=_top>display[this]</a> target and text.
        </li>
        <li>
        Style 1 <a href="http://foo.bar" target=_top>http://foo.bar</a> target only.
        </li>
        <li>
        Style 2 <a href="http://foo.bar" target=_top>display[this]</a> text and target.
        </li>
        <li>
        Style 2 <a href="../../..">display[this]</a> text and local target.
        </li>
        <li>
        Style 2 <a href="http://foo.bar" target=_top>http://foo.bar</a> target only.
        </li>
        <li>
        Style 2 <a href="foo#bar">foo#bar</a> local target only.
        </li>
        <li>
        Style 2 [display[this]]() text only.
        </li>
        <li>
        Style 2 []() empty text and target.
        </li>
        </ul>
        </dd>

        </dl>
        </body>
        </html>
       """)
    self.maxDiff = None
    self.Run('html', markdown, expected, title='New Title')

  def testHTMLSynopsis(self):
    markdown = textwrap.dedent("""\
        # GCLOUD_COMPUTE_BACKEND-SERVICES_UPDATE-BACKEND(1)


        ## NAME

        gcloud compute backend-services update-backend - update an existing backend in a backend service


        ## SYNOPSIS

        `gcloud compute backend-services update-backend` _NAME_ *--instance-group*=_INSTANCE_GROUP_ [*--balancing-mode*=_BALANCING_MODE_] [*--capacity-scaler*=_CAPACITY_SCALER_] [*--description*=_DESCRIPTION_] [*--max-utilization*=_MAX_UTILIZATION_] [*--instance-group-zone*=_INSTANCE_GROUP_ZONE_ | *--zone*=_ZONE_] [*--max-connections*=_MAX_CONNECTIONS_ | *--max-connections-per-instance*=_MAX_CONNECTIONS_PER_INSTANCE_ | *--max-rate*=_MAX_RATE_ | *--max-rate-per-instance*=_MAX_RATE_PER_INSTANCE_] [_GLOBAL-FLAG ..._]


        ## DESCRIPTION

        *gcloud compute backend-services update-backend* updates a backend that is part of a backend
        service. This is useful for changing the way a backend
        behaves. Example changes that can be made include changing the
        load balancing policy and `_draining_` a backend by setting
        its capacity scaler to zero.
        """)
    expected = textwrap.dedent("""\
        <html>
        <head>
        <title>New Title</title>
        <style>
          code { color: green; }
        </style>
        <script>
          window.onload = function() {
            if (parent.navigation.navigate) {
              parent.navigation.navigate(document.location.href);
            }
          }
        </script>
        <!--
                THIS DOC IS GENERATED.  DO NOT EDIT.
          -->
        <style>
          dd {
            margin-bottom: 1ex;
          }
          li {
            margin-top: 1ex; margin-bottom: 1ex;
          }
          .hangingindent {
            padding-left: 1.5em;
            text-indent: -1.5em;
          }
          .normalfont {
            font-weight: normal;
          }
          .notopmargin {
            margin-top: 0em;
          }
          .sectionbody {
            margin-top: .2em;
          }
        </style>
        </head>
        <body>
        <dl>

        <dt><h4>NAME</h4></dt>
        <dd class="sectionbody">
        <dl class="notopmargin"><dt class="hangingindent"><span class="normalfont">
        gcloud compute backend-services update-backend - update an existing backend in a backend service
        </span></dt></dl>
        </dd>

        <dt><h4>SYNOPSIS</h4></dt>
        <dd class="sectionbody">
        <dl class="notopmargin"><dt class="hangingindent"><span class="normalfont">
        <code>gcloud compute backend-services update-backend</code> <code><var>NAME</var></code> <code>--instance-group</code>=<code><var>INSTANCE_GROUP</var></code> <nobr>[<code>--balancing-mode</code>=<code><var>BALANCING_MODE</var></code>]</nobr> <nobr>[<code>--capacity-scaler</code>=<code><var>CAPACITY_SCALER</var></code>]</nobr> <nobr>[<code>--description</code>=<code><var>DESCRIPTION</var></code>]</nobr> <nobr>[<code>--max-utilization</code>=<code><var>MAX_UTILIZATION</var></code>]</nobr> <nobr>[<code>--instance-group-zone</code>=<code><var>INSTANCE_GROUP_ZONE</var></code></nobr> <nobr>&nbsp;&nbsp;&nbsp;&nbsp;| <code>--zone</code>=<code><var>ZONE</var></code>]</nobr> <nobr>[<code>--max-connections</code>=<code><var>MAX_CONNECTIONS</var></code></nobr> <nobr>&nbsp;&nbsp;&nbsp;&nbsp;| <code>--max-connections-per-instance</code>=<code><var>MAX_CONNECTIONS_PER_INSTANCE</var></code></nobr> <nobr>&nbsp;&nbsp;&nbsp;&nbsp;| <code>--max-rate</code>=<code><var>MAX_RATE</var></code></nobr> <nobr>&nbsp;&nbsp;&nbsp;&nbsp;| <code>--max-rate-per-instance</code>=<code><var>MAX_RATE_PER_INSTANCE</var></code>]</nobr> <nobr>[<code><var>GLOBAL-FLAG &hellip;</var></code>]</nobr>
        </span></dt></dl>
        </dd>

        <dt><h4>DESCRIPTION</h4></dt>
        <dd class="sectionbody">
        <code>gcloud compute backend-services update-backend</code> updates a backend
        that is part of a backend service. This is useful for changing the way a backend
        behaves. Example changes that can be made include changing the load balancing
        policy and <code><code><var>draining</var></code></code> a backend by setting
        its capacity scaler to zero.
        </dd>

        </dl>
        </body>
        </html>
""")
    self.maxDiff = None
    self.Run('html', markdown, expected, title='New Title')

  def testHTMLDefinitionList(self):
    markdown = self.DEFINITION_LIST_MARKDOWN
    expected = textwrap.dedent("""\
        <html>
        <head>
        <title>New Title</title>
        <style>
          code { color: green; }
        </style>
        <script>
          window.onload = function() {
            if (parent.navigation.navigate) {
              parent.navigation.navigate(document.location.href);
            }
          }
        </script>
        <!--
                THIS DOC IS GENERATED.  DO NOT EDIT.
          -->
        <style>
          dd {
            margin-bottom: 1ex;
          }
          li {
            margin-top: 1ex; margin-bottom: 1ex;
          }
          .hangingindent {
            padding-left: 1.5em;
            text-indent: -1.5em;
          }
          .normalfont {
            font-weight: normal;
          }
          .notopmargin {
            margin-top: 0em;
          }
          .sectionbody {
            margin-top: .2em;
          }
        </style>
        </head>
        <body>
        <dl>

        <dt><h4>NESTED DEFINITION LISTS</h4></dt>
        <dd class="sectionbody">
        Intro text.
        <dl>
        <dt id="first-top-definition-name"><span class="normalfont"><code>first top definition name</code></span></dt>
        <dd>
        First top definition description.
        <dl>
        <dt id="first-nested-definition-name"><span class="normalfont"><code>first nested definition name</code></span></dt>
        <dd>
        First nested definition description.
        </dd>
        <dt id="last-nested-definition-name"><span class="normalfont"><code>last nested definition name</code></span></dt>
        <dd>
        Last nested definition description.
        </dd>
        </dl>
        Nested summary text.
        </dd>
        <dt id="last-top-definition-name"><span class="normalfont"><code>last top definition name</code></span></dt>
        <dd>
        Last top definition description.
        </dd>
        </dl>
        Top summary text.
        </dd>

        <dt><h4>NESTED DEFINITION LISTS WITH POP</h4></dt>
        <dd class="sectionbody">
        Intro text.
        <dl>
        <dt id="first-top-definition-name-1"><span class="normalfont"><code>first top definition name</code></span></dt>
        <dd>
        First top definition description.
        <dl>
        <dt id="first-nested-definition-name-1"><span class="normalfont"><code>first nested definition name</code></span></dt>
        <dd>
        First nested definition description.
        </dd>
        <dt id="last-nested-definition-name-1"><span class="normalfont"><code>last nested definition name</code></span></dt>
        <dd>
        Last nested definition description.
        </dd>
        </dl>
        </dd>
        </dl>
        Top summary text.
        </dd>

        </dl>
        </body>
        </html>
""")
    self.maxDiff = None
    self.Run('html', markdown, expected, title='New Title')

  def testHTMLDefinitionListEmptyItem(self):
    markdown = self.DEFINITION_LIST_EMPTY_ITEM_MARKDOWN
    expected = textwrap.dedent("""\
        <html>
        <head>
        <title>New Title</title>
        <style>
          code { color: green; }
        </style>
        <script>
          window.onload = function() {
            if (parent.navigation.navigate) {
              parent.navigation.navigate(document.location.href);
            }
          }
        </script>
        <!--
                THIS DOC IS GENERATED.  DO NOT EDIT.
          -->
        <style>
          dd {
            margin-bottom: 1ex;
          }
          li {
            margin-top: 1ex; margin-bottom: 1ex;
          }
          .hangingindent {
            padding-left: 1.5em;
            text-indent: -1.5em;
          }
          .normalfont {
            font-weight: normal;
          }
          .notopmargin {
            margin-top: 0em;
          }
          .sectionbody {
            margin-top: .2em;
          }
        </style>
        </head>
        <body>
        <dl>

        <dt><h3>DEFINITION LIST EMPTY ITEM TESTS</h3></dt>
        <dd class="sectionbody">
        </dd>

        <dt><h4>POSITIONAL ARGUMENTS</h4></dt>
        <dd class="sectionbody">
        <dl class="notopmargin">
        <dt id="SUPERFLUOUS"><span class="normalfont">SUPERFLUOUS</span></dt>
        <dd>
        Superfluous definition to bump the list nesting level.
        <dl>
        <dt><span class="normalfont">
        g2 group description. At least one of these must be specified:
        <dl>
        <dt id="FILE"><span class="normalfont"><code><var>FILE</var></code></span></dt>
        <dd>
        The input file.
        </dd>
        <dd>
        g21 details. At most one of these may be specified:
        <dl>
        <dt id="--flag-21-a"><span class="normalfont"><code>--flag-21-a</code>=<code><var>FLAG_21_A</var></code></span></dt>
        <dd>
        Help 21 a.
        </dd>
        <dt id="--flag-21-b"><span class="normalfont"><code>--flag-21-b</code>=<code><var>FLAG_21_B</var></code></span></dt>
        <dd>
        Help 21 b.
        </dd>
        </dl>
        </dd>
        <dd>
        g22 details. At most one of these may be specified:
        <dl>
        <dt id="--flag-22-a"><span class="normalfont"><code>--flag-22-a</code>=<code><var>FLAG_22_A</var></code></span></dt>
        <dd>
        Help 22 a.
        </dd>
        <dt id="--flag-22-b"><span class="normalfont"><code>--flag-22-b</code>=<code><var>FLAG_22_B</var></code></span></dt>
        <dd>
        Help 22 b.
        </dd>
        </dl>
        </dd>
        </dl>
        </dt>
        <dt><span class="normalfont">
        And an extraneous paragraph.
        </dt>
        </dl>
        </dd>
        </dl>
        </dd>

        <dt><h4>REQUIRED FLAGS</h4></dt>
        <dd class="sectionbody">
        <dl class="notopmargin">
        <dt><span class="normalfont">
        g1 group details. Exactly one of these must be specified:
        <dl>
        <dd>
        g11 details.
        <dl>
        <dt id="--flag-11-a"><span class="normalfont"><code>--flag-11-a</code>=<code><var>FLAG_11_A</var></code></span></dt>
        <dd>
        Help 11 a. This is a modal flag. It must be specified if any of the other
        arguments in the group are specified.
        </dd>
        <dt id="--flag-11-b"><span class="normalfont"><code>--flag-11-b</code>=<code><var>FLAG_11_B</var></code></span></dt>
        <dd>
        Help 11 b.
        </dd>
        </dl>
        </dd>
        <dd>
        g12 details.
        <dl>
        <dt id="--flag-12-a"><span class="normalfont"><code>--flag-12-a</code>=<code><var>FLAG_12_A</var></code></span></dt>
        <dd>
        Help 12 a. This is a modal flag. It must be specified if any of the other
        arguments in the group are specified.
        </dd>
        <dt id="--flag-12-b"><span class="normalfont"><code>--flag-12-b</code>=<code><var>FLAG_12_B</var></code></span></dt>
        <dd>
        Help 12 b.
        </dd>
        </dl>
        </dd>
        </dl>
        </dt>
        </dl>
        </dd>

        </dl>
        </body>
        </html>
""")
    self.maxDiff = None
    self.Run('html', markdown, expected, title='New Title')


if __name__ == '__main__':
  test_base.main()
