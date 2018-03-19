# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Tests for the token_renderer module."""

from __future__ import absolute_import
from __future__ import unicode_literals
import io

from googlecloudsdk.core.document_renderers import render_document
from googlecloudsdk.core.document_renderers import token_renderer
from tests.lib.core.document_renderers import test_base
from prompt_toolkit.token import Token


class TokenMarkdownTests(test_base.Markdown):

  def SetUp(self):
    self.maxDiff = None

  def Run(self, markdown, expected, width=60, height=50):
    actual = render_document.MarkdownRenderer(
        token_renderer.TokenRenderer(
            width=width, height=height),
        fin=io.StringIO(markdown)).Run()
    self.assertEqual(expected, actual)

  def testTokenNullInput(self):
    markdown = self.NULL_MARKDOWN
    self.Run(
        markdown,
        [])

  def testTokenNewNotes(self):
    markdown = self.NEW_NOTES_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'Test Title')],
         [(Token.Markdown.Section, 'SECTION'),
          (Token.Markdown.Normal, ' Section prose.')]])

  def testTokenInsertNotes(self):
    markdown = self.INSERT_NOTES_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'Test Title')],
         [(Token.Markdown.Section, 'SECTION'),
          (Token.Markdown.Normal, ' Section prose.')],
         [(Token.Markdown.Section, 'NOTES'),
          (Token.Markdown.Normal, ' Original note.')]])

  def testTokenTitle(self):
    markdown = self.TITLE_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'Test Title')],
         [(Token.Markdown.Section, 'SECTION'),
          (Token.Markdown.Normal, ' Section prose.')]])

  def testTokenEmptyName(self):
    markdown = """\
## NAME
"""
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'NAME')]])

  def testTokenItsAHeadingBazinga(self):
    markdown = """\
## Faux heading ahead
====
"""
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'Faux heading ahead'),
          (Token.Markdown.Normal, ' ====')]])

  def testTokenEmptyTable(self):
    markdown = """\
## TABLE

[options="header",format="csv",grid="none",frame="none"]
"""
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'TABLE')]])

  def testTokenTable(self):
    markdown = """\
## TABLE

[options="header",format="csv",grid="none",frame="none"]
abc,123,A B C
pdq xyz,789012,X Y Z

And a sentence after the table.
"""
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'TABLE'),
          (Token.Markdown.Normal, '  abc     123    A B C')],
         [(Token.Markdown.Normal, '  pdq xyz 789012 X Y Z')],
         [],
         [(Token.Markdown.Normal, '  And a sentence after the table.')]])

  # The Synopsis tests verify that the NAME and SYNOPSYS justification stays
  # within the page width and does not split flag and positional groups in
  # confusing places.

  def testTokenLongSynopsis(self):
    markdown = self.LONG_SYNOPSIS_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'NAME'),
          (Token.Markdown.Normal,
           ' gcloud compute instances - read and manipulate Google')],
         [(Token.Markdown.Normal,
           '    Compute Engine virtual machine instances')],
         [(Token.Markdown.Section, 'SYNOPSIS'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Code, 'gcloud compute instances'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'COMMAND'),
          (Token.Markdown.Normal, ' ['),
          (Token.Markdown.Bold, '--format'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'FORMAT'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Bold, '--help'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--project'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'PROJECT_ID'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Bold, '--quiet'),
          (Token.Markdown.Normal, ', '),
          (Token.Markdown.Bold, '-q'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--trace-token'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'TRACE_TOKEN'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Bold, '-h'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Section, 'DESCRIPTION'),
          (Token.Markdown.Normal,
           ' Read and manipulate Google Compute Engine')],
         [(Token.Markdown.Normal, 'virtual machine instances.')]])

  def testTokenLongSynopsisGroup(self):
    markdown = self.LONG_SYNOPSIS_GROUP_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'NAME'),
          (Token.Markdown.Normal,
           ' gcloud compute images deprecate - manage deprecation status')],
         [(Token.Markdown.Normal, '    of Google Compute Engine images')],
         [(Token.Markdown.Section, 'SYNOPSIS'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Code, 'gcloud compute images deprecate'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'NAME')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--delete-in'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'DELETE_IN'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Bold, '--delete-on'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'DELETE_ON'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--obsolete-in'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'OBSOLETE_IN'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Bold, '--obsolete-on'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'OBSOLETE_ON'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--replacement'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'REPLACEMENT'),
          (Token.Markdown.Normal, '] '),
          (Token.Markdown.Bold, '--state'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'STATE')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Italic, 'GLOBAL-FLAG ...'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Section, 'DESCRIPTION'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'gcloud compute images deprecate'),
          (Token.Markdown.Normal, ' is used to')],
         [(Token.Markdown.Normal, 'deprecate images.')]])

  def testTokenLongerSynopsis(self):
    markdown = self.LONGER_SYNOPSIS_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'NAME'),
          (Token.Markdown.Normal,
           ' gcloud compute instances - read and manipulate Google')],
         [(Token.Markdown.Normal,
           '    Compute Engine virtual machine instances')],
         [(Token.Markdown.Section, 'SYNOPSIS'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Code, 'gcloud compute instances'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'COMMAND'),
          (Token.Markdown.Normal, ' ['),
          (Token.Markdown.Bold, '--format'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'FORMAT'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Bold, '--help'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '-A'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Bold, '-B'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Bold, '-C'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Bold, '-D'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Bold, '-E'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Bold, '--project'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'PROJECT_ID'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--quiet'),
          (Token.Markdown.Normal, ', '),
          (Token.Markdown.Bold, '-q'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Bold, '--trace-token'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'TRACE_TOKEN'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Bold, '-h'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Section, 'DESCRIPTION'),
          (Token.Markdown.Normal,
           ' Read and manipulate Google Compute Engine')],
         [(Token.Markdown.Normal, 'virtual machine instances.')]])

  def testTokenLongestSynopsis(self):
    markdown = self.LONGEST_SYNOPSIS_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'NAME'),
          (Token.Markdown.Normal,
           ' gcloud compute instances create - create Google Compute')],
         [(Token.Markdown.Normal, '    Engine virtual machine instances')],
         [(Token.Markdown.Section, 'SYNOPSIS'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Code, 'gcloud compute instances create'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'NAME'),
          (Token.Markdown.Normal, ' ['),
          (Token.Markdown.Italic, 'NAME'),
          (Token.Markdown.Normal, ' ...]')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--boot-disk-device-name'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'BOOT_DISK_DEVICE_NAME'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--boot-disk-size'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'BOOT_DISK_SIZE'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--boot-disk-type'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'BOOT_DISK_TYPE'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Bold, '--can-ip-forward'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--description'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'DESCRIPTION'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--disk'),
          (Token.Markdown.Normal, ' ['),
          (Token.Markdown.Italic, 'PROPERTY'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'VALUE'),
          (Token.Markdown.Normal, ',...]]')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--image'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'IMAGE'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Italic, 'centos-6'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Italic, 'centos-7'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Italic, 'container-vm')],
         [(Token.Markdown.Normal, '      | '),
          (Token.Markdown.Italic, 'coreos'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Italic, 'debian-7'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Italic, 'debian-7-backports')],
         [(Token.Markdown.Normal, '      | '),
          (Token.Markdown.Italic, 'opensuse-13'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Italic, 'rhel-6'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Italic, 'rhel-7'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Italic, 'sles-11'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Italic, 'sles-12')],
         [(Token.Markdown.Normal, '      | '),
          (Token.Markdown.Italic, 'ubuntu-12-04'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Italic, 'ubuntu-14-04'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Italic, 'ubuntu-14-10')],
         [(Token.Markdown.Normal, '      | '),
          (Token.Markdown.Italic, 'ubuntu-15-04'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Italic, 'windows-2008-r2'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Italic, 'windows-2012-r2'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--image-project'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'IMAGE_PROJECT'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--local-ssd'),
          (Token.Markdown.Normal, ' ['),
          (Token.Markdown.Italic, 'PROPERTY'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'VALUE'),
          (Token.Markdown.Normal, ',...]]')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--machine-type'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'MACHINE_TYPE'),
          (Token.Markdown.Normal, '; default="n1-standard-1"]')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--maintenance-policy'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'MAINTENANCE_POLICY'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--metadata'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'KEY'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'VALUE'),
          (Token.Markdown.Normal, ',['),
          (Token.Markdown.Italic, 'KEY'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'VALUE'),
          (Token.Markdown.Normal, ',...]]')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--metadata-from-file')],
         [(Token.Markdown.Normal, '      '),
          (Token.Markdown.Italic, 'KEY'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'LOCAL_FILE_PATH'),
          (Token.Markdown.Normal, ',['),
          (Token.Markdown.Italic, 'KEY'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'LOCAL_FILE_PATH'),
          (Token.Markdown.Normal, ',...]]')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--network'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'NETWORK'),
          (Token.Markdown.Normal, '; default="default"]')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--address'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'ADDRESS'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Bold, '--no-address'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--no-boot-disk-auto-delete'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Bold, '--no-restart-on-failure'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--preemptible'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--no-scopes')],
         [(Token.Markdown.Normal, '      | '),
          (Token.Markdown.Bold, '--scopes'),
          (Token.Markdown.Normal, ' ['),
          (Token.Markdown.Italic, 'ACCOUNT'),
          (Token.Markdown.Normal, '=]'),
          (Token.Markdown.Italic, 'SCOPE'),
          (Token.Markdown.Normal, ',[['),
          (Token.Markdown.Italic, 'ACCOUNT'),
          (Token.Markdown.Normal, '=]'),
          (Token.Markdown.Italic, 'SCOPE'),
          (Token.Markdown.Normal, ',...]]')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--tags'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'TAG'),
          (Token.Markdown.Normal, ',['),
          (Token.Markdown.Italic, 'TAG'),
          (Token.Markdown.Normal, ',...]] ['),
          (Token.Markdown.Bold, '--zone'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'ZONE'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Italic, 'GLOBAL-FLAG ...'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Section, 'DESCRIPTION'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'gcloud compute instances create'),
          (Token.Markdown.Normal, ' facilitates the')],
         [(Token.Markdown.Normal,
           'creation of Google Compute Engine virtual machines.')]])

  def testTokenLongSynopsisFlagValue(self):
    markdown = """## SYNOPSIS

`gcloud alpha compute backend-services create` _NAME_ [*--https-health-checks*=_HTTPS_HEALTH_CHECK_,[_HTTPS_HEALTH_CHECK_,...]] [*--iap*=[_disabled_],[_enabled_],[_oauth2-client-id_=_OAUTH2-CLIENT-ID_],[_oauth2-client-secret_=_OAUTH2-CLIENT-SECRET_]] [*--load-balancing-scheme*=_LOAD_BALANCING_SCHEME_; default="EXTERNAL"] [*--port-name*=_PORT_NAME_] [*--protocol*=_PROTOCOL_] [*--cache-key-query-string-blacklist*=[_QUERY_STRING_,...] | *--cache-key-query-string-whitelist*=_QUERY_STRING_,[_QUERY_STRING_,...]] [*--server*=_SERVER_,[_SERVER_,...], *-s* _SERVER_,[_SERVER_,...]; default="gcr.io,us.gcr.io,eu.gcr.io,asia.gcr.io,b.gcr.io,bucket.gcr.io,appengine.gcr.io,gcr.kubernetes.io"] [*--global* | *--region*=_REGION_] [_GLOBAL-FLAG ..._]
"""
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'SYNOPSIS'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Code,
           'gcloud alpha compute backend-services create'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'NAME')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--https-health-checks'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'HTTPS_HEALTH_CHECK'),
          (Token.Markdown.Normal, ',')],
         [(Token.Markdown.Normal, '      ['),
          (Token.Markdown.Italic, 'HTTPS_HEALTH_CHECK'),
          (Token.Markdown.Normal, ',...]]')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--iap'),
          (Token.Markdown.Normal, '=['),
          (Token.Markdown.Italic, 'disabled'),
          (Token.Markdown.Normal, '],['),
          (Token.Markdown.Italic, 'enabled'),
          (Token.Markdown.Normal, '],')],
         [(Token.Markdown.Normal, '      ['),
          (Token.Markdown.Italic, 'oauth2-client-id'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'OAUTH2-CLIENT-ID'),
          (Token.Markdown.Normal, '],')],
         [(Token.Markdown.Normal, '      ['),
          (Token.Markdown.Italic, 'oauth2-client-secret'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'OAUTH2-CLIENT-SECRET'),
          (Token.Markdown.Normal, ']]')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--load-balancing-scheme'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'LOAD_BALANCING_SCHEME'),
          (Token.Markdown.Normal, ';')],
         [(Token.Markdown.Normal, '      default="EXTERNAL"] ['),
          (Token.Markdown.Bold, '--port-name'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'PORT_NAME'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--protocol'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'PROTOCOL'),
          (Token.Markdown.Normal, ']')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--cache-key-query-string-blacklist'),
          (Token.Markdown.Normal, '=['),
          (Token.Markdown.Italic, 'QUERY_STRING'),
          (Token.Markdown.Normal, ',...]')],
         [(Token.Markdown.Normal, '      | '),
          (Token.Markdown.Bold, '--cache-key-query-string-whitelist'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'QUERY_STRING'),
          (Token.Markdown.Normal, ',')],
         [(Token.Markdown.Normal, '      ['),
          (Token.Markdown.Italic, 'QUERY_STRING'),
          (Token.Markdown.Normal, ',...]]')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--server'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'SERVER'),
          (Token.Markdown.Normal, ',['),
          (Token.Markdown.Italic, 'SERVER'),
          (Token.Markdown.Normal, ',...], '),
          (Token.Markdown.Bold, '-s'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'SERVER'),
          (Token.Markdown.Normal, ',['),
          (Token.Markdown.Italic, 'SERVER'),
          (Token.Markdown.Normal, ',...];')],
         [(Token.Markdown.Normal,
           '      default="gcr.io,us.gcr.io,eu.gcr.io,asia.gcr.io,')],
         [(Token.Markdown.Normal, '      b.gcr.io,')],
         [(Token.Markdown.Normal,
           '      bucket.gcr.io,appengine.gcr.io,gcr.kubernetes.io"]')],
         [(Token.Markdown.Normal, '    ['),
          (Token.Markdown.Bold, '--global'),
          (Token.Markdown.Normal, ' | '),
          (Token.Markdown.Bold, '--region'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Italic, 'REGION'),
          (Token.Markdown.Normal, '] ['),
          (Token.Markdown.Italic, 'GLOBAL-FLAG ...'),
          (Token.Markdown.Normal, ']')]])

  def testTokenCodeBlock(self):
    markdown = self.CODE_BLOCK_MARKDOWN
    expected = [
        [(Token.Markdown.Section, 'DESCRIPTION'),
         (Token.Markdown.Normal,
          ' The basic format of a YAML argument file is:')],
        [(Token.Markdown.Normal, '    arg-group1:')],
        [(Token.Markdown.Normal, '      arg1: value1  # a comment')],
        [(Token.Markdown.Normal, '      arg2: value2')],
        [(Token.Markdown.Normal, '      ...')],
        [(Token.Markdown.Normal, '    # Another comment')],
        [(Token.Markdown.Normal, '    arg-group2:')],
        [(Token.Markdown.Normal, '      arg3: value3')],
        [(Token.Markdown.Normal, '      ...')],
        [(Token.Markdown.Normal, 'and pretty printed as yaml:')],
        [(Token.Markdown.Normal, '    arg-group1:')],
        [(Token.Markdown.Normal, '      arg1: value1  # a comment')],
        [(Token.Markdown.Normal, '      arg2: value2')],
        [(Token.Markdown.Normal, '      ...')],
        [(Token.Markdown.Normal, '    # Another comment')],
        [(Token.Markdown.Normal, '    arg-group2:')],
        [(Token.Markdown.Normal, '      arg3: value3')],
        [(Token.Markdown.Normal, '      ...')],
        [(Token.Markdown.Normal,
          'List arguments may be specified within square brackets:')],
        [(Token.Markdown.Normal, '    device-ids: [Nexus5, Nexus6, Nexus9]')],
        [(Token.Markdown.Normal,
          'or by using the alternate YAML list notation with one dash')],
        [(Token.Markdown.Normal,
          'per list item with an unindented code block:')],
        [(Token.Markdown.Normal, '    device-ids:')],
        [(Token.Markdown.Normal, '      - Nexus5')],
        [(Token.Markdown.Normal, '      - Nexus6')],
        [(Token.Markdown.Normal, '      - Nexus9')],
        [(Token.Markdown.Normal, '    device-numbers:')],
        [(Token.Markdown.Normal, '      - 5')],
        [(Token.Markdown.Normal, '      - 6')],
        [(Token.Markdown.Normal, '      - 9')],
        [(Token.Markdown.Normal, 'and some python code for coverage:')],
        [(Token.Markdown.Normal, '    class Xyz(object):')],
        [(Token.Markdown.Normal, "      '''Some class.'''")],
        [(Token.Markdown.Normal, '      def __init__(self, value):')],
        [(Token.Markdown.Normal, '        self.value = value')],
        [(Token.Markdown.Normal,
          'If a list argument only contains a single value, you may')],
        [(Token.Markdown.Normal, 'omit the square brackets:')],
        [(Token.Markdown.Normal, '    device-ids: Nexus9')],
        [(Token.Markdown.Normal, '  '),
         (Token.Markdown.Section, 'Composition'),
         (Token.Markdown.Normal, ' A special '),
         (Token.Markdown.Bold, 'include: ['),
         (Token.Markdown.BoldItalic, 'ARG_GROUP1'),
         (Token.Markdown.Bold, ', ...]'),
         (Token.Markdown.Normal, ' syntax')],
        [(Token.Markdown.Normal,
          'allows merging or composition of argument groups (see')],
        [(Token.Markdown.Bold, 'EXAMPLES'),
         (Token.Markdown.Normal, ' below). Included argument groups can '),
         (Token.Markdown.Bold, 'include:')],
        [(Token.Markdown.Normal,
          'other argument groups within the same YAML file, with')],
        [(Token.Markdown.Normal, 'unlimited nesting.')]]
    # Height large enough to avoid truncation.
    self.Run(markdown, expected, height=100)
    # Height 0 to disable truncation.
    self.Run(markdown, expected, height=0)

  def testTokenCodeBlockHeight8(self):
    markdown = self.CODE_BLOCK_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'DESCRIPTION'),
          (Token.Markdown.Normal,
           ' The basic format of a YAML argument file is:')],
         [(Token.Markdown.Normal, '    arg-group1:')],
         [(Token.Markdown.Normal, '      arg1: value1  # a comment')],
         [(Token.Markdown.Normal, '      arg2: value2')],
         [(Token.Markdown.Normal, '      ...')],
         [(Token.Markdown.Normal, '    # Another comment')],
         [(Token.Markdown.Normal, '    arg-group2:')],
         [(Token.Markdown.Normal, '      arg3: value3'),
          (Token.Markdown.Truncated, '...')]],
        height=8)

  def testTokenExampleBlock(self):
    markdown = self.EXAMPLE_BLOCK_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'DESCRIPTION'),
          (Token.Markdown.Normal, ' The basic example is:')],
         [(Token.Markdown.Normal, '    # Run first:')],
         [(Token.Markdown.Normal, '    gcloud foo bar')],
         [(Token.Markdown.Normal, '    # Run last:')],
         [(Token.Markdown.Normal, '    gcloud bar foo')],
         [(Token.Markdown.Normal,
           'However, in non-leap year months with a blue moon:')],
         [(Token.Markdown.Normal, '    # Run first:')],
         [(Token.Markdown.Normal, '    gcloud bar foo')],
         [(Token.Markdown.Normal, '    # Run last:')],
         [(Token.Markdown.Normal, '    gcloud foo bar')],
         [(Token.Markdown.Normal, '    # Run again')],
         [(Token.Markdown.Normal, '    gcloud foo foo')],
         [(Token.Markdown.Normal, '    device-ids: [Nexus5, Nexus6, Nexus9]')],
         [(Token.Markdown.Normal, "And that's it.")]])

  def testTokenQuotedFontEmphasis(self):
    markdown = self.FONT_EMPHASIS_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'Test Title')],
         [(Token.Markdown.Section, 'SECTION'),
          (Token.Markdown.Normal,
           " Double air quotes ``+-*/'' on non-identifier chars")],
         [(Token.Markdown.Normal,
           "or single identifier chars ``x'' and inline "),
          (Token.Markdown.Code, '*code`_blocks')],
         [(Token.Markdown.Normal,
           'should disable markdown in the quoted string with air')],
         [(Token.Markdown.Normal, 'quotes '),
          (Token.Markdown.Code, 'retained/'),
          (Token.Markdown.Normal, ' and code block quotes consumed.')]])

  def testTokenLink(self):
    markdown = self.LINK_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'Test Title')],
         [(Token.Markdown.Section, 'SECTION'),
          (Token.Markdown.Normal, ' Here are the link styles:')],
         [(Token.Markdown.Normal,
           '  \u25aa Style 1 display[this] (http://foo.bar) target and')],
         [(Token.Markdown.Normal, '    text.')],
         [(Token.Markdown.Normal,
           '  \u25aa Style 1 http://foo.bar target only.')],
         [(Token.Markdown.Normal,
           '  \u25aa Style 2 display[this] (http://foo.bar) text and')],
         [(Token.Markdown.Normal, '    target.')],
         [(Token.Markdown.Normal,
           '  \u25aa Style 2 display[this] text and local target.')],
         [(Token.Markdown.Normal,
           '  \u25aa Style 2 http://foo.bar target only.')],
         [(Token.Markdown.Normal,
           '  \u25aa Style 2 foo#bar local target only.')],
         [(Token.Markdown.Normal,
           '  \u25aa Style 2 [display[this]]() text only.')],
         [(Token.Markdown.Normal,
           '  \u25aa Style 2 []() empty text and target.')]])

  def testTokenDefinitionList(self):
    markdown = self.DEFINITION_LIST_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'NESTED DEFINITION LISTS'),
          (Token.Markdown.Normal, ' Intro text.')],
         [(Token.Markdown.Normal, ' '),
          (Token.Markdown.Definition, 'first top definition name')],
         [(Token.Markdown.Normal, '    First top definition description.')],
         [(Token.Markdown.Normal, '     '),
          (Token.Markdown.Definition, 'first nested definition name')],
         [(Token.Markdown.Normal,
           '        First nested definition description.')],
         [(Token.Markdown.Normal, '     '),
          (Token.Markdown.Definition, 'last nested definition name')],
         [(Token.Markdown.Normal,
           '        Last nested definition description.')],
         [(Token.Markdown.Normal, '    Nested summary text.')],
         [(Token.Markdown.Normal, ' '),
          (Token.Markdown.Definition, 'last top definition name')],
         [(Token.Markdown.Normal, '    Last top definition description.')],
         [(Token.Markdown.Normal, 'Top summary text.')],
         [(Token.Markdown.Section, 'NESTED DEFINITION LISTS WITH POP'),
          (Token.Markdown.Normal, ' Intro text.')],
         [(Token.Markdown.Normal, ' '),
          (Token.Markdown.Definition, 'first top definition name')],
         [(Token.Markdown.Normal, '    First top definition description.')],
         [(Token.Markdown.Normal, '     '),
          (Token.Markdown.Definition, 'first nested definition name')],
         [(Token.Markdown.Normal,
           '        First nested definition description.')],
         [(Token.Markdown.Normal, '     '),
          (Token.Markdown.Definition, 'last nested definition name')],
         [(Token.Markdown.Normal,
           '        Last nested definition description.')],
         [(Token.Markdown.Normal, 'Top summary text.')]])

  def testTokenDefinitionListEmptyItem(self):
    markdown = self.DEFINITION_LIST_EMPTY_ITEM_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'DEFINITION LIST EMPTY ITEM TESTS')],
         [(Token.Markdown.Section, 'POSITIONAL ARGUMENTS')],
         [(Token.Markdown.Normal, ' '),
          (Token.Markdown.Definition, 'SUPERFLUOUS')],
         [(Token.Markdown.Normal,
           '    Superfluous definition to bump the list nesting level.')],
         [(Token.Markdown.Normal,
           '     g2 group description. At least one of these must be')],
         [(Token.Markdown.Normal, '     specified:')],
         [(Token.Markdown.Normal, '       '),
          (Token.Markdown.Definition, 'FILE')],
         [(Token.Markdown.Normal, '          The input file.')],
         [(Token.Markdown.Normal,
           '       g21 details. At most one of these may be specified:')],
         [(Token.Markdown.Normal, '         '),
          (Token.Markdown.Definition, '--flag-21-a'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Value, 'FLAG_21_A')],
         [(Token.Markdown.Normal, '            Help 21 a.')],
         [(Token.Markdown.Normal, '         '),
          (Token.Markdown.Definition, '--flag-21-b'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Value, 'FLAG_21_B')],
         [(Token.Markdown.Normal, '            Help 21 b.')],
         [(Token.Markdown.Normal,
           '       g22 details. At most one of these may be specified:')],
         [(Token.Markdown.Normal, '         '),
          (Token.Markdown.Definition, '--flag-22-a'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Value, 'FLAG_22_A')],
         [(Token.Markdown.Normal, '            Help 22 a.')],
         [(Token.Markdown.Normal, '         '),
          (Token.Markdown.Definition, '--flag-22-b'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Value, 'FLAG_22_B')],
         [(Token.Markdown.Normal, '            Help 22 b.')],
         [(Token.Markdown.Normal, '     And an extraneous paragraph.')],
         [(Token.Markdown.Section, 'REQUIRED FLAGS')],
         [(Token.Markdown.Normal,
           'g1 group details. Exactly one of these must be specified:')],
         [(Token.Markdown.Normal, '   g11 details.')],
         [(Token.Markdown.Normal, '     '),
          (Token.Markdown.Definition, '--flag-11-a'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Value, 'FLAG_11_A')],
         [(Token.Markdown.Normal,
           '        Help 11 a. This is a modal flag. It must be')],
         [(Token.Markdown.Normal,
           '        specified if any of the other arguments in the')],
         [(Token.Markdown.Normal, '        group are specified.')],
         [(Token.Markdown.Normal, '     '),
          (Token.Markdown.Definition, '--flag-11-b'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Value, 'FLAG_11_B')],
         [(Token.Markdown.Normal, '        Help 11 b.')],
         [(Token.Markdown.Normal, '   g12 details.')],
         [(Token.Markdown.Normal, '     '),
          (Token.Markdown.Definition, '--flag-12-a'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Value, 'FLAG_12_A')],
         [(Token.Markdown.Normal,
           '        Help 12 a. This is a modal flag. It must be')],
         [(Token.Markdown.Normal,
           '        specified if any of the other arguments in the')],
         [(Token.Markdown.Normal, '        group are specified.')],
         [(Token.Markdown.Normal, '     '),
          (Token.Markdown.Definition, '--flag-12-b'),
          (Token.Markdown.Normal, '='),
          (Token.Markdown.Value, 'FLAG_12_B')],
         [(Token.Markdown.Normal, '        Help 12 b.')]])

  def testTokenGroupHelp(self):
    markdown = """\
# GCLOUD_COMPUTE(1)


## NAME

gcloud compute - create and manipulate Google Compute Engine resources


## SYNOPSIS

`gcloud compute` _GROUP_ | _COMMAND_ [_GLOBAL-FLAG ..._]


## DESCRIPTION

The gcloud compute command group lets you create, configure and
manipulate Google Compute Engine virtual machines.

With Compute Engine you can create and run virtual machines
on Google infrastructure. Compute Engine offers scale, performance, and
value that allows you to easily launch large compute clusters on
Google's infrastructure.

More information on Compute Engine can be found here:
https://cloud.google.com/compute/ and detailed documentation can be
found here: https://cloud.google.com/compute/docs/


## GLOBAL FLAGS

Run *$ link:gcloud[gcloud] help* for a description of flags available to
all commands.


## GROUPS

`_GROUP_` is one of the following:

*link:gcloud/compute/addresses[addresses]*::

Read and manipulate Google Compute Engine addresses

*link:gcloud/compute/backend-services[backend-services]*::

List, create, and delete backend services

*link:gcloud/compute/disk-types[disk-types]*::

Read Google Compute Engine virtual disk types

*link:gcloud/compute/disks[disks]*::

Read and manipulate Google Compute Engine disks

*link:gcloud/compute/firewall-rules[firewall-rules]*::

List, create, update, and delete Google Compute Engine firewall rules

*link:gcloud/compute/forwarding-rules[forwarding-rules]*::

Read and manipulate forwarding rules to send traffic to load balancers

*link:gcloud/compute/health-checks[health-checks]*::

Read and manipulate health checks for load balanced instances

*link:gcloud/compute/http-health-checks[http-health-checks]*::

Read and manipulate HTTP health checks for load balanced instances

*link:gcloud/compute/https-health-checks[https-health-checks]*::

Read and manipulate HTTPS health checks for load balanced instances

*link:gcloud/compute/images[images]*::

List, create, and delete Google Compute Engine images

*link:gcloud/compute/instance-groups[instance-groups]*::

Read and manipulate Google Compute Engine instance groups.

*link:gcloud/compute/instance-templates[instance-templates]*::

Read and manipulate Google Compute Engine instances templates.

*link:gcloud/compute/instances[instances]*::

Read and manipulate Google Compute Engine virtual machine instances

*link:gcloud/compute/machine-types[machine-types]*::

Read Google Compute Engine virtual machine types

*link:gcloud/compute/networks[networks]*::

List, create, and delete Google Compute Engine networks

*link:gcloud/compute/operations[operations]*::

Read and manipulate Google Compute Engine operations

*link:gcloud/compute/project-info[project-info]*::

Read and manipulate project-level data like quotas and metadata

*link:gcloud/compute/regions[regions]*::

List Google Compute Engine regions

*link:gcloud/compute/routers[routers]*::

List, create, and delete Google Compute Engine routers

*link:gcloud/compute/routes[routes]*::

Read and manipulate routes

*link:gcloud/compute/snapshots[snapshots]*::

List, describe, and delete Google Compute Engine snapshots

*link:gcloud/compute/ssl-certificates[ssl-certificates]*::

List, create, and delete Google Compute Engine SSL certificates

*link:gcloud/compute/target-http-proxies[target-http-proxies]*::

List, create, and delete target HTTP proxies

*link:gcloud/compute/target-https-proxies[target-https-proxies]*::

List, create, and delete target HTTPS proxies

*link:gcloud/compute/target-instances[target-instances]*::

Read and manipulate Google Compute Engine virtual target instances

*link:gcloud/compute/target-pools[target-pools]*::

Control Compute Engine target pools for network load balancing.

*link:gcloud/compute/target-ssl-proxies[target-ssl-proxies]*::

List, create, and delete target SSL proxies

*link:gcloud/compute/target-vpn-gateways[target-vpn-gateways]*::

Read and manipulate Google Compute Engine VPN Gateways

*link:gcloud/compute/url-maps[url-maps]*::

List, create, and delete URL maps

*link:gcloud/compute/vpn-tunnels[vpn-tunnels]*::

Read and manipulate Google Compute Engine VPN Tunnels

*link:gcloud/compute/zones[zones]*::

List Google Compute Engine zones


## COMMANDS

`_COMMAND_` is one of the following:

*link:gcloud/compute/config-ssh[config-ssh]*::

Populate SSH config files with Host entries from each instance

*link:gcloud/compute/connect-to-serial-port[connect-to-serial-port]*::

Connect to the serial port of an instance.

*link:gcloud/compute/copy-files[copy-files]*::

Copy files to and from Google Compute Engine virtual machines

*link:gcloud/compute/reset-windows-password[reset-windows-password]*::

Reset and return a password for a Windows machine instance

*link:gcloud/compute/ssh[ssh]*::

SSH into a virtual machine instance
"""
    expected = [
        [(Token.Markdown.Section, 'NAME'),
         (Token.Markdown.Normal,
          ' gcloud compute - create and manipulate Google Compute Engine '
          'resources')],
        [(Token.Markdown.Section, 'SYNOPSIS'),
         (Token.Markdown.Normal, ' '),
         (Token.Markdown.Code, 'gcloud compute'),
         (Token.Markdown.Normal, ' '),
         (Token.Markdown.Italic, 'GROUP'),
         (Token.Markdown.Normal, ' | '),
         (Token.Markdown.Italic, 'COMMAND'),
         (Token.Markdown.Normal, ' ['),
         (Token.Markdown.Italic, 'GLOBAL-FLAG ...'),
         (Token.Markdown.Normal, ']')],
        [(Token.Markdown.Section, 'DESCRIPTION'),
         (Token.Markdown.Normal,
          ' The gcloud compute command group lets you create, configure and')],
        [(Token.Markdown.Normal,
          'manipulate Google Compute Engine virtual machines.')],
        [(Token.Markdown.Normal,
          'With Compute Engine you can create and run virtual machines on '
          'Google')],
        [(Token.Markdown.Normal,
          'infrastructure. Compute Engine offers scale, performance, and '
          'value that allows')],
        [(Token.Markdown.Normal,
          "you to easily launch large compute clusters on Google's "
          'infrastructure.')],
        [(Token.Markdown.Normal,
          'More information on Compute Engine can be found here:')],
        [(Token.Markdown.Normal,
          'https://cloud.google.com/compute/ and detailed documentation can '
          'be found her'),
         (Token.Markdown.Truncated, '...')]
    ]
    self.Run(markdown, expected, width=80, height=9)

  def testTokenCommandHelp(self):
    markdown = """\
# GCLOUD_COMPUTE_SSH(1)


## NAME

gcloud compute ssh - SSH into a virtual machine instance


## SYNOPSIS

`gcloud compute ssh` [_USER_@]_INSTANCE_ _SSH_ARGS_ [*--command*=_COMMAND_] [*--container*=_CONTAINER_] [*--dry-run*] [*--force-key-file-overwrite*] [*--plain*] [*--ssh-flag*=_SSH_FLAG_] [*--ssh-key-file*=_SSH_KEY_FILE_] [*--strict-host-key-checking*=_STRICT_HOST_KEY_CHECKING_] [*--zone*=_ZONE_] [_GLOBAL-FLAG ..._]


## DESCRIPTION

*ssh* is a thin wrapper around the *ssh(1)* command that
takes care of authentication and the translation of the
instance name into an IP address.

This command ensures that the user's public SSH key is present
in the project's metadata. If the user does not have a public
SSH key, one is generated using *ssh-keygen(1)* (if the `--quiet`
flag is given, the generated key will have an empty passphrase).


## POSITIONAL ARGUMENTS

[_USER_@]_INSTANCE_::

Specifies the instance to SSH into.
+
`_USER_` specifies the username with which to SSH. If omitted,
$USER from the environment is selected.

_SSH_ARGS_::

Flags and positionals passed to the underlying ssh implementation.
+

The '--' argument must be specified between gcloud specific args on the left and SSH_ARGS on the right. IMPORTANT: previously, commands allowed the omission of the --, and unparsed arguments were treated as implementation args. This usage is being deprecated and will be removed in March 2017. Example:
+
        $ link:gcloud/compute[gcloud compute] ssh example-instance --zone us-central1-a -- -vvv \
      -L 80:%INSTANCE%:80


## FLAGS

*--command*=_COMMAND_::

A command to run on the virtual machine.
+
Runs the command on the target instance and then exits.

*--container*=_CONTAINER_::

The name of a container inside of the virtual machine instance to
connect to. This only applies to virtual machines that are using
a Google container virtual machine image. For more information,
see [](https://cloud.google.com/compute/docs/containers)

*--dry-run*::

Print the equivalent scp/ssh command that would be run to stdout, instead of executing it.

*--force-key-file-overwrite*::

If enabled, the gcloud command-line tool will regenerate and overwrite
the files associated with a broken SSH key without asking for
confirmation in both interactive and non-interactive environments.
+
If disabled, the files associated with a broken SSH key will not be
regenerated and will fail in both interactive and non-interactive
environments.
+

*--plain*::

Suppress the automatic addition of *ssh(1)*/*scp(1)* flags. This flag
is useful if you want to take care of authentication yourself or
use specific ssh/scp features.

*--ssh-flag*=_SSH_FLAG_::

Additional flags to be passed to *ssh(1)*. It is recommended that flags
be passed using an assignment operator and quotes. This flag will
replace occurences of `_%USER%_` and `_%INSTANCE%_` with their
dereferenced values. Example:
+
  $ link:gcloud/compute[gcloud compute] ssh example-instance --zone us-central1-a \
      --ssh-flag="-vvv" --ssh-flag="-L 80:%INSTANCE%:80"
+
is equivalent to passing the flags `_--vvv_` and `_-L
80:162.222.181.197:80_` to *ssh(1)* if the external IP address of
'example-instance' is 162.222.181.197.

*--ssh-key-file*=_SSH_KEY_FILE_::

The path to the SSH key file. By default, this is `_~/.ssh/google_compute_engine_`.

*--strict-host-key-checking*=_STRICT_HOST_KEY_CHECKING_::
Override the default behavior of StrictHostKeyChecking for the connection.
By default, StrictHostKeyChecking is set to 'no' the first time you
connect to an instance, and will be set to 'yes' for all
subsequent connections. _STRICT_HOST_KEY_CHECKING_ must be one of: *ask*, *no*, *yes*.

*--zone*=_ZONE_::

The zone of the instance to connect to. If not specified, you will be prompted to select a zone.
+
To avoid prompting when this flag is omitted, you can set the
`_compute/zone_` property:
+
  $ link:gcloud/config[gcloud config] set compute/zone ZONE
+
A list of zones can be fetched by running:
+
  $ link:gcloud/compute/zones[gcloud compute zones] list
+
To unset the property, run:
+
  $ link:gcloud/config[gcloud config] unset compute/zone
+
Alternatively, the zone can be stored in the environment variable
`_CLOUDSDK_COMPUTE_ZONE_`.


## GLOBAL FLAGS

Run *$ link:gcloud[gcloud] help* for a description of flags available to
all commands.


## EXAMPLES

To SSH into 'example-instance' in zone `_us-central1-a_`, run:

  $ ssh example-instance --zone us-central1-a

You can also run a command on the virtual machine. For
example, to get a snapshot of the guest's process tree, run:

  $ ssh example-instance --zone us-central1-a --command "ps -ejH"

If you are using the Google container virtual machine image, you
can SSH into one of your containers with:

  $ ssh example-instance --zone us-central1-a --container CONTAINER
"""
    expected = [
        [(Token.Markdown.Section, 'NAME'),
         (Token.Markdown.Normal,
          ' gcloud compute ssh - SSH into a virtual machine instance')],
        [(Token.Markdown.Section, 'SYNOPSIS'),
         (Token.Markdown.Normal, ' '),
         (Token.Markdown.Code, 'gcloud compute ssh'),
         (Token.Markdown.Normal, ' ['),
         (Token.Markdown.Italic, 'USER'),
         (Token.Markdown.Normal, '@]'),
         (Token.Markdown.Italic, 'INSTANCE'),
         (Token.Markdown.Normal, ' '),
         (Token.Markdown.Italic, 'SSH_ARGS'),
         (Token.Markdown.Normal, ' ['),
         (Token.Markdown.Bold, '--command'),
         (Token.Markdown.Normal, '='),
         (Token.Markdown.Italic, 'COMMAND'),
         (Token.Markdown.Normal, ']')],
        [(Token.Markdown.Normal, '    ['),
         (Token.Markdown.Bold, '--container'),
         (Token.Markdown.Normal, '='),
         (Token.Markdown.Italic, 'CONTAINER'),
         (Token.Markdown.Normal, '] ['),
         (Token.Markdown.Bold, '--dry-run'),
         (Token.Markdown.Normal, '] ['),
         (Token.Markdown.Bold, '--force-key-file-overwrite'),
         (Token.Markdown.Normal, '] ['),
         (Token.Markdown.Bold, '--plain'),
         (Token.Markdown.Normal, ']')],
        [(Token.Markdown.Normal, '    ['),
         (Token.Markdown.Bold, '--ssh-flag'),
         (Token.Markdown.Normal, '='),
         (Token.Markdown.Italic, 'SSH_FLAG'),
         (Token.Markdown.Normal, '] ['),
         (Token.Markdown.Bold, '--ssh-key-file'),
         (Token.Markdown.Normal, '='),
         (Token.Markdown.Italic, 'SSH_KEY_FILE'),
         (Token.Markdown.Normal, ']')],
        [(Token.Markdown.Normal, '    ['),
         (Token.Markdown.Bold, '--strict-host-key-checking'),
         (Token.Markdown.Normal, '='),
         (Token.Markdown.Italic, 'STRICT_HOST_KEY_CHECKING'),
         (Token.Markdown.Normal, '] ['),
         (Token.Markdown.Bold, '--zone'),
         (Token.Markdown.Normal, '='),
         (Token.Markdown.Italic, 'ZONE'),
         (Token.Markdown.Normal, ']')],
        [(Token.Markdown.Normal, '    ['),
         (Token.Markdown.Italic, 'GLOBAL-FLAG ...'),
         (Token.Markdown.Normal, ']')],
        [(Token.Markdown.Section, 'DESCRIPTION'),
         (Token.Markdown.Normal, ' '),
         (Token.Markdown.Bold, 'ssh'),
         (Token.Markdown.Normal, ' is a thin wrapper around the '),
         (Token.Markdown.Bold, 'ssh(1)'),
         (Token.Markdown.Normal, ' command that takes care of')],
        [(Token.Markdown.Normal,
          'authentication and the translation of the instance name into an '
          'IP address.')],
        [(Token.Markdown.Normal,
          "This command ensures that the user's public SSH key is present "
          "in the project"),
         (Token.Markdown.Truncated, '...')]
    ]
    self.Run(markdown, expected, width=80, height=9)

  def testTokenTruncation_1(self):
    markdown = 'a b c d e f g h i j k l m'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'a b c d e f g'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_2(self):
    markdown = 'ab cd ef gh ij kl mn op qr'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'ab cd ef gh i'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_3(self):
    markdown = 'abc def ghi jkl mno pqr stu'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abc def ghi j'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_4(self):
    markdown = 'abcd efgh ijkl mnop qrst uvwx'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcd efgh ijk'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_5(self):
    markdown = 'abcde fghij klmno pqrst uvwxy'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcde fghij'),
          (Token.Markdown.Normal, ' k'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_6(self):
    markdown = 'abcdef ghijkl mnopqr stuvwx yzABCD'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdef ghijkl'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_7(self):
    markdown = 'abcdefg hijklmn opqrstu vwxyzA BCDEFGH IJKLMNO'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefg hijkl'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_8(self):
    markdown = 'abcdefgh ijklmnop qrstuvwx yzABCDEFG HIJKLMNO'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefgh'),
          (Token.Markdown.Normal, ' ijkl'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_9(self):
    markdown = 'abcdefghi jklmnopqr stuvwxyzA BCDEFGHIJK LMNOPQRST'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefghi'),
          (Token.Markdown.Normal, ' jkl'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_10(self):
    markdown = 'abcdefghij klmnopqrst uvwxyzABCD EFGHIJKLMNO PQRSTUVWXYZ'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefghij'),
          (Token.Markdown.Normal, ' kl'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_11(self):
    markdown = 'abcdefghijk lmnopqrstuv wxyzABCDEFG HIJKLMNOPQRS TUVWXYZ1234'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefghijk'),
          (Token.Markdown.Normal, ' l'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_12(self):
    markdown = 'abcdefghijkl mnopqrstuvwx yzABCDEFGHIJ KLMNOPQRSTUVW'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefghijkl'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_13(self):
    markdown = 'abcdefghijklm nopqrstuvwxyz ABCDEFGHIJKLM NOPQRSTUVWXYZ'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefghijklm'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_14(self):
    markdown = 'abcdefghijklmn opqrstuvwxyzAB CDEFGHIJKLMNOP QRSTUVWXYZ1234'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefghijklm'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_15(self):
    markdown = 'abcdefghijklmno pqrstuvwxyzABCD EFGHIJKLMNOPQRS'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefghijklm'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_16(self):
    markdown = 'abcdefghijklmnop qrstuvwxyzABCDEF GHIJKLMNOPQRSTUV'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefghijklm'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_17(self):
    markdown = 'abcdefghijklmnopq rstuvwxyzABCDEFGH'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefghijklm'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_8_7(self):
    markdown = 'abcdefgh ijklmno'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefgh'),
          (Token.Markdown.Normal, ' ijkl'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_8_8(self):
    markdown = 'abcdefgh ijklmnop'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefgh'),
          (Token.Markdown.Normal, ' ijkl'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncation_8_9(self):
    markdown = 'abcdefgh ijklmnopq'
    self.Run(
        markdown,
        [[(Token.Markdown.Normal, 'abcdefgh'),
          (Token.Markdown.Normal, ' ijkl'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncationAlternatingEmbellishments_1(self):
    markdown = '*a* _b_ *c* _d_ *e* _f_ *g* _h_ *i* _j_ *k* _l_ *m*'
    self.Run(
        markdown,
        [[(Token.Markdown.Bold, 'a'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'b'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'c'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'd'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'e'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'f'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'g'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncationAlternatingEmbellishments_2(self):
    markdown = '*ab* _cd_ *ef* _gh_ *ij* _kl_ *mn* _op_ *qr*'
    self.Run(
        markdown,
        [[(Token.Markdown.Bold, 'ab'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'cd'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'ef'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'gh'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'i'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)

  def testTokenTruncationAlternatingEmbellishments_3(self):
    markdown = '*abc* _def_ *ghi* _jkl_ *mno* _pqr_ *stu*'
    self.Run(
        markdown,
        [[(Token.Markdown.Bold, 'abc'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'def'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'ghi'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Italic, 'j'),
          (Token.Markdown.Truncated, '...')]],
        width=16,
        height=1)


class TokenUTF8MarkdownTests(test_base.UTF8):

  def SetUp(self):
    self.maxDiff = None

  def Run(self, markdown, expected, width=60, height=50):
    actual = render_document.MarkdownRenderer(
        token_renderer.TokenRenderer(
            width=width, height=height),
        fin=io.StringIO(markdown)).Run()
    self.assertEqual(expected, actual)

  def testTokenBulletList(self):
    markdown = self.BULLET_MARKDOWN
    self.Run(
        markdown,
        [[(Token.Markdown.Section, 'ANSI + UTF-8 Tests')],
         [(Token.Markdown.Section, 'Bullets')],
         [(Token.Markdown.Normal, '  \u25aa bullet 1.1 '),
          (Token.Markdown.Bold, 'bold')],
         [(Token.Markdown.Normal, '    \u25c6 bullet 2.1 '),
          (Token.Markdown.Italic, 'italic')],
         [(Token.Markdown.Normal, '      \u25b8 bullet 3.1 '),
          (Token.Markdown.BoldItalic, 'bold-italic')],
         [(Token.Markdown.Normal, '    \u25c6 bullet 2.2 '),
          (Token.Markdown.BoldItalic, 'italic-bold')],
         [(Token.Markdown.Normal, '      \u25b8 bullet 3.2 normal')],
         [(Token.Markdown.Normal, '  \u25aa bullet 1.2')],
         [(Token.Markdown.Section, 'Justification'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word')],
         [(Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, ' '),
          (Token.Markdown.Bold, 'word'),
          (Token.Markdown.Normal, '.')]])


if __name__ == '__main__':
  test_base.main()
