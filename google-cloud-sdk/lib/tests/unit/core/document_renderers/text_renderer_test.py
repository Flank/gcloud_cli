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
"""Tests for text_renderer.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib.core.document_renderers import test_base


class TextRendererTests(test_base.Style):

  def testStyle1(self):
    self.Run(__file__, [], 'text', '')

  def testStyle2(self):
    self.Run(__file__, ['markdown'], 'text', '')

  def testStyle3(self):
    self.Run(__file__, ['markdown', 'markdown-command'], 'text', '')

  def testStyle4(self):
    self.Run(__file__, ['hidden-group'], 'text', '')

  def testStyle5(self):
    self.Run(__file__, ['hidden-group', 'hidden-command'], 'text', '')

  def testStyle6(self):
    self.Run(__file__, ['README'], 'text', '')

  def testStyle7(self):
    self.Run(__file__, ['RELEASE_NOTES'], 'text', '')


class TextMarkdownTests(test_base.Markdown):

  def testTextNullInput(self):
    markdown = self.NULL_MARKDOWN
    expected = ''
    self.Run('text', markdown, expected)

  def testTextNewNotes(self):
    markdown = self.NEW_NOTES_MARKDOWN
    expected = textwrap.dedent("""\
        Test Title

        SECTION
            Section prose.

        NOTES
            New note.
        """)
    self.Run('text', markdown, expected, notes='New note.')

  def testTextInsertNotes(self):
    markdown = self.INSERT_NOTES_MARKDOWN
    expected = textwrap.dedent("""\
        Test Title

        SECTION
            Section prose.

        NOTES
            New note.

            Original note.
       """)
    self.Run('text', markdown, expected, notes='New note.')

  def testTextTitle(self):
    markdown = self.TITLE_MARKDOWN
    expected = textwrap.dedent("""\
        Test Title

        SECTION
            Section prose.
        """)
    self.Run('text', markdown, expected, title='New Title')

  def testTextRoot(self):
    markdown = self.ROOT_MARKDOWN
    expected = textwrap.dedent("""\
      SYNOPSIS
          gcloud component [ flags ] [ positionals ]

      SECTION
          Section prose about the gcloud component command.

      GCLOUD WIDE FLAGS
          These are available in all commands: --foo, --bar and --verbosity.
      """)
    self.Run('text', markdown, expected)

  def testTextEmptyName(self):
    markdown = textwrap.dedent("""\
        == NAME ==
        """)
    expected = textwrap.dedent("""\
        NAME
        """)
    self.Run('text', markdown, expected)

  def testTextItsAHeadingBazinga(self):
    markdown = textwrap.dedent("""\
        == Faux heading ahead ==
        ====
        """)
    expected = textwrap.dedent("""\
        Faux heading ahead
            ====
        """)
    self.Run('text', markdown, expected)

  def testTextTableEmpty(self):
    markdown = textwrap.dedent("""\
        == TABLE ==

        [options="header",format="csv",grid="none",frame="none"]
        """)
    expected = textwrap.dedent("""\
        TABLE
            [options="header",format="csv",grid="none",frame="none"]
        """)
    self.Run('text', markdown, expected)

  def testTextTableNoSpace(self):
    markdown = textwrap.dedent("""\
        ## TABLE

        Left | Right
        --- | ---
        abc | /def/ghijkl/mnop
        z | /foo/bar

        Next line.
        """)
    expected = textwrap.dedent("""\
        TABLE
              Left  Right
              abc   /def/ghijkl/mnop
              z     /foo/bar

            Next line.
        """)
    self.Run('text', markdown, expected)

  def testTextTableFixedNoSpace(self):
    markdown = textwrap.dedent("""\
        ## TABLE

        Left | Right
        -------- | ---
        abc | /def/ghijkl/mnop
        z | /foo/bar

        Next line.
        """)
    expected = textwrap.dedent("""\
        TABLE
              Left      Right
              abc       /def/ghijkl/mnop
              z         /foo/bar

            Next line.
        """)
    self.Run('text', markdown, expected)

  def testTextTableSpace(self):
    markdown = textwrap.dedent("""\
        ## TABLE

        Left | Right
        --- | ---
        abc | Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbisit amet elit nulla.
        z | Sed at cursus risus. Praesent facilisis at ligula at mattis. Vestibulum et quam et ipsum.

        Next line.
        """)
    expected = textwrap.dedent("""\
        TABLE
              Left  Right
              abc   Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbisit
                    amet elit nulla.
              z     Sed at cursus risus. Praesent facilisis at ligula at mattis.
                    Vestibulum et quam et ipsum.

            Next line.
        """)
    self.Run('text', markdown, expected)

  def testTextTableFixedSpace(self):
    markdown = textwrap.dedent("""\
        ## TABLE

        Left | Right
        -------- | ---
        abc | Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbisit amet elit nulla.
        z | Sed at cursus risus. Praesent facilisis at ligula at mattis. Vestibulum et quam et ipsum.

        Next line.
        """)
    expected = textwrap.dedent("""\
        TABLE
              Left      Right
              abc       Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                        Morbisit amet elit nulla.
              z         Sed at cursus risus. Praesent facilisis at ligula at mattis.
                        Vestibulum et quam et ipsum.

            Next line.
        """)
    self.Run('text', markdown, expected)

  # The Synopsis tests verify that the NAME and SYNOPSYS justification stays
  # within the page width and does not split flag and positional groups in
  # confusing places.

  def testTextLongSynopsis(self):
    markdown = self.LONG_SYNOPSIS_MARKDOWN
    expected = textwrap.dedent("""\
        NAME
            gcloud compute instances - read and manipulate Google Compute Engine
                virtual machine instances

        SYNOPSIS
            gcloud compute instances COMMAND [--format FORMAT] [--help]
                [--project PROJECT_ID] [--quiet, -q] [--trace-token TRACE_TOKEN] [-h]

        DESCRIPTION
            Read and manipulate Google Compute Engine virtual machine instances.
        """)
    self.Run('text', markdown, expected)

  def testTextLongSynopsisGroup(self):
    markdown = self.LONG_SYNOPSIS_GROUP_MARKDOWN
    expected = textwrap.dedent("""\
        NAME
            gcloud compute images deprecate - manage deprecation status of Google
                Compute Engine images

        SYNOPSIS
            gcloud compute images deprecate NAME
                [--delete-in DELETE_IN | --delete-on DELETE_ON]
                [--obsolete-in OBSOLETE_IN | --obsolete-on OBSOLETE_ON]
                [--replacement REPLACEMENT] --state STATE [GCLOUD_WIDE_FLAG ...]

        DESCRIPTION
            gcloud compute images deprecate is used to deprecate images.
        """)
    self.Run('text', markdown, expected)

  def testTextLongerSynopsis(self):
    markdown = self.LONGER_SYNOPSIS_MARKDOWN
    expected = textwrap.dedent("""\
        NAME
            gcloud compute instances - read and manipulate Google Compute Engine
                virtual machine instances

        SYNOPSIS
            gcloud compute instances COMMAND [--format FORMAT] [--help] [-A] [-B] [-C]
                [-D] [-E] [--project PROJECT_ID] [--quiet, -q]
                [--trace-token TRACE_TOKEN] [-h]

        DESCRIPTION
            Read and manipulate Google Compute Engine virtual machine instances.
        """)
    self.Run('text', markdown, expected)

  def testTextLongestSynopsis(self):
    markdown = self.LONGEST_SYNOPSIS_MARKDOWN
    expected = textwrap.dedent("""\
        NAME
            gcloud compute instances create - create Google Compute Engine virtual
                machine instances

        SYNOPSIS
            gcloud compute instances create NAME [NAME ...]
                [--boot-disk-device-name BOOT_DISK_DEVICE_NAME]
                [--boot-disk-size BOOT_DISK_SIZE] [--boot-disk-type BOOT_DISK_TYPE]
                [--can-ip-forward] [--description DESCRIPTION]
                [--disk [PROPERTY=VALUE,...]]
                [--image IMAGE | centos-6 | centos-7 | container-vm | coreos | debian-7
                  | debian-7-backports | opensuse-13 | rhel-6 | rhel-7 | sles-11
                  | sles-12 | ubuntu-12-04 | ubuntu-14-04 | ubuntu-14-10 | ubuntu-15-04
                  | windows-2008-r2 | windows-2012-r2] [--image-project IMAGE_PROJECT]
                [--local-ssd [PROPERTY=VALUE,...]]
                [--machine-type MACHINE_TYPE; default="n1-standard-1"]
                [--maintenance-policy MAINTENANCE_POLICY]
                [--metadata KEY=VALUE,[KEY=VALUE,...]]
                [--metadata-from-file KEY=LOCAL_FILE_PATH,[KEY=LOCAL_FILE_PATH,...]]
                [--network NETWORK; default="default"]
                [--address ADDRESS | --no-address] [--no-boot-disk-auto-delete]
                [--no-restart-on-failure] [--preemptible]
                [--no-scopes | --scopes [ACCOUNT=]SCOPE,[[ACCOUNT=]SCOPE,...]]
                [--tags TAG,[TAG,...]] [--zone ZONE] [GCLOUD_WIDE_FLAG ...]

        DESCRIPTION
            gcloud compute instances create facilitates the creation of Google Compute
            Engine virtual machines.
        """)
    self.Run('text', markdown, expected)

  def testTextLongSynopsisFlagValue(self):
    markdown = """## SYNOPSIS

`gcloud alpha compute backend-services create` _NAME_ [*--https-health-checks*=_HTTPS_HEALTH_CHECK_,[_HTTPS_HEALTH_CHECK_,...]] [*--iap*=[_disabled_],[_enabled_],[_oauth2-client-id_=_OAUTH2-CLIENT-ID_],[_oauth2-client-secret_=_OAUTH2-CLIENT-SECRET_]] [*--load-balancing-scheme*=_LOAD_BALANCING_SCHEME_; default="EXTERNAL"] [*--port-name*=_PORT_NAME_] [*--protocol*=_PROTOCOL_] [*--cache-key-query-string-blacklist*=[_QUERY_STRING_,...] | *--cache-key-query-string-whitelist*=_QUERY_STRING_,[_QUERY_STRING_,...]] [*--server*=_SERVER_,[_SERVER_,...], *-s* _SERVER_,[_SERVER_,...]; default="gcr.io,us.gcr.io,eu.gcr.io,asia.gcr.io,b.gcr.io,bucket.gcr.io,appengine.gcr.io,gcr.kubernetes.io"] [*--global* | *--region*=_REGION_] [_GCLOUD_WIDE_FLAG ..._]
"""
    expected = """SYNOPSIS
    gcloud alpha compute backend-services create NAME
        [--https-health-checks=HTTPS_HEALTH_CHECK,[HTTPS_HEALTH_CHECK,...]]
        [--iap=[disabled],[enabled],[oauth2-client-id=OAUTH2-CLIENT-ID],
          [oauth2-client-secret=OAUTH2-CLIENT-SECRET]]
        [--load-balancing-scheme=LOAD_BALANCING_SCHEME; default="EXTERNAL"]
        [--port-name=PORT_NAME] [--protocol=PROTOCOL]
        [--cache-key-query-string-blacklist=[QUERY_STRING,...]
          | --cache-key-query-string-whitelist=QUERY_STRING,[QUERY_STRING,...]]
        [--server=SERVER,[SERVER,...], -s SERVER,[SERVER,...];
          default="gcr.io,us.gcr.io,eu.gcr.io,asia.gcr.io,
          b.gcr.io,bucket.gcr.io,appengine.gcr.io,gcr.kubernetes.io"]
        [--global | --region=REGION] [GCLOUD_WIDE_FLAG ...]

"""
    self.Run('text', markdown, expected)

  def testTextCodeBlock(self):
    markdown = self.CODE_BLOCK_MARKDOWN
    expected = textwrap.dedent("""\
        DESCRIPTION
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

                arg-group1:
                  arg1: value1  # a comment
                  arg2: value2
                  ...

                # Another comment
                arg-group2:
                  arg3: value3
                  ...

            List arguments may be specified within square brackets:

                device-ids: [Nexus5, Nexus6, Nexus9]

            or by using the alternate YAML list notation with one dash per list item
            with an unindented code block:

                device-ids:
                  - Nexus5
                  - Nexus6
                  - Nexus9

                device-numbers:
                  - 5
                  - 6
                  - 9

            and some python code for coverage:

                class Xyz(object):
                  '''Some class.'''

                  def __init__(self, value):
                    self.value = value

            If a list argument only contains a single value, you may omit the square
            brackets:

                device-ids: Nexus9

          Composition
            A special include: [ARG_GROUP1, ...] syntax allows merging or composition
            of argument groups (see EXAMPLES below). Included argument groups can
            include: other argument groups within the same YAML file, with unlimited
            nesting.
        """)
    self.Run('text', markdown, expected)

  def testTextExampleBlock(self):
    markdown = self.EXAMPLE_BLOCK_MARKDOWN
    expected = textwrap.dedent("""\
        DESCRIPTION
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
    self.Run('text', markdown, expected)

  def testTextQuotedFontEmphasis(self):
    markdown = self.FONT_EMPHASIS_MARKDOWN
    expected = textwrap.dedent("""\
        Test Title

        SECTION
            Double air quotes ``+-*/'' on non-identifier chars or single identifier
            chars ``x'' and inline *code`_blocks should disable markdown in the quoted
            string with air quotes retained/ and code block quotes consumed.
        """)
    self.Run('text', markdown, expected)

  def testTextLink(self):
    markdown = self.LINK_MARKDOWN
    expected = """\
Test Title

SECTION
    Here are the link styles:
      o Style 1 display[this] (http://foo.bar) target and text.
      o Style 1 http://foo.bar target only.
      o Style 2 display[this] (http://foo.bar) text and target.
      o Style 2 display[this] text and local target.
      o Style 2 http://foo.bar target only.
      o Style 2 foo#bar local target only.
      o Style 2 [display[this]]() text only.
      o Style 2 []() empty text and target.
"""
    self.Run('text', markdown, expected, title='New Title')


class TextUTF8Tests(test_base.UTF8):

  def testTextScreen(self):
    markdown = self.BULLET_MARKDOWN
    expected = textwrap.dedent("""\
        \x1b[m\x1b[1mANSI + UTF-8 Tests\x1b[m

        \x1b[m\x1b[1mBullets\x1b[m
              ▪ bullet 1.1 \x1b[1mbold\x1b[m
                ◆ bullet 2.1 \x1b[4mitalic\x1b[m
                  ▸ bullet 3.1 \x1b[1m\x1b[1;4mbold-italic\x1b[1m\x1b[m
                ◆ bullet 2.2 \x1b[4m\x1b[1;4mitalic-bold\x1b[4m\x1b[m
                  ▸ bullet 3.2 normal
              ▪ bullet 1.2

        \x1b[m\x1b[1mJustification\x1b[m
            \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m
            \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m.
        \x1b[m""")
    self.Run('text', 'screen', markdown, expected)

  def testTextXterm(self):
    markdown = self.BULLET_MARKDOWN
    expected = textwrap.dedent("""\
        \x1b[m\x1b[1mANSI + UTF-8 Tests\x1b[m

        \x1b[m\x1b[1mBullets\x1b[m
              ▪ bullet 1.1 \x1b[1mbold\x1b[m
                ◆ bullet 2.1 \x1b[4mitalic\x1b[m
                  ▸ bullet 3.1 \x1b[1m\x1b[1;4mbold-italic\x1b[1m\x1b[m
                ◆ bullet 2.2 \x1b[4m\x1b[1;4mitalic-bold\x1b[4m\x1b[m
                  ▸ bullet 3.2 normal
              ▪ bullet 1.2

        \x1b[m\x1b[1mJustification\x1b[m
            \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m
            \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m.
        \x1b[m""")
    self.Run('text', 'xterm', markdown, expected)

  def testTextXterm256(self):
    markdown = self.BULLET_MARKDOWN
    expected = textwrap.dedent("""\
        \x1b[m\x1b[1mANSI + UTF-8 Tests\x1b[m

        \x1b[m\x1b[1mBullets\x1b[m
              ▪ bullet 1.1 \x1b[1mbold\x1b[m
                ◆ bullet 2.1 \x1b[4mitalic\x1b[m
                  ▸ bullet 3.1 \x1b[1m\x1b[1;4mbold-italic\x1b[1m\x1b[m
                ◆ bullet 2.2 \x1b[4m\x1b[1;4mitalic-bold\x1b[4m\x1b[m
                  ▸ bullet 3.2 normal
              ▪ bullet 1.2

        \x1b[m\x1b[1mJustification\x1b[m
            \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m
            \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m \x1b[1mword\x1b[m.
        \x1b[m""")
    self.Run('text', 'xterm-256', markdown, expected)

  # The Synopsis tests verify that the NAME and SYNOPSYS justification stays
  # within the page width and does not split flag and positional groups in
  # confusing places and also does not split terminal escape sequences.

  def testTextLongSynopsisXterm(self):
    markdown = self.LONG_SYNOPSIS_MARKDOWN
    expected = textwrap.dedent("""\
        \x1b[m\x1b[1mNAME\x1b[m
            gcloud compute instances - read and manipulate Google Compute Engine
                virtual machine instances

        \x1b[m\x1b[1mSYNOPSIS\x1b[m
            \x1b[1mgcloud compute instances\x1b[m \x1b[4mCOMMAND\x1b[m [\x1b[1m--format\x1b[m \x1b[4mFORMAT\x1b[m] [\x1b[1m--help\x1b[m]
                [\x1b[1m--project\x1b[m \x1b[4mPROJECT_ID\x1b[m] [\x1b[1m--quiet\x1b[m, \x1b[1m-q\x1b[m] [\x1b[1m--trace-token\x1b[m \x1b[4mTRACE_TOKEN\x1b[m] [\x1b[1m-h\x1b[m]

        \x1b[m\x1b[1mDESCRIPTION\x1b[m
            Read and manipulate Google Compute Engine virtual machine instances.
        \x1b[m""")
    self.Run('text', 'xterm', markdown, expected)

  def testTextLongSynopsisGroupXterm(self):
    markdown = self.LONG_SYNOPSIS_GROUP_MARKDOWN
    expected = textwrap.dedent("""\
        \x1b[m\x1b[1mNAME\x1b[m
            gcloud compute images deprecate - manage deprecation status of Google
                Compute Engine images

        \x1b[m\x1b[1mSYNOPSIS\x1b[m
            \x1b[1mgcloud compute images deprecate\x1b[m \x1b[4mNAME\x1b[m
                [\x1b[1m--delete-in\x1b[m \x1b[4mDELETE_IN\x1b[m | \x1b[1m--delete-on\x1b[m \x1b[4mDELETE_ON\x1b[m]
                [\x1b[1m--obsolete-in\x1b[m \x1b[4mOBSOLETE_IN\x1b[m | \x1b[1m--obsolete-on\x1b[m \x1b[4mOBSOLETE_ON\x1b[m]
                [\x1b[1m--replacement\x1b[m \x1b[4mREPLACEMENT\x1b[m] \x1b[1m--state\x1b[m \x1b[4mSTATE\x1b[m [\x1b[4mGCLOUD_WIDE_FLAG ...\x1b[m]

        \x1b[m\x1b[1mDESCRIPTION\x1b[m
            \x1b[1mgcloud compute images deprecate\x1b[m is used to deprecate images.
        \x1b[m""")
    self.Run('text', 'xterm', markdown, expected)

  def testTextLongerSynopsisXterm(self):
    markdown = self.LONGER_SYNOPSIS_MARKDOWN
    expected = textwrap.dedent("""\
        \x1b[m\x1b[1mNAME\x1b[m
            gcloud compute instances - read and manipulate Google Compute Engine
                virtual machine instances

        \x1b[m\x1b[1mSYNOPSIS\x1b[m
            \x1b[1mgcloud compute instances\x1b[m \x1b[4mCOMMAND\x1b[m [\x1b[1m--format\x1b[m \x1b[4mFORMAT\x1b[m] [\x1b[1m--help\x1b[m] [\x1b[1m-A\x1b[m] [\x1b[1m-B\x1b[m] [\x1b[1m-C\x1b[m]
                [\x1b[1m-D\x1b[m] [\x1b[1m-E\x1b[m] [\x1b[1m--project\x1b[m \x1b[4mPROJECT_ID\x1b[m] [\x1b[1m--quiet\x1b[m, \x1b[1m-q\x1b[m]
                [\x1b[1m--trace-token\x1b[m \x1b[4mTRACE_TOKEN\x1b[m] [\x1b[1m-h\x1b[m]

        \x1b[m\x1b[1mDESCRIPTION\x1b[m
            Read and manipulate Google Compute Engine virtual machine instances.
        \x1b[m""")
    self.Run('text', 'xterm', markdown, expected)

  def testTextLongestSynopsisXterm(self):
    markdown = self.LONGEST_SYNOPSIS_MARKDOWN
    expected = textwrap.dedent("""\
        \x1b[m\x1b[1mNAME\x1b[m
            gcloud compute instances create - create Google Compute Engine virtual
                machine instances

        \x1b[m\x1b[1mSYNOPSIS\x1b[m
            \x1b[1mgcloud compute instances create\x1b[m \x1b[4mNAME\x1b[m [\x1b[4mNAME\x1b[m ...]
                [\x1b[1m--boot-disk-device-name\x1b[m \x1b[4mBOOT_DISK_DEVICE_NAME\x1b[m]
                [\x1b[1m--boot-disk-size\x1b[m \x1b[4mBOOT_DISK_SIZE\x1b[m] [\x1b[1m--boot-disk-type\x1b[m \x1b[4mBOOT_DISK_TYPE\x1b[m]
                [\x1b[1m--can-ip-forward\x1b[m] [\x1b[1m--description\x1b[m \x1b[4mDESCRIPTION\x1b[m]
                [\x1b[1m--disk\x1b[m [\x1b[4mPROPERTY\x1b[m=\x1b[4mVALUE\x1b[m,...]]
                [\x1b[1m--image\x1b[m \x1b[4mIMAGE\x1b[m | \x1b[4mcentos-6\x1b[m | \x1b[4mcentos-7\x1b[m | \x1b[4mcontainer-vm\x1b[m | \x1b[4mcoreos\x1b[m | \x1b[4mdebian-7\x1b[m
                  | \x1b[4mdebian-7-backports\x1b[m | \x1b[4mopensuse-13\x1b[m | \x1b[4mrhel-6\x1b[m | \x1b[4mrhel-7\x1b[m | \x1b[4msles-11\x1b[m
                  | \x1b[4msles-12\x1b[m | \x1b[4mubuntu-12-04\x1b[m | \x1b[4mubuntu-14-04\x1b[m | \x1b[4mubuntu-14-10\x1b[m | \x1b[4mubuntu-15-04\x1b[m
                  | \x1b[4mwindows-2008-r2\x1b[m | \x1b[4mwindows-2012-r2\x1b[m] [\x1b[1m--image-project\x1b[m \x1b[4mIMAGE_PROJECT\x1b[m]
                [\x1b[1m--local-ssd\x1b[m [\x1b[4mPROPERTY\x1b[m=\x1b[4mVALUE\x1b[m,...]]
                [\x1b[1m--machine-type\x1b[m \x1b[4mMACHINE_TYPE\x1b[m; default="n1-standard-1"]
                [\x1b[1m--maintenance-policy\x1b[m \x1b[4mMAINTENANCE_POLICY\x1b[m]
                [\x1b[1m--metadata\x1b[m \x1b[4mKEY\x1b[m=\x1b[4mVALUE\x1b[m,[\x1b[4mKEY\x1b[m=\x1b[4mVALUE\x1b[m,...]]
                [\x1b[1m--metadata-from-file\x1b[m \x1b[4mKEY\x1b[m=\x1b[4mLOCAL_FILE_PATH\x1b[m,[\x1b[4mKEY\x1b[m=\x1b[4mLOCAL_FILE_PATH\x1b[m,...]]
                [\x1b[1m--network\x1b[m \x1b[4mNETWORK\x1b[m; default="default"]
                [\x1b[1m--address\x1b[m \x1b[4mADDRESS\x1b[m | \x1b[1m--no-address\x1b[m] [\x1b[1m--no-boot-disk-auto-delete\x1b[m]
                [\x1b[1m--no-restart-on-failure\x1b[m] [\x1b[1m--preemptible\x1b[m]
                [\x1b[1m--no-scopes\x1b[m | \x1b[1m--scopes\x1b[m [\x1b[4mACCOUNT\x1b[m=]\x1b[4mSCOPE\x1b[m,[[\x1b[4mACCOUNT\x1b[m=]\x1b[4mSCOPE\x1b[m,...]]
                [\x1b[1m--tags\x1b[m \x1b[4mTAG\x1b[m,[\x1b[4mTAG\x1b[m,...]] [\x1b[1m--zone\x1b[m \x1b[4mZONE\x1b[m] [\x1b[4mGCLOUD_WIDE_FLAG ...\x1b[m]

        \x1b[m\x1b[1mDESCRIPTION\x1b[m
            \x1b[1mgcloud compute instances create\x1b[m facilitates the creation of Google Compute
            Engine virtual machines.
        \x1b[m""")
    self.Run('text', 'xterm', markdown, expected)

  def testTextQuotedFontEmphasisXterm(self):
    markdown = self.FONT_EMPHASIS_MARKDOWN
    expected = textwrap.dedent("""\
        \x1b[m\x1b[1mTest Title\x1b[m

        \x1b[m\x1b[1mSECTION\x1b[m
            Double air quotes ``+-*/'' on non-identifier chars or single identifier
            chars ``x'' and inline \x1b[1m*code`_blocks\x1b[m should disable markdown in the quoted
            string with air quotes \x1b[1mretained/\x1b[m and code block quotes consumed.
        \x1b[m""")
    self.Run('text', 'xterm', markdown, expected)

  def testTextDefinitionList(self):
    markdown = self.DEFINITION_LIST_MARKDOWN
    expected = textwrap.dedent("""\
        \x1b[m\x1b[1mNESTED DEFINITION LISTS\x1b[m
            Intro text.
             \x1b[1mfirst top definition name\x1b[m
                First top definition description.
                 \x1b[1mfirst nested definition name\x1b[m
                    First nested definition description.
                 \x1b[1mlast nested definition name\x1b[m
                    Last nested definition description.
                Nested summary text.
             \x1b[1mlast top definition name\x1b[m
                Last top definition description.
            Top summary text.

        \x1b[m\x1b[1mNESTED DEFINITION LISTS WITH POP\x1b[m
            Intro text.
             \x1b[1mfirst top definition name\x1b[m
                First top definition description.
                 \x1b[1mfirst nested definition name\x1b[m
                    First nested definition description.
                 \x1b[1mlast nested definition name\x1b[m
                    Last nested definition description.
            Top summary text.
        \x1b[m""")
    self.Run('text', 'xterm', markdown, expected)

  def testTextDefinitionListEmptyItem(self):
    markdown = self.DEFINITION_LIST_EMPTY_ITEM_MARKDOWN
    expected = textwrap.dedent("""\
        \x1b[m\x1b[1mDEFINITION LIST EMPTY ITEM TESTS\x1b[m

        \x1b[m\x1b[1mPOSITIONAL ARGUMENTS\x1b[m
             SUPERFLUOUS
                Superfluous definition to bump the list nesting level.

                 g2 group description. At least one of these must be specified:

                   \x1b[4mFILE\x1b[m
                      The input file.

                   g21 details. At most one of these may be specified:

                     \x1b[1m--flag-21-a\x1b[m=\x1b[4mFLAG_21_A\x1b[m
                        Help 21 a.

                     \x1b[1m--flag-21-b\x1b[m=\x1b[4mFLAG_21_B\x1b[m
                        Help 21 b.

                   g22 details. At most one of these may be specified:

                     \x1b[1m--flag-22-a\x1b[m=\x1b[4mFLAG_22_A\x1b[m
                        Help 22 a.

                     \x1b[1m--flag-22-b\x1b[m=\x1b[4mFLAG_22_B\x1b[m
                        Help 22 b.

                 And an extraneous paragraph.

        \x1b[m\x1b[1mREQUIRED FLAGS\x1b[m
             g1 group details. Exactly one of these must be specified:

               g11 details.
                 \x1b[1m--flag-11-a\x1b[m=\x1b[4mFLAG_11_A\x1b[m
                    Help 11 a. This is a modal flag. It must be specified if any of the
                    other arguments in the group are specified.

                 \x1b[1m--flag-11-b\x1b[m=\x1b[4mFLAG_11_B\x1b[m
                    Help 11 b.

               g12 details.
                 \x1b[1m--flag-12-a\x1b[m=\x1b[4mFLAG_12_A\x1b[m
                    Help 12 a. This is a modal flag. It must be specified if any of the
                    other arguments in the group are specified.

                 \x1b[1m--flag-12-b\x1b[m=\x1b[4mFLAG_12_B\x1b[m
                    Help 12 b.
        \x1b[m""")
    self.Run('text', 'xterm', markdown, expected)


if __name__ == '__main__':
  test_base.main()
