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
"""Tests for devsite_renderer.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib.core.document_renderers import test_base


class DevSiteRendererTests(test_base.Style):

  def testStyle1(self):
    self.Run(__file__, [], 'devsite', '.devsite')

  def testStyle2(self):
    self.Run(__file__, ['markdown'], 'devsite', '.devsite')

  def testStyle3(self):
    self.Run(__file__, ['markdown', 'markdown-command'], 'devsite', '.devsite')

  def testStyle4(self):
    self.Run(__file__, ['hidden-group'], 'devsite', '.devsite')

  def testStyle5(self):
    self.Run(__file__,
             ['hidden-group', 'hidden-command'], 'devsite', '.devsite')

  def testStyle6(self):
    self.Run(__file__, ['README'], 'devsite', '.devsite')

  def testStyle7(self):
    self.Run(__file__, ['RELEASE_NOTES'], 'devsite', '.devsite')


class DevSiteMarkdownTests(test_base.Markdown):

  def testDevSiteNullInput(self):
    markdown = self.NULL_MARKDOWN
    expected = textwrap.dedent("""\
        <html devsite="">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="project_path" value="/sdk/docs/_project.yaml">
        <meta name="book_path" value="/sdk/_book.yaml">
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
    self.Run('devsite', markdown, expected)

  def testDevSiteNewNotes(self):
    markdown = self.NEW_NOTES_MARKDOWN
    expected = textwrap.dedent("""\
        <html devsite="">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="project_path" value="/sdk/docs/_project.yaml">
        <meta name="book_path" value="/sdk/_book.yaml">
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

        <section id="Test-Title">
        <dt>Test Title</dt>
        <dd class="sectionbody">
        </dd>
        </section>

        <section id="SECTION">
        <dt>SECTION</dt>
        <dd class="sectionbody">
        Section prose.
        </dd>
        </section>

        <section id="NOTES">
        <dt>NOTES</dt>
        <dd class="sectionbody">
        New note.
        </dd>
        </section>

        </dl>
        </body>
        </html>
        """)
    self.Run('devsite', markdown, expected, notes='New note.')

  def testDevSiteInsertNotes(self):
    markdown = self.INSERT_NOTES_MARKDOWN
    expected = textwrap.dedent("""\
        <html devsite="">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="project_path" value="/sdk/docs/_project.yaml">
        <meta name="book_path" value="/sdk/_book.yaml">
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

        <section id="Test-Title">
        <dt>Test Title</dt>
        <dd class="sectionbody">
        </dd>
        </section>

        <section id="SECTION">
        <dt>SECTION</dt>
        <dd class="sectionbody">
        Section prose.
        </dd>
        </section>

        <section id="NOTES">
        <dt>NOTES</dt>
        <dd class="sectionbody">
        New note.
        <p>
        Original note.
        </dd>
        </section>

        </dl>
        </body>
        </html>
        """)
    self.Run('devsite', markdown, expected, notes='New note.')

  def testDevSiteTitle(self):
    markdown = self.TITLE_MARKDOWN
    expected = textwrap.dedent("""\
        <html devsite="">
        <head>
        <title>New Title</title>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="project_path" value="/sdk/docs/_project.yaml">
        <meta name="book_path" value="/sdk/_book.yaml">
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

        <section id="Test-Title">
        <dt>Test Title</dt>
        <dd class="sectionbody">
        </dd>
        </section>

        <section id="SECTION">
        <dt>SECTION</dt>
        <dd class="sectionbody">
        Section prose.
        </dd>
        </section>

        </dl>
        </body>
        </html>
        """)
    self.Run('devsite', markdown, expected, title='New Title')

  def testDevSiteRoot(self):
    markdown = self.ROOT_MARKDOWN
    expected = textwrap.dedent("""\
        <html devsite="">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="project_path" value="/sdk/docs/_project.yaml">
        <meta name="book_path" value="/sdk/_book.yaml">
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

        <section id="SYNOPSIS">
        <dt>SYNOPSIS</dt>
        <dd class="sectionbody">
        <dl class="notopmargin"><dt class="hangingindent"><span class="normalfont">
        gcloud component <nobr>[ <code><var>flags</var></code> ]</nobr> <nobr>[ <code><var>positionals</var></code> ]</nobr>
        </span></dt></dl>
        </dd>
        </section>

        <section id="SECTION">
        <dt>SECTION</dt>
        <dd class="sectionbody">
        Section prose about the gcloud component command.
        </dd>
        </section>

        <section id="GCLOUD-WIDE-FLAGS">
        <dt>GCLOUD WIDE FLAGS</dt>
        <dd class="sectionbody">
        These are available in all commands: <a href="/sdk/gcloud
        component/reference/#--foo">--foo</a>, <a href="/sdk/gcloud
        component/reference/#--bar">--bar</a> and <a href="/sdk/gcloud
        component/reference/#--verbosity">--verbosity</a>.
        </dd>
        </section>

        </dl>
        </body>
        </html>
        """)
    self.Run('devsite', markdown, expected)

  def testDevSiteLinkOnly(self):
    markdown = self.LINK_ONLY_MARKDOWN
    expected = textwrap.dedent("""\
        <html devsite="">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="project_path" value="/sdk/docs/_project.yaml">
        <meta name="book_path" value="/sdk/_book.yaml">
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

        <section id="Test-Title">
        <dt>Test Title</dt>
        <dd class="sectionbody">
        </dd>
        </section>

        <section id="SECTION">
        <dt>SECTION</dt>
        <dd class="sectionbody">
        Test embedded[http://link/this]link in text.
        </dd>
        </section>

        </dl>
        </body>
        </html>
        """)
    self.Run('devsite', markdown, expected)

  def testDevSiteLink(self):
    markdown = self.LINK_MARKDOWN
    expected = textwrap.dedent("""\
        <html devsite="">
        <head>
        <title>New Title</title>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="project_path" value="/sdk/docs/_project.yaml">
        <meta name="book_path" value="/sdk/_book.yaml">
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

        <section id="Test-Title">
        <dt>Test Title</dt>
        <dd class="sectionbody">
        </dd>
        </section>

        <section id="SECTION">
        <dt>SECTION</dt>
        <dd class="sectionbody">
        Here are the link styles:
        <ul style="list-style-type:disc">
        <li>
        Style 1 <a href="http://foo.bar">display[this]</a> target and text.
        </li>
        <li>
        Style 1 <a href="http://foo.bar">http://foo.bar</a> target only.
        </li>
        <li>
        Style 2 <a href="http://foo.bar">display[this]</a> text and target.
        </li>
        <li>
        Style 2 <a href="../../..">display[this]</a> text and local target.
        </li>
        <li>
        Style 2 <a href="http://foo.bar">http://foo.bar</a> target only.
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
        </section>

        </dl>
        </body>
        </html>
       """)
    self.Run('devsite', markdown, expected, title='New Title')

  def testDevSiteLinkGcloud(self):
    markdown = self.LINK_GCLOUD_MARKDOWN
    expected = textwrap.dedent("""\
        <html devsite="">
        <head>
        <title>New Title</title>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="project_path" value="/sdk/docs/_project.yaml">
        <meta name="book_path" value="/sdk/_book.yaml">
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
        See <code><a href="/sdk/gcloud/reference/markdown">gcloud markdown</a></code>
        for an overview of markdown.
        <p>
        See <code><a href="/sdk/gcloud/reference">gcloud</a></code> for an overview of
        everything.

        </dl>
        </body>
        </html>
       """)
    self.Run('devsite', markdown, expected, title='New Title')

  def testDevSiteCodeBlock(self):
    markdown = self.CODE_BLOCK_MARKDOWN
    expected = textwrap.dedent("""\
        <html devsite="">
        <head>
        <title>New Title</title>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="project_path" value="/sdk/docs/_project.yaml">
        <meta name="book_path" value="/sdk/_book.yaml">
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

        <section id="DESCRIPTION">
        <dt>DESCRIPTION</dt>
        <dd class="sectionbody">
        The basic format of a YAML argument file is:
        <pre>
          arg-group1:
            arg1: value1  # a comment
            arg2: value2
            &hellip;
        </pre>

        <pre>
          # Another comment
          arg-group2:
            arg3: value3
            &hellip;
        </pre>

        <p>
        and pretty printed as yaml:
        <pre class="prettyprint">
          arg-group1:
            arg1: value1  # a comment
            arg2: value2
            &hellip;

          # Another comment
          arg-group2:
            arg3: value3
            &hellip;
        </pre>

        <p>
        List arguments may be specified within square brackets:
        <pre>
          device-ids: [Nexus5, Nexus6, Nexus9]
        </pre>

        <p>
        or by using the alternate YAML list notation with one dash per list item with an
        unindented code block:
        <pre>
          device-ids:
            - Nexus5
            - Nexus6
            - Nexus9

          device-numbers:
            - 5
            - 6
            - 9
        </pre>

        <p>
        and some python code for coverage:
        <pre class="prettyprint lang-python">
          class Xyz(object):
            '''Some class.'''

            def __init__(self, value):
              self.value = value
        </pre>

        <p>
        If a list argument only contains a single value, you may omit the square
        brackets:
        <pre>
          device-ids: Nexus9
        </pre>

        </dd>
        </section>

        <section id="Composition">
        <dt>Composition</dt>
        <dd class="sectionbody">
        A special <code>include: [<code><var>ARG_GROUP1</var></code>, &hellip;]</code>
        syntax allows merging or composition of argument groups (see
        <code>EXAMPLES</code> below). Included argument groups can <code>include:</code>
        other argument groups within the same YAML file, with unlimited nesting.
        </dd>
        </section>

        </dl>
        </body>
        </html>
       """)
    self.maxDiff = None  # pylint: disable=invalid-name
    self.Run('devsite', markdown, expected, title='New Title')

  def testDevSiteExampleBlock(self):
    markdown = self.EXAMPLE_BLOCK_MARKDOWN
    expected = textwrap.dedent("""\
        <html devsite="">
        <head>
        <title>New Title</title>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="project_path" value="/sdk/docs/_project.yaml">
        <meta name="book_path" value="/sdk/_book.yaml">
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

        <section id="DESCRIPTION">
        <dt>DESCRIPTION</dt>
        <dd class="sectionbody">
        The basic example is:
        <pre>
          # Run first:
          gcloud foo bar
        </pre>

        <pre>
          # Run last:
          gcloud bar foo
        </pre>

        <p>
        However, in non-leap year months with a blue moon:
        <pre>
          # Run first:
          gcloud bar foo
        </pre>

        <pre>
          # Run last:
          gcloud foo bar
        </pre>

        <pre>
          # Run again
          gcloud foo foo
        </pre>

        <pre>
          device-ids: [Nexus5, Nexus6, Nexus9]
        </pre>

        <p>
        And that's it.
        </dd>
        </section>

        </dl>
        </body>
        </html>
       """)
    self.maxDiff = None  # pylint: disable=invalid-name
    self.Run('devsite', markdown, expected, title='New Title')

  def testDevSiteDefinitionList(self):
    markdown = self.DEFINITION_LIST_MARKDOWN
    expected = textwrap.dedent("""\
        <html devsite="">
        <head>
        <title>New Title</title>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="project_path" value="/sdk/docs/_project.yaml">
        <meta name="book_path" value="/sdk/_book.yaml">
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

        <section id="NESTED-DEFINITION-LISTS">
        <dt>NESTED DEFINITION LISTS</dt>
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
        </section>

        <section id="NESTED-DEFINITION-LISTS-WITH-POP">
        <dt>NESTED DEFINITION LISTS WITH POP</dt>
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
        </section>

        </dl>
        </body>
        </html>
       """)
    self.maxDiff = None  # pylint: disable=invalid-name
    self.Run('devsite', markdown, expected, title='New Title')

  def testDevSiteDefinitionListEmptyItem(self):
    markdown = self.DEFINITION_LIST_EMPTY_ITEM_MARKDOWN
    expected = textwrap.dedent("""\
        <html devsite="">
        <head>
        <title>New Title</title>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="project_path" value="/sdk/docs/_project.yaml">
        <meta name="book_path" value="/sdk/_book.yaml">
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

        <section id="DEFINITION-LIST-EMPTY-ITEM-TESTS">
        <dt>DEFINITION LIST EMPTY ITEM TESTS</dt>
        <dd class="sectionbody">
        </dd>
        </section>

        <section id="POSITIONAL-ARGUMENTS">
        <dt>POSITIONAL ARGUMENTS</dt>
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
        </section>

        <section id="REQUIRED-FLAGS">
        <dt>REQUIRED FLAGS</dt>
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
        </section>

        </dl>
        </body>
        </html>
       """)
    self.maxDiff = None  # pylint: disable=invalid-name
    self.Run('devsite', markdown, expected, title='New Title')


if __name__ == '__main__':
  test_base.main()
