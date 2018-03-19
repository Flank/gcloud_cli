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

"""Unit tests for the resource_filter module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_filter
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_projection_parser
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.util import times
from tests.lib import sdk_test_base
from tests.lib import subtests
from tests.lib import test_case


class Resource(object):

  def __init__(self):
    self.compound = self.Compound(self.CompoundNumber(),
                                  self.CompoundString())
    self.t = 1
    self.false = False
    self.floating = 3.14
    self.integer = 2
    self.logical = 'abc or xyz'
    self.lower = 'string'
    self.mixed = 'StrIng'
    self.none = None
    self.subject = 'abcpdqxyz'
    self.timestamp = '2016-08-11T12:34:56.789-04:00'
    self.true = True
    self.upper = 'STRING'
    self.double = 'a" "z'
    self.single = "a' 'z"

  class Compound(object):

    def __init__(self, number, string):
      self.number = number
      self.string = string

  class CompoundNumber(object):

    def __init__(self):
      self.array = [1, 2, 3.14]
      self.dictionary = {1: 'abc', 2: 'Def', 3.14: 'ghI'}
      self.value = 1234

  class CompoundString(object):

    def __init__(self):
      self.array = ['abc', 'Def', 'ghI', 'JKL']
      self.dictionary = {'abc': 1, 'Def': 2, 'ghI': 3.14}
      self.value = 'Compound String'


class ResourceFilterTest(subtests.Base, sdk_test_base.WithLogCapture):

  _ALIASES = {
      'i': resource_lex.Lexer('integer').Key(),
      'v': resource_lex.Lexer('compound.string.value').Key(),
  }

  def SetUp(self):
    self.resource = None
    self.StartObjectPatch(times, 'Now', return_value=times.ParseDateTime(
        '2016-11-11T12:34:56.789-04:00'))

  def SetResource(self, resource):
    """Sets the resource for the next set of subtests."""
    self.resource = resource

  def RunSubTest(self, expression, deprecated=False):

    def _Error(resource=None):
      """Always raises ValueError for testing.

      Args:
        resource: The resource object.

      Raises:
        ValueError: Always for testing.
      """
      _ = resource
      raise ValueError('Transform function value error.')

    default_symbols = {
        'date': resource_transform.TransformDate,
        'len': lambda r, x=None: resource_transform.TransformLen(x or r),
    }
    defaults = resource_projection_parser.Parse(
        '(compound.string:alias=s, floating:alias=f)',
        symbols=default_symbols,
        aliases=self._ALIASES)
    symbols = {
        'error': _Error,  # 'error' not a magic name.
    }
    defaults = resource_projection_spec.ProjectionSpec(
        defaults=defaults, symbols=symbols)
    evaluate = resource_filter.Compile(expression, defaults=defaults).Evaluate
    if isinstance(self.resource, list):
      results = []
      for r in self.resource:
        results.append(evaluate(r))
      return results
    actual = evaluate(self.resource)
    err = self.GetErr()
    self.ClearErr()
    warning = ('WARNING: --filter : operator evaluation is changing for '
               'consistency across Google APIs.')
    if err and not deprecated:
      self.fail('Error [%s] not expected.' % err)
    elif not err and deprecated:
      self.fail('Warning [%s] expected.' % warning)
    elif err and deprecated and warning not in err:
      self.fail('Warning [%s] expected but got [%s].' % (warning, err))
    return actual

  def testResourceFilter(self):

    def T(expected, expression, deprecated=False, exception=None):
      if exception is None and expected is None:
        exception = resource_exceptions.ExpressionSyntaxError
      self.Run(expected, expression, deprecated=deprecated, depth=2,
               exception=exception)

    self.SetResource(Resource())

    # empty expression

    T(True, '')

    # integer terms

    T(False, 'integer:3')
    T(True, 'integer:2')
    T(False, 'integer:1')
    T(False, 'integer:-1')
    T(True, '-integer:3')
    T(False, '-integer:2')
    T(True, '-integer:1')
    T(True, '-integer:-1')
    T(True, 'NOT integer:3')
    T(False, 'NOT integer:2')
    T(True, 'NOT integer:1')
    T(True, 'NOT integer:-1')

    T(False, 'integer=3')
    T(True, 'integer=2')
    T(False, 'integer=1')
    T(False, 'integer=-1')
    T(True, '-integer=3')
    T(False, '-integer=2')
    T(True, '-integer=1')
    T(True, '-integer=-1')
    T(True, 'NOT integer=3')
    T(False, 'NOT integer=2')
    T(True, 'NOT integer=1')
    T(True, 'NOT integer=-1')

    T(True, 'integer<3')
    T(False, 'integer<2')
    T(False, 'integer<1')
    T(False, 'integer<-1')
    T(False, '-integer<3')
    T(True, '-integer<2')
    T(True, '-integer<1')
    T(True, '-integer<-1')
    T(False, 'NOT integer<3')
    T(True, 'NOT integer<2')
    T(True, 'NOT integer<1')
    T(True, 'NOT integer<-1')

    T(True, 'integer<=3')
    T(True, 'integer<=2')
    T(False, 'integer<=1')
    T(False, 'integer<=-1')
    T(False, '-integer<=3')
    T(False, '-integer<=2')
    T(True, '-integer<=1')
    T(True, '-integer<=-1')
    T(False, 'NOT integer<=3')
    T(False, 'NOT integer<=2')
    T(True, 'NOT integer<=1')
    T(True, 'NOT integer<=-1')

    T(False, 'integer>=3')
    T(True, 'integer>=2')
    T(True, 'integer>=1')
    T(True, 'integer>=-1')
    T(True, '-integer>=3')
    T(False, '-integer>=2')
    T(False, '-integer>=1')
    T(False, '-integer>=-1')
    T(True, 'NOT integer>=3')
    T(False, 'NOT integer>=2')
    T(False, 'NOT integer>=1')
    T(False, 'NOT integer>=-1')

    T(False, 'integer>3')
    T(False, 'integer>2')
    T(True, 'integer>1')
    T(True, 'integer>-1')
    T(True, '-integer>3')
    T(True, '-integer>2')
    T(False, '-integer>1')
    T(False, '-integer>-1')
    T(True, 'NOT integer>3')
    T(True, 'NOT integer>2')
    T(False, 'NOT integer>1')
    T(False, 'NOT integer>-1')

    T(True, 'integer!=3')
    T(False, 'integer!=2')
    T(True, 'integer!=1')
    T(True, 'integer!=-1')
    T(False, '-integer!=3')
    T(True, '-integer!=2')
    T(False, '-integer!=1')
    T(False, '-integer!=-1')
    T(False, 'NOT integer!=3')
    T(True, 'NOT integer!=2')
    T(False, 'NOT integer!=1')
    T(False, 'NOT integer!=-1')

    # numeric operand mismatches

    T(False, 'string > 1.23')
    T(True, 'integer > 1.23')

    # Boolean terms

    T(False, 'none:0')
    T(False, 'none:False')
    T(False, 'none:false')
    T(False, 'none:1')
    T(False, 'none:True')
    T(False, 'none:true')

    T(True, 'false:0')
    T(True, 'false:False')
    T(True, 'false:false')
    T(False, 'false:1')
    T(False, 'false:True')
    T(False, 'false:true')

    T(False, 'true:0')
    T(False, 'true:False')
    T(False, 'true:false')
    T(True, 'true:1')
    T(True, 'true:True')
    T(True, 'true:true')

    T(False, 'none=0')
    T(False, 'none=False')
    T(False, 'none=false')
    T(False, 'none=1')
    T(False, 'none=True')
    T(False, 'none=true')

    T(True, 'false=0')
    T(True, 'false=False')
    T(True, 'false=false')
    T(False, 'false=1')
    T(False, 'false=True')
    T(False, 'false=true')

    T(False, 'true=0')
    T(False, 'true=False')
    T(False, 'true=false')
    T(True, 'true=1')
    T(True, 'true=True')
    T(True, 'true=true')

    # case sensitive equality

    T(False, 'lower=ing')
    T(False, 'lower=Str')
    T(True, 'lower=string')
    T(True, 'lower=String')
    T(True, 'lower=STRING')

    T(False, 'mixed=ing')
    T(False, 'mixed=Str')
    T(True, 'mixed=String')
    T(True, 'mixed=StrIng')
    T(True, 'mixed=STRING')

    T(False, 'upper=ing')
    T(False, 'upper=Str')
    T(True, 'upper=string')
    T(True, 'upper=String')
    T(True, 'upper=STRING')

    T(False, 'undefined=String')
    T(False, 'undefined=STRING')
    T(False, 'undefined=string')
    T(False, 'undefined=Str')
    T(False, 'undefined=ing')

    # case insensitive : string match

    T(True, 'lower:String')
    T(True, 'lower:STRING')
    T(True, 'lower:string')
    T(True, 'lower:Str', deprecated=True)
    T(True, 'lower:ing', deprecated=True)

    T(True, 'mixed:STRING')
    T(True, 'mixed:Str', deprecated=True)
    T(True, 'mixed:String')
    T(True, 'mixed:ing', deprecated=True)
    T(True, 'mixed:string')

    T(True, 'upper:STRING')
    T(True, 'upper:Str', deprecated=True)
    T(True, 'upper:String')
    T(True, 'upper:ing', deprecated=True)
    T(True, 'upper:string')

    T(False, 'undefined:STRING')
    T(False, 'undefined:Str')
    T(False, 'undefined:String')
    T(False, 'undefined:ing')
    T(False, 'undefined:string')

    # case insensitive : string comma separated list match

    T(True, 'lower:(string, error)')
    T(True, 'lower:(String, Error)')
    T(False, 'lower:(no, match)')
    T(False, 'lower:(No, Match)')

    T(True, 'mixed:(string, error)')
    T(True, 'mixed:(String, Error)')
    T(False, 'mixed:(no, match)')
    T(False, 'mixed:(No, Match)')

    T(True, 'upper:(string, error)')
    T(True, 'upper:(String, Error)')
    T(False, 'upper:(no, match)')
    T(False, 'upper:(No, Match)')

    T(False, 'undefined:(string, error)')
    T(False, 'undefined:(String, Error)')
    T(False, 'undefined:(no, match)')
    T(False, 'undefined:(No, Match)')

    # case insensitive : string space separated list match

    T(True, 'lower:(string error)')
    T(True, 'lower:(String Error)')
    T(False, 'lower:(no match)')
    T(False, 'lower:(No Match)')

    T(True, 'mixed:(string error)')
    T(True, 'mixed:(String Error)')
    T(False, 'mixed:(no match)')
    T(False, 'mixed:(No Match)')

    T(True, 'upper:(string error)')
    T(True, 'upper:(String Error)')
    T(False, 'upper:(no match)')
    T(False, 'upper:(No Match)')

    T(False, 'undefined:(string error)')
    T(False, 'undefined:(String Error)')
    T(False, 'undefined:(no match)')
    T(False, 'undefined:(No Match)')

    # case insensitive : string OR separated list match

    T(True, 'lower:(string OR error)')
    T(True, 'lower:(String OR Error)')
    T(False, 'lower:(no OR match)')
    T(False, 'lower:(No OR Match)')

    T(True, 'mixed:(string OR error)')
    T(True, 'mixed:(String OR Error)')
    T(False, 'mixed:(no OR match)')
    T(False, 'mixed:(No OR Match)')

    T(True, 'upper:(string OR error)')
    T(True, 'upper:(String OR Error)')
    T(False, 'upper:(no OR match)')
    T(False, 'upper:(No OR Match)')

    T(False, 'logical:(string OR error)')
    T(False, 'logical:(String OR Error)')
    T(True, 'logical:(abc OR XYZ)')
    T(True, 'logical:(ABC OR xyz)')
    T(True, 'logical:(a* OR *Z)')
    T(False, 'logical:(aaa OR X*)', deprecated=True)
    T(True, 'logical:(aaa OR *Z)', deprecated=True)

    T(False, 'undefined:(string OR error)')
    T(False, 'undefined:(String OR Error)')
    T(False, 'undefined:(no OR match)')
    T(False, 'undefined:(No OR Match)')

    # anchored prefix/suffix case insensitive : string match

    T(True, 'lower:*')
    T(True, 'lower:*ing', deprecated=True)
    T(True, 'lower:S*ing', deprecated=True)
    T(True, 'lower:STR*ING', deprecated=True)
    T(True, 'lower:Str*ing', deprecated=True)
    T(True, 'lower:s*g', deprecated=True)
    T(True, 'lower:str*')

    T(True, 'mixed:*')
    T(True, 'mixed:*ing', deprecated=True)
    T(True, 'mixed:S*ing', deprecated=True)
    T(True, 'mixed:STR*ING', deprecated=True)
    T(True, 'mixed:Str*ing', deprecated=True)
    T(True, 'mixed:s*g', deprecated=True)
    T(True, 'mixed:str*')

    T(True, 'upper:*')
    T(True, 'upper:*ing', deprecated=True)
    T(True, 'upper:S*ing', deprecated=True)
    T(True, 'upper:STR*ING', deprecated=True)
    T(True, 'upper:Str*ing', deprecated=True)
    T(True, 'upper:s*g', deprecated=True)
    T(True, 'upper:str*')

    T(False, 'undefined:*')
    T(False, 'undefined:*ing')
    T(False, 'undefined:STR*ING')
    T(False, 'undefined:Str*ing')
    T(False, 'undefined:s*g')
    T(False, 'undefined:str*')

    # _Has() docstring examples

    T(True, 'subject:abc*xyz', deprecated=True)
    T(True, 'subject:abc*')
    T(True, 'subject:abc', deprecated=True)
    T(False, 'subject:*abc')
    T(False, 'subject:pdq*')
    T(True, 'subject:pdq', deprecated=True)
    T(False, 'subject:*pdq')
    T(True, 'subject:*')
    T(False, 'none:*')
    T(False, 'subject:xyz*')
    T(True, 'subject:xyz', deprecated=True)
    T(True, 'subject:*xyz', deprecated=True)

    # ~ regex match where ^ matches start of value, $ matches end of value

    T(True, 'lower~[a-z]')
    T(False, 'lower~[A-Z]')
    T(True, 'lower~ing')
    T(True, 'lower~ing$')
    T(True, 'lower~s.*g')
    T(True, 'lower~^s.*g')
    T(True, 'lower~^s.*g$')
    T(True, 'lower~s.*ing')
    T(True, 'lower~str')
    T(True, 'lower~^str')
    T(True, 'lower~st.*ng')
    T(True, 'lower~^st.*ng')
    T(True, 'lower~st.*ng$')
    T(True, 'lower~^st.*ng$')
    T(False, 'lower~STRING')
    T(False, 'lower~^STRING')
    T(False, 'lower~STRING$')
    T(False, 'lower~^STRING$')
    T(True, 'f~3.14')

    # !~ regex not match where ^ matches start of value, $ matches end of value

    T(False, 'lower!~[a-z]')
    T(True, 'lower!~[A-Z]')
    T(False, 'lower!~ing')
    T(False, 'lower!~ing$')
    T(False, 'lower!~s.*g')
    T(False, 'lower!~^s.*g')
    T(False, 'lower!~^s.*g$')
    T(False, 'lower!~s.*ing')
    T(False, 'lower!~str')
    T(False, 'lower!~^str')
    T(False, 'lower!~st.*ng')
    T(False, 'lower!~^st.*ng')
    T(False, 'lower!~st.*ng$')
    T(False, 'lower!~^st.*ng$')
    T(True, 'lower!~STRING')
    T(True, 'lower!~^STRING')
    T(True, 'lower!~STRING$')
    T(True, 'lower!~^STRING$')

    # "..." string operands for :

    T(True, 'lower:"STRING"')
    T(True, 'lower:"Str"', deprecated=True)
    T(True, 'lower:"Str*"')
    T(True, 'lower:"ri"', deprecated=True)
    T(True, 'lower:"rI"', deprecated=True)
    T(True, 'lower:"StrIng"')
    T(True, 'lower:"String"')
    T(True, 'lower:"ing"', deprecated=True)
    T(True, 'lower:"*ing"', deprecated=True)
    T(True, 'lower:"string"')

    T(True, 'mixed:"STRING"')
    T(True, 'mixed:"Str"', deprecated=True)
    T(True, 'mixed:"Str*"')
    T(True, 'mixed:"StrIng"')
    T(True, 'mixed:"String"')
    T(True, 'mixed:"ing"', deprecated=True)
    T(True, 'mixed:"*ing"', deprecated=True)

    T(True, 'upper:"STRING"')
    T(True, 'upper:"Str"', deprecated=True)
    T(True, 'upper:"Str*"')
    T(True, 'upper:"String"')
    T(True, 'upper:"ing"', deprecated=True)
    T(True, 'upper:"*ing"', deprecated=True)
    T(True, 'upper:"string"')

    T(False, 'undefined:"STRING"')
    T(False, 'undefined:"Str"')
    T(False, 'undefined:"Str"')
    T(False, 'undefined:"String"')
    T(False, 'undefined:"ing"')
    T(False, 'undefined:"ing"')
    T(False, 'undefined:"string"')

    T(True, 'compound.string.value:"Compound String"')
    T(True, 'compound.string.value:"Compound string"')
    T(True, 'compound.string.value:"c*g"', deprecated=True)
    T(True, 'compound.string.value:"compound string"')

    # "..." string operands for =

    T(False, 'lower="ing"')
    T(False, 'lower="str"')
    T(False, 'lower="Str"')
    T(True, 'lower="string"')
    T(True, 'lower="String"')
    T(True, 'lower="StrIng"')
    T(True, 'lower="STRING"')

    T(False, 'mixed="ing"')
    T(False, 'mixed="Ing"')
    T(False, 'mixed="Str"')
    T(True, 'mixed="String"')
    T(True, 'mixed="StrIng"')
    T(True, 'mixed="STRING"')

    T(False, 'upper="ing"')
    T(False, 'upper="Str"')
    T(True, 'upper="string"')
    T(True, 'upper="String"')
    T(True, 'upper="StrIng"')
    T(True, 'upper="STRING"')

    T(False, 'undefined="ing"')
    T(False, 'undefined="Str"')
    T(False, 'undefined="string"')
    T(False, 'undefined="String"')
    T(False, 'undefined="STRING"')

    T(True, 'compound.string.value="compound string"')
    T(True, 'compound.string.value="Compound string"')
    T(True, 'compound.string.value="Compound String"')

    # (number, string) X (list, dict) : tests

    T(True, 'compound.number.array:1')
    T(True, 'compound.number.array:3.14')
    T(False, 'compound.number.array:5')
    T(False, 'compound.number.array:abc')
    T(False, 'compound.number.array:Abc')

    T(True, 'compound.number.dictionary:1')
    T(True, 'compound.number.dictionary:3.14')
    T(False, 'compound.number.dictionary:5')
    T(True, 'compound.number.dictionary:Abc')
    T(True, 'compound.number.dictionary:abc')

    T(False, 'compound.string.array:1')
    T(False, 'compound.string.array:3.14')
    T(False, 'compound.string.array:5')
    T(True, 'compound.string.array:abc')
    T(True, 'compound.string.array:Abc')
    T(True, 'compound.string.array:ab', deprecated=True)
    T(True, 'compound.string.array:b', deprecated=True)
    T(True, 'compound.string.array:b', deprecated=True)
    T(True, 'compound.string.array:ab*')
    T(True, 'compound.string.array:*bC', deprecated=True)

    T(True, 'compound.string.dictionary:3.14')
    T(False, 'compound.string.dictionary:5')
    T(True, 'compound.string.dictionary:Abc')
    T(True, 'compound.string.dictionary:abc')
    T(True, 'compound.string.dictionary:ab', deprecated=True)
    T(True, 'compound.string.dictionary:ab*')

    # (...) set operands for :

    T(True, 'compound.string.array:(ab)', deprecated=True)
    T(True, 'compound.string.array:(ab*)')
    T(True, 'compound.string.dictionary:(b)', deprecated=True)
    T(True, 'compound.string.dictionary:(ab*)')

    T(True, 'compound.number.array:(1)')
    T(True, 'compound.number.array:(aaa,1,zzz)')
    T(True, 'compound.number.array:(aaa, 1, zzz)')
    T(True, 'compound.number.array:(aaa 1 zzz)')
    T(True, 'compound.number.array:(aaa\n1\nzzz)')
    T(True, 'compound.number.array:(  aaa  1  zzz )')
    T(False, 'compound.number.array:(  aaa  5  zzz )')
    T(False, 'compound.number.array:(  aaa  zzz )')

    T(True, 'compound.number.dictionary:(1)')
    T(True, 'compound.number.dictionary:(aaa,1,zzz)')
    T(True, 'compound.number.dictionary:(aaa, 1, zzz)')
    T(True, 'compound.number.dictionary:(aaa 1 zzz)')
    T(True, 'compound.number.dictionary:(aaa\n1\nzzz)')
    T(True, 'compound.number.dictionary:(  aaa  1  zzz )')
    T(False, 'compound.number.dictionary:(  aaa  5  zzz )')
    T(False, 'compound.number.dictionary:(  aaa  zzz )')

    T(True, 'compound.string.array:(abc)')
    T(True, 'compound.string.array:(aaa,abc,zzz)')
    T(True, 'compound.string.array:(aaa, abc, zzz)')
    T(True, 'compound.string.array:(aaa abc zzz)')
    T(True, 'compound.string.array:(aaa\nabc\nzzz)')
    T(True, 'compound.string.array:(  aaa  abc  zzz )')
    T(False, 'compound.string.array:(  aaa  zzz )')

    T(True, 'compound.string.dictionary:(abc)')
    T(True, 'compound.string.dictionary:(aaa,abc,zzz)')
    T(True, 'compound.string.dictionary:(aaa, abc, zzz)')
    T(True, 'compound.string.dictionary:(aaa abc zzz)')
    T(True, 'compound.string.dictionary:(aaa\nabc\nzzz)')
    T(True, 'compound.string.dictionary:(  aaa  abc  zzz )')
    T(False, 'compound.string.dictionary:(  aaa  zzz )')

    # string X (list, dict) = tests

    T(False, 'compound.string.array=ab')
    T(False, 'compound.string.dictionary=ab')

    # (...) set operands for =

    T(False, 'compound.string.array=(ab)')
    T(False, 'compound.string.dictionary=(ab)')

    T(True, 'compound.number.array=(1)')
    T(True, 'compound.number.array=(aaa,1,zzz)')
    T(True, 'compound.number.array=(aaa, 1, zzz)')
    T(True, 'compound.number.array=(aaa 1 zzz)')
    T(True, 'compound.number.array=(aaa\n1\nzzz)')
    T(True, 'compound.number.array=(  aaa  1  zzz )')
    T(False, 'compound.number.array=(3)', deprecated=True)
    T(False, 'compound.number.array=(aaa,3,zzz)', deprecated=True)
    T(False, 'compound.number.array=(aaa, 3, zzz)', deprecated=True)
    T(False, 'compound.number.array=(aaa 3 zzz)', deprecated=True)
    T(False, 'compound.number.array=(aaa\n3\nzzz)', deprecated=True)
    T(False, 'compound.number.array=(  aaa  3  zzz )', deprecated=True)
    T(False, 'compound.number.array=(  aaa  5  zzz )')
    T(False, 'compound.number.array=(  aaa  zzz )')

    T(True, 'compound.number.dictionary=(1)')
    T(True, 'compound.number.dictionary=(aaa,1,zzz)')
    T(True, 'compound.number.dictionary=(aaa, 1, zzz)')
    T(True, 'compound.number.dictionary=(aaa 1 zzz)')
    T(True, 'compound.number.dictionary=(aaa\n1\nzzz)')
    T(True, 'compound.number.dictionary=(  aaa  1  zzz )')
    T(False, 'compound.number.dictionary=(3)', deprecated=True)
    T(False, 'compound.number.dictionary=(aaa,3,zzz)', deprecated=True)
    T(False, 'compound.number.dictionary=(aaa, 3, zzz)', deprecated=True)
    T(False, 'compound.number.dictionary=(aaa 3 zzz)', deprecated=True)
    T(False, 'compound.number.dictionary=(aaa\n3\nzzz)', deprecated=True)
    T(False, 'compound.number.dictionary=(  aaa  3  zzz )', deprecated=True)
    T(False, 'compound.number.dictionary=(  aaa  5  zzz )')
    T(False, 'compound.number.dictionary=(  aaa  zzz )')

    T(True, 'compound.string.array=(abc)')
    T(True, 'compound.string.array=(aaa,abc,zzz)')
    T(True, 'compound.string.array=(aaa, abc, zzz)')
    T(True, 'compound.string.array=(aaa abc zzz)')
    T(True, 'compound.string.array=(aaa\nabc\nzzz)')
    T(True, 'compound.string.array=(  aaa  abc  zzz )')
    T(False, 'compound.string.array=(ab)')
    T(False, 'compound.string.array=(aaa,ab,zzz)')
    T(False, 'compound.string.array=(aaa, ab, zzz)')
    T(False, 'compound.string.array=(aaa ab zzz)')
    T(False, 'compound.string.array=(aaa\nab\nzzz)')
    T(False, 'compound.string.array=(  aaa  ab  zzz )')
    T(False, 'compound.string.array=(  aaa  zzz )')

    T(True, 'compound.string.dictionary=(abc)')
    T(True, 'compound.string.dictionary=(aaa,abc,zzz)')
    T(True, 'compound.string.dictionary=(aaa, abc, zzz)')
    T(True, 'compound.string.dictionary=(aaa abc zzz)')
    T(True, 'compound.string.dictionary=(aaa\nabc\nzzz)')
    T(True, 'compound.string.dictionary=(  aaa  abc  zzz )')
    T(False, 'compound.string.dictionary=(ab)')
    T(False, 'compound.string.dictionary=(aaa,ab,zzz)')
    T(False, 'compound.string.dictionary=(aaa, ab, zzz)')
    T(False, 'compound.string.dictionary=(aaa ab zzz)')
    T(False, 'compound.string.dictionary=(aaa\nab\nzzz)')
    T(False, 'compound.string.dictionary=(  aaa  ab  zzz )')
    T(False, 'compound.string.dictionary=(  aaa  zzz )')

    # AND precedence over OR - see the OnePlatform comment below

    # OR precedence over adjacent conjunction

    T(False, 'integer:0 integer:0 OR integer:0')
    T(False, '(integer:0 integer:0) OR integer:0')
    T(False, 'integer:0 AND (integer:0 OR integer:0)')

    T(False, 'integer:0 integer:0 OR integer:2')
    T(True, '(integer:0 integer:0) OR integer:2')
    T(False, 'integer:0 AND (integer:0 OR integer:2)')

    T(False, 'integer:0 integer:2 OR integer:0')
    T(False, '(integer:0 integer:2) OR integer:0')
    T(False, 'integer:0 AND (integer:2 OR integer:0)')

    T(False, 'integer:0 integer:2 OR integer:2')
    T(True, '(integer:0 integer:2) OR integer:2')
    T(False, 'integer:0 AND (integer:2 OR integer:2)')

    T(False, 'integer:2 integer:0 OR integer:0')
    T(False, '(integer:2 integer:0) OR integer:0')
    T(False, 'integer:2 AND (integer:0 OR integer:0)')

    T(True, 'integer:2 integer:0 OR integer:2')
    T(True, '(integer:2 integer:0) OR integer:2')
    T(True, 'integer:2 AND (integer:0 OR integer:2)')

    T(True, 'integer:2 integer:2 OR integer:0')
    T(True, '(integer:2 integer:2) OR integer:0')
    T(True, 'integer:2 AND (integer:2 OR integer:0)')

    T(True, 'integer:2 integer:2 OR integer:2')
    T(True, '(integer:2 integer:2) OR integer:2')
    T(True, 'integer:2 AND (integer:2 OR integer:2)')

    T(False, 'integer:0 OR integer:0 integer:0')
    T(False, 'integer:0 OR (integer:0 integer:0)')
    T(False, '(integer:0 OR integer:0) AND integer:0')

    T(False, 'integer:0 OR integer:0 integer:2')
    T(False, 'integer:0 OR (integer:0 integer:2)')
    T(False, '(integer:0 OR integer:0) AND integer:2')

    T(False, 'integer:0 OR integer:2 integer:0')
    T(False, 'integer:0 OR (integer:2 integer:0)')
    T(False, '(integer:0 OR integer:2) AND integer:0')

    T(True, 'integer:0 OR integer:2 integer:2')
    T(True, 'integer:0 OR (integer:2 integer:2)')
    T(True, '(integer:0 OR integer:2) AND integer:2')

    T(False, 'integer:2 OR integer:0 integer:0')
    T(True, 'integer:2 OR (integer:0 integer:0)')
    T(False, '(integer:2 OR integer:0) AND integer:0')

    T(True, 'integer:2 OR integer:0 integer:2')
    T(True, 'integer:2 OR (integer:0 integer:2)')
    T(True, '(integer:2 OR integer:0) AND integer:2')

    T(False, 'integer:2 OR integer:2 integer:0')
    T(True, 'integer:2 OR (integer:2 integer:0)')
    T(False, '(integer:2 OR integer:2) AND integer:0')

    T(True, 'integer:2 OR integer:2 integer:2')
    T(True, 'integer:2 OR (integer:2 integer:2)')
    T(True, '(integer:2 OR integer:2) AND integer:2')

    T(True, 'integer=2 OR floating=3.14')
    T(True, 'integer=2 floating=3.14')
    T(True, 'integer=2 ( floating=3.14 )')
    T(True, '( integer=2 ) floating=3.14')
    T(True, '( integer=2 floating=3.14 )')

    # AND, NOT OR and (...) combinations

    T(True, 't:1 AND ( t:1 OR t:1 )')
    T(True, 't:1 AND ( t:1 OR t:0 )')
    T(True, 't:1 AND ( t:0 OR t:1 )')
    T(False, 't:1 AND ( t:0 OR t:0 )')
    T(False, 't:0 AND ( t:1 OR t:1 )')
    T(False, 't:0 AND ( t:1 OR t:0 )')
    T(False, 't:0 AND ( t:0 OR t:1 )')
    T(False, 't:0 AND ( t:0 OR t:0 )')

    T(True, '( t:1 OR t:1 ) AND t:1')
    T(True, '( t:0 OR t:1 ) AND t:1')
    T(False, '( t:1 OR t:1 ) AND t:0')
    T(False, '( t:0 OR t:1 ) AND t:0')
    T(True, '( t:1 OR t:0 ) AND t:1')
    T(False, '( t:0 OR t:0 ) AND t:1')
    T(False, '( t:1 OR t:0 ) AND t:0')
    T(False, '( t:0 OR t:0 ) AND t:0')

    T(False, 'NOT t:1 AND ( t:1 OR t:1 )')
    T(False, 'NOT t:1 AND ( t:1 OR t:0 )')
    T(False, 'NOT t:1 AND ( t:0 OR t:1 )')
    T(False, 'NOT t:1 AND ( t:0 OR t:0 )')
    T(True, 'NOT t:0 AND ( t:1 OR t:1 )')
    T(True, 'NOT t:0 AND ( t:1 OR t:0 )')
    T(True, 'NOT t:0 AND ( t:0 OR t:1 )')
    T(False, 'NOT t:0 AND ( t:0 OR t:0 )')

    T(False, 'NOT ( t:1 OR t:1 ) AND t:1')
    T(False, 'NOT ( t:0 OR t:1 ) AND t:1')
    T(False, 'NOT ( t:1 OR t:1 ) AND t:0')
    T(False, 'NOT ( t:0 OR t:1 ) AND t:0')
    T(False, 'NOT ( t:1 OR t:0 ) AND t:1')
    T(True, 'NOT ( t:0 OR t:0 ) AND t:1')
    T(False, 'NOT ( t:1 OR t:0 ) AND t:0')
    T(False, 'NOT ( t:0 OR t:0 ) AND t:0')

    # OnePlatform queries have non-standard OR >>> AND precedence. Cloud SDK
    # requires parentheses when AND and OR are combined to clarify user intent.

    # This group adds (...) to achieve standard AND/OR precedence.

    T(True, '(integer>0 AND floating>0) OR integer>0')
    T(True, '(integer>0 AND floating>0) OR integer<0')
    T(True, '(integer>0 AND floating<0) OR integer>0')
    T(False, '(integer>0 AND floating<0) OR integer<0')
    T(True, '(integer<0 AND floating>0) OR integer>0')
    T(False, '(integer<0 AND floating>0) OR integer<0')
    T(True, '(integer<0 AND floating<0) OR integer>0')
    T(False, '(integer<0 AND floating<0) OR integer<0')

    T(True, 'integer>0 OR (integer>0 AND floating>0)')
    T(True, 'integer<0 OR (integer>0 AND floating>0)')
    T(True, 'integer>0 OR (integer>0 AND floating<0)')
    T(False, 'integer<0 OR (integer>0 AND floating<0)')
    T(True, 'integer>0 OR (integer<0 AND floating>0)')
    T(False, 'integer<0 OR (integer<0 AND floating>0)')
    T(True, 'integer>0 OR (integer<0 AND floating<0)')
    T(False, 'integer<0 OR (integer<0 AND floating<0)')

    T(True, '(NOT integer>0 AND floating>0) OR integer>0')
    T(False, '(NOT integer>0 AND floating>0) OR integer<0')
    T(True, '(NOT integer>0 AND floating<0) OR integer>0')
    T(False, '(NOT integer>0 AND floating<0) OR integer<0')
    T(True, '(NOT integer<0 AND floating>0) OR integer>0')
    T(True, '(NOT integer<0 AND floating>0) OR integer<0')
    T(True, '(NOT integer<0 AND floating<0) OR integer>0')
    T(False, '(NOT integer<0 AND floating<0) OR integer<0')

    T(True, 'NOT integer>0 OR (integer>0 AND floating>0)')
    T(True, 'NOT integer<0 OR (integer>0 AND floating>0)')
    T(False, 'NOT integer>0 OR (integer>0 AND floating<0)')
    T(True, 'NOT integer<0 OR (integer>0 AND floating<0)')
    T(False, 'NOT integer>0 OR (integer<0 AND floating>0)')
    T(True, 'NOT integer<0 OR (integer<0 AND floating>0)')
    T(False, 'NOT integer>0 OR (integer<0 AND floating<0)')
    T(True, 'NOT integer<0 OR (integer<0 AND floating<0)')

    T(False, '(integer:0 AND integer:0) OR integer:0')
    T(True, '(integer:0 AND integer:0) OR integer:2')
    T(False, '(integer:0 AND integer:2) OR integer:0')
    T(True, '(integer:0 AND integer:2) OR integer:2')
    T(False, '(integer:2 AND integer:0) OR integer:0')

    T(True, '(integer:2 AND integer:0) OR integer:2')
    T(True, '(integer:2 AND integer:2) OR integer:0')
    T(True, '(integer:2 AND integer:2) OR integer:2')

    T(False, 'integer:0 OR (integer:0 AND integer:0)')
    T(False, 'integer:0 OR (integer:0 AND integer:2)')
    T(False, 'integer:0 OR (integer:2 AND integer:0)')

    T(True, 'integer:0 OR (integer:2 AND integer:2)')
    T(True, 'integer:2 OR (integer:0 AND integer:0)')
    T(True, 'integer:2 OR (integer:0 AND integer:2)')
    T(True, 'integer:2 OR (integer:2 AND integer:0)')
    T(True, 'integer:2 OR (integer:2 AND integer:2)')

    # This group checks the AND/OR combination detection.

    T(None, 'integer>0 AND floating>0 OR integer>0')
    T(None, 'integer>0 AND floating>0 OR integer<0')
    T(None, 'integer>0 AND floating<0 OR integer>0')
    T(None, 'integer>0 AND floating<0 OR integer<0')
    T(None, 'integer<0 AND floating>0 OR integer>0')
    T(None, 'integer<0 AND floating>0 OR integer<0')
    T(None, 'integer<0 AND floating<0 OR integer>0')
    T(None, 'integer<0 AND floating<0 OR integer<0')

    T(None, 'integer>0 OR integer>0 AND floating>0')
    T(None, 'integer<0 OR integer>0 AND floating>0')
    T(None, 'integer>0 OR integer>0 AND floating<0')
    T(None, 'integer<0 OR integer>0 AND floating<0')
    T(None, 'integer>0 OR integer<0 AND floating>0')
    T(None, 'integer<0 OR integer<0 AND floating>0')
    T(None, 'integer>0 OR integer<0 AND floating<0')
    T(None, 'integer<0 OR integer<0 AND floating<0')

    T(None, 'NOT integer>0 AND floating>0 OR integer>0')
    T(None, 'NOT integer>0 AND floating>0 OR integer<0')
    T(None, 'NOT integer>0 AND floating<0 OR integer>0')
    T(None, 'NOT integer>0 AND floating<0 OR integer<0')
    T(None, 'NOT integer<0 AND floating>0 OR integer>0')
    T(None, 'NOT integer<0 AND floating>0 OR integer<0')
    T(None, 'NOT integer<0 AND floating<0 OR integer>0')
    T(None, 'NOT integer<0 AND floating<0 OR integer<0')

    T(None, 'NOT integer>0 OR integer>0 AND floating>0')
    T(None, 'NOT integer<0 OR integer>0 AND floating>0')
    T(None, 'NOT integer>0 OR integer>0 AND floating<0')
    T(None, 'NOT integer<0 OR integer>0 AND floating<0')
    T(None, 'NOT integer>0 OR integer<0 AND floating>0')
    T(None, 'NOT integer<0 OR integer<0 AND floating>0')
    T(None, 'NOT integer>0 OR integer<0 AND floating<0')
    T(None, 'NOT integer<0 OR integer<0 AND floating<0')

    T(None, 'integer:0 AND integer:0 OR integer:0')
    T(None, 'integer:0 AND integer:0 OR integer:2')
    T(None, 'integer:0 AND integer:2 OR integer:0')
    T(None, 'integer:0 AND integer:2 OR integer:2')
    T(None, 'integer:2 AND integer:0 OR integer:0')
    T(None, 'integer:2 AND integer:0 OR integer:2')
    T(None, 'integer:2 AND integer:2 OR integer:0')
    T(None, 'integer:2 AND integer:2 OR integer:2')
    T(None, 'integer:0 OR integer:0 AND integer:0')
    T(None, 'integer:0 OR integer:0 AND integer:2')
    T(None, 'integer:0 OR integer:2 AND integer:0')
    T(None, 'integer:0 OR integer:2 AND integer:2')
    T(None, 'integer:2 OR integer:0 AND integer:0')
    T(None, 'integer:2 OR integer:0 AND integer:2')
    T(None, 'integer:2 OR integer:2 AND integer:0')
    T(None, 'integer:2 OR integer:2 AND integer:2')

    # > 1 of the same operator for off-by-1 grammar production bugs

    T(False, 'integer:1 AND integer:2 AND integer:3')
    T(True, 'integer>1 AND integer:2 AND integer<3')
    T(True, 'integer:1 OR integer:2 OR integer:3')
    T(False, 'integer<1 OR -integer:2 OR integer>3')

    # (...) nesting

    T(False, '( t:0 OR t:0 ) AND ( t:0 OR t:0 )')
    T(False, '( t:0 OR t:0 ) AND ( t:0 OR t:1 )')
    T(False, '( t:0 OR t:0 ) AND ( t:1 OR t:0 )')
    T(False, '( t:0 OR t:0 ) AND ( t:1 OR t:1 )')

    T(False, '( t:0 OR t:1 ) AND ( t:0 OR t:0 )')
    T(True, '( t:0 OR t:1 ) AND ( t:0 OR t:1 )')
    T(True, '( t:0 OR t:1 ) AND ( t:1 OR t:0 )')
    T(True, '( t:0 OR t:1 ) AND ( t:1 OR t:1 )')

    T(False, '( t:1 OR t:0 ) AND ( t:0 OR t:0 )')
    T(True, '( t:1 OR t:0 ) AND ( t:0 OR t:1 )')
    T(True, '( t:1 OR t:0 ) AND ( t:1 OR t:0 )')
    T(True, '( t:1 OR t:0 ) AND ( t:1 OR t:1 )')

    T(False, '( t:1 OR t:1 ) AND ( t:0 OR t:0 )')
    T(True, '( t:1 OR t:1 ) AND ( t:0 OR t:1 )')
    T(True, '( t:1 OR t:1 ) AND ( t:1 OR t:0 )')
    T(True, '( t:1 OR t:1 ) AND ( t:1 OR t:1 )')

    # space combinations

    T(True, 'integer:2')
    T(True, 'integer:2  ')
    T(True, 'integer:  2')
    T(True, 'integer  :2')
    T(True, '  integer:2')
    T(True, 'integer:  2  ')
    T(True, 'integer  :2  ')
    T(True, '  integer:2  ')
    T(True, 'integer  :  2')
    T(True, '  integer:  2')
    T(True, '  integer  :2')
    T(True, 'integer  :  2  ')
    T(True, '  integer:  2  ')
    T(True, ' integer :  2')
    T(True, '  integer  :  2  ')

    T(False, '-integer:2')
    T(False, '-integer:2  ')
    T(False, '-integer:  2')
    T(False, '-integer  :2')
    T(False, '-integer:  2  ')
    T(False, '-integer  :2  ')
    T(False, '-integer  :  2')
    T(False, '-integer  :  2  ')

    T(False, '  -integer:2')
    T(False, '  -integer:2  ')
    T(False, '  -integer:  2')
    T(False, '  -integer  :2')
    T(False, '  -integer:  2  ')
    T(False, '  -integer  :2  ')
    T(False, '  -integer  :  2')
    T(False, '  -integer  :  2  ')

    T(False, '-  integer:2')
    T(False, '-  integer:2  ')
    T(False, '-  integer:  2')
    T(False, '-  integer  :2')
    T(False, '-  integer:  2  ')
    T(False, '- integer :  2')
    T(False, '-  integer  :  2  ')
    T(False, '  -  integer:2')
    T(False, '  -  integer:2  ')
    T(False, '  -  integer:  2')
    T(False, '  -  integer  :2')
    T(False, '  -  integer:  2  ')
    T(False, '  - integer :  2')
    T(False, '  -  integer  :  2  ')
    T(False, '  -  integer:2')
    T(False, '  -  integer:2  ')
    T(False, '  -  integer:  2')
    T(False, '  -  integer  :2')
    T(False, '  -    integer:2')
    T(False, '  -  integer:  2  ')
    T(False, '  -  integer  :2  ')
    T(False, '  -    integer:2  ')
    T(False, '  -  integer  :  2')
    T(False, '  -    integer:  2')
    T(False, '  -    integer  :2')
    T(False, '  -  integer  :  2  ')
    T(False, '  -    integer:  2  ')
    T(False, '  -   integer :  2')
    T(False, '  -    integer  :  2  ')

    T(False, 'NOT  integer:2')
    T(False, 'NOT  integer:2  ')
    T(False, 'NOT  integer:  2')
    T(False, 'NOT  integer  :2')
    T(False, 'NOT    integer:2')
    T(False, 'NOT  integer:  2  ')
    T(False, 'NOT  integer  :2  ')
    T(False, 'NOT    integer:2  ')
    T(False, 'NOT  integer  :  2')
    T(False, 'NOT    integer:  2')
    T(False, 'NOT    integer  :2')
    T(False, 'NOT  integer  :  2  ')
    T(False, 'NOT    integer:  2  ')
    T(False, 'NOT   integer :  2')
    T(False, 'NOT    integer  :  2  ')

    T(False, '  NOT  integer:2')
    T(False, '  NOT  integer:2  ')
    T(False, '  NOT  integer:  2')
    T(False, '  NOT  integer  :2')
    T(False, '  NOT    integer:2')
    T(False, '  NOT  integer:  2  ')
    T(False, '  NOT  integer  :2  ')
    T(False, '  NOT    integer:2  ')
    T(False, '  NOT  integer  :  2')
    T(False, '  NOT    integer:  2')
    T(False, '  NOT    integer  :2')
    T(False, '  NOT  integer  :  2  ')
    T(False, '  NOT    integer:  2  ')
    T(False, '  NOT   integer :  2')
    T(False, '  NOT    integer  :  2  ')

    # key restrictions

    T(True, 'lower.len():6')
    T(True, 'lower.len()=6')
    T(False, 'lower.len()<6')
    T(None, 'integer.error()=0', exception=ValueError)

    # global function restrictions

    T(4, 'len(junk)')
    T(True, 'len(junk)=4')
    T(False, 'len')
    T(False, 'len (junk)')
    T(False, 'len OR (junk)')
    T(False, 'len (abc)')
    T(True, 'len OR (abc)')
    T(True, 'len OR abc')

    # global restrictions

    T(True, 'abc')
    T(True, 'pdq')
    T(True, 'xyz')
    T(False, 'aaa pdq zzz')
    T(True, 'aaa OR pdq OR zzz')
    T(False, 'aaa zzz')

    T(True, '(abc)')
    T(True, '(pdq)')
    T(True, 'abc (pdq)')
    T(True, '(abc) pdq')
    T(True, '(abc) (pdq)')

    # quotes

    T(True, 'lower="string"')
    T(True, 'double=a\\"" "\\"z')
    T(True, 'double=\'a" "z\'')
    T(True, "single=a\\'' '\\'z")
    T(True, "single=\"a' 'z\"")

    T(True, 'v~""')
    T(True, 'v~" "')

    T(True, 'v~"" OR i:1')
    T(True, 'v~"" OR i:2')
    T(False, 'v~"" AND i:1')
    T(True, 'v~"" AND i:2')
    T(True, 'v~"" NOT i:1')
    T(False, 'v~"" NOT i:2')

    T(True, 'i:1 OR v~""')
    T(True, 'i:2 OR v~""')
    T(False, 'i:1 AND v~""')
    T(True, 'i:2 AND v~""')
    T(True, 'NOT i:1 v~""')
    T(False, 'NOT i:2 v~""')

    T(True, 'v~" " OR i:1')
    T(True, 'v~" " OR i:2')
    T(False, 'v~" " AND i:1')
    T(True, 'v~" " AND i:2')
    T(True, 'v~" " NOT i:1')
    T(False, 'v~" " NOT i:2')

    # aliases

    T(True, 'i=2 OR f=3.14')
    T(True, 'i=2 f=3.14')
    T(True, 'i=2 ( f=3.14 )')
    T(True, '( i=2 ) f=3.14')
    T(True, '( i=2 f=3.14 )')

    T(False, 's.value="c*g"')
    T(True, 's.value:"c*g"', deprecated=True)
    T(False, 's.value="C*g"')
    T(True, 's.value:"C*g"', deprecated=True)
    T(True, 's.value="compound string"')
    T(True, 's.value:"compound string"')
    T(True, 's.value="Compound string"')
    T(True, 's.value:"Compound string"')
    T(True, 's.value="Compound String"')
    T(True, 's.value:"Compound String"')

    T(False, 'v="c*g"')
    T(True, 'v:"c*g"', deprecated=True)
    T(False, 'v="C*g"')
    T(True, 'v:"C*g"', deprecated=True)
    T(True, 'v="compound string"')
    T(True, 'v:"compound string"')
    T(True, 'v="Compound string"')
    T(True, 'v:"Compound string"')
    T(True, 'v="Compound String"')
    T(True, 'v:"Compound String"')

    # datetime

    T(True, 'timestamp.date(%Y)=2016')
    T(True, 'timestamp>"January 2016" timestamp<2016-09-01')
    T(True, 'timestamp<-p1m')
    T(False, 'timestamp<-p1y')

    # bad key OK global restriction

    T(True, '.')
    T(False, '..')
    T(False, '...')
    T(False, '.foo')
    T(False, 'foo.')
    T(False, 'foo..bar')

    # syntax errors

    T(None, 'AND')
    T(None, 'NOT')
    T(None, 'OR')
    T(None, '..len()')
    T(None, '.foo.len()')
    T(None, 'foo..len()')
    T(None, 'foo..bar.len()')
    T(None, 'foo.len(')
    T(None, 'foo.len)')
    T(None, '(')
    T(None, ')')
    T(None, ':')
    T(None, 'foo:')
    T(None, ':bar')
    T(None, ':.foo')
    T(None, 'foo> (')
    T(None, 'foo>bar (')
    T(None, '(')
    T(None, 'foo )')
    T(None, 'foo> )')
    T(None, 'foo>bar )')
    T(None, ')')
    T(None, '"')
    T(None, "'")
    T(None, 'foo:"bar')
    T(None, 'foo<(bar)')
    T(None, 'foo>(bar, baz)')

    T(None, 'a!b')
    T(None, 'a!!b')
    T(None, 'a!:b')
    T(None, 'a!<b')
    T(None, 'a!>b')
    T(None, 'a:!b')
    T(None, 'a::b')
    T(None, 'a:=b')
    T(None, 'a:<b')
    T(None, 'a:>b')
    T(None, 'a=!b')
    T(None, 'a=:b')
    T(None, 'a==b')
    T(None, 'a=<b')
    T(None, 'a=>b')
    T(None, 'a<!b')
    T(None, 'a<:b')
    T(None, 'a<<b')
    T(None, 'a<>b')
    T(None, 'a>!b')
    T(None, 'a>:b')
    T(None, 'a><b')
    T(None, 'a>>b')

    T(None, 'a:"b')
    T(None, "a:'b")
    T(None, 'a:\\"b"')

    T(None, '>1')
    T(None, 'NOT >1')
    T(None, 'a.foo()')

    T(None, 'a:b OR')
    T(None, 'a:b AND')
    T(None, 'a:b NOT')

    T(None, 'a: OR b:1')
    T(None, 'a: AND b:1')
    T(None, 'a: NOT b:1')

    T(None, 'a:b (')
    T(None, 'a:b )')
    T(None, 'a:b ()')

    T(None, 'v:"c*d s*g"')

    # ~ regex errors.

    T(None, 'v~*')
    T(None, 'v~)')

    # OnePlatform examples.

    self.SetResource({
        'foo': 'bar',
        'obj': {
            'x': 10,
            'y': 20,
        },
        'ids': [2, 3, 4],
        'required': True,
        'ptr': None,
        'members': [
            {
                'name': 'Joe',
                'age': 40,
            },
            {
                'name': 'Jane',
                'age': 50,
            },
        ],
    })

    T(True, 'foo = bar')
    T(True, 'obj.x = 10')
    T(True, 'required = true')
    T(True, 'ptr = null')
    T(True, 'members.name = Jane')
    T(True, 'members.age > 40')

    # Repeated value examples.

    self.SetResource([
        {
            'name': 'instance-1',
            'networkInterfaces': [
                {
                    'accessConfigs': [
                        {
                            'natIP': '23.251.133.75'
                        },
                        {
                            'natIP': '23.251.133.76'
                        },
                        {
                            'foo': 'bar'
                        }
                    ],
                    'networkIP': '10.0.0.1'
                },
                {
                    'accessConfigs': [
                        {
                            'natIP': '23.251.133.74'
                        }
                    ],
                    'networkIP': '10.0.0.2'
                },
                {
                    'bar': 'foo'
                }
            ]
        },
        {
            'name': 'instance-2',
            'networkInterfaces': [
                {
                    'accessConfigs': [
                        {
                            'natIP': '23.251.133.74'
                        }
                    ],
                    'networkIP': '10.0.0.2'
                },
                {
                    'foo': 'bar'
                }
            ]
        },
        {
            'name': 'instance-3',
            'networkInterfaces': [
                {
                    'accessConfigs': [
                        {
                            'natIP': '23.251.133.76'
                        }
                    ],
                    'networkIP': '10.0.0.3'
                }
            ]
        }
    ])

    T([False, False, False], 'networkInterfaces.len() > 3')
    T([False, False, False], 'networkInterfaces[3]:*')
    T([True, False, False], 'networkInterfaces.len() > 2')
    T([True, False, False], 'networkInterfaces[2]:*')
    T([True, True, False], 'networkInterfaces.len() > 1')
    T([True, True, False], 'networkInterfaces[1]:*')
    T([True, True, True], 'networkInterfaces.len() > 0')
    T([True, True, True], 'networkInterfaces[0]:*')


if __name__ == '__main__':
  test_case.main()
