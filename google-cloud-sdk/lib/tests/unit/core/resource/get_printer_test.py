# -*- coding: utf-8 -*-
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

"""Unit tests for csv_printer.GetPrinter."""

from __future__ import absolute_import
from __future__ import unicode_literals
import sys
import textwrap

from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_printer_base
from tests.lib import sdk_test_base
from tests.lib.core.resource import resource_printer_test_base


class GetAttributeTest(resource_printer_test_base.Base):

  def SetUp(self):
    self.SetEncoding('utf8')

  def testDefaultNames(self):
    self.Print(style='get', fields='(name)', count=6)
    self.AssertOutputEquals(textwrap.dedent("""\
        Ṁöë
        Larry
        Shemp
        Curly
        Joe
        Curly Joe
        """))

  def testDefaultQuotes(self):
    self.Print(style='get', fields='(quote)', count=6)
    self.AssertOutputEquals(textwrap.dedent("""\
        .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW
        ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.
        Hey, Ṁöë! Hey, Larry!
        Søɨŧɇnłɏ!
        Oh, cut it ouuuuuut!
        One of these days, you're gonna poke my eyes out.
        """))

  def testDefaultIds(self):
    self.Print(style='get', fields='(id)', count=6)
    self.AssertOutputEquals(textwrap.dedent("""\
        1267
        1245
        lrlrlrl
        1234
        new;6789
        new=890
        """))

  def testDefaultIdsDelimiterNewline(self):
    self.Print(style='get', fields='(id)', attributes='[delimiter="\n"]',
               count=6)
    self.AssertOutputEquals(textwrap.dedent("""\
        1267
        1245
        lrlrlrl
        1234
        new
        6789
        new=890
        """))

  def testDefaultIdsTerminator(self):
    self.Print(style='get', fields='(id)', attributes='[terminator=":"]',
               count=6)
    self.AssertOutputEquals(textwrap.dedent("""\
        1267:1245:lrlrlrl:1234:new;6789:new=890:"""))

  def testNoProjection(self):
    with self.assertRaises(resource_printer_base.ProjectionRequiredError):
      resource_printer.Print([], 'get')


class GetPrivateAttributeTest(sdk_test_base.WithLogCapture,
                              resource_printer_test_base.Base):

  _SECRET = 'too many secrets'
  _RESOURCE = [{'message': _SECRET}]

  def testGetNoPrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, 'get(message)', out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testGetNoPrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, 'get(message)', out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testGetPrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, '[private]get(message)',
                           out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testGetPrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, '[private]get(message)',
                           out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testGetNoPrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, 'get(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testGetPrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, '[private]get(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testGetPrivateAttributeLogStatus(self):
    resource_printer.Print(self._RESOURCE, '[private]get(message)',
                           out=log.status)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testGetPrivateAttributeStdout(self):
    resource_printer.Print(self._RESOURCE, '[private]get(message)',
                           out=sys.stdout)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testGetPrivateAttributeStderr(self):
    resource_printer.Print(self._RESOURCE, '[private]get(message)',
                           out=sys.stderr)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)


class GetNoQuoteAttributeTest(sdk_test_base.WithLogCapture,
                              resource_printer_test_base.Base):

  _MESSAGE_1 = 'Too\nmany\nbugs.'
  _RESOURCE_1 = [{'message': _MESSAGE_1}]

  def testGetQuoteNewlines(self):
    resource_printer.Print(self._RESOURCE_1, 'get[quote](message)', out=None)
    self.AssertOutputEquals('"' + self._MESSAGE_1 + '"\n')

  def testGetNoQuoteNewlines(self):
    resource_printer.Print(self._RESOURCE_1, 'get(message)', out=None)
    self.AssertOutputEquals(self._MESSAGE_1 + '\n')

  _MESSAGE_2 = 'Too\tmany\tbugs.'
  _RESOURCE_2 = [{'message': _MESSAGE_2}]

  def testGetQuoteTabs(self):
    resource_printer.Print(self._RESOURCE_2, 'get[quote](message)', out=None)
    self.AssertOutputEquals('"' + self._MESSAGE_2 + '"\n')

  def testGetNoQuoteTabs(self):
    resource_printer.Print(self._RESOURCE_2, 'get(message)', out=None)
    self.AssertOutputEquals(self._MESSAGE_2 + '\n')

  _MESSAGE_3 = 'Too"many"bugs.'
  _RESOURCE_3 = [{'message': _MESSAGE_3}]

  def testGetQuoteQuotes(self):
    resource_printer.Print(self._RESOURCE_3, 'get[quote](message)', out=None)
    self.AssertOutputEquals('"' + self._MESSAGE_3.replace('"', '""') + '"\n')

  def testGetNoQuoteQuotes(self):
    resource_printer.Print(self._RESOURCE_3, 'get(message)', out=None)
    self.AssertOutputEquals(self._MESSAGE_3 + '\n')

  def testGetQuoteQuotesDefaultTransforms(self):
    resource_printer.Print(self._RESOURCE_3,
                           ':(message.len()) get[quote](message)',
                           out=None)
    self.AssertOutputEquals('"' + self._MESSAGE_3.replace('"', '""') + '"\n')

  def testGetNoQuoteQuotesDefaultTransforms(self):
    resource_printer.Print(self._RESOURCE_3,
                           ':(message.len()) get(message)',
                           out=None)
    self.AssertOutputEquals(self._MESSAGE_3 + '\n')

  def testGetQuoteQuotesEnableTransforms(self):
    resource_printer.Print(self._RESOURCE_3,
                           ':(message.len()) get[quote,transforms](message)',
                           out=None)
    self.AssertOutputEquals('{0}\n'.format(len(self._MESSAGE_3)))

  def testGetNoQuoteQuotesEnableTransforms(self):
    resource_printer.Print(self._RESOURCE_3,
                           ':(message.len()) get[transforms](message)',
                           out=None)
    self.AssertOutputEquals('{0}\n'.format(len(self._MESSAGE_3)))


if __name__ == '__main__':
  resource_printer_test_base.main()
