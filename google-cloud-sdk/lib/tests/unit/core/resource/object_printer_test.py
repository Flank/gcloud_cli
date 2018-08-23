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

"""Unit tests for the object_printer module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib.core.resource import resource_printer_test_base


class _Quote(object):

  def __init__(self, moniker, quote):
    self.moniker = moniker
    self.quote = quote

  def __str__(self):
    return '<{0}>="{1}"\n'.format(self.moniker, self.quote)


class ObjectPrinterTest(resource_printer_test_base.Base):

  _RESOURCE_LIST = [
      ['Moe', "We're gettin' no place fast."],
      ['Larry', "I didn't wanna say yes, but I couldn't say no."],
      ['Shemp', 'Hey, Moe! Hey, Larry!'],
      ['Curly', 'Soitenly!'],
      ['Joe', ['Oh, cut it ouuuuuut!', 1]],
      ['Curly Joe', {"One of these days, you're gonna poke my eyes out.": 2}],
  ]

  _RESOURCE_DICT = [
      {'Moe': "We're gettin' no place fast."},
      {'Larry': "I didn't wanna say yes, but I couldn't say no."},
      {'Shemp': 'Hey, Moe! Hey, Larry!'},
      {'Curly': 'Soitenly!'},
      {'Joe': ['Oh, cut it ouuuuuut!', 1]},
      {'Curly Joe': {"One of these days, you're gonna poke my eyes out.": 2}},
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

  def testrPrintList(self):
    self.Print(style='object', resource=self._RESOURCE_LIST)
    self.AssertOutputMatches("""\
\\[u?'Moe', u?"We're gettin' no place fast."]\
\\[u?'Larry', u?"I didn't wanna say yes, but I couldn't say no."]\
\\[u?'Shemp', u?'Hey, Moe! Hey, Larry!']\
\\[u?'Curly', u?'Soitenly!']\
\\[u?'Joe', \\[u?'Oh, cut it ouuuuuut!', 1]]\
\\[u?'Curly Joe', {u?"One of these days, you're gonna poke my eyes out.": 2}]\
""")

  def testrPrintListTerminator(self):
    self.Print(
        style='object[terminator=""]', resource=self._RESOURCE_LIST)
    self.AssertOutputMatches("""\
\\[u?'Moe', u?"We're gettin' no place fast."]
\\[u?'Larry', u?"I didn't wanna say yes, but I couldn't say no."]
\\[u?'Shemp', u?'Hey, Moe! Hey, Larry!']
\\[u?'Curly', u?'Soitenly!']
\\[u?'Joe', \\[u?'Oh, cut it ouuuuuut!', 1]]
\\[u?'Curly Joe', {u?"One of these days, you're gonna poke my eyes out.": 2}]
""")

  def testrPrintDict(self):
    self.Print(style='object', resource=self._RESOURCE_DICT)
    self.AssertOutputMatches("""\
{u?'Moe': u?"We're gettin' no place fast."}\
{u?'Larry': u?"I didn't wanna say yes, but I couldn't say no."}\
{u?'Shemp': u?'Hey, Moe! Hey, Larry!'}\
{u?'Curly': u?'Soitenly!'}\
{u?'Joe': \\[u?'Oh, cut it ouuuuuut!', 1]}\
{u?'Curly Joe': {u?"One of these days, you're gonna poke my eyes out.": 2}}\
""")

  def testrPrintDictSeparatorEmpty(self):
    self.Print(style='object[separator=""]', resource=self._RESOURCE_DICT)
    self.AssertOutputMatches("""\
{u?'Moe': u?"We're gettin' no place fast."}
{u?'Larry': u?"I didn't wanna say yes, but I couldn't say no."}
{u?'Shemp': u?'Hey, Moe! Hey, Larry!'}
{u?'Curly': u?'Soitenly!'}
{u?'Joe': \\[u?'Oh, cut it ouuuuuut!', 1]}
{u?'Curly Joe': {u?"One of these days, you're gonna poke my eyes out.": 2}}\
""")

  def testrPrintDictTerminatorEmpty(self):
    self.Print(style='object[terminator=""]', resource=self._RESOURCE_DICT)
    self.AssertOutputMatches("""\
{u?'Moe': u?"We're gettin' no place fast."}
{u?'Larry': u?"I didn't wanna say yes, but I couldn't say no."}
{u?'Shemp': u?'Hey, Moe! Hey, Larry!'}
{u?'Curly': u?'Soitenly!'}
{u?'Joe': \\[u?'Oh, cut it ouuuuuut!', 1]}
{u?'Curly Joe': {u?"One of these days, you're gonna poke my eyes out.": 2}}
""")

  def testrPrintDictSeparator(self):
    self.Print(
        style='object[separator="<SEPARATOR>"]', resource=self._RESOURCE_DICT)
    self.AssertOutputMatches("""\
{u?'Moe': u?"We're gettin' no place fast."}<SEPARATOR>
{u?'Larry': u?"I didn't wanna say yes, but I couldn't say no."}<SEPARATOR>
{u?'Shemp': u?'Hey, Moe! Hey, Larry!'}<SEPARATOR>
{u?'Curly': u?'Soitenly!'}<SEPARATOR>
{u?'Joe': \\[u?'Oh, cut it ouuuuuut!', 1]}<SEPARATOR>
{u?'Curly Joe': {u?"One of these days, you're gonna poke my eyes out.": 2}}\
""")

  def testrPrintDictTerminator(self):
    self.Print(
        style='object[terminator="<TERMINATOR>"]', resource=self._RESOURCE_DICT)
    self.AssertOutputMatches("""\
{u?'Moe': u?"We're gettin' no place fast."}<TERMINATOR>
{u?'Larry': u?"I didn't wanna say yes, but I couldn't say no."}<TERMINATOR>
{u?'Shemp': u?'Hey, Moe! Hey, Larry!'}<TERMINATOR>
{u?'Curly': u?'Soitenly!'}<TERMINATOR>
{u?'Joe': \\[u?'Oh, cut it ouuuuuut!', 1]}<TERMINATOR>
{u?'Curly Joe': {u?"One of these days, you're gonna poke my eyes out.": 2}}<TERMINATOR>
""")

  def testrPrintDictSeparatorAndTerminator(self):
    self.Print(
        style='object[separator="<SEPARATOR>",terminator="<TERMINATOR>"]',
        resource=self._RESOURCE_DICT)
    self.AssertOutputMatches("""\
{u?'Moe': u?"We're gettin' no place fast."}<TERMINATOR>
<SEPARATOR>
{u?'Larry': u?"I didn't wanna say yes, but I couldn't say no."}<TERMINATOR>
<SEPARATOR>
{u?'Shemp': u?'Hey, Moe! Hey, Larry!'}<TERMINATOR>
<SEPARATOR>
{u?'Curly': u?'Soitenly!'}<TERMINATOR>
<SEPARATOR>
{u?'Joe': \\[u?'Oh, cut it ouuuuuut!', 1]}<TERMINATOR>
<SEPARATOR>
{u?'Curly Joe': {u?"One of these days, you're gonna poke my eyes out.": 2}}<TERMINATOR>
""")

  def testrPrintObject(self):
    self.Print(style='object', resource=self._RESOURCE_OBJECT)
    self.AssertOutputEquals("""\
<Ṁöë>=".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW"
<Larry>="ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ."
<Shemp>="Hey, Ṁöë! Hey, Larry!"
<Curly>="Søɨŧɇnłɏ!"
<Joe>="Oh, cut it ouuuuuut!"
<Curly Joe>="One of these days, you're gonna poke my eyes out."
""")


if __name__ == '__main__':
  resource_printer_test_base.main()
