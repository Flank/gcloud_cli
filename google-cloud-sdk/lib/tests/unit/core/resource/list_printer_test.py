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

"""Unit tests for the list_printer module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
import textwrap

from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer
from tests.lib import sdk_test_base
from tests.lib.core.resource import resource_printer_test_base

import six


class _Quote(object):

  def __init__(self, moniker, quote):
    self.moniker = moniker
    self.quote = quote


class ListPrinterAttributeTest(resource_printer_test_base.Base):

  _RESOURCE = [
      ['Ṁöë', ".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW"],
      ['Larry', "ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ."],
      ['Shemp', 'Hey, Ṁöë! Hey, Larry!'],
      ['Curly', 'Søɨŧɇnłɏ!'],
      ['Joe', ['Oh, cut it ouuuuuut!', 1]],
      ['Curly Joe', {"One of these days, you're gonna poke my eyes out.": 2}],
  ]

  _RESOURCE_DICT = [{
      'Ṁöë': ".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW",
      'Larry': "ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",
      'Shemp': 'Hey, Ṁöë! Hey, Larry!',
      'Curly': 'Søɨŧɇnłɏ!',
      'Joe': ['Oh, cut it ouuuuuut!', 1],
      'Curly Joe': {"One of these days, you're gonna poke my eyes out.": 2},
  }]

  _RESOURCE_LIST = [
      ".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW",
      "ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.",
      'Hey, Ṁöë! Hey, Larry!',
      'Søɨŧɇnłɏ!',
      'Oh, cut it ouuuuuut!',
      "One of these days, you're gonna poke my eyes out.",
  ]

  _RESOURCE_OBJECT = [
      _Quote('Ṁöë', ".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW"),
      _Quote('Larry', "ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ."),
      _Quote('Shemp', 'Hey, Ṁöë! Hey, Larry!'),
      _Quote('Curly', 'Søɨŧɇnłɏ!'),
      _Quote('Joe', 'Oh, cut it ouuuuuut!'),
      _Quote('Curly Joe', "One of these days, you're gonna poke my eyes out."),
  ]

  def SetUp(self):
    self.SetEncoding('utf8')

  def testList(self):
    self.Print(style='list', fields='')
    self.AssertOutputEquals(' - Ṁöë\n - Larry\n - Shemp\n - Curly\n')

  def testListDict(self):
    self.Print(style='list', fields='', resource=self._RESOURCE_DICT)
    if six.PY2:
      self.AssertOutputContains("""\
 - Curly: Søɨŧɇnłɏ!
   Curly Joe: {u"One of these days, you're gonna poke my eyes out.": 2}
   Joe: [u'Oh, cut it ouuuuuut!', 1]
   Larry: ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.
   Shemp: Hey, Ṁöë! Hey, Larry!
   Ṁöë: .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW
""")
    else:
      self.AssertOutputContains("""\
 - Curly: Søɨŧɇnłɏ!
   Curly Joe: {"One of these days, you're gonna poke my eyes out.": 2}
   Joe: ['Oh, cut it ouuuuuut!', 1]
   Larry: ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.
   Shemp: Hey, Ṁöë! Hey, Larry!
   Ṁöë: .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW
""")

  def testListList(self):
    self.Print(style='list', fields='', resource=self._RESOURCE_LIST)
    self.AssertOutputContains("""\
 - .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW
 - ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.
 - Hey, Ṁöë! Hey, Larry!
 - Søɨŧɇnłɏ!
 - Oh, cut it ouuuuuut!
 - One of these days, you're gonna poke my eyes out.
""")

  def testListListUtf8(self):
    self.Print(style='list', fields='',
               resource=[x.encode('utf8') for x in self._RESOURCE_LIST])
    self.AssertOutputContains("""\
 - .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW
 - ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.
 - Hey, Ṁöë! Hey, Larry!
 - Søɨŧɇnłɏ!
 - Oh, cut it ouuuuuut!
 - One of these days, you're gonna poke my eyes out.
""")

  def testListObject(self):
    self.Print(style='list', attributes='[compact]', fields='(moniker, quote)',
               resource=self._RESOURCE_OBJECT)
    self.AssertOutputContains("""\
 - Ṁöë .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW
 - Larry ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.
 - Shemp Hey, Ṁöë! Hey, Larry!
 - Curly Søɨŧɇnłɏ!
 - Joe Oh, cut it ouuuuuut!
 - Curly Joe One of these days, you're gonna poke my eyes out.
""")

  def testListEmpty(self):
    self.Print(style='list', fields='()', resource=[])
    self.AssertOutputEquals('')

  def testListEmptyTitle(self):
    self.Print(style='list', attributes='[title="Four Three Stooges"]',
               fields='()', resource=[])
    self.AssertOutputEquals('')

  def testListEmptyTitleWithAlwaysListTitle(self):
    self.Print(style='list',
               attributes='[title="Four Three Stooges",always-display-title]',
               fields='()', resource=[])
    self.AssertOutputEquals('Four Three Stooges\n')

  def testListTitle(self):
    self.Print(style='list', attributes='[title="Four Three Stooges"]',
               fields='()')
    self.AssertOutputEquals(textwrap.dedent("""\
        Four Three Stooges
         - Ṁöë
         - Larry
         - Shemp
         - Curly
        """))


class ListPrivateAttributeTest(sdk_test_base.WithLogCapture,
                               resource_printer_test_base.Base):

  _SECRET = 'too many secrets'
  _RESOURCE = [{'message': _SECRET}]

  def testListNoPrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, 'list(message)', out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testListNoPrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, 'list(message)', out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testListPrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, '[private]list(message)',
                           out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testListPrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, '[private]list(message)',
                           out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testListNoPrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, 'list(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testListPrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, '[private]list(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testListPrivateAttributeLogStatus(self):
    resource_printer.Print(self._RESOURCE, '[private]list(message)',
                           out=log.status)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testListPrivateAttributeStdout(self):
    resource_printer.Print(self._RESOURCE, '[private]list(message)',
                           out=sys.stdout)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testListPrivateAttributeStderr(self):
    resource_printer.Print(self._RESOURCE, '[private]list(message)',
                           out=sys.stderr)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)


class ListRepeatedKeyTest(resource_printer_test_base.Base):

  def testRepeatedKeyAttribute(self):
    resource_printer.Print(self.repeated_resource, 'list(selfLink, selfLink)')
    self.AssertOutputEquals("""\
 - /1/2/3/4/5
   /1/2/3/4/5
 - /i/ii/iii/iv/v/vi
   /i/ii/iii/iv/v/vi
 - /I/II/III/IV/V/VI
   /I/II/III/IV/V/VI
""")

  def testRepeatedKeyAttributeCompact(self):
    resource_printer.Print(
        self.repeated_resource, 'list[compact](selfLink, selfLink)')
    self.AssertOutputEquals("""\
 - /1/2/3/4/5 /1/2/3/4/5
 - /i/ii/iii/iv/v/vi /i/ii/iii/iv/v/vi
 - /I/II/III/IV/V/VI /I/II/III/IV/V/VI
""")

  def testRepeatedKeyTransform(self):
    resource_printer.Print(self.repeated_resource,
                           'list(selfLink.segment(1),'
                           '     selfLink.segment(3),'
                           '     selfLink.segment(5))')
    self.AssertOutputEquals("""\
 - 1
   3
   5
 - i
   iii
   v
 - I
   III
   V
""")


class ListNoneValueTest(resource_printer_test_base.Base):

  def testNoneDictValueEmptyProjection(self):
    resource_printer.Print(self.none_dict_resource, 'list')
    self.AssertOutputEquals("""\
 - n: nnn
   z: xyz
 - a: abc
   z: xyz
 - \

""")

  def testNoneDictValueEmptyProjectionCompact(self):
    resource_printer.Print(self.none_dict_resource, 'list[compact]')
    self.AssertOutputEquals("""\
 - n: nnn z: xyz
 - a: abc z: xyz
 - \

""")

  def testNoneDictValueNonEmptyProjection(self):
    resource_printer.Print(self.none_dict_resource, 'list(a,n,z)')
    self.AssertOutputEquals("""\
 - nnn
   xyz
 - abc
   xyz
 - \

""")

  def testNoneListValue(self):
    resource_printer.Print(self.none_list_resource, 'list')
    self.AssertOutputEquals("""\
 - nnn
   xyz
 - abc
   xyz
 - \

""")


if __name__ == '__main__':
  resource_printer_test_base.main()
