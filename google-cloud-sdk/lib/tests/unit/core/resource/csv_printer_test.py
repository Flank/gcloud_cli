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

"""Unit tests for the csv_printer module."""

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


class CsvPrinterTest(resource_printer_test_base.Base):

  def SetUp(self):
    self.SetEncoding('utf8')

  def testDefault(self):
    self.Print(style='csv')
    self.AssertOutputEquals(textwrap.dedent("""\
        name,quote,id
        Ṁöë,.TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW,1267
        Larry,"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",1245
        Shemp,"Hey, Ṁöë! Hey, Larry!",lrlrlrl
        Curly,Søɨŧɇnłɏ!,1234
        """))

  def testDefaultUtf8(self):
    self.Print(style='csv', encoding='utf8')
    self.AssertOutputEquals(textwrap.dedent("""\
        name,quote,id
        Ṁöë,.TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW,1267
        Larry,"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",1245
        Shemp,"Hey, Ṁöë! Hey, Larry!",lrlrlrl
        Curly,Søɨŧɇnłɏ!,1234
        """))

  def testNoHeading(self):
    self.Print(style='csv', attributes='[no-heading]')
    self.AssertOutputEquals(textwrap.dedent("""\
        Ṁöë,.TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW,1267
        Larry,"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",1245
        Shemp,"Hey, Ṁöë! Hey, Larry!",lrlrlrl
        Curly,Søɨŧɇnłɏ!,1234
        """))

  def testHeading(self):
    self.Print(style='csv', heading=['moniker', 'quote', 'number'])
    self.AssertOutputEquals(textwrap.dedent("""\
        moniker,quote,number
        Ṁöë,.TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW,1267
        Larry,"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",1245
        Shemp,"Hey, Ṁöë! Hey, Larry!",lrlrlrl
        Curly,Søɨŧɇnłɏ!,1234
        """))

  def testInnerListAndDict(self):
    self.Print(style='csv', count=6)
    self.AssertOutputEquals(textwrap.dedent("""\
        name,quote,id
        Ṁöë,.TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW,1267
        Larry,"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",1245
        Shemp,"Hey, Ṁöë! Hey, Larry!",lrlrlrl
        Curly,Søɨŧɇnłɏ!,1234
        Joe,"Oh, cut it ouuuuuut!",new;6789
        Curly Joe,"One of these days, you're gonna poke my eyes out.",new=890
        """))

  def testObjectResourceSerialization(self):
    self.Print(style='csv', resource=self.CreateObjectResourceList(3))
    self.AssertOutputEquals(textwrap.dedent("""\
        name,quote,id
        B0,a=0;b=0.1,0
        B1,a=1;b=1.2,1
        B2,a=2;b=2.3,2
        """))


class CsvPrinterAttributeTest(resource_printer_test_base.Base):

  def SetUp(self):
    self.SetEncoding('utf8')

  def testDefault(self):
    self.Print(style='csv')
    self.AssertOutputEquals(textwrap.dedent("""\
        name,quote,id
        Ṁöë,.TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW,1267
        Larry,"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",1245
        Shemp,"Hey, Ṁöë! Hey, Larry!",lrlrlrl
        Curly,Søɨŧɇnłɏ!,1234
        """))

  def testNoHeading(self):
    self.Print(style='csv', attributes='[no-heading]')
    self.AssertOutputEquals(textwrap.dedent("""\
        Ṁöë,.TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW,1267
        Larry,"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",1245
        Shemp,"Hey, Ṁöë! Hey, Larry!",lrlrlrl
        Curly,Søɨŧɇnłɏ!,1234
        """))

  def testHeading(self):
    self.Print(style='csv', heading=['moniker', 'quote', 'number'])
    self.AssertOutputEquals(textwrap.dedent("""\
        moniker,quote,number
        Ṁöë,.TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW,1267
        Larry,"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",1245
        Shemp,"Hey, Ṁöë! Hey, Larry!",lrlrlrl
        Curly,Søɨŧɇnłɏ!,1234
        """))

  def testInnerListAndDict(self):
    self.Print(style='csv', count=6)
    self.AssertOutputEquals(textwrap.dedent("""\
        name,quote,id
        Ṁöë,.TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW,1267
        Larry,"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",1245
        Shemp,"Hey, Ṁöë! Hey, Larry!",lrlrlrl
        Curly,Søɨŧɇnłɏ!,1234
        Joe,"Oh, cut it ouuuuuut!",new;6789
        Curly Joe,"One of these days, you're gonna poke my eyes out.",new=890
        """))

  def testSeparator(self):
    self.Print(style='csv', attributes='[separator=";"]')
    self.AssertOutputEquals(textwrap.dedent("""\
        name;quote;id
        Ṁöë;.TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW;1267
        Larry;ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.;1245
        Shemp;Hey, Ṁöë! Hey, Larry!;lrlrlrl
        Curly;Søɨŧɇnłɏ!;1234
        """))

  def testDelimiter(self):
    self.Print(style='csv', attributes='[delimiter=".."]',
               resource=self.CreateObjectResourceList(3))
    self.AssertOutputEquals(textwrap.dedent("""\
        name,quote,id
        B0,a=0..b=0.1,0
        B1,a=1..b=1.2,1
        B2,a=2..b=2.3,2
        """))

  def testSeparatorDelimiterNewline(self):
    self.Print(style='csv',
               attributes='[no-heading,separator="\n",delimiter="\n"]',
               resource=self.CreateObjectResourceList(3))
    self.AssertOutputEquals(textwrap.dedent("""\
        B0
        a=0
        b=0.1
        0
        B1
        a=1
        b=1.2
        1
        B2
        a=2
        b=2.3
        2
        """))

  def testTerminator(self):
    self.Print(style='csv',
               attributes='[no-heading,terminator="..."]',
               resource=self.CreateObjectResourceList(3))
    self.AssertOutputEquals(textwrap.dedent("""\
        B0,a=0;b=0.1,0...B1,a=1;b=1.2,1...B2,a=2;b=2.3,2..."""))

  def testUnicode(self):
    resource = self.CreateResourceList(2)
    self.Print(style='csv', fields='(name, unicode)', resource=resource)
    self.AssertOutputEquals(textwrap.dedent("""\
        name,unicode
        my-instance-a-0,python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ
        my-instance-az-1,python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ
        """))

  def testNoProjection(self):
    with self.assertRaises(resource_printer_base.ProjectionRequiredError):
      resource_printer.Print([], 'csv')


class CsvPrivateAttributeTest(sdk_test_base.WithLogCapture,
                              resource_printer_test_base.Base):

  _SECRET = 'too many secrets'
  _RESOURCE = [{'message': _SECRET}]

  def testCsvNoPrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, 'csv(message)', out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testCsvNoPrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, 'csv(message)', out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testCsvPrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, '[private]csv(message)',
                           out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testCsvPrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, '[private]csv(message)',
                           out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testCsvNoPrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, 'csv(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testCsvPrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, '[private]csv(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testCsvPrivateAttributeLogStatus(self):
    resource_printer.Print(self._RESOURCE, '[private]csv(message)',
                           out=log.status)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testCsvPrivateAttributeStdout(self):
    resource_printer.Print(self._RESOURCE, '[private]csv(message)',
                           out=sys.stdout)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testCsvPrivateAttributeStderr(self):
    resource_printer.Print(self._RESOURCE, '[private]csv(message)',
                           out=sys.stderr)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)


class CsvPrintFloatTest(resource_printer_test_base.Base):

  def testFloat(self):
    resource_printer.Print(self.float_resource,
                           'csv(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t)',
                           single=True)
    self.AssertOutputEquals("""\
a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t
1.0,-1.0,1.00001,-1.00009,1.0009,-1.009,1.009,-1.09,1.9,-1.33333,1.66667,\
-12.3457,123.457,-1234.57,12345.7,-123456.8,1234567.9,-12345678.9,123456789.0,\
-1.23457e+09
""")


class CsvRepeatedKeyTest(resource_printer_test_base.Base):

  def testRepeatedKeyAttribute(self):
    resource_printer.Print(self.repeated_resource,
                           'csv(selfLink:label=left,'
                           '    selfLink:label=right)')
    self.AssertOutputEquals("""\
left,right
/1/2/3/4/5,/1/2/3/4/5
/i/ii/iii/iv/v/vi,/i/ii/iii/iv/v/vi
/I/II/III/IV/V/VI,/I/II/III/IV/V/VI
""")

  def testRepeatedKeyTransform(self):
    resource_printer.Print(self.repeated_resource,
                           'csv(selfLink.segment(1):label=left,'
                           '    selfLink.segment(3):label=middle,'
                           '    selfLink.segment(5):label=right)')
    self.AssertOutputEquals("""\
left,middle,right
1,3,5
i,iii,v
I,III,V
""")


class CsvNoneValueTest(resource_printer_test_base.Base):

  def testNoneValue(self):
    resource_printer.Print(self.none_dict_resource, 'csv(a,n,z)')
    self.AssertOutputEquals("""\
a,n,z
,nnn,xyz
abc,,xyz
,,
""")

  def testNoneImplicitRepeatedValue(self):
    resource_printer.Print(self.CreateResourceList(1),
                           'csv(metadata.items.a)')
    self.AssertOutputEquals("""\
a
b
""")

  def testNoneExplicitRepeatedValue(self):
    resource_printer.Print(self.CreateResourceList(1),
                           'csv(metadata.items[].a)')
    self.AssertOutputEquals("""\
a
;;;
""")


if __name__ == '__main__':
  resource_printer_test_base.main()
