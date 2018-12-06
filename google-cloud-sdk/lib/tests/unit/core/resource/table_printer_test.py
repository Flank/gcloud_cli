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

"""Unit tests for the table_printer module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import sys
import textwrap

from googlecloudsdk.calliope import display_taps
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.document_renderers import render_document
from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_printer_base
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.core.resource import table_printer
from googlecloudsdk.core.util import peek_iterable
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.core.resource import resource_printer_test_base

_ZERO_WIDTH_SPACE = '\u200b'
_SOFT_HYPHEN = '\u00ad'


def Pager(resources, records_per_page):
  tap = display_taps.Pager(records_per_page)
  return peek_iterable.Tapper(resources, tap)


class TablePrinterTest(resource_printer_test_base.Base):

  def SetUp(self):
    self._printer = resource_printer.Printer('table')

  def testEmptyDefault(self):
    self._printer.Finish()
    self.AssertOutputEquals('')

  def testSingleResourceCase(self):
    self._printer.AddHeading(['name', 'zone', 'guestCpus', 'memoryMb'])
    self._printer.AddRecord(['f1-micro', 'zone-1', 1, 614])
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        name      zone    guestCpus  memoryMb
        f1-micro  zone-1  1          614
        """))

  def testMultiResourceCase(self):
    self._printer.AddHeading(['name', 'zone', 'guestCpus', 'memoryMb'])
    self._printer.AddRecord(['f1-micro', 'zone-1', 1, 614])
    self._printer.AddRecord(['n1-standard-1', 'zone-1', 1, 3840])
    self._printer.AddRecord(['n1-highmem-2', 'zone-2', 2, 13312])
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        name           zone    guestCpus  memoryMb
        f1-micro       zone-1  1          614
        n1-standard-1  zone-1  1          3840
        n1-highmem-2   zone-2  2          13312
        """))


class TablePrinterNoProjectionTest(resource_printer_test_base.Base):

  def SetUp(self):
    self._printer = table_printer.TablePrinter(name='table')

  def testEmptyDefault(self):
    self._printer.Finish()
    self.AssertOutputEquals('')

  def testSingleResourceCase(self):
    self._printer.AddHeading(['name', 'zone', 'guestCpus', 'memoryMb'])
    self._printer.AddRecord(['f1-micro', 'zone-1', 1, 614])
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        name      zone    guestCpus  memoryMb
        f1-micro  zone-1  1          614
        """))

  def testMultiResourceCase(self):
    self._printer.AddHeading(['name', 'zone', 'guestCpus', 'memoryMb'])
    self._printer.AddRecord(['f1-micro', 'zone-1', 1, 614])
    self._printer.AddRecord(['n1-standard-1', 'zone-1', 1, 3840])
    self._printer.AddRecord(['n1-highmem-2', 'zone-2', 2, 13312])
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        name           zone    guestCpus  memoryMb
        f1-micro       zone-1  1          614
        n1-standard-1  zone-1  1          3840
        n1-highmem-2   zone-2  2          13312
        """))


class TablePrinterFormatZeroIndexTest(resource_printer_test_base.Base):

  def SetUp(self):
    self._printer = resource_printer.Printer(
        'table(name, kind, networkInterfaces[0].networkIP)')

  def testMultipleStreamedResourceCase(self):
    for resource in self.CreateResourceList(4):
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME                KIND              NETWORK_IP
        my-instance-a-0     compute#instance  10.240.150.0
        my-instance-az-1    compute#instance  10.240.150.1
        my-instance-azz-2   compute#instance  10.240.150.2
        my-instance-azzz-3  compute#instance  10.240.150.3
        """))


class TablePrinterFormatAliasTest(resource_printer_test_base.Base):

  def testEmptyKeyDefaultLabel(self):
    printer = resource_printer.Printer("""\
        table(firstof(name), firstof(kind):label=K)
        """)
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME                K
        my-instance-a-0     compute#instance
        my-instance-az-1    compute#instance
        my-instance-azz-2   compute#instance
        my-instance-azzz-3  compute#instance
        """))

  def testEmptyKeyAlias(self):
    printer = resource_printer.Printer("""\
        table(firstof(name), firstof(kind):label=K)
        table(NAME, K.split('#').list():label=kind)
        """)
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME                kind
        my-instance-a-0     compute,instance
        my-instance-az-1    compute,instance
        my-instance-azz-2   compute,instance
        my-instance-azzz-3  compute,instance
        """))


class TablePrinterFormatHeadingTest(resource_printer_test_base.Base):

  def testNoHeading(self):
    printer = resource_printer.Printer(
        'table[no-heading](name:label=MONIKER:sort=2, kind:sort=1)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        my-instance-a-0     compute#instance
        my-instance-az-1    compute#instance
        my-instance-azz-2   compute#instance
        my-instance-azzz-3  compute#instance
        """))

  def testEmptyHeading(self):
    printer = resource_printer.Printer(
        'table(name:label="":sort=2, kind:sort=1)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
                            KIND
        my-instance-a-0     compute#instance
        my-instance-az-1    compute#instance
        my-instance-azz-2   compute#instance
        my-instance-azzz-3  compute#instance
        """))

  def testEmptyOptionalHeading(self):
    printer = resource_printer.Printer(
        'table(name:sort=2, unknown:optional, kind:sort=1)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME                KIND
        my-instance-a-0     compute#instance
        my-instance-az-1    compute#instance
        my-instance-azz-2   compute#instance
        my-instance-azzz-3  compute#instance
        """))

  def testEmptyOptionalNoHeading(self):
    printer = resource_printer.Printer(
        'table[no-heading](name:sort=2, unknown:optional, kind:sort=1)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        my-instance-a-0     compute#instance
        my-instance-az-1    compute#instance
        my-instance-azz-2   compute#instance
        my-instance-azzz-3  compute#instance
        """))

  def testMultipleStreamedResourceCase(self):
    printer = resource_printer.Printer(
        'table(name:label=MONIKER:sort=2, kind:sort=1, '
        'networkInterfaces[0].networkIP:label=IP)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        MONIKER             KIND              IP
        my-instance-a-0     compute#instance  10.240.150.0
        my-instance-az-1    compute#instance  10.240.150.1
        my-instance-azz-2   compute#instance  10.240.150.2
        my-instance-azzz-3  compute#instance  10.240.150.3
        """))


class TableFormatTest(resource_printer_test_base.Base):

  def testMultipleStreamedResourceCase(self):
    printer = resource_printer.Printer('table(name, kind)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME                KIND
        my-instance-a-0     compute#instance
        my-instance-az-1    compute#instance
        my-instance-azz-2   compute#instance
        my-instance-azzz-3  compute#instance
        """))

  def testFixedWidthNarrow(self):
    printer = resource_printer.Printer('table(name:width=16, kind)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME                KIND
        my-instance-a-0     compute#instance
        my-instance-az-1    compute#instance
        my-instance-azz-2   compute#instance
        my-instance-azzz-3  compute#instance
        """))

  def testFixedWidthWide(self):
    printer = resource_printer.Printer('table(name:width=32, kind)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME                              KIND
        my-instance-a-0                   compute#instance
        my-instance-az-1                  compute#instance
        my-instance-azz-2                 compute#instance
        my-instance-azzz-3                compute#instance
        """))

  def testFixedWidthAlignLastCenter(self):
    printer = resource_printer.Printer(
        'table(abc:label=LEFT:align=left:width=8,'
        '      xyz:label=RIGHT:align=center:width=9)')
    resources = [
        {'abc': 'A', 'xyz': 'Z'},
        {'abc': 'AB', 'xyz': 'YZ'},
        {'abc': 'ABC', 'xyz': 'XYZ'},
    ]
    for resource in resources:
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        LEFT        RIGHT
        A             Z
        AB            YZ
        ABC          XYZ
        """))

  def testFixedWidthAlignLastRight(self):
    printer = resource_printer.Printer(
        'table(abc:label=LEFT:align=left:width=8,'
        '      xyz:label=RIGHT:align=right:width=8)')
    resources = [
        {'abc': 'A', 'xyz': 'Z'},
        {'abc': 'AB', 'xyz': 'YZ'},
        {'abc': 'ABC', 'xyz': 'XYZ'},
    ]
    for resource in resources:
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        LEFT         RIGHT
        A                Z
        AB              YZ
        ABC            XYZ
        """))


class TablePrinterWrapTest(resource_printer_test_base.Base):

  def SetUpPrinter(self, fmt, columns=80, encoding=None):
    if encoding:
      self.SetEncoding(encoding)
    self._printer = resource_printer.Printer(fmt)
    self.StartObjectPatch(self._printer._console_attr, 'GetTermSize',
                          return_value=(columns, 100))

  def testWrap(self):
    self.SetUpPrinter('table(name, description:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': (
             'Lorem ipsum dolor sit amet, consectetur '
             'adipiscing elit. Morbi sit amet elit nulla.')},  # 83 chars
        {'name': 'my-instance-az-1',
         'description': (
             'Sed at cursus risus. Praesent facilisis '
             'at ligula at mattis. Vestibulum et quam et ipsum .')}  # 90 chars
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME              DESCRIPTION
        my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi
                          sit amet elit nulla.
        my-instance-az-1  Sed at cursus risus. Praesent facilisis at ligula at mattis.
                          Vestibulum et quam et ipsum .
        """))

  def testWrapBox(self):
    self.SetUpPrinter('table[box, ascii](name, description:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.')},
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +------------------+-----------------------------------------------------------+
        |       NAME       |                        DESCRIPTION                        |
        +------------------+-----------------------------------------------------------+
        | my-instance-a-0  | Lorem ipsum dolor sit amet, consectetur adipiscing elit.  |
        |                  | Morbi sit amet elit nulla.                                |
        | my-instance-az-1 | Sed at cursus risus. Praesent facilisis at ligula at      |
        |                  | mattis. Vestibulum et quam et ipsum .                     |
        +------------------+-----------------------------------------------------------+
        """))

  def testWrapBoxWithMargin(self):
    self.SetUpPrinter('table[box, ascii, margin=8](name, description:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.')},
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +------------------+---------------------------------------------------+
        |       NAME       |                    DESCRIPTION                    |
        +------------------+---------------------------------------------------+
        | my-instance-a-0  | Lorem ipsum dolor sit amet, consectetur           |
        |                  | adipiscing elit. Morbi sit amet elit nulla.       |
        | my-instance-az-1 | Sed at cursus risus. Praesent facilisis at ligula |
        |                  | at mattis. Vestibulum et quam et ipsum .          |
        +------------------+---------------------------------------------------+
        """))

  def testWrapBoxWithWidth(self):
    self.SetUpPrinter('table[box, ascii, width=60](name, description:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.')},
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +------------------+---------------------------------------+
        |       NAME       |              DESCRIPTION              |
        +------------------+---------------------------------------+
        | my-instance-a-0  | Lorem ipsum dolor sit amet,           |
        |                  | consectetur adipiscing elit. Morbi    |
        |                  | sit amet elit nulla.                  |
        | my-instance-az-1 | Sed at cursus risus. Praesent         |
        |                  | facilisis at ligula at mattis.        |
        |                  | Vestibulum et quam et ipsum .         |
        +------------------+---------------------------------------+
        """))

  def testWrapBoxWithWidtAndMargin(self):
    self.SetUpPrinter(
        'table[box, ascii, width=70, margin=10](name, description:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.')},
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +------------------+---------------------------------------+
        |       NAME       |              DESCRIPTION              |
        +------------------+---------------------------------------+
        | my-instance-a-0  | Lorem ipsum dolor sit amet,           |
        |                  | consectetur adipiscing elit. Morbi    |
        |                  | sit amet elit nulla.                  |
        | my-instance-az-1 | Sed at cursus risus. Praesent         |
        |                  | facilisis at ligula at mattis.        |
        |                  | Vestibulum et quam et ipsum .         |
        +------------------+---------------------------------------+
        """))

  def testWrapUnicodeData(self):
    self.SetUpPrinter('table(name, description:wrap)', encoding='utf8')
    for resource in [
        {'name': 'my-instance-a-0',
         # string length is 82 but display width 62, should not need wrapping.
         'description': (
             'Lorem ipsum dolor sit amet, consectetur '
             'adipiscing elit. Morbi{}'.format(
                 (_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20))},
        {'name': 'my-instance-az-1',
         # string length is 60 but display width is 70, should be wrapped.
         'description': (
             'Sed at cursus risus. Praesent facilisis at ligula '
             '車車車車車車車車車車')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME              DESCRIPTION
        my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi{}
        my-instance-az-1  Sed at cursus risus. Praesent facilisis at ligula
                          車車車車車車車車車車
        """.format((_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20)))

  def testWrapBoxUnicodeData(self):
    self.SetUpPrinter('table[box](name, description:wrap)', encoding='utf8')
    for resource in [
        {'name': 'my-instance-a-0',
         # display width is 57, length is 77, should not need wrapping.
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. {}'.format(
                             (_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20))},
        {'name': 'my-instance-az-1',
         # display width is 60, length is 50, should be wrapped (col width = 57)
         'description': ('Sed at cursus risus. Praesent facilisis '
                         '車車車車車車車車車車')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌──────────────────┬───────────────────────────────────────────────────────────┐
        │       NAME       │                        DESCRIPTION                        │
        ├──────────────────┼───────────────────────────────────────────────────────────┤
        │ my-instance-a-0  │ Lorem ipsum dolor sit amet, consectetur adipiscing elit. {} │
        │ my-instance-az-1 │ Sed at cursus risus. Praesent facilisis                   │
        │                  │ 車車車車車車車車車車                                      │
        └──────────────────┴───────────────────────────────────────────────────────────┘
        """.format((_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20)))

  def _RenderAsMarkdown(self, text):
    orig = io.StringIO(text)
    rendered_text = io.StringIO()
    render_document.RenderDocument('text',
                                   orig,
                                   out=rendered_text,
                                   width=len(text) + 4)
    return rendered_text.getvalue().splitlines()[0].lstrip()

  def testWrapWithCtrlSeqUtf(self):
    self.SetUpPrinter('table(name, description:wrap)', encoding='utf8')
    # First sentence will be 68 chars but display width is 62 without
    # "control sequences". Wrapping should start after first sentence because
    # max width of this column is 62.
    desc = ('Lorem ipsum dolor sit amet, consectetur *adipiscing* elit Morbi. '
            'Sed')
    for resource in [{'name': 'my-instance-a-0',
                      'description': self._RenderAsMarkdown(desc)}]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME             DESCRIPTION
        my-instance-a-0  Lorem ipsum dolor sit amet, consectetur {}adipiscing{} elit Morbi.
                         Sed
        """.format(self._printer._console_attr.GetFontCode(bold=True),
                   self._printer._console_attr.GetFontCode(bold=False))))

  def testWrapWithCtrlSeqBox(self):
    self.SetUpPrinter('table[box](name, description:wrap)', encoding='utf8')
    # First sentence will be 63 chars but display width is 57 without
    # "control sequences". Wrapping should begin after first sentence because
    # max width of this column is 57.
    desc = ('Lorem ipsum dolor sit amet, consectetur *adipiscing* elit... '
            'Morbi')
    for resource in [{'name': 'my-instance-a-0',
                      'description': self._RenderAsMarkdown(desc)}]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌─────────────────┬────────────────────────────────────────────────────────────┐
        │       NAME      │                        DESCRIPTION                         │
        ├─────────────────┼────────────────────────────────────────────────────────────┤
        │ my-instance-a-0 │ Lorem ipsum dolor sit amet, consectetur {}adipiscing{} elit... │
        │                 │ Morbi                                                      │
        └─────────────────┴────────────────────────────────────────────────────────────┘
        """.format(self._printer._console_attr.GetFontCode(bold=True),
                   self._printer._console_attr.GetFontCode(bold=False))))

  def testWrapWithCtrlSeqEnjambed(self):
    self.SetUpPrinter('table(name:wrap, description:wrap)', encoding='utf8')
    # The max width of this column is 39, so the bold text will wrap around.
    desc = ('Lorem ipsum dolor sit amet, *consectetur adipiscing elit*')
    for resource in [{'name': 'my-loooooooooooooooooong-instance-name',
                      'description': self._RenderAsMarkdown(desc)}]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputContains(textwrap.dedent("""\
        NAME                                     DESCRIPTION
        my-loooooooooooooooooong-instance-name   Lorem ipsum dolor sit amet, {0}consectetur{1}
                                                 {0}adipiscing elit{1}
        """.format(self._printer._console_attr.GetFontCode(bold=True),
                   self._printer._console_attr.GetFontCode(bold=False))))

  def testWrapWithCtrlSeqEnjambedBox(self):
    self.SetUpPrinter('table[box](name:wrap, description:wrap)',
                      encoding='utf8')
    # The max width of this column is 36, so the bold text will wrap around.
    desc = ('Lorem ipsum dolor sit *amet, consectetur adipiscing*')
    for resource in [{'name': self._RenderAsMarkdown(desc),
                      'description': self._RenderAsMarkdown(desc)}]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌──────────────────────────────────────┬──────────────────────────────────────┐
        │                 NAME                 │             DESCRIPTION              │
        ├──────────────────────────────────────┼──────────────────────────────────────┤
        │ Lorem ipsum dolor sit {0}amet,{1}          │ Lorem ipsum dolor sit {0}amet,{1}          │
        │ {0}consectetur adipiscing{1}               │ {0}consectetur adipiscing{1}               │
        └──────────────────────────────────────┴──────────────────────────────────────┘
        """.format(self._printer._console_attr.GetFontCode(bold=True),
                   self._printer._console_attr.GetFontCode(bold=False))))

  def testNewlinesDontContributeToWidth(self):
    self.SetUpPrinter('table(name:wrap, description:wrap)', encoding='utf8')
    # The max width of this column is 39, so the bold text will wrap around.
    desc = ('Lorem ipsum dolor sit amet, *consectetur adipiscing elit*')
    for resource in [{'name': 'my-instance-a-0\ntwo-lines',
                      'description': self._RenderAsMarkdown(desc)}]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputContains(textwrap.dedent("""\
        NAME             DESCRIPTION
        my-instance-a-0  Lorem ipsum dolor sit amet, {0}consectetur adipiscing elit{1}
        two-lines
        """.format(self._printer._console_attr.GetFontCode(bold=True),
                   self._printer._console_attr.GetFontCode())))

  def testWrapUtf8Data(self):
    self.SetUpPrinter('table(name, description:wrap)', encoding='utf8')
    for resource in [
        {'name': 'my-instance-a-0',
         # string length is 82 but display width 62, should not need wrapping.
         'description': (
             'Lorem ipsum dolor sit amet, consectetur '
             'adipiscing elit. Morbi{}'.format(
                 (_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20))},
        {'name': 'my-instance-az-1',
         # string length is 60 but display width is 70, should be wrapped.
         'description': (
             'Sed at cursus risus. Praesent facilisis at ligula '
             '車車車車車車車車車車').encode('utf-8')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME              DESCRIPTION
        my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi{}
        my-instance-az-1  Sed at cursus risus. Praesent facilisis at ligula
                          車車車車車車車車車車
        """.format((_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20)))

  def testWrapBoxUtf8Data(self):
    self.SetUpPrinter('table[box](name, description:wrap)', encoding='utf8')
    for resource in [
        {'name': 'my-instance-a-0',
         # display width is 57, length is 77, should not need wrapping.
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. {}'.format(
                             (_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20))},
        {'name': 'my-instance-az-1',
         # display width is 60, length is 50, should be wrapped (col width = 57)
         'description': ('Sed at cursus risus. Praesent facilisis '
                         '車車車車車車車車車車').encode('utf-8')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌──────────────────┬───────────────────────────────────────────────────────────┐
        │       NAME       │                        DESCRIPTION                        │
        ├──────────────────┼───────────────────────────────────────────────────────────┤
        │ my-instance-a-0  │ Lorem ipsum dolor sit amet, consectetur adipiscing elit. {} │
        │ my-instance-az-1 │ Sed at cursus risus. Praesent facilisis                   │
        │                  │ 車車車車車車車車車車                                      │
        └──────────────────┴───────────────────────────────────────────────────────────┘
        """.format((_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20)))

  def testWrapUnicodeName(self):
    self.SetUpPrinter('table(name, description:wrap)', encoding='utf8')
    for resource in [
        {'name': 'Ṁöë{}'.format(
            (_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20),  # 20 0-width chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur '
             'adipiscing elit. Morbi sit amet elit nulla.')},  # 83 chars
        {'name': 'Lαrry',
         'description': (
             'Sed at cursus risus. Praesent facilisis '
             'at ligula at mattis. Vestibulum et quam et ipsum .')}  # 90 chars
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    # Description column should be 73 characters wide.
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME   DESCRIPTION
        Ṁöë{}    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi sit amet
               elit nulla.
        Lαrry  Sed at cursus risus. Praesent facilisis at ligula at mattis. Vestibulum
               et quam et ipsum .
        """.format((_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20)))

  def testWrapBoxUnicodeName(self):
    self.SetUpPrinter('table[box](name, description:wrap)', encoding='utf8')
    for resource in [
        {'name': 'Ṁöë{}'.format((_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20),
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.')},
        {'name': 'Lαrry',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    # Description column should be 73 characters wide.
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌───────┬──────────────────────────────────────────────────────────────────────┐
        │  NAME │                             DESCRIPTION                              │
        ├───────┼──────────────────────────────────────────────────────────────────────┤
        │ Ṁöë{}   │ Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi sit   │
        │       │ amet elit nulla.                                                     │
        │ Lαrry │ Sed at cursus risus. Praesent facilisis at ligula at mattis.         │
        │       │ Vestibulum et quam et ipsum .                                        │
        └───────┴──────────────────────────────────────────────────────────────────────┘
        """.format((_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20)))

  def testWrapAllBoxUnicodeName(self):
    self.SetUpPrinter('table[all-box](name, description:wrap)',
                      encoding='utf8')
    for resource in [
        {'name': 'Ṁöë{}'.format((_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20),
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.')},
        {'name': 'Lαrry',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    # Description column should be 73 characters wide.
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌───────┬──────────────────────────────────────────────────────────────────────┐
        │  NAME │                             DESCRIPTION                              │
        ├───────┼──────────────────────────────────────────────────────────────────────┤
        │ Ṁöë{}   │ Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi sit   │
        │       │ amet elit nulla.                                                     │
        ├───────┼──────────────────────────────────────────────────────────────────────┤
        │ Lαrry │ Sed at cursus risus. Praesent facilisis at ligula at mattis.         │
        │       │ Vestibulum et quam et ipsum .                                        │
        └───────┴──────────────────────────────────────────────────────────────────────┘
        """.format((_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 20)))

  def testWrapDiffTermSize(self):
    self.SetUpPrinter('table(name, description:wrap)', columns=88)
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.')},
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME              DESCRIPTION
        my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi sit
                          amet elit nulla.
        my-instance-az-1  Sed at cursus risus. Praesent facilisis at ligula at mattis.
                          Vestibulum et quam et ipsum .
        """))

  def testWrapBoxDiffTermSize(self):
    self.SetUpPrinter('table[box, ascii](name, description:wrap)', columns=88)
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.')},
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +------------------+-------------------------------------------------------------------+
        |       NAME       |                            DESCRIPTION                            |
        +------------------+-------------------------------------------------------------------+
        | my-instance-a-0  | Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi    |
        |                  | sit amet elit nulla.                                              |
        | my-instance-az-1 | Sed at cursus risus. Praesent facilisis at ligula at mattis.      |
        |                  | Vestibulum et quam et ipsum .                                     |
        +------------------+-------------------------------------------------------------------+
        """))

  def testWrapWithNewLines(self):
    self.SetUpPrinter('table(name, description:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': (
             'Lorem ipsum dolor sit amet,\nconsectetur '
             'adipiscing elit.\nMorbi sit amet elit nulla.')},  # 83 chars
        {'name': 'my-instance-az-1',
         'description': (
             'Sed at cursus risus.\nPraesent facilisis '
             'at ligula at mattis.\nVestibulum et quam et ipsum .')}  # 90 chars
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME              DESCRIPTION
        my-instance-a-0   Lorem ipsum dolor sit amet,
                          consectetur adipiscing elit.
                          Morbi sit amet elit nulla.
        my-instance-az-1  Sed at cursus risus.
                          Praesent facilisis at ligula at mattis.
                          Vestibulum et quam et ipsum .
        """))

  def testWrapBoxWithNewLines(self):
    self.SetUpPrinter('table[box, ascii](name, description:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit.\nMorbi sit amet elit nulla.')},
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis.\nVestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +------------------+-----------------------------------------------------------+
        |       NAME       |                        DESCRIPTION                        |
        +------------------+-----------------------------------------------------------+
        | my-instance-a-0  | Lorem ipsum dolor sit amet, consectetur adipiscing elit.  |
        |                  | Morbi sit amet elit nulla.                                |
        | my-instance-az-1 | Sed at cursus risus. Praesent facilisis at ligula at      |
        |                  | mattis.                                                   |
        |                  | Vestibulum et quam et ipsum .                             |
        +------------------+-----------------------------------------------------------+
        """))

  def testWrapAllBoxWithNewLines(self):
    self.SetUpPrinter('table[all-box, ascii](name, description:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit.\nMorbi sit amet elit nulla.')},
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis.\nVestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +------------------+-----------------------------------------------------------+
        |       NAME       |                        DESCRIPTION                        |
        +------------------+-----------------------------------------------------------+
        | my-instance-a-0  | Lorem ipsum dolor sit amet, consectetur adipiscing elit.  |
        |                  | Morbi sit amet elit nulla.                                |
        +------------------+-----------------------------------------------------------+
        | my-instance-az-1 | Sed at cursus risus. Praesent facilisis at ligula at      |
        |                  | mattis.                                                   |
        |                  | Vestibulum et quam et ipsum .                             |
        +------------------+-----------------------------------------------------------+
        """))

  def testWrapLongTitle(self):
    long_title = (
        'Pellentesque faucibus luctus tincidunt. Class aptent taciti '
        'sociosqu ad litora torquent per conubia nostra.')  # 107 chars
    self.SetUpPrinter(
        'table[title="{0}"](name, description:wrap)'.format(long_title))
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.')},
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        Pellentesque faucibus luctus tincidunt. Class aptent taciti sociosqu ad litora torquent per conubia nostra.
        NAME              DESCRIPTION
        my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi
                          sit amet elit nulla.
        my-instance-az-1  Sed at cursus risus. Praesent facilisis at ligula at mattis.
                          Vestibulum et quam et ipsum .
        """))

  def testWrapBoxLongTitle(self):
    long_title = (
        'Pellentesque faucibus luctus tincidunt. Class aptent taciti '
        'sociosqu ad litora torquent per conubia nostra.')  # 107 chars
    self.SetUpPrinter(
        'table[box, ascii, title="{0}"](name, description:wrap)'.format(
            long_title))
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.')},
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +------------------------------------------------------------------------------+
        |Pellentesque faucibus luctus tincidunt. Class aptent taciti sociosqu ad litora torquent per conubia nostra.|
        +------------------+-----------------------------------------------------------+
        |       NAME       |                        DESCRIPTION                        |
        +------------------+-----------------------------------------------------------+
        | my-instance-a-0  | Lorem ipsum dolor sit amet, consectetur adipiscing elit.  |
        |                  | Morbi sit amet elit nulla.                                |
        | my-instance-az-1 | Sed at cursus risus. Praesent facilisis at ligula at      |
        |                  | mattis. Vestibulum et quam et ipsum .                     |
        +------------------+-----------------------------------------------------------+
        """))

  def testWrapUnicodeLongTitle(self):
    long_title = (
        'Pellentesque faucibus luctus tincidunt. Class aptent taciti '
        '{}'.format('車' * 15))  # display width 90, string length 75
    self.SetUpPrinter(
        'table[title="{0}"](name, description:wrap)'.format(long_title),
        encoding='utf8')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.')},
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        Pellentesque faucibus luctus tincidunt. Class aptent taciti {}
        NAME              DESCRIPTION
        my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi
                          sit amet elit nulla.
        my-instance-az-1  Sed at cursus risus. Praesent facilisis at ligula at mattis.
                          Vestibulum et quam et ipsum .
        """.format('車' * 15)))

  def testWrapBoxUnicodeLongTitle(self):
    long_title = (
        'Pellentesque faucibus luctus tincidunt. Class aptent taciti '
        '車車車車車車車車車車車車車車車')  # display width 90, string length 75
    self.SetUpPrinter(
        'table[box, title="{}"](name, description:wrap)'.format(long_title),
        encoding='utf8')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.')},
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌──────────────────────────────────────────────────────────────────────────────┐
        │Pellentesque faucibus luctus tincidunt. Class aptent taciti {}│
        ├──────────────────┬───────────────────────────────────────────────────────────┤
        │       NAME       │                        DESCRIPTION                        │
        ├──────────────────┼───────────────────────────────────────────────────────────┤
        │ my-instance-a-0  │ Lorem ipsum dolor sit amet, consectetur adipiscing elit.  │
        │                  │ Morbi sit amet elit nulla.                                │
        │ my-instance-az-1 │ Sed at cursus risus. Praesent facilisis at ligula at      │
        │                  │ mattis. Vestibulum et quam et ipsum .                     │
        └──────────────────┴───────────────────────────────────────────────────────────┘
        """.format('車' * 15)))

  def testWrapTwoWrappedColumns(self):
    self.SetUpPrinter(
        'table(name, description:wrap, continued:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.'),
         'continued': ('Sed at cursus risus.\nPraesent facilisis '
                       'at ligula at mattis.\nVestibulum et quam et ipsum .')},
        {'name': 'my-instance-az-1',
         'description': 'short description',
         'continued': 'more short description'}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME              DESCRIPTION                     CONTINUED
        my-instance-a-0   Lorem ipsum dolor sit amet,     Sed at cursus risus.
                          consectetur adipiscing elit.    Praesent facilisis at ligula
                          Morbi sit amet elit nulla.      at mattis.
                                                          Vestibulum et quam et ipsum .
        my-instance-az-1  short description               more short description
        """))

  def testWrapBoxTwoWrappedColumns(self):
    self.SetUpPrinter(
        'table[box](name, description:wrap, continued:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.'),
         'continued': ('Sed at cursus risus. Praesent facilisis '
                       'at ligula at mattis.\nVestibulum et quam et ipsum .')},
        {'name': 'my-instance-az-1',
         'description': 'short description',
         'continued': 'more short description'}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +------------------+-----------------------------+-----------------------------+
        |       NAME       |         DESCRIPTION         |          CONTINUED          |
        +------------------+-----------------------------+-----------------------------+
        | my-instance-a-0  | Lorem ipsum dolor sit amet, | Sed at cursus risus.        |
        |                  | consectetur adipiscing      | Praesent facilisis at       |
        |                  | elit. Morbi sit amet elit   | ligula at mattis.           |
        |                  | nulla.                      | Vestibulum et quam et ipsum |
        |                  |                             | .                           |
        | my-instance-az-1 | short description           | more short description      |
        +------------------+-----------------------------+-----------------------------+
        """))

  def testWrapShortRecords(self):
    self.SetUpPrinter(
        'table(name, description:wrap, continued:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': 'short description',
         'continued': 'short continuation'},
        {'name': 'my-instance-az-1',
         'description': 'even shorter',
         'continued': 'shortest'}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME              DESCRIPTION        CONTINUED
        my-instance-a-0   short description  short continuation
        my-instance-az-1  even shorter       shortest
        """))

  def testWrapBoxShortRecords(self):
    self.SetUpPrinter(
        'table[box](name, description:wrap, continued:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': 'short description',
         'continued': 'short continuation'},
        {'name': 'my-instance-az-1',
         'description': 'even shorter',
         'continued': 'shortest'}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +------------------+-------------------+--------------------+
        |       NAME       |    DESCRIPTION    |     CONTINUED      |
        +------------------+-------------------+--------------------+
        | my-instance-a-0  | short description | short continuation |
        | my-instance-az-1 | even shorter      | shortest           |
        +------------------+-------------------+--------------------+
        """))

  def testWrapAllBoxShortRecords(self):
    self.SetUpPrinter(
        'table[all-box](name, description:wrap, continued:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': 'short description',
         'continued': 'short continuation'},
        {'name': 'my-instance-az-1',
         'description': 'even shorter',
         'continued': 'shortest'}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +------------------+-------------------+--------------------+
        |       NAME       |    DESCRIPTION    |     CONTINUED      |
        +------------------+-------------------+--------------------+
        | my-instance-a-0  | short description | short continuation |
        +------------------+-------------------+--------------------+
        | my-instance-az-1 | even shorter      | shortest           |
        +------------------+-------------------+--------------------+
        """))

  def testWrapWithSubformat(self):
    self.SetUpPrinter(
        'table(name, description:wrap, metadata:format=json)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.'),
         'metadata': {'field_a': 'text', 'field_b': 'other text'}
        },
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .'),
         'metadata': {'field_a': 'stuff', 'field_b': 'other stuff'}
        }
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME              DESCRIPTION
        my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi
                          sit amet elit nulla.
            {
              "field_a": "text",
              "field_b": "other text"
            }
        my-instance-az-1  Sed at cursus risus. Praesent facilisis at ligula at mattis.
                          Vestibulum et quam et ipsum .
            {
              "field_a": "stuff",
              "field_b": "other stuff"
            }
        """))

  def testWrapBoxWithSubformat(self):
    self.SetUpPrinter(
        'table[box](name, description:wrap, metadata:format=json)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': ('Lorem ipsum dolor sit amet, consectetur '
                         'adipiscing elit. Morbi sit amet elit nulla.'),
         'metadata': {'field_a': 'text', 'field_b': 'other text'}
        },
        {'name': 'my-instance-az-1',
         'description': ('Sed at cursus risus. Praesent facilisis '
                         'at ligula at mattis. Vestibulum et quam et ipsum .'),
         'metadata': {'field_a': 'stuff', 'field_b': 'other stuff'}
        }
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +------------------+-----------------------------------------------------------+
        |       NAME       |                        DESCRIPTION                        |
        +------------------+-----------------------------------------------------------+
        | my-instance-a-0  | Lorem ipsum dolor sit amet, consectetur adipiscing elit.  |
        |                  | Morbi sit amet elit nulla.                                |
        +------------------+-----------------------------------------------------------+
            {
              "field_a": "text",
              "field_b": "other text"
            }
        +------------------+-----------------------------------------------------------+
        | my-instance-az-1 | Sed at cursus risus. Praesent facilisis at ligula at      |
        |                  | mattis. Vestibulum et quam et ipsum .                     |
        +------------------+-----------------------------------------------------------+
            {
              "field_a": "stuff",
              "field_b": "other stuff"
            }
        """))

  def testWrapWithColor(self):
    self.SetUpPrinter(
        'table(name, description.color(red="Lorem"|"Sed"):wrap)',
        encoding='utf8')
    # Mock out colorizing
    def FakeColorize(string, color, _, **unused_kwargs):
      return '<{color}>{string}</{color}>'.format(color=color, string=string)
    self.StartObjectPatch(self._printer._console_attr, 'Colorize',
                          side_effect=FakeColorize)

    for resource in [
        {'name': 'my-instance-a-0',
         'description': (
             'Lorem ipsum dolor sit amet, consectetur '
             'adipiscing elit. Morbi sit amet elit nulla.')},  # 83 chars
        {'name': 'my-instance-az-1',
         'description': (
             'Sed at cursus risus. Praesent facilisis '
             'at ligula at mattis. Vestibulum et quam et ipsum .')}  # 90 chars
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME              DESCRIPTION
        my-instance-a-0   <red>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi</red>
                          <red> sit amet elit nulla.</red>
        my-instance-az-1  <red>Sed at cursus risus. Praesent facilisis at ligula at mattis. </red>
                          <red>Vestibulum et quam et ipsum .</red>
        """))

  def testWrapBoxWithColor(self):
    self.SetUpPrinter(
        'table[box](name, description.color(red="Lorem"|"Sed"):wrap)',
        encoding='utf8')
    # Mock colorizing, with hackery to replace 'justify' param
    def FakeColorize(string, color, _, **unused_kwargs):
      return '<{color}>{string}{spaces}</{color}>'.format(
          color=color, string=string, spaces=' ' * (57 - len(string)))
    self.StartObjectPatch(self._printer._console_attr, 'Colorize',
                          side_effect=FakeColorize)
    for resource in [
        {'name': 'my-instance-a-0',
         'description': (
             'Lorem ipsum dolor sit amet, consectetur '
             'adipiscing elit. Morbi sit amet elit nulla.')},  # 83 chars
        {'name': 'my-instance-az-1',
         'description': (
             'Sed at cursus risus. Praesent facilisis '
             'at ligula at mattis. Vestibulum et quam et ipsum .')}  # 90 chars
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌──────────────────┬───────────────────────────────────────────────────────────┐
        │       NAME       │                        DESCRIPTION                        │
        ├──────────────────┼───────────────────────────────────────────────────────────┤
        │ my-instance-a-0  │ <red>Lorem ipsum dolor sit amet, consectetur adipiscing elit. </red> │
        │                  │ <red>Morbi sit amet elit nulla.                               </red> │
        │ my-instance-az-1 │ <red>Sed at cursus risus. Praesent facilisis at ligula at     </red> │
        │                  │ <red>mattis. Vestibulum et quam et ipsum .                    </red> │
        └──────────────────┴───────────────────────────────────────────────────────────┘
        """))

  def testWrapLongWhitespace(self):
    self.SetUpPrinter('table(name, description:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': (
             'Lorem ipsum dolor sit amet, consectetur '
             'adipiscing elit.                        ')},
        {'name': 'my-instance-az-1',
         'description': (
             'Sed at cursus risus. Praesent facilisis '
             'at ligula at mattis. Vestibulum et quam et ipsum .')}  # 90 chars
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME              DESCRIPTION
        my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit.
        my-instance-az-1  Sed at cursus risus. Praesent facilisis at ligula at mattis.
                          Vestibulum et quam et ipsum .
        """))

  def testWrapLongWhitespaceWithColor(self):
    self.SetUpPrinter(
        'table(name, description.color(red="Lorem"):wrap)', encoding='utf8')
    # Mock out colorizing
    def FakeColorize(string, color, _, **unused_kwargs):
      return '<{color}>{string}</{color}>'.format(color=color, string=string)
    self.StartObjectPatch(self._printer._console_attr, 'Colorize',
                          side_effect=FakeColorize)

    for resource in [
        # 80 characters, colorized. Should result in wrapped whitespace,
        # all colorized
        {'name': 'my-instance-a-0',
         'description': (
             'Lorem ipsum dolor sit amet,             '
             '                                        ')},
        # 80 characters, no color. Should not require wrapping.
        {'name': 'my-instance-az-1',
         'description': (
             'Morem ipsum dolor sit amet,             '
             '                                        ')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME              DESCRIPTION
        my-instance-a-0   <red>Lorem ipsum dolor sit amet,                                   </red>
                          <red>                  </red>
        my-instance-az-1  Morem ipsum dolor sit amet,
        """))

# pylint: disable=line-too-long
  def testWrapDefaultMinimum(self):
    self.SetUpPrinter('table(name, description, extra:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',  # 15 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': (
             'The quick brown fox.')},  # 27 chars
        {'name': 'my-instance-az-1',  # 16 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': ('x')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    # The last column is wrapped and will be printed at a minimum width of 10.
    self.AssertOutputEquals("""\
NAME              DESCRIPTION                                               EXTRA
my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit.  The quick
                                                                            brown fox.
my-instance-az-1  Lorem ipsum dolor sit amet, consectetur adipiscing elit.  x
""")

  def testWrapDefaultMinimumTwoWrapped(self):
    self.SetUpPrinter('table(name, description, extra:wrap, more:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',  # 15 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': (
             'The quick brown fox.'),  # 27 chars
         'more': (
             'Jumps over the lazy dog.')},  # 24
        {'name': 'my-instance-az-1',  # 16 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': ('x'),
         'more': ('y')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    # Each column should print in a minimum of 10.
    self.AssertOutputEquals("""\
NAME              DESCRIPTION                                               EXTRA       MORE
my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit.  The quick   Jumps over
                                                                            brown fox.  the lazy
                                                                                        dog.
my-instance-az-1  Lorem ipsum dolor sit amet, consectetur adipiscing elit.  x           y
""")

  def testWrapDefaultMinimumBox(self):
    self.SetUpPrinter('table[box](name, description, extra:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',  # 15 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': (
             'The quick brown fox.')},  # 27 chars
        {'name': 'my-instance-az-1',  # 16 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': ('x')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals("""\
+------------------+----------------------------------------------------------+------------+
|       NAME       |                       DESCRIPTION                        |   EXTRA    |
+------------------+----------------------------------------------------------+------------+
| my-instance-a-0  | Lorem ipsum dolor sit amet, consectetur adipiscing elit. | The quick  |
|                  |                                                          | brown fox. |
| my-instance-az-1 | Lorem ipsum dolor sit amet, consectetur adipiscing elit. | x          |
+------------------+----------------------------------------------------------+------------+
""")

  def testWrapDefaultMinimumTwoWrappedBox(self):
    self.SetUpPrinter('table[box](name, description, extra:wrap, more:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',  # 15 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': (
             'The quick brown fox.'),  # 27 chars
         'more': (
             'Jumps over the lazy dog.')},  # 24
        {'name': 'my-instance-az-1',  # 16 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': ('x'),
         'more': ('y')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals("""\
+------------------+----------------------------------------------------------+------------+------------+
|       NAME       |                       DESCRIPTION                        |   EXTRA    |    MORE    |
+------------------+----------------------------------------------------------+------------+------------+
| my-instance-a-0  | Lorem ipsum dolor sit amet, consectetur adipiscing elit. | The quick  | Jumps over |
|                  |                                                          | brown fox. | the lazy   |
|                  |                                                          |            | dog.       |
| my-instance-az-1 | Lorem ipsum dolor sit amet, consectetur adipiscing elit. | x          | y          |
+------------------+----------------------------------------------------------+------------+------------+
""")

  def testWrapMinimumOverridesShorter(self):
    self.SetUpPrinter('table(name, description, extra:wrap=5)')
    for resource in [
        {'name': 'my-instance-a-0',  # 15 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': (
             'The quick brown fox.')},  # 27 chars
        {'name': 'my-instance-az-1',  # 16 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': ('x')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    # The minimum is shorter than the default but still more than the available
    # space.
    self.AssertOutputEquals("""\
NAME              DESCRIPTION                                               EXTRA
my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit.  The
                                                                            quick
                                                                            brown
                                                                            fox.
my-instance-az-1  Lorem ipsum dolor sit amet, consectetur adipiscing elit.  x
""")

  def testWrapMinimumOverridesZero(self):
    self.SetUpPrinter('table(name, description, a:wrap=1)')
    for resource in [
        {'name': 'my-instance-a-0',  # 15 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit. abc'),  # 60 chars
         'a': (
             'foo')},  # 3 chars
        {'name': 'my-instance-az-1',  # 16 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'a': ('x')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    # The default minimum is 0, but should be increased to 1.
    self.AssertOutputEquals("""\
NAME              DESCRIPTION                                                   A
my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit. abc  f
                                                                                o
                                                                                o
my-instance-az-1  Lorem ipsum dolor sit amet, consectetur adipiscing elit.      x
""")

  def testWrapMinimumOverridesLonger(self):
    self.SetUpPrinter('table(name, description, extra:wrap=15)')
    for resource in [
        {'name': 'my-instance-a-0',  # 15 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': (
             'The quick brown fox.')},  # 27 chars
        {'name': 'my-instance-az-1',  # 16 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': ('x')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    # The minimum is longer than the default.
    self.AssertOutputEquals("""\
NAME              DESCRIPTION                                               EXTRA
my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit.  The quick brown
                                                                            fox.
my-instance-az-1  Lorem ipsum dolor sit amet, consectetur adipiscing elit.  x
""")

  def testWrapMinimumOverridesTwoDifferentValues(self):
    self.SetUpPrinter('table(name, description, extra:wrap=15, more:wrap=5)')
    for resource in [
        {'name': 'my-instance-a-0',  # 15 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': (
             'The quick brown fox.'),  # 27 chars
         'more': 'Jumps over the lazy dog.'},  # 24 chars
        {'name': 'my-instance-az-1',  # 16 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': ('x')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    # Each column has a different minimum override.
    self.AssertOutputEquals("""\
NAME              DESCRIPTION                                               EXTRA            MORE
my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit.  The quick brown  Jumps
                                                                            fox.             over
                                                                                             the
                                                                                             lazy
                                                                                             dog.
my-instance-az-1  Lorem ipsum dolor sit amet, consectetur adipiscing elit.  x
""")

  def testWrapMinimumOverridesOneOverrideTwoWrapped(self):
    self.SetUpPrinter('table(name, description, extra:wrap=15, more:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',  # 15 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': (
             'The quick brown fox.'),  # 27 chars
         'more': 'Jumps over the lazy dog.'},  # 24 chars
        {'name': 'my-instance-az-1',  # 16 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': ('x')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    # EXTRA prints with a width of 15 (override), MORE with the default minimum.
    self.AssertOutputEquals("""\
NAME              DESCRIPTION                                               EXTRA            MORE
my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit.  The quick brown  Jumps over
                                                                            fox.             the lazy
                                                                                             dog.
my-instance-az-1  Lorem ipsum dolor sit amet, consectetur adipiscing elit.  x
""")

  def testWrapMinimumOverridesNoWrapNeeded(self):
    self.SetUpPrinter('table(name, a:wrap=15, description)')
    for resource in [
        {'name': 'my-instance-a-0',  # 15 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'a': ('foo')},
        {'name': 'my-instance-az-1',  # 16 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'a': ('x')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    # Column A prints as usual because it's shorter than the available space.
    self.AssertOutputEquals("""\
NAME              A    DESCRIPTION
my-instance-a-0   foo  Lorem ipsum dolor sit amet, consectetur adipiscing elit.
my-instance-az-1  x    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
""")

  def testWrapMinimumOverridesMoreThanNeeded(self):
    self.SetUpPrinter('table(name, extra:wrap=15, description)')
    for resource in [
        {'name': 'my-instance-a-0',  # 15 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': ('foobar')},
        {'name': 'my-instance-az-1',  # 16 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': ('x')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    # Column A prints with a width of 6 even though the override is 15, because
    # that's all the space it needs.
    self.AssertOutputEquals("""\
NAME              EXTRA   DESCRIPTION
my-instance-a-0   foobar  Lorem ipsum dolor sit amet, consectetur adipiscing elit.
my-instance-az-1  x       Lorem ipsum dolor sit amet, consectetur adipiscing elit.
""")

  def testWrapMinimumOverridesBox(self):
    self.SetUpPrinter('table[box](name, description, extra:wrap=15)')
    for resource in [
        {'name': 'my-instance-a-0',  # 15 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': (
             'The quick brown fox.')},  # 27 chars
        {'name': 'my-instance-az-1',  # 16 chars
         'description': (
             'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'),  # 56 chars
         'extra': ('x')}
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals("""\
+------------------+----------------------------------------------------------+-----------------+
|       NAME       |                       DESCRIPTION                        |      EXTRA      |
+------------------+----------------------------------------------------------+-----------------+
| my-instance-a-0  | Lorem ipsum dolor sit amet, consectetur adipiscing elit. | The quick brown |
|                  |                                                          | fox.            |
| my-instance-az-1 | Lorem ipsum dolor sit amet, consectetur adipiscing elit. | x               |
+------------------+----------------------------------------------------------+-----------------+
""")

# pylint: enable=line-too-long

  def testTablePrinterVariableWidthMultiLine(self):
    self.SetUpPrinter('table[box](head, data:wrap, tail)', encoding='utf8')
    for resource in self.multiline_width_resource:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌──────┬────────────────────────────────────────────────────────────────┬──────┐
        │ HEAD │                              DATA                              │ TAIL │
        ├──────┼────────────────────────────────────────────────────────────────┼──────┤
        │ zero │ :{0}:                                                             │ ZERO │
        │ one  │ :ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ │ ONE  │
        │      │ ÜÜÜ:                                                           │      │
        │ two  │ :車車車車車車車車車車車車車車車車車車車車車車車車車車車車車車  │ TWO  │
        │      │ 車車車車車車車車車車車車車車車車車車車車車車車車車車車車車車車 │      │
        │      │ 車車車:                                                        │      │
        └──────┴────────────────────────────────────────────────────────────────┴──────┘
    """.format((_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 64)))

  def testTablePrinterVariableWidthMultiLineAllBox(self):
    self.SetUpPrinter('table[all-box](head, data:wrap, tail)', encoding='utf8')
    for resource in self.multiline_width_resource:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌──────┬────────────────────────────────────────────────────────────────┬──────┐
        │ HEAD │                              DATA                              │ TAIL │
        ├──────┼────────────────────────────────────────────────────────────────┼──────┤
        │ zero │ :{0}:                                                             │ ZERO │
        ├──────┼────────────────────────────────────────────────────────────────┼──────┤
        │ one  │ :ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ │ ONE  │
        │      │ ÜÜÜ:                                                           │      │
        ├──────┼────────────────────────────────────────────────────────────────┼──────┤
        │ two  │ :車車車車車車車車車車車車車車車車車車車車車車車車車車車車車車  │ TWO  │
        │      │ 車車車車車車車車車車車車車車車車車車車車車車車車車車車車車車車 │      │
        │      │ 車車車:                                                        │      │
        └──────┴────────────────────────────────────────────────────────────────┴──────┘
    """.format((_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 64)))

  def testTablePrinterVariableWidthMultiLineNoBox(self):
    self.SetUpPrinter('table(head, data:wrap, tail)', encoding='utf8')
    for resource in self.multiline_width_resource:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        HEAD  DATA                                                                  TAIL
        zero  :{0}:                                                                    ZERO
        one   :ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ:    ONE
        two   :車車車車車車車車車車車車車車車車車車車車車車車車車車車車車車車車車   TWO
              車車車車車車車車車車車車車車車車車車車車車車車車車車車車車車車:
    """.format((_ZERO_WIDTH_SPACE + _SOFT_HYPHEN) * 64)))

  def testWrapWithPager(self):
    mock_more = self.StartObjectPatch(console_io, 'More')
    self.SetUpPrinter('table[pager](name, description:wrap)')
    for resource in [
        {'name': 'my-instance-a-0',
         'description': (
             'Lorem ipsum dolor sit amet, consectetur '
             'adipiscing elit. Morbi sit amet elit nulla.')},  # 83 chars
        {'name': 'my-instance-az-1',
         'description': (
             'Sed at cursus risus. Praesent facilisis '
             'at ligula at mattis. Vestibulum et quam et ipsum .')}  # 90 chars
    ]:
      self._printer.AddRecord(resource)
    self._printer.Finish()
    mock_more.assert_called_once_with(textwrap.dedent("""\
        NAME              DESCRIPTION
        my-instance-a-0   Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi
                          sit amet elit nulla.
        my-instance-az-1  Sed at cursus risus. Praesent facilisis at ligula at mattis.
                          Vestibulum et quam et ipsum .
        """), out=log.out)


class TablePrinterFormatSortTest(resource_printer_test_base.Base):

  def testMultipleStreamedResourceCase(self):
    printer = resource_printer.Printer(
        'table(name:label=MONIKER:sort=102, kind:sort=101, '
        'networkInterfaces[0].networkIP:label=IP)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        MONIKER             KIND              IP
        my-instance-a-0     compute#instance  10.240.150.0
        my-instance-az-1    compute#instance  10.240.150.1
        my-instance-azz-2   compute#instance  10.240.150.2
        my-instance-azzz-3  compute#instance  10.240.150.3
        """))

  def testMultipleStreamedResourceCaseWithPager(self):
    mock_more = self.StartObjectPatch(console_io, 'More')
    printer = resource_printer.Printer(
        'table[pager](name:label=MONIKER:sort=102, kind:sort=101, '
        'networkInterfaces[0].networkIP:label=IP)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    mock_more.assert_called_once_with(textwrap.dedent("""\
        MONIKER             KIND              IP
        my-instance-a-0     compute#instance  10.240.150.0
        my-instance-az-1    compute#instance  10.240.150.1
        my-instance-azz-2   compute#instance  10.240.150.2
        my-instance-azzz-3  compute#instance  10.240.150.3
        """), out=log.out)

  def testHiddenSortByMultipleStreamedResourceCase(self):
    printer = resource_printer.Printer(
        'table(name:label=MONIKER:sort=102, kind:sort=101)'
        ':(networkInterfaces[0].networkIP:sort=1:reverse)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        MONIKER             KIND
        my-instance-azzz-3  compute#instance
        my-instance-azz-2   compute#instance
        my-instance-az-1    compute#instance
        my-instance-a-0     compute#instance
        """))

  def testHiddenOptionalSortByMultipleStreamedResourceCase(self):
    printer = resource_printer.Printer(
        'table(name:label=MONIKER:sort=102, empty:optional:sort=101)'
        ':(networkInterfaces[0].networkIP:sort=1:reverse)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        MONIKER
        my-instance-azzz-3
        my-instance-azz-2
        my-instance-az-1
        my-instance-a-0
        """))

  def testHiddenSortByMultipleStreamedResourceCaseBox(self):
    printer = resource_printer.Printer(
        'table[box,ascii](name:label=MONIKER:sort=102, kind:sort=101)'
        ':(networkInterfaces[0].networkIP:sort=1:reverse)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +--------------------+------------------+
        |      MONIKER       |       KIND       |
        +--------------------+------------------+
        | my-instance-azzz-3 | compute#instance |
        | my-instance-azz-2  | compute#instance |
        | my-instance-az-1   | compute#instance |
        | my-instance-a-0    | compute#instance |
        +--------------------+------------------+
        """))

  def testHiddenSortByMultipleStreamedResourceCaseAllBox(self):
    printer = resource_printer.Printer(
        'table[all-box,ascii](name:label=MONIKER:sort=102, kind:sort=101)'
        ':(networkInterfaces[0].networkIP:sort=1:reverse)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +--------------------+------------------+
        |      MONIKER       |       KIND       |
        +--------------------+------------------+
        | my-instance-azzz-3 | compute#instance |
        +--------------------+------------------+
        | my-instance-azz-2  | compute#instance |
        +--------------------+------------------+
        | my-instance-az-1   | compute#instance |
        +--------------------+------------------+
        | my-instance-a-0    | compute#instance |
        +--------------------+------------------+
        """))

  def testVisibleSortByMultipleStreamedResourceCase(self):
    printer = resource_printer.Printer(
        'table(name:label=MONIKER:sort=102, kind:sort=101, '
        'networkInterfaces[0].networkIP:label=IP)'
        ':(networkInterfaces[0].networkIP:sort=1:reverse)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        MONIKER             KIND              IP
        my-instance-azzz-3  compute#instance  10.240.150.3
        my-instance-azz-2   compute#instance  10.240.150.2
        my-instance-az-1    compute#instance  10.240.150.1
        my-instance-a-0     compute#instance  10.240.150.0
        """))

  def testMultipleStreamedResourceCaseReverseByDefault(self):
    printer = resource_printer.Printer(
        'table(name:label=MONIKER:sort=102:reverse, kind:sort=101, '
        'networkInterfaces[0].networkIP:label=IP)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        MONIKER             KIND              IP
        my-instance-azzz-3  compute#instance  10.240.150.3
        my-instance-azz-2   compute#instance  10.240.150.2
        my-instance-az-1    compute#instance  10.240.150.1
        my-instance-a-0     compute#instance  10.240.150.0
        """))

  def testMultipleStreamedResourceCaseReverseExplicitComposition(self):
    printer = resource_printer.Printer(
        'table(name:label=MONIKER:sort=102, kind:sort=101, '
        'networkInterfaces[0].networkIP:label=IP)'
        ':(name:reverse)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        MONIKER             KIND              IP
        my-instance-azzz-3  compute#instance  10.240.150.3
        my-instance-azz-2   compute#instance  10.240.150.2
        my-instance-az-1    compute#instance  10.240.150.1
        my-instance-a-0     compute#instance  10.240.150.0
        """))

  def testMultipleStreamedResourceCaseNoReverseExplicitComposition(self):
    printer = resource_printer.Printer(
        'table(name:label=MONIKER:sort=102:reverse, kind:sort=101, '
        'networkInterfaces[0].networkIP:label=IP)'
        ':(name:no-reverse)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        MONIKER             KIND              IP
        my-instance-a-0     compute#instance  10.240.150.0
        my-instance-az-1    compute#instance  10.240.150.1
        my-instance-azz-2   compute#instance  10.240.150.2
        my-instance-azzz-3  compute#instance  10.240.150.3
        """))

  def testMultipleStreamedResourceCaseMultipleReverse(self):
    printer = resource_printer.Printer(
        'table(name:sort=102, metadata.kind:sort=101:reverse)')
    for resource in self.CreateResourceList(9):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME                     KIND
        my-instance-a-0          compute#metadata.2
        my-instance-azzz-3       compute#metadata.2
        my-instance-azzzzzz-6    compute#metadata.2
        my-instance-az-1         compute#metadata.1
        my-instance-azzzz-4      compute#metadata.1
        my-instance-azzzzzzz-7   compute#metadata.1
        my-instance-azz-2        compute#metadata.0
        my-instance-azzzzz-5     compute#metadata.0
        my-instance-azzzzzzzz-8  compute#metadata.0
        """))

  def testMultipleStreamedResourceCaseMultipleReverseAll(self):
    printer = resource_printer.Printer(
        'table(name:sort=102:reverse, metadata.kind:sort=101:reverse)')
    for resource in self.CreateResourceList(9):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME                     KIND
        my-instance-azzzzzz-6    compute#metadata.2
        my-instance-azzz-3       compute#metadata.2
        my-instance-a-0          compute#metadata.2
        my-instance-azzzzzzz-7   compute#metadata.1
        my-instance-azzzz-4      compute#metadata.1
        my-instance-az-1         compute#metadata.1
        my-instance-azzzzzzzz-8  compute#metadata.0
        my-instance-azzzzz-5     compute#metadata.0
        my-instance-azz-2        compute#metadata.0
        """))

  def testMultipleStreamedResourceCasePageFlagSmall(self):
    printer = resource_printer.Printer(
        'table[title=Kinds]'
        '(name:sort=102, metadata.kind)')
    resources = Pager(self.CreateResourceList(10), 4)
    for resource in resources:
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
                        Kinds
        NAME                KIND
        my-instance-a-0     compute#metadata.2
        my-instance-az-1    compute#metadata.1
        my-instance-azz-2   compute#metadata.0
        my-instance-azzz-3  compute#metadata.2

        NAME                    KIND
        my-instance-azzzz-4     compute#metadata.1
        my-instance-azzzzz-5    compute#metadata.0
        my-instance-azzzzzz-6   compute#metadata.2
        my-instance-azzzzzzz-7  compute#metadata.1

        NAME                      KIND
        my-instance-azzzzzzzz-8   compute#metadata.0
        my-instance-azzzzzzzzz-9  compute#metadata.2
        """))

  def testMultipleStreamedResourceCaseBoxPageFlagSmall(self):
    printer = resource_printer.Printer(
        'table[box,ascii,title=Kinds]'
        '(name:sort=102, metadata.kind)')
    for resource in Pager(self.CreateResourceList(10), 4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +-----------------------------------------+
        |                  Kinds                  |
        +--------------------+--------------------+
        |        NAME        |        KIND        |
        +--------------------+--------------------+
        | my-instance-a-0    | compute#metadata.2 |
        | my-instance-az-1   | compute#metadata.1 |
        | my-instance-azz-2  | compute#metadata.0 |
        | my-instance-azzz-3 | compute#metadata.2 |
        +--------------------+--------------------+
        +------------------------+--------------------+
        |          NAME          |        KIND        |
        +------------------------+--------------------+
        | my-instance-azzzz-4    | compute#metadata.1 |
        | my-instance-azzzzz-5   | compute#metadata.0 |
        | my-instance-azzzzzz-6  | compute#metadata.2 |
        | my-instance-azzzzzzz-7 | compute#metadata.1 |
        +------------------------+--------------------+
        +--------------------------+--------------------+
        |           NAME           |        KIND        |
        +--------------------------+--------------------+
        | my-instance-azzzzzzzz-8  | compute#metadata.0 |
        | my-instance-azzzzzzzzz-9 | compute#metadata.2 |
        +--------------------------+--------------------+
        """))

  def testMultipleStreamedResourceCaseBoxPageFlagExact(self):
    printer = resource_printer.Printer(
        'table[box,ascii,title=Kinds]'
        '(name:sort=102, metadata.kind)')
    for resource in Pager(self.CreateResourceList(10), 10):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        +-----------------------------------------------+
        |                     Kinds                     |
        +--------------------------+--------------------+
        |           NAME           |        KIND        |
        +--------------------------+--------------------+
        | my-instance-a-0          | compute#metadata.2 |
        | my-instance-az-1         | compute#metadata.1 |
        | my-instance-azz-2        | compute#metadata.0 |
        | my-instance-azzz-3       | compute#metadata.2 |
        | my-instance-azzzz-4      | compute#metadata.1 |
        | my-instance-azzzzz-5     | compute#metadata.0 |
        | my-instance-azzzzzz-6    | compute#metadata.2 |
        | my-instance-azzzzzzz-7   | compute#metadata.1 |
        | my-instance-azzzzzzzz-8  | compute#metadata.0 |
        | my-instance-azzzzzzzzz-9 | compute#metadata.2 |
        +--------------------------+--------------------+
        """))

  def testMultipleAllOptionalFirstEmpty(self):
    printer = resource_printer.Printer(
        'table(empty:optional, kind:optional, '
        'networkInterfaces[0].networkIP:optional)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        KIND              NETWORK_IP
        compute#instance  10.240.150.0
        compute#instance  10.240.150.1
        compute#instance  10.240.150.2
        compute#instance  10.240.150.3
        """))

  def testMultipleAllOptionalMiddleEmpty(self):
    printer = resource_printer.Printer(
        'table(name:optional, empty:optional, '
        'networkInterfaces[0].networkIP:optional)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME                NETWORK_IP
        my-instance-a-0     10.240.150.0
        my-instance-az-1    10.240.150.1
        my-instance-azz-2   10.240.150.2
        my-instance-azzz-3  10.240.150.3
        """))

  def testMultipleAllOptionalLastEmpty(self):
    printer = resource_printer.Printer(
        'table(name:optional, kind:optional, empty:optional)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME                KIND
        my-instance-a-0     compute#instance
        my-instance-az-1    compute#instance
        my-instance-azz-2   compute#instance
        my-instance-azzz-3  compute#instance
        """))

  def testMultipleAllOptionalTwoEmpty(self):
    printer = resource_printer.Printer(
        'table(name:optional, empty_kind:optional, empty:optional)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME
        my-instance-a-0
        my-instance-az-1
        my-instance-azz-2
        my-instance-azzz-3
        """))

  def testMultipleAllOptionalAllEmpty(self):
    printer = resource_printer.Printer(
        'table(empty_name:optional, empty_kind:optional, empty:optional)')
    for resource in self.CreateResourceList(4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals('')


class TablePrinterAttributeTest(resource_printer_test_base.Base):

  def SetUp(self):
    self.SetEncoding('utf8')

  def testTableEmptyTitle(self):
    self.Print(attributes='[title="Four Three Stooges"]', count=0)
    self.AssertOutputEquals('')

  def testTableOneTitle(self):
    self.Print(attributes='[title="Four Three Stooges"]', count=1)
    self.AssertOutputEquals(textwrap.dedent("""\
                   Four Three Stooges
        NAME  QUOTE                         ID
        Ṁöë   .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW  1267
        """))

  def testTablePad1(self):
    self.Print(attributes='[pad=1]')
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME  QUOTE                                          ID
        Ṁöë   .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW                   1267
        Larry ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ. 1245
        Shemp Hey, Ṁöë! Hey, Larry!                          lrlrlrl
        Curly Søɨŧɇnłɏ!                                      1234
        """))

  def testTablePad3(self):
    self.Print(attributes='[pad=3]')
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME    QUOTE                                            ID
        Ṁöë     .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW                     1267
        Larry   ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.   1245
        Shemp   Hey, Ṁöë! Hey, Larry!                            lrlrlrl
        Curly   Søɨŧɇnłɏ!                                        1234
        """))

  def testTablePad0(self):
    self.Print(attributes='[pad=0]')
    self.AssertOutputEquals(textwrap.dedent("""\
        NAME QUOTE                                         ID
        Ṁöë  .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW                  1267
        Larryι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.1245
        ShempHey, Ṁöë! Hey, Larry!                         lrlrlrl
        CurlySøɨŧɇnłɏ!                                     1234
        """))

  def testTablePrinterVariableWidthCharacters(self):
    resource_printer.Print(self.width_resource, 'table[box](head, data, tail)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌──────┬──────┬──────┐
        │ HEAD │ DATA │ TAIL │
        ├──────┼──────┼──────┤
        │ zero │ :\u200b\u00ad:   │ ZERO │
        │ one  │ :Ü:  │ ONE  │
        │ two  │ :車: │ TWO  │
        └──────┴──────┴──────┘
        """))

  def testTablePrinterUnicodeKeys(self):
    resource_printer.Print(self.unicode_key_resource,
                           'table[box](ħɇȺđ, ∂αтα, täïḷ)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌──────┬──────┬──────┐
        │ ĦɆȺĐ │ ∂ΑТΑ │ TÄÏḶ │
        ├──────┼──────┼──────┤
        │ zero │ :\u200b\u00ad:   │ ZERO │
        │ one  │ :Ü:  │ ONE  │
        │ two  │ :車: │ TWO  │
        └──────┴──────┴──────┘
        """))

  def testTablePrinterUnicodeKeysAndTitleBox(self):
    resource_printer.Print(self.unicode_key_resource,
                           'table[box,title="東京"](ħɇȺđ, ∂αтα, täïḷ)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌────────────────────┐
        │        東京        │
        ├──────┬──────┬──────┤
        │ ĦɆȺĐ │ ∂ΑТΑ │ TÄÏḶ │
        ├──────┼──────┼──────┤
        │ zero │ :\u200b\u00ad:   │ ZERO │
        │ one  │ :Ü:  │ ONE  │
        │ two  │ :車: │ TWO  │
        └──────┴──────┴──────┘
        """))

  def testTablePrinterUnicodeKeysAndTitleNoBox(self):
    resource_printer.Print(self.unicode_key_resource,
                           'table[title="東京"](ħɇȺđ, ∂αтα, täïḷ)')
    self.AssertOutputEquals(textwrap.dedent("""\
              東京
        ĦɆȺĐ  ∂ΑТΑ  TÄÏḶ
        zero  :\u200b\u00ad:    ZERO
        one   :Ü:   ONE
        two   :車:  TWO
        """))

  def testNoProjection(self):
    with self.assertRaises(resource_printer_base.ProjectionRequiredError):
      resource_printer.Print([], 'table')


class TablePrinterFormatUriTest(resource_printer_test_base.Base):

  def SetUp(self):
    self._printer = resource_printer.Printer(
        'table(uri():label="")')

  def testMultipleStreamedResourceCase(self):
    for resource in self.CreateResourceList(4):
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        http://g/selfie/a-0
        http://g/selfie/az-1
        http://g/selfie/azz-2
        http://g/selfie/azzz-3
        """))


class TablePrintTest(resource_printer_test_base.Base):

  _RESOURCE = [{'a': 1, 'b': 2, 'c': 3}]

  def testSinglePrintWithTableCols(self):
    resource_printer.Print(self._RESOURCE[0], 'table(a, c)',
                           single=True)
    self.AssertOutputEquals(textwrap.dedent("""\
        A  C
        1  3
        """))

  def testPrintWithTableCols(self):
    resource_printer.Print(self._RESOURCE, 'table(a, c)')
    self.AssertOutputEquals(textwrap.dedent("""\
        A  C
        1  3
        """))

  def testSinglePrintWithTableUri(self):
    resource_printer.Print(self._RESOURCE[0], 'table(uri())',
                           single=True)
    self.AssertOutputEquals(textwrap.dedent("""\
        URI
        .
        """))

  def testPrintWithTableUri(self):
    resource_printer.Print(self._RESOURCE, 'table(uri())')
    self.AssertOutputEquals(textwrap.dedent("""\
        URI
        .
        """))


class TableLastColumnTrailingSpaceTest(resource_printer_test_base.Base):

  _RESOURCE = [{'a': 'aaa', 'b': 'bbb'},
               {'a': '', 'b': ''},
               {'a': 'yyy', 'b': 'zzz'},
              ]

  def testLastColumnTrailingSpace(self):
    resource_printer.Print(self._RESOURCE, 'table(a, b)')
    self.AssertOutputEquals(textwrap.dedent("""\
        A    B
        aaa  bbb

        yyy  zzz
        """))


class TableLabelTest(resource_printer_test_base.Base):

  _RESOURCE = [{'aIPdEf': 'aaa', 'gHIJkLm': 'bbb'},
               {'aIPdEf': '', 'gHIJkLm': ''},
               {'aIPdEf': 'yyy', 'gHIJkLm': 'zzz'},
              ]

  def testLastColumnTrailingSpace(self):
    resource_printer.Print(self._RESOURCE, 'table(aIPdEf, gHIJkLm)')
    self.AssertOutputEquals(textwrap.dedent("""\
        A_IPD_EF  G_HIJK_LM
        aaa       bbb

        yyy       zzz
        """))


class TableRepeatedKeyTest(resource_printer_test_base.Base):

  def testRepeatedKeyAttribute(self):
    resource_printer.Print(self.repeated_resource,
                           'table(selfLink:label=LEFT,'
                           '      selfLink:label=RIGHT)')
    self.AssertOutputEquals("""\
LEFT               RIGHT
/1/2/3/4/5         /1/2/3/4/5
/i/ii/iii/iv/v/vi  /i/ii/iii/iv/v/vi
/I/II/III/IV/V/VI  /I/II/III/IV/V/VI
""")

  def testRepeatedKeyTransform(self):
    resource_printer.Print(self.repeated_resource,
                           'table(selfLink.segment(1):label=LEFT,'
                           '      selfLink.segment(3):label=MIDDLE,'
                           '      selfLink.segment(5):label=RIGHT)')
    self.AssertOutputEquals("""\
LEFT  MIDDLE  RIGHT
1     3       5
i     iii     v
I     III     V
""")


class TablePrinterConsoleAttrTest(resource_printer_test_base.Base):

  def testTableASCIIBox(self):
    self.Print(attributes='[box]')
    self.AssertOutputEquals(textwrap.dedent("""\
        +-------+------------------------------------------------+---------+
        |  NAME |                     QUOTE                      |    ID   |
        +-------+------------------------------------------------+---------+
        | ???   | .T?A? ??Alq o? '?iTT?g ??'?W                   | 1267    |
        | Larry | ? ????'? ????? ??? ???, ??? ? ??????'? ??? ??. | 1245    |
        | Shemp | Hey, ???! Hey, Larry!                          | lrlrlrl |
        | Curly | S????n??!                                      | 1234    |
        +-------+------------------------------------------------+---------+
        """))

  def testTableASCIIAllBox(self):
    self.Print(attributes='[all-box]')
    self.AssertOutputEquals(textwrap.dedent("""\
        +-------+------------------------------------------------+---------+
        |  NAME |                     QUOTE                      |    ID   |
        +-------+------------------------------------------------+---------+
        | ???   | .T?A? ??Alq o? '?iTT?g ??'?W                   | 1267    |
        +-------+------------------------------------------------+---------+
        | Larry | ? ????'? ????? ??? ???, ??? ? ??????'? ??? ??. | 1245    |
        +-------+------------------------------------------------+---------+
        | Shemp | Hey, ???! Hey, Larry!                          | lrlrlrl |
        +-------+------------------------------------------------+---------+
        | Curly | S????n??!                                      | 1234    |
        +-------+------------------------------------------------+---------+
        """))

  def testTableASCIIBoxTitle(self):
    self.Print(attributes='[box,title="Four Three Stooges"]')
    self.AssertOutputEquals(textwrap.dedent("""\
        +------------------------------------------------------------------+
        |                        Four Three Stooges                        |
        +-------+------------------------------------------------+---------+
        |  NAME |                     QUOTE                      |    ID   |
        +-------+------------------------------------------------+---------+
        | ???   | .T?A? ??Alq o? '?iTT?g ??'?W                   | 1267    |
        | Larry | ? ????'? ????? ??? ???, ??? ? ??????'? ??? ??. | 1245    |
        | Shemp | Hey, ???! Hey, Larry!                          | lrlrlrl |
        | Curly | S????n??!                                      | 1234    |
        +-------+------------------------------------------------+---------+
        """))

  def testTablASCIIBoxVariableWidthCharacters(self):
    resource_printer.Print(self.width_resource, 'table[box](head, data, tail)')
    self.AssertOutputEquals(textwrap.dedent("""\
        +------+------+------+
        | HEAD | DATA | TAIL |
        +------+------+------+
        | zero | :??: | ZERO |
        | one  | :?:  | ONE  |
        | two  | :?:  | TWO  |
        +------+------+------+
        """))

  def testTableUtf8Box(self):
    self.SetEncoding('utf8')
    self.Print(attributes='[box]')
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌───────┬────────────────────────────────────────────────┬─────────┐
        │  NAME │                     QUOTE                      │    ID   │
        ├───────┼────────────────────────────────────────────────┼─────────┤
        │ Ṁöë   │ .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW                   │ 1267    │
        │ Larry │ ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ. │ 1245    │
        │ Shemp │ Hey, Ṁöë! Hey, Larry!                          │ lrlrlrl │
        │ Curly │ Søɨŧɇnłɏ!                                      │ 1234    │
        └───────┴────────────────────────────────────────────────┴─────────┘
        """))

  def testTableUtf8AllBox(self):
    self.SetEncoding('utf8')
    self.Print(attributes='[all-box]')
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌───────┬────────────────────────────────────────────────┬─────────┐
        │  NAME │                     QUOTE                      │    ID   │
        ├───────┼────────────────────────────────────────────────┼─────────┤
        │ Ṁöë   │ .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW                   │ 1267    │
        ├───────┼────────────────────────────────────────────────┼─────────┤
        │ Larry │ ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ. │ 1245    │
        ├───────┼────────────────────────────────────────────────┼─────────┤
        │ Shemp │ Hey, Ṁöë! Hey, Larry!                          │ lrlrlrl │
        ├───────┼────────────────────────────────────────────────┼─────────┤
        │ Curly │ Søɨŧɇnłɏ!                                      │ 1234    │
        └───────┴────────────────────────────────────────────────┴─────────┘
        """))

  def testTableWinBox(self):
    self.SetEncoding('cp437')
    self.Print(attributes='[box]')
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌───────┬────────────────────────────────────────────────┬─────────┐
        │  NAME │                     QUOTE                      │    ID   │
        ├───────┼────────────────────────────────────────────────┼─────────┤
        │ ?öë   │ .T?A? ??Alq o? '?iTT?g ??'?W                   │ 1267    │
        │ Larry │ ? ????'? ?α??α ?α? ???, ??? ? ¢σ????'? ?α? ?σ. │ 1245    │
        │ Shemp │ Hey, ?öë! Hey, Larry!                          │ lrlrlrl │
        │ Curly │ S????n??!                                      │ 1234    │
        └───────┴────────────────────────────────────────────────┴─────────┘
        """))

  def testTableWinAllBox(self):
    self.SetEncoding('cp437')
    self.Print(attributes='[all-box]')
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌───────┬────────────────────────────────────────────────┬─────────┐
        │  NAME │                     QUOTE                      │    ID   │
        ├───────┼────────────────────────────────────────────────┼─────────┤
        │ ?öë   │ .T?A? ??Alq o? '?iTT?g ??'?W                   │ 1267    │
        ├───────┼────────────────────────────────────────────────┼─────────┤
        │ Larry │ ? ????'? ?α??α ?α? ???, ??? ? ¢σ????'? ?α? ?σ. │ 1245    │
        ├───────┼────────────────────────────────────────────────┼─────────┤
        │ Shemp │ Hey, ?öë! Hey, Larry!                          │ lrlrlrl │
        ├───────┼────────────────────────────────────────────────┼─────────┤
        │ Curly │ S????n??!                                      │ 1234    │
        └───────┴────────────────────────────────────────────────┴─────────┘
        """))

  def testMultipleStreamedResourceCaseBoxUtf8PageFlagSmall(self):
    """Make sure the intermediate corners are correct."""
    self.SetEncoding('utf8')
    printer = resource_printer.Printer(
        'table[box,title=Kinds]'
        '(name:sort=102, metadata.kind)')
    for resource in Pager(self.CreateResourceList(10), 4):
      printer.AddRecord(resource)
    printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        ┌─────────────────────────────────────────┐
        │                  Kinds                  │
        ├────────────────────┬────────────────────┤
        │        NAME        │        KIND        │
        ├────────────────────┼────────────────────┤
        │ my-instance-a-0    │ compute#metadata.2 │
        │ my-instance-az-1   │ compute#metadata.1 │
        │ my-instance-azz-2  │ compute#metadata.0 │
        │ my-instance-azzz-3 │ compute#metadata.2 │
        └────────────────────┴────────────────────┘
        ┌────────────────────────┬────────────────────┐
        │          NAME          │        KIND        │
        ├────────────────────────┼────────────────────┤
        │ my-instance-azzzz-4    │ compute#metadata.1 │
        │ my-instance-azzzzz-5   │ compute#metadata.0 │
        │ my-instance-azzzzzz-6  │ compute#metadata.2 │
        │ my-instance-azzzzzzz-7 │ compute#metadata.1 │
        └────────────────────────┴────────────────────┘
        ┌──────────────────────────┬────────────────────┐
        │           NAME           │        KIND        │
        ├──────────────────────────┼────────────────────┤
        │ my-instance-azzzzzzzz-8  │ compute#metadata.0 │
        │ my-instance-azzzzzzzzz-9 │ compute#metadata.2 │
        └──────────────────────────┴────────────────────┘
        """))


class TablePrivateAttributeTest(sdk_test_base.WithLogCapture,
                                resource_printer_test_base.Base,
                                parameterized.TestCase):

  _SECRET = 'too many secrets'
  _RESOURCE = [{'message': _SECRET}]

  @parameterized.named_parameters(
      ('', 'table(message)'),
      ('WithPager', '[pager]table(message)'))
  def testTableNoPrivateAttributeDefaultOut(self, format_string):
    resource_printer.Print(self._RESOURCE, format_string, out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  @parameterized.named_parameters(
      ('', 'table(message)'),
      ('WithPager', '[pager]table(message)'))
  def testTableNoPrivateAttributeLogOut(self, format_string):
    resource_printer.Print(self._RESOURCE, format_string, out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  @parameterized.named_parameters(
      ('', '[private]table(message)'),
      ('WithPager', '[private,pager]table(message)'))
  def testTablePrivateAttributeDefaultOut(self, format_string):
    resource_printer.Print(self._RESOURCE, format_string,
                           out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  @parameterized.named_parameters(
      ('', '[private]table(message)'),
      ('WithPager', '[private,pager]table(message)'))
  def testTablePrivateAttributeLogOut(self, format_string):
    resource_printer.Print(self._RESOURCE, format_string,
                           out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  @parameterized.named_parameters(
      ('', 'table(message)'),
      ('WithPager', '[pager]table(message)'))
  def testTableNoPrivateAttributeLogErr(self, format_string):
    resource_printer.Print(self._RESOURCE, format_string,
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  @parameterized.named_parameters(
      ('', '[private]table(message)'),
      ('WithPager', '[private,pager]table(message)'))
  def testTablePrivateAttributeLogErr(self, format_string):
    resource_printer.Print(self._RESOURCE, format_string,
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  @parameterized.named_parameters(
      ('', '[private]table(message)'),
      ('WithPager', '[private,pager]table(message)'))
  def testTablePrivateAttributeLogStatus(self, format_string):
    resource_printer.Print(self._RESOURCE, format_string,
                           out=log.status)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  @parameterized.named_parameters(
      ('', '[private]table(message)'),
      ('WithPager', '[private,pager]table(message)'))
  def testTablePrivateAttributeStdout(self, format_string):
    resource_printer.Print(self._RESOURCE, format_string,
                           out=sys.stdout)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  @parameterized.named_parameters(
      ('', '[private]table(message)'),
      ('WithPager', '[private,pager]table(message)'))
  def testTablePrivateAttributeStderr(self, format_string):
    resource_printer.Print(self._RESOURCE, format_string,
                           out=sys.stderr)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)


class TableNestedFormatTest(sdk_test_base.WithLogCapture,
                            resource_printer_test_base.Base):

  def testTableNestedTableNoBox(self):
    resource_printer.Print(
        self.CreateResourceList(3),
        'table(name, kind, metadata.kind, '
        '      metadata.items:format="table(key, value)")')
    self.AssertOutputEquals("""\
NAME               KIND              METADATA_KIND
my-instance-a-0    compute#instance  compute#metadata.2
    KEY  VALUE
    a    b
    c    d
    e    f
    g    h
my-instance-az-1   compute#instance  compute#metadata.1
    KEY  VALUE
    a    b
    c    d
    e    f
    g    h
my-instance-azz-2  compute#instance  compute#metadata.0
    KEY  VALUE
    a    b
    c    d
    e    f
    g    h
""")

  def testTableNestedTable(self):
    resource_printer.Print(
        self.CreateResourceList(3),
        'table[box](name, kind, metadata.kind, '
        '           metadata.items:format="table[box,no-heading](key, value)")')
    self.AssertOutputEquals("""\
+-------------------+------------------+--------------------+
|        NAME       |       KIND       |   METADATA_KIND    |
+-------------------+------------------+--------------------+
| my-instance-a-0   | compute#instance | compute#metadata.2 |
+-------------------+------------------+--------------------+
    +---+---+
    | a | b |
    | c | d |
    | e | f |
    | g | h |
    +---+---+
+-------------------+------------------+--------------------+
| my-instance-az-1  | compute#instance | compute#metadata.1 |
+-------------------+------------------+--------------------+
    +---+---+
    | a | b |
    | c | d |
    | e | f |
    | g | h |
    +---+---+
+-------------------+------------------+--------------------+
| my-instance-azz-2 | compute#instance | compute#metadata.0 |
+-------------------+------------------+--------------------+
    +---+---+
    | a | b |
    | c | d |
    | e | f |
    | g | h |
    +---+---+
""")

  def testTableNestedJson(self):
    resource_printer.Print(
        self.CreateResourceList(3),
        'table[box](name, kind, metadata.kind, metadata.items:format=json)')
    self.AssertOutputEquals("""\
+-------------------+------------------+--------------------+
|        NAME       |       KIND       |   METADATA_KIND    |
+-------------------+------------------+--------------------+
| my-instance-a-0   | compute#instance | compute#metadata.2 |
+-------------------+------------------+--------------------+
    [
      {
        "key": "a",
        "value": "b"
      },
      {
        "key": "c",
        "value": "d"
      },
      {
        "key": "e",
        "value": "f"
      },
      {
        "key": "g",
        "value": "h"
      }
    ]
+-------------------+------------------+--------------------+
| my-instance-az-1  | compute#instance | compute#metadata.1 |
+-------------------+------------------+--------------------+
    [
      {
        "key": "a",
        "value": "b"
      },
      {
        "key": "c",
        "value": "d"
      },
      {
        "key": "e",
        "value": "f"
      },
      {
        "key": "g",
        "value": "h"
      }
    ]
+-------------------+------------------+--------------------+
| my-instance-azz-2 | compute#instance | compute#metadata.0 |
+-------------------+------------------+--------------------+
    [
      {
        "key": "a",
        "value": "b"
      },
      {
        "key": "c",
        "value": "d"
      },
      {
        "key": "e",
        "value": "f"
      },
      {
        "key": "g",
        "value": "h"
      }
    ]
""")

  def testTableAggregateEmptyResource(self):
    printer = resource_printer.Printer(
        'table(inputs:format="table(name)", outputs:format="table(name)")')
    printer.Print([])
    self.AssertOutputEquals('')
    self.assertFalse(printer.ResourcesWerePrinted())

  def testTableAggregateEmptySubResources(self):
    printer = resource_printer.Printer(
        'table(inputs:format="table(name)", outputs:format="table(name)")')
    printer.Print([[], []])
    self.AssertOutputEquals('')
    self.assertFalse(printer.ResourcesWerePrinted())

  def testTableAggregateNotEmptyNoMatchingKeys(self):
    printer = resource_printer.Printer(
        'table(inputs:format="table(name)", outputs:format="table(name)")')
    printer.Print([{'a': 1}])
    self.AssertOutputEquals('')
    self.assertFalse(printer.ResourcesWerePrinted())

  def testTableAggregateNotEmptyInputsMatchingKey(self):
    printer = resource_printer.Printer(
        'table(inputs:format="table(name)", outputs:format="table(name)")')
    printer.Print([{'inputs': {'name': 'alfalfa'}}])
    self.AssertOutputEquals('NAME\nalfalfa\n')
    self.assertTrue(printer.ResourcesWerePrinted())

  def testTableAggregateNotEmptyOutputsMatchingKey(self):
    printer = resource_printer.Printer(
        'table(inputs:format="table(name)", outputs:format="table(name)")')
    printer.Print([{'outputs': {'name': 'clover'}}])
    self.AssertOutputEquals('NAME\nclover\n')
    self.assertTrue(printer.ResourcesWerePrinted())

  def testTableAggregateNotEmptyAllMatchingKeys(self):
    printer = resource_printer.Printer(
        'table(inputs:format="table(name)", outputs:format="table(name)")')
    printer.Print([{'outputs': {'name': 'clover'}},
                   {'inputs': {'name': 'alfalfa'}}])
    self.AssertOutputEquals('NAME\nalfalfa\nNAME\nclover\n')
    self.assertTrue(printer.ResourcesWerePrinted())

  def testTableAggregateTable(self):
    resource_printer.Print(
        self.CreateResourceList(3),
        'table(metadata.items:format="table[box](key, value)")')
    self.AssertOutputEquals("""\
+-----+-------+
| KEY | VALUE |
+-----+-------+
| a   | b     |
| c   | d     |
| e   | f     |
| g   | h     |
| a   | b     |
| c   | d     |
| e   | f     |
| g   | h     |
| a   | b     |
| c   | d     |
| e   | f     |
| g   | h     |
+-----+-------+
""")

  def testTableAggregateTableIntermediateJSON(self):
    resource_printer.Print(
        self.CreateResourceList(3),
        'table(metadata.items[0]:format=json)')
    self.AssertOutputEquals("""\
[
  {
    "key": "a",
    "value": "b"
  },
  {
    "key": "a",
    "value": "b"
  },
  {
    "key": "a",
    "value": "b"
  }
]
""")

  def testTableNestedTableParentDefaults(self):
    symbols = {
        'upper': lambda x: x.upper(),
        }
    defaults = resource_projection_spec.ProjectionSpec(symbols=symbols)
    resource_printer.Print(
        self.CreateResourceList(3),
        'table(name, kind, metadata.kind, '
        '      metadata.items:format="table(key, value.upper())")',
        defaults=defaults
    )
    self.AssertOutputEquals("""\
NAME               KIND              METADATA_KIND
my-instance-a-0    compute#instance  compute#metadata.2
    KEY  VALUE
    a    B
    c    D
    e    F
    g    H
my-instance-az-1   compute#instance  compute#metadata.1
    KEY  VALUE
    a    B
    c    D
    e    F
    g    H
my-instance-azz-2  compute#instance  compute#metadata.0
    KEY  VALUE
    a    B
    c    D
    e    F
    g    H
""")

  def testTableAggregateTableParentDefaults(self):
    symbols = {
        'upper': lambda x: x.upper(),
        }
    defaults = resource_projection_spec.ProjectionSpec(symbols=symbols)
    resource_printer.Print(
        self.CreateResourceList(3),
        'table(metadata.items:format="table(key)",'
        '      metadata.items:format="table(key.upper():label=NAME)")',
        defaults=defaults
    )
    self.AssertOutputEquals("""\
KEY
a
c
e
g
a
c
e
g
a
c
e
g
NAME
A
C
E
G
A
C
E
G
A
C
E
G
""")

  def testTableAggregateNestedTable(self):
    resources = [
        {
            'bindings': [
                {
                    'members': [
                        'first-1',
                        'first-2',
                    ],
                    'role': 'first',
                },
                {
                    'members': [
                        'middle-1',
                        'middle-2',
                    ],
                    'role': 'middle',
                },
                {
                    'members': [
                        'last-1',
                        'last-2',
                    ],
                    'role': 'last',
                },
            ],
        },
    ]

    resource_printer.Print(
        resources, 'table(bindings:format="table(role, members:format=list)")')
    self.AssertOutputEquals("""\
ROLE
first
     - first-1
     - first-2
middle
     - middle-1
     - middle-2
last
     - last-1
     - last-2
""")

  def testTableNestedTableDuplicateKeyName(self):
    resources = [
        {
            'predictions': [
                {
                    'key': 0,
                    'predictions': [
                        1,
                        2,
                        3,
                    ],
                },
                {
                    'key': 1,
                    'predictions': [
                        4,
                        5,
                        6,
                    ],
                },
            ],
        },
        {
            'predictions': [
                {
                    'key': 2,
                    'predictions': [
                        7,
                        8,
                    ],
                },
                {
                    'key': 3,
                    'predictions': [
                        9,
                    ],
                },
            ],
        },
    ]

    resource_printer.Print(
        resources, 'table(predictions:format="table(key, predictions.list())")')
    self.AssertOutputEquals("""\
KEY  PREDICTIONS
0    1,2,3
1    4,5,6
2    7,8
3    9
""")

  def testTableNestedTableNoBoxWithPager(self):
    mock_more = self.StartObjectPatch(console_io, 'More')
    resource_printer.Print(
        self.CreateResourceList(3),
        'table[pager](name, kind, metadata.kind, '
        '      metadata.items:format="table(key, value)")')
    mock_more.assert_called_once_with("""\
NAME               KIND              METADATA_KIND
my-instance-a-0    compute#instance  compute#metadata.2
    KEY  VALUE
    a    b
    c    d
    e    f
    g    h
my-instance-az-1   compute#instance  compute#metadata.1
    KEY  VALUE
    a    b
    c    d
    e    f
    g    h
my-instance-azz-2  compute#instance  compute#metadata.0
    KEY  VALUE
    a    b
    c    d
    e    f
    g    h
""", out=log.out)


class TablePrintFormatTest(resource_printer_test_base.Base):

  def testTableFormatTransform(self):
    symbols = {
        'hello': lambda x: 'hello',
        }
    defaults = resource_projection_spec.ProjectionSpec(symbols=symbols)
    resource_printer.Print(
        self.CreateResourceList(3),
        'table(hello():label=HI)',
        defaults=defaults
    )
    self.AssertOutputEquals("""\
HI
hello
hello
hello
""")

  def testTableNestedFormatTransform(self):
    symbols = {
        'upper': lambda x: x.upper(),
        }
    defaults = resource_projection_spec.ProjectionSpec(symbols=symbols)
    resource_printer.Print(
        self.CreateResourceList(3),
        'table(metadata.items:format='
        '        "table(format(\'{0}={1}\', key, value))",'
        '      metadata.items:format="table(key, value.upper())"'
        ')',
        defaults=defaults
    )
    self.AssertOutputEquals("""\
VALUE
a=b
c=d
e=f
g=h
a=b
c=d
e=f
g=h
a=b
c=d
e=f
g=h
KEY  VALUE
a    B
c    D
e    F
g    H
a    B
c    D
e    F
g    H
a    B
c    D
e    F
g    H
""")

  def testTableSynthesizeNestedFormatTransform(self):
    resource = [
        {
            'id': 'abc-123',
            'downInfo': {
                'foo': 0,
                'bar': 'no',
            },
            'upInfo': {
                'foo': 1,
                'bar': 'yes',
            },
        },
        {
            'id': 'xyz-789',
            'downInfo': {
                'foo': 2,
                'bar': 'maybe',
            },
            'upInfo': {
                'foo': 3,
                'bar': 'never',
            },
        },
    ]
    resource_printer.Print(
        resource,
        'table(id, synthesize((name:up, upInfo), (name:down, downInfo))'
        '      :format="table(name, foo, bar)"'
        ')',
    )
    self.AssertOutputEquals("""\
ID
abc-123
    NAME  FOO  BAR
    up    1    yes
    down  0    no
xyz-789
    NAME  FOO  BAR
    up    3    never
    down  2    maybe
""")

  def testTableSynthesizeExplicitAttributesNestedFormatTransform(self):
    resource = [
        {
            'id': 'abc-123',
            'downInfo': {
                'foo': 0,
                'bar': 'no',
            },
            'upInfo': {
                'foo': 1,
                'bar': 'yes',
            },
        },
        {
            'id': 'xyz-789',
            'downInfo': {
                'foo': 2,
                'bar': 'maybe',
            },
            'upInfo': {
                'foo': 3,
                'bar': 'never',
            },
        },
    ]
    resource_printer.Print(
        resource,
        'table(id, synthesize((name:up, foo=upInfo.foo),'
        '                     (name:down, foo=downInfo.foo))'
        '      :format="table(name, foo)"'
        ')',
    )
    self.AssertOutputEquals("""\
ID
abc-123
    NAME  FOO
    up    1
    down  0
xyz-789
    NAME  FOO
    up    3
    down  2
""")

  def testTableSynthesizeError(self):
    resource = []
    with self.assertRaises(resource_exceptions.ExpressionSyntaxError):
      resource_printer.Print(
          resource,
          'table(id, synthesize(name:up, foo=upInfo.foo,'
          '                     (name:down, foo=downInfo.foo))'
          '      :format="table(name, foo)"'
          ')',
      )

  def testTableExtractJoin(self):
    resource = [
        {'dir': 'bin', 'file': 'abc'},
        {'dir': 'usr'},
        {'dir': 'lost+found', 'file': 'tmp/junk'},
    ]
    resource_printer.Print(
        resource,
        'table(extract(dir, file).join():label=PATH)',
    )
    self.AssertOutputEquals("""\
PATH
bin/abc
usr
lost+found/tmp/junk
""")


class TablePrintFloatTest(resource_printer_test_base.Base):

  def testFloat(self):
    resource_printer.Print(self.float_resource,
                           'table(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t)',
                           single=True)
    self.AssertOutputEquals("""\
A    B     C        D         E       F       G      H      I    J         \
K        L         M        N         O        P          Q          \
R            S            T
1.0  -1.0  1.00001  -1.00009  1.0009  -1.009  1.009  -1.09  1.9  -1.33333  \
1.66667  -12.3457  123.457  -1234.57  12345.7  -123456.8  1234567.9  \
-12345678.9  123456789.0  -1.23457e+09
""")


if __name__ == '__main__':
  resource_printer_test_base.main()
