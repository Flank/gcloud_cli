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
"""Base class for the document renderer tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os
import textwrap

from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.document_renderers import render_document
from googlecloudsdk.core.util import pkg_resources
from tests.lib import sdk_test_base
from tests.lib import test_case

import six


class DocumentRendererTestBase(sdk_test_base.WithOutputCapture):
  """Save and restore console attributes state."""

  def SetUp(self):
    self.StartEnvPatch({})


class Style(DocumentRendererTestBase):
  """Document renderer file to file test support.

  Supports document renderer tests that convert a markdown file to a document
  in a requested style.

  Example for the 'bar' command in the 'foo' group:

    class StyleTest(test_base.Style):
      def testStyle1(self):
        self.Run(['foo', 'bar'], 'style', '.suffix')

  The input file is
    core/document_renderers/tests/foo_bar.md
  end the expected (golden) output file is
    core/document_renderers/tests/foo_bar.suffix
  """

  def SetUp(self):
    # Ensure ascii embellishments.
    os.environ['TERM'] = 'dumb'
    os.environ['LC_ALL'] = 'C'
    console_attr.GetConsoleAttr('ascii', reset=True)

  def Run(self, test_file_path, path, style, suffix, exception=None):
    file_base = '_'.join(path)
    markdown_path = self.GetTestdataPath(
        test_file_path, file_base + '.src.md')
    try:
      markdown_data = console_attr.Decode(
          pkg_resources.GetResourceFromFile(markdown_path))
    except IOError:
      file_base = '_'.join(['gcloud'] + path)
      markdown_path = self.GetTestdataPath(
          test_file_path, 'markdown', file_base + '.md')
      markdown_data = console_attr.Decode(
          pkg_resources.GetResourceFromFile(markdown_path))
    f = io.StringIO(markdown_data)
    try:
      e = None
      render_document.RenderDocument(style, fin=f, out=log.out,
                                     notes='A special note.',
                                     title=' '.join(['gcloud'] + path))
    except Exception as e:  # pylint: disable=broad-except
      e = e.message
    if e != exception:
      if not exception:
        self.fail('Exception not expected but [%s] caught.' % e)
      else:
        self.fail('Exception [%s] expected but caught [%s].' % (exception, e))
    self.AssertOutputIsGolden(test_file_path, file_base + suffix)
    self.ClearOutput()


class Markdown(DocumentRendererTestBase):
  """Document renderer string to string test support.

  Supports document renderer tests that convert a markdown string to a document
  string in a requested style.

  Example usage:

    class MarkdownTest(test_base.Markdown):
      def testMarkdown1(self):
        self.Run(style=STYLE, markdown=self.SOME_PREDEFINED_MARKDOWN,
                 expected=EXPECTED_OUTPUT_STRING,
                 notes=EXTRA_NOTES,
                 title='SOME TITLE'):
  """

  CODE_BLOCK_MARKDOWN = textwrap.dedent("""\
      ## DESCRIPTION

      The basic format of a YAML argument file is:

        arg-group1:
          arg1: value1  # a comment
          arg2: value2
          ...

        # Another comment
        arg-group2:
          arg3: value3
          ...

      and pretty printed as yaml:

        ```yaml
        arg-group1:
          arg1: value1  # a comment
          arg2: value2
          ...

        # Another comment
        arg-group2:
          arg3: value3
          ...
        ```

      List arguments may be specified within square brackets:

        device-ids: [Nexus5, Nexus6, Nexus9]

      or by using the alternate YAML list notation with one dash per list
      item with an unindented code block:

      ```
      device-ids:
        - Nexus5
        - Nexus6
        - Nexus9

      device-numbers:
        - 5
        - 6
        - 9
      ```

      and some python code for coverage:

        ```python
        class Xyz(object):
          '''Some class.'''

          def __init__(self, value):
            self.value = value
        ```

      If a list argument only contains a single value, you may omit the
      square brackets:

        device-ids: Nexus9

      ### Composition

      A special *include: [_ARG_GROUP1_, ...]* syntax allows merging or
      composition of argument groups (see *EXAMPLES* below). Included
      argument groups can *include:* other argument groups within the
      same YAML file, with unlimited nesting.
      """)

  DEEP_BULLET_MARKDOWN = textwrap.dedent("""\
      # Deep Bullet Test

      ## SECTION

      - Level 1 bullet.
      -- Level 2 bullet.
      --- Level 3 bullet.
      ---- Level 4 bullet.
      ----- Level 5 bullet.
      ------ Level 6 bullet.
      ------- Level 7 bullet.
      -------- Level 8 bullet.
      --------- Level 9 bullet.
      -------- Level 8 bullet.
      ------- Level 7 bullet.
      ------ Level 6 bullet.
      ----- Level 5 bullet.
      ---- Level 4 bullet.
      --- Level 3 bullet.
      -- Level 2 bullet.
      - Level 1 bullet.

      Post-list prose.
      """)

  DEEP_HEADING_MARKDOWN = textwrap.dedent("""\
      = Deep Heading Test =

      == SECTION ==

      Section prose.

      === Level 3 heading. ===

      Level 3 heading prose.

      ==== Level 4 heading. ====

      Level 4 heading prose.

      ===== Level 5 heading. =====

      Level 5 heading prose.

      ====== Level 6 heading. ======

      Level 6 heading prose.

      ======= Level 7 heading. =======

      Level 7 heading prose.

      ======== Level 8 heading. ========

      Level 8 heading prose.

      ========= Level 9 heading. =========

      Level 9 heading prose.

      ======== Level 8 heading. ========

      Level 8 heading prose.

      ======= Level 7 heading. =======

      Level 7 heading prose.

      ====== Level 6 heading. ======

      Level 6 heading prose.

      ===== Level 5 heading. =====

      Level 5 heading prose.

      ==== Level 4 heading. ====

      Level 4 heading prose.

      === Level 3 heading. ===

      Level 3 heading prose.

      == ANOTHER SECTION ==

      Another section prose.
      """)

  DEEP_HEADING_MARKDOWN_NO_TAIL = textwrap.dedent("""\
      # Deep Heading Test

      ## SECTION

      Section prose.

      ### Level 3 heading.

      Level 3 heading prose.

      #### Level 4 heading.

      Level 4 heading prose.

      ##### Level 5 heading.

      Level 5 heading prose.

      ###### Level 6 heading.

      Level 6 heading prose.

      ####### Level 7 heading.

      Level 7 heading prose.

      ######## Level 8 heading.

      Level 8 heading prose.

      ######### Level 9 heading.

      Level 9 heading prose.

      ######## Level 8 heading.

      Level 8 heading prose.

      ####### Level 7 heading.

      Level 7 heading prose.

      ###### Level 6 heading.

      Level 6 heading prose.

      ##### Level 5 heading.

      Level 5 heading prose.

      #### Level 4 heading.

      Level 4 heading prose.

      ### Level 3 heading.

      Level 3 heading prose.

      ## ANOTHER SECTION

      Another section prose.
      """)

  DEEP_HEADING_MARKDOWN_HASH = textwrap.dedent("""\
      # Deep Heading Test #

      ## SECTION ##

      Section prose.

      ### Level 3 heading. ###

      Level 3 heading prose.

      #### Level 4 heading. ####

      Level 4 heading prose.

      ##### Level 5 heading. #####

      Level 5 heading prose.

      ###### Level 6 heading. ######

      Level 6 heading prose.

      ####### Level 7 heading. #######

      Level 7 heading prose.

      ######## Level 8 heading. ########

      Level 8 heading prose.

      ######### Level 9 heading. #########

      Level 9 heading prose.

      ######## Level 8 heading. ########

      Level 8 heading prose.

      ####### Level 7 heading. #######

      Level 7 heading prose.

      ###### Level 6 heading. ######

      Level 6 heading prose.

      ##### Level 5 heading. #####

      Level 5 heading prose.

      #### Level 4 heading. ####

      Level 4 heading prose.

      ### Level 3 heading. ###

      Level 3 heading prose.

      ## ANOTHER SECTION ##

      Another section prose.
      """)

  DEEP_HEADING_MARKDOWN_HASH_NO_TAIL = textwrap.dedent("""\
      # Deep Heading Test

      ## SECTION

      Section prose.

      ### Level 3 heading.

      Level 3 heading prose.

      #### Level 4 heading.

      Level 4 heading prose.

      ##### Level 5 heading.

      Level 5 heading prose.

      ###### Level 6 heading.

      Level 6 heading prose.

      ####### Level 7 heading.

      Level 7 heading prose.

      ######## Level 8 heading.

      Level 8 heading prose.

      ######### Level 9 heading.

      Level 9 heading prose.

      ######## Level 8 heading.

      Level 8 heading prose.

      ####### Level 7 heading.

      Level 7 heading prose.

      ###### Level 6 heading.

      Level 6 heading prose.

      ##### Level 5 heading.

      Level 5 heading prose.

      #### Level 4 heading.

      Level 4 heading prose.

      ### Level 3 heading.

      Level 3 heading prose.

      ## ANOTHER SECTION

      Another section prose.
      """)

  DEFINITION_LIST_MARKDOWN = textwrap.dedent("""\
      ## NESTED DEFINITION LISTS

      Intro text.
      *first top definition name*::
      First top definition description.
      *first nested definition name*:::
      First nested definition description.
      *last nested definition name*:::
      Last nested definition description.
      :::
      Nested summary text.
      *last top definition name*::
      Last top definition description.
      ::
      Top summary text.

      ## NESTED DEFINITION LISTS WITH POP

      Intro text.
      *first top definition name*::
      First top definition description.
      *first nested definition name*:::
      First nested definition description.
      *last nested definition name*:::
      Last nested definition description.
      ::
      Top summary text.
      """)

  DEFINITION_LIST_EMPTY_ITEM_MARKDOWN = textwrap.dedent("""\
        # DEFINITION LIST EMPTY ITEM TESTS

        ## POSITIONAL ARGUMENTS

        SUPERFLUOUS:: Superfluous definition to bump the list nesting level.

        ::: g2 group description.
        At least one of these must be specified:

        _FILE_::::

        The input file.

        :::: g21 details.
        At most one of these may be specified:

        *--flag-21-a*=_FLAG_21_A_:::::

        Help 21 a.

        *--flag-21-b*=_FLAG_21_B_:::::

        Help 21 b.

        :::: g22 details.
        At most one of these may be specified:

        *--flag-22-a*=_FLAG_22_A_:::::

        Help 22 a.

        *--flag-22-b*=_FLAG_22_B_:::::

        Help 22 b.

        ::: And an extraneous paragraph.


        ## REQUIRED FLAGS

        :: g1 group details.
        Exactly one of these must be specified:

        ::: g11 details.

        *--flag-11-a*=_FLAG_11_A_::::

        Help 11 a. This is a modal flag. It must be specified if any of the other arguments in the group are specified.

        *--flag-11-b*=_FLAG_11_B_::::

        Help 11 b.

        ::: g12 details.

        *--flag-12-a*=_FLAG_12_A_::::

        Help 12 a. This is a modal flag. It must be specified if any of the other arguments in the group are specified.

        *--flag-12-b*=_FLAG_12_B_::::

        Help 12 b.
      """)

  EXAMPLE_BLOCK_MARKDOWN = textwrap.dedent("""\
      ## DESCRIPTION

      The basic example is:

        # Run first:
        gcloud foo bar

        # Run last:
        gcloud bar foo

      However, in non-leap year months with a blue moon:

        # Run first:
        gcloud bar foo

        # Run last:
        gcloud foo bar

        # Run again
        gcloud foo foo

        device-ids: [Nexus5, Nexus6, Nexus9]

      And that's it.
      """)

  FONT_EMPHASIS_MARKDOWN = textwrap.dedent("""\
      # Test Title

      ## SECTION

      Double air quotes ``+-*/'' on non-identifier chars or single identifier
      chars ``x'' and inline ```*code`_blocks``` should disable markdown in the
      quoted string with air quotes `retained/` and code block quotes consumed.
      """)

  INSERT_NOTES_MARKDOWN = textwrap.dedent("""\
      # Test Title

      ## SECTION

      Section prose.

      ## NOTES

      Original note.
      """)

  LINK_GCLOUD_MARKDOWN = textwrap.dedent("""\
      See `link:gcloud/markdown[gcloud markdown]` for an overview of markdown.

      See `link:gcloud[gcloud]` for an overview of everything.
      """)

  LINK_MARKDOWN = textwrap.dedent("""\
      # Test Title

      ## SECTION

      Here are the link styles:
      * Style 1 http://foo.bar[display[this]] target and text.
      * Style 1 http://foo.bar[] target only.
      * Style 2 [display[this]](http://foo.bar) text and target.
      * Style 2 [display[this]](../../..) text and local target.
      * Style 2 [](http://foo.bar) target only.
      * Style 2 [](foo#bar) local target only.
      * Style 2 [display[this]]() text only.
      * Style 2 []() empty text and target.
      """)

  LINK_ONLY_MARKDOWN = textwrap.dedent("""\
      # Test Title

      ## SECTION

      Test embedded[http://link/this]link in text.
      """)

  LONG_SYNOPSIS_MARKDOWN = textwrap.dedent("""\
      ## NAME

      gcloud compute instances - read and manipulate Google Compute Engine virtual machine instances

      ## SYNOPSIS

      `gcloud compute instances` _COMMAND_ [*--format* _FORMAT_] [*--help*]                                         [*--project* _PROJECT_ID_] [*--quiet*, *-q*] [*--trace-token* _TRACE_TOKEN_] [*-h*]

      ## DESCRIPTION

      Read and manipulate Google Compute Engine virtual machine instances.
      """)

  LONG_SYNOPSIS_GROUP_MARKDOWN = textwrap.dedent("""\
      ## NAME

      gcloud compute images deprecate - manage deprecation status of Google Compute Engine images

      ## SYNOPSIS

      `gcloud compute images deprecate` _NAME_ [*--delete-in* _DELETE_IN_ | *--delete-on* _DELETE_ON_] [*--obsolete-in* _OBSOLETE_IN_ | *--obsolete-on* _OBSOLETE_ON_] [*--replacement* _REPLACEMENT_] *--state* _STATE_ [_GCLOUD_WIDE_FLAG ..._]

      ## DESCRIPTION

      *gcloud compute images deprecate* is used to deprecate images.
      """)

  LONGER_SYNOPSIS_MARKDOWN = textwrap.dedent("""\
      ## NAME

      gcloud compute instances - read and manipulate Google Compute Engine virtual machine instances

      ## SYNOPSIS

      `gcloud compute instances` _COMMAND_ [*--format* _FORMAT_] [*--help*] [*-A*]                                         [*-B*] [*-C*] [*-D*] [*-E*] [*--project* _PROJECT_ID_] [*--quiet*, *-q*] [*--trace-token* _TRACE_TOKEN_] [*-h*]

      ## DESCRIPTION

      Read and manipulate Google Compute Engine virtual machine instances.
      """)

  LONGEST_SYNOPSIS_MARKDOWN = textwrap.dedent("""\
      ## NAME

      gcloud compute instances create - create Google Compute Engine virtual machine instances

      ## SYNOPSIS

      `gcloud compute instances create` _NAME_ [_NAME_ ...] [*--boot-disk-device-name* _BOOT_DISK_DEVICE_NAME_] [*--boot-disk-size* _BOOT_DISK_SIZE_] [*--boot-disk-type* _BOOT_DISK_TYPE_] [*--can-ip-forward*] [*--description* _DESCRIPTION_] [*--disk* [_PROPERTY_=_VALUE_,...]] [*--image* _IMAGE_ | _centos-6_ | _centos-7_ | _container-vm_ | _coreos_ | _debian-7_ | _debian-7-backports_ | _opensuse-13_ | _rhel-6_ | _rhel-7_ | _sles-11_ | _sles-12_ | _ubuntu-12-04_ | _ubuntu-14-04_ | _ubuntu-14-10_ | _ubuntu-15-04_ | _windows-2008-r2_ | _windows-2012-r2_] [*--image-project* _IMAGE_PROJECT_] [*--local-ssd* [_PROPERTY_=_VALUE_,...]] [*--machine-type* _MACHINE_TYPE_; default="n1-standard-1"] [*--maintenance-policy* _MAINTENANCE_POLICY_] [*--metadata* _KEY_=_VALUE_,[_KEY_=_VALUE_,...]] [*--metadata-from-file* _KEY_=_LOCAL_FILE_PATH_,[_KEY_=_LOCAL_FILE_PATH_,...]] [*--network* _NETWORK_; default="default"] [*--address* _ADDRESS_ | *--no-address*] [*--no-boot-disk-auto-delete*] [*--no-restart-on-failure*] [*--preemptible*] [*--no-scopes* | *--scopes* [_ACCOUNT_=]_SCOPE_,[[_ACCOUNT_=]_SCOPE_,...]] [*--tags* _TAG_,[_TAG_,...]] [*--zone* _ZONE_] [_GCLOUD_WIDE_FLAG ..._]

      ## DESCRIPTION

      *gcloud compute instances create* facilitates the creation of Google Compute Engine
      virtual machines.
      """)

  NEW_NOTES_MARKDOWN = textwrap.dedent("""\
      # Test Title

      ## SECTION

      Section prose.
      """)

  NULL_MARKDOWN = ''

  ROOT_MARKDOWN = textwrap.dedent("""\
      # GCLOUD COMPONENT(1)

      ## SYNOPSIS

      gcloud component [ _flags_ ] [ _positionals_ ]

      ## SECTION

      Section prose about the gcloud component command.

      ## GCLOUD WIDE FLAGS

      These are available in all commands: --foo, --bar and --verbosity.
      """)

  TITLE_MARKDOWN = textwrap.dedent("""\
      # Test Title

      ## SECTION

      Section prose.
      """)

  def SetUp(self):
    # Ensure ascii embellishments.
    os.environ['TERM'] = 'dumb'
    os.environ['LC_ALL'] = 'C'
    self.maxDiff = None  # pylint: disable=invalid-name
    console_attr.GetConsoleAttr(encoding='ascii', reset=True)

  def Run(self, style, markdown, expected=None, exception=None, notes=None,
          title=None, command_metadata=None):
    fin = io.StringIO(markdown)
    err = None
    try:
      render_document.RenderDocument(style=style, fin=fin, notes=notes,
                                     title=title,
                                     command_metadata=command_metadata)
    except Exception as e:  # pylint: disable=broad-except
      err = six.text_type(e)
    if err != exception:
      if not exception:
        self.fail('Exception not expected but [%s] caught.' % err)
      else:
        self.fail('Exception [%s] expected but caught [%s].' % (exception, err))
    actual = self.GetOutput()
    self.assertMultiLineEqual(expected, actual)
    self.ClearOutput()


class UTF8(Markdown):
  """Document renderer UTF8 output test support.

  Sets the TERM environment variable type and renders the input markdown string
  to the expected document style output string.

  Example usage:

    class testUTF8(test_base.UTF8):
      self.Run(style=STYLE, term=TERM_VALUE,
               markdown=self.SOME_MARKDORN,
               expected=EXPECTED_STYLE_OUTPUT)
  """

  BULLET_MARKDOWN = textwrap.dedent("""\
      # ANSI + UTF-8 Tests

      ## Bullets

      - bullet 1.1 *bold*
      -- bullet 2.1 _italic_
      --- bullet 3.1 *_bold-italic_*
      -- bullet 2.2 _*italic-bold*_
      --- bullet 3.2 normal
      - bullet 1.2

      ## Justification

      *word* *word* *word* *word* *word* *word* *word* *word* *word* *word* *word* *word* *word* *word* *word* *word* *word* *word* *word*.
      """)

  def SetUp(self):
    self.maxDiff = None  # pylint: disable=invalid-name

  def Run(self, style, term, markdown, expected=None, exception=None):
    os.environ['LC_ALL'] = 'en_US.UTF-8'
    os.environ['TERM'] = term
    fin = io.StringIO(markdown)
    console_attr.GetConsoleAttr(reset=True, encoding='utf8')
    try:
      e = None
      render_document.RenderDocument(style=style, fin=fin, out=log.out)
    except Exception as e:  # pylint: disable=broad-except
      e = str(e)
    if e != exception:
      if not exception:
        self.fail('Exception not expected but [%s] caught.' % e)
      else:
        self.fail('Exception [%s] expected but caught [%s].' % (exception, e))
    actual = self.GetOutput()
    self.maxDiff = None
    self.assertMultiLineEqual(expected, actual)
    self.ClearOutput()


class Command(DocumentRendererTestBase, test_case.WithInput):
  """render_document standalone command test support.

  Sets the TERM environment variable type and renders the input markdown string
  to the expected document style output string. The output is compared against
  the expected output string.

  Example usage:

    class testCommand(test_base.Command):
      self.Run(argv,
               markdown=self.SOME_MARKDORN,
               expected=EXPECTED_STYLE_OUTPUT)
  """

  COMMAND_MARKDOWN = textwrap.dedent("""\
      # document command test

      ## NAME

      gcloud compute instances - read and manipulate Google Compute Engine virtual machine instances

      ## SYNOPSIS

      `gcloud compute instances` _COMMAND_ [*--format* _FORMAT_] [*--help*] [*--project* _PROJECT_ID_] [*--quiet*, *-q*] [*--trace-token* _TRACE_TOKEN_] [*-h*]

      ## DESCRIPTION

      Read and manipulate Google Compute Engine virtual machine instances.""")

  def SetUp(self):
    # Ensure ascii embellishments.
    os.environ['TERM'] = 'dumb'
    os.environ['LC_ALL'] = 'C'
    self.maxDiff = None  # pylint: disable=invalid-name

  def Run(self, argv, markdown, expected=None, exception=None):
    self.WriteInput(markdown)
    console_attr.GetConsoleAttr(reset=True)
    err = None
    try:
      render_document.main(argv)
    except Exception as e:  # pylint: disable=broad-except
      err = six.text_type(e)
    if err != exception:
      if not exception:
        self.fail('Exception not expected but [%s] caught.' % err)
      else:
        self.fail('Exception [%s] expected but caught [%s].' % (exception, err))
    actual = self.GetOutput()
    self.assertMultiLineEqual(expected, actual)
    self.ClearOutput()


def main():
  sdk_test_base.main()
