# -*- coding: utf-8 -*-
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

"""Unit tests for csv_printer.ValuePrinter."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
import textwrap

from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_printer_base
from tests.lib import sdk_test_base
from tests.lib.core.resource import resource_printer_test_base


class ValueAttributeTest(resource_printer_test_base.Base):

  def SetUp(self):
    self.SetEncoding('utf8')

  def testDefaultNames(self):
    self.Print(style='value', fields='(name)', count=6)
    self.AssertOutputEquals(textwrap.dedent("""\
        Ṁöë
        Larry
        Shemp
        Curly
        Joe
        Curly Joe
        """))

  def testDefaultQuotes(self):
    self.Print(style='value', fields='(quote)', count=6)
    self.AssertOutputEquals(textwrap.dedent("""\
        .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW
        ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.
        Hey, Ṁöë! Hey, Larry!
        Søɨŧɇnłɏ!
        Oh, cut it ouuuuuut!
        One of these days, you're gonna poke my eyes out.
        """))

  def testDefaultIds(self):
    self.Print(style='value', fields='(id)', count=6)
    self.AssertOutputEquals(textwrap.dedent("""\
        1267
        1245
        lrlrlrl
        1234
        new;6789
        new=890
        """))

  def testDefaultIdsDelimiterNewline(self):
    self.Print(style='value', fields='(id)', attributes='[delimiter="\n"]',
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
    self.Print(style='value', fields='(id)', attributes='[terminator=":"]',
               count=6)
    self.AssertOutputEquals(textwrap.dedent("""\
        1267:1245:lrlrlrl:1234:new;6789:new=890:"""))

  def testNoProjection(self):
    with self.assertRaises(resource_printer_base.ProjectionRequiredError):
      resource_printer.Print([], 'value')


class ValuePrivateAttributeTest(sdk_test_base.WithLogCapture,
                                resource_printer_test_base.Base):

  _SECRET = 'too many secrets'
  _RESOURCE = [{'message': _SECRET}]

  def testValueNoPrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, 'value(message)', out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testValueNoPrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, 'value(message)', out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testValuePrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, '[private]value(message)',
                           out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testValuePrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, '[private]value(message)',
                           out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testValueNoPrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, 'value(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testValuePrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, '[private]value(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testValuePrivateAttributeLogStatus(self):
    resource_printer.Print(self._RESOURCE, '[private]value(message)',
                           out=log.status)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testValuePrivateAttributeStdout(self):
    resource_printer.Print(self._RESOURCE, '[private]value(message)',
                           out=sys.stdout)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testValuePrivateAttributeStderr(self):
    resource_printer.Print(self._RESOURCE, '[private]value(message)',
                           out=sys.stderr)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)


class ValueNoQuoteAttributeTest(sdk_test_base.WithLogCapture,
                                resource_printer_test_base.Base):

  _MESSAGE_1 = 'Too\nmany\nbugs.'
  _RESOURCE_1 = [{'message': _MESSAGE_1}]

  def testValueQuoteNewlines(self):
    resource_printer.Print(self._RESOURCE_1, 'value[quote](message)', out=None)
    self.AssertOutputEquals('"' + self._MESSAGE_1 + '"\n')

  def testValueNoQuoteNewlines(self):
    resource_printer.Print(self._RESOURCE_1, 'value(message)', out=None)
    self.AssertOutputEquals(self._MESSAGE_1 + '\n')

  _MESSAGE_2 = 'Too\tmany\tbugs.'
  _RESOURCE_2 = [{'message': _MESSAGE_2}]

  def testValueQuoteTabs(self):
    resource_printer.Print(self._RESOURCE_2, 'value[quote](message)', out=None)
    self.AssertOutputEquals('"' + self._MESSAGE_2 + '"\n')

  def testValueNoQuoteTabs(self):
    resource_printer.Print(self._RESOURCE_2, 'value(message)', out=None)
    self.AssertOutputEquals(self._MESSAGE_2 + '\n')

  _MESSAGE_3 = 'Too"many"bugs.'
  _RESOURCE_3 = [{'message': _MESSAGE_3}]

  def testValueQuoteQuotes(self):
    resource_printer.Print(self._RESOURCE_3, 'value[quote](message)', out=None)
    self.AssertOutputEquals('"' + self._MESSAGE_3.replace('"', '""') + '"\n')

  def testValueNoQuoteQuotes(self):
    resource_printer.Print(self._RESOURCE_3, 'value(message)', out=None)
    self.AssertOutputEquals(self._MESSAGE_3 + '\n')


class ValueNoneValueTest(resource_printer_test_base.Base):

  def testNoneValue(self):
    resource_printer.Print(self.none_dict_resource, 'value(a,n,z)')
    self.AssertOutputEquals("""\
\tnnn\txyz
abc\t\txyz
\t\t
""")

  def testNoneImplicitRepeatedValue(self):
    resource_printer.Print(self.CreateResourceList(1),
                           'value(metadata.items.a)')
    self.AssertOutputEquals("""\
b
""")

  def testNoneExplicitRepeatedValue(self):
    resource_printer.Print(self.CreateResourceList(1),
                           'value(metadata.items[].a)')
    self.AssertOutputEquals("""\
;;;
""")


if __name__ == '__main__':
  resource_printer_test_base.main()
