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

"""Unit tests for the resource_expr module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_expr
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_transform
from tests.lib import sdk_test_base
from tests.lib import subtests
from tests.lib import test_case


R = {
    'e': None,
    'f': 3.14159265359,
    'i': 2,
    'j': 1,
    'l': [1, 'bcd', 3, 'fgh', 3.14, 'pi', 4, 'XYZ'],
    'm': 'StrIng',
    'n': False,
    'o': [{'name': 'Joe', 'age': 50}, {'name': 'Jan', 'age': 40}],
    's': 'string',
    't': (1, 'bcd', 3, 'fgh', 3.14, 'pi', 4, 'XYZ'),
    'u': 'STRING',
    'w': 'abc xyz',
    'y': True,
    'A': 'ABCGHIRSTXYZ',
    'D': {},
    'F': '3.14159265359',
    'L': [],
    'T': (),
    'date_aware': '2016-09-08T05:10:33.324-07:00',
    'date_naive': '2016-09-08 05:10:33.324',
    'TRUE': (),
}


def _Truthiness(value):
  return 'ýep' if value else 'ñope'


class ResourceExprTest(test_case.Base):

  def SetUp(self):
    self.backend = resource_expr.Backend()
    self.false = self.backend.ExprNOT(self.backend.ExprTRUE())
    self.true = self.backend.ExprTRUE()

  def Operand(self, value):
    """Returns an ExprOperand for value.

    Args:
      value: ExprOperand returned for this value.

    Returns:
      ExprOperand for value.
    """
    return self.backend.ExprOperand(value)

  # Logic operators.

  def testExprTRUE(self):
    expr = self.true
    self.assertTrue(expr.Evaluate(R))

  def testExprNOT0(self):
    expr = self.backend.ExprNOT(self.false)
    self.assertTrue(expr.Evaluate(R))

  def testExprNOT1(self):
    expr = self.backend.ExprNOT(self.true)
    self.assertFalse(expr.Evaluate(R))

  def testExprAND00(self):
    expr = self.backend.ExprAND(self.false, self.false)
    self.assertFalse(expr.Evaluate(R))

  def testExprAND01(self):
    expr = self.backend.ExprAND(self.false, self.true)
    self.assertFalse(expr.Evaluate(R))

  def testExprAND10(self):
    expr = self.backend.ExprAND(self.true, self.false)
    self.assertFalse(expr.Evaluate(R))

  def testExprAND11(self):
    expr = self.backend.ExprAND(self.true, self.true)
    self.assertTrue(expr.Evaluate(R))

  def testExprOR00(self):
    expr = self.backend.ExprOR(self.false, self.false)
    self.assertFalse(expr.Evaluate(R))

  def testExprOR01(self):
    expr = self.backend.ExprOR(self.false, self.true)
    self.assertTrue(expr.Evaluate(R))

  def testExprOxyzSTAR0(self):
    expr = self.backend.ExprOR(self.true, self.false)
    self.assertTrue(expr.Evaluate(R))

  def testExprOxyzSTAR1(self):
    expr = self.backend.ExprOR(self.true, self.true)
    self.assertTrue(expr.Evaluate(R))

  # Functions and operands.

  def testExprGlobal(self):
    call = resource_lex.MakeTransform(
        'len', lambda r, x: len(x), args=['12345'])
    expr = self.backend.ExprGlobal(call)
    self.assertEqual(5, expr.Evaluate(R))

  def testExprOperandStringValue(self):
    expr = self.Operand('abc')
    self.assertEqual('abc', expr.string_value)
    self.assertEqual(None, expr.numeric_value)

  def testExprOperandIntValue(self):
    expr = self.Operand('123')
    self.assertEqual('123', expr.string_value)
    self.assertEqual(123, expr.numeric_value)

  def testExprOperandFloatValue(self):
    expr = self.Operand('123.456')
    self.assertEqual('123.456', expr.string_value)
    self.assertEqual(123.456, expr.numeric_value)

  def testExprOperandInvalidNumericValue(self):
    expr = self.Operand('123.456.789')
    self.assertEqual('123.456.789', expr.string_value)
    self.assertEqual(None, expr.numeric_value)

  # Operators.

  def testExprLTlt(self):
    expr = self.backend.ExprLT(['i'], self.Operand('3'))
    self.assertTrue(expr.Evaluate(R))

  def testExprLTeq(self):
    expr = self.backend.ExprLT(['i'], self.Operand('2'))
    self.assertFalse(expr.Evaluate(R))

  def testExprLTgt(self):
    expr = self.backend.ExprLT(['i'], self.Operand('1'))
    self.assertFalse(expr.Evaluate(R))

  def testExprLtNonelt(self):
    expr = self.backend.ExprLT(['e'], self.Operand('3'))
    self.assertTrue(expr.Evaluate(R))

  def testExprLElt(self):
    expr = self.backend.ExprLE(['i'], self.Operand('3'))
    self.assertTrue(expr.Evaluate(R))

  def testExprLEeq(self):
    expr = self.backend.ExprLE(['i'], self.Operand('2'))
    self.assertTrue(expr.Evaluate(R))

  def testExprLEgt(self):
    expr = self.backend.ExprLE(['i'], self.Operand('1'))
    self.assertFalse(expr.Evaluate(R))

  def testExprEQne(self):
    expr = self.backend.ExprEQ(['i'], self.Operand('1'))
    self.assertFalse(expr.Evaluate(R))

  def testExprEQeq(self):
    expr = self.backend.ExprEQ(['i'], self.Operand('2'))
    self.assertTrue(expr.Evaluate(R))

  def testExprEQNonene(self):
    expr = self.backend.ExprEQ(['e'], self.Operand('2'))
    self.assertFalse(expr.Evaluate(R))

  def testExprNEne(self):
    expr = self.backend.ExprNE(['i'], self.Operand('1'))
    self.assertTrue(expr.Evaluate(R))

  def testExprNEeq(self):
    expr = self.backend.ExprNE(['i'], self.Operand('2'))
    self.assertFalse(expr.Evaluate(R))

  def testExprNENonene(self):
    expr = self.backend.ExprNE(['e'], self.Operand('2'))
    self.assertTrue(expr.Evaluate(R))

  def testExprGElt(self):
    expr = self.backend.ExprGE(['i'], self.Operand('3'))
    self.assertFalse(expr.Evaluate(R))

  def testExprGEeq(self):
    expr = self.backend.ExprGE(['i'], self.Operand('2'))
    self.assertTrue(expr.Evaluate(R))

  def testExprGEgt(self):
    expr = self.backend.ExprGE(['i'], self.Operand('1'))
    self.assertTrue(expr.Evaluate(R))

  def testExprGTlt(self):
    expr = self.backend.ExprGT(['i'], self.Operand('3'))
    self.assertFalse(expr.Evaluate(R))

  def testExprGTeq(self):
    expr = self.backend.ExprGT(['i'], self.Operand('2'))
    self.assertFalse(expr.Evaluate(R))

  def testExprGTgt(self):
    expr = self.backend.ExprGT(['i'], self.Operand('1'))
    self.assertTrue(expr.Evaluate(R))

  def testExprGTNonelt(self):
    expr = self.backend.ExprGT(['e'], self.Operand('3'))
    self.assertFalse(expr.Evaluate(R))

  # Unanchored RE match.

  def testExprREStringString(self):
    expr = self.backend.ExprRE(['F'], self.Operand('3.14'))
    self.assertTrue(expr.Evaluate(R))

  def testExprREStringNumber(self):
    expr = self.backend.ExprRE(['F'], self.Operand(3.14))
    self.assertTrue(expr.Evaluate(R))

  def testExprRENumberString(self):
    expr = self.backend.ExprRE(['f'], self.Operand('3.14'))
    self.assertTrue(expr.Evaluate(R))

  def testExprRENumberNumber(self):
    expr = self.backend.ExprRE(['f'], self.Operand(3.14))
    self.assertTrue(expr.Evaluate(R))

  # Unanchored RE NOT match.

  def testExprNotREStringString(self):
    expr = self.backend.ExprNotRE(['F'], self.Operand('3.14'))
    self.assertFalse(expr.Evaluate(R))

  def testExprNotREStringNumber(self):
    expr = self.backend.ExprNotRE(['F'], self.Operand(3.14))
    self.assertFalse(expr.Evaluate(R))

  def testExprNotRENumberString(self):
    expr = self.backend.ExprNotRE(['f'], self.Operand('3.14'))
    self.assertFalse(expr.Evaluate(R))

  def testExprNotRENumberNumber(self):
    expr = self.backend.ExprNotRE(['f'], self.Operand(3.14))
    self.assertFalse(expr.Evaluate(R))

  def testExprLTDateTimeNaiveVsNaive(self):
    expr = self.backend.ExprLT(
        ['date_naive'], self.Operand('2016-10-08T05:10:33.324'))
    self.assertTrue(expr.Evaluate(R))

  def testExprGTDateTimeNaiveVsNaive(self):
    expr = self.backend.ExprGT(
        ['date_naive'], self.Operand('2016-10-08T05:10:33.324'))
    self.assertFalse(expr.Evaluate(R))

  def testExprLTDateTimeNaiveVsNaiveDuration(self):
    expr = self.backend.ExprLT(['date_naive'], self.Operand('-P1TS'))
    self.assertTrue(expr.Evaluate(R))

  def testExprGTDateTimeNaiveVsNaiveDuration(self):
    expr = self.backend.ExprGT(['date_naive'], self.Operand('-P1TS'))
    self.assertFalse(expr.Evaluate(R))

  def testExprLTDateTimeNaiveVsAware(self):
    expr = self.backend.ExprLT(
        ['date_naive'], self.Operand('2016-10-08T05:10:33.324-04:00'))
    self.assertTrue(expr.Evaluate(R))

  def testExprGTDateTimeNaiveVsAware(self):
    expr = self.backend.ExprGT(
        ['date_naive'], self.Operand('2016-10-08T05:10:33.324-04:00'))
    self.assertFalse(expr.Evaluate(R))

  def testExprLTDateTimeAwareVsNaive(self):
    expr = self.backend.ExprLT(
        ['date_aware'], self.Operand('2016-10-08T05:10:33.324-04:00'))
    self.assertTrue(expr.Evaluate(R))

  def testExprGTDateTimeAwareVsNaive(self):
    expr = self.backend.ExprGT(
        ['date_aware'], self.Operand('2016-10-08T05:10:33.324-04:00'))
    self.assertFalse(expr.Evaluate(R))

  def testExprLTDateTimeAwareVsNaiveDuration(self):
    expr = self.backend.ExprLT(['date_aware'], self.Operand('-P1TS'))
    self.assertTrue(expr.Evaluate(R))

  def testExprGTDateTimeAwareVsNaiveDuration(self):
    expr = self.backend.ExprGT(['date_aware'], self.Operand('-P1TS'))
    self.assertFalse(expr.Evaluate(R))

  def testExprLTDateTimeAwareVsAware(self):
    expr = self.backend.ExprLT(
        ['date_aware'], self.Operand('2016-10-08T05:10:33.324-04:00'))
    self.assertTrue(expr.Evaluate(R))

  def testExprGTDateTimeAwareVsAware(self):
    expr = self.backend.ExprGT(
        ['date_aware'], self.Operand('2016-10-08T05:10:33.324-04:00'))
    self.assertFalse(expr.Evaluate(R))


class DeprecationWarningTest(sdk_test_base.WithLogCapture):

  def SetUp(self):
    self.backend = resource_expr.Backend()

  def testExprHASOneDeprecationWarningDoesButWont(self):
    warning = ('WARNING: --filter : operator evaluation is changing for '
               'consistency across Google APIs.  v:pdq currently matches but '
               'will not match in the near future.  Run '
               '`gcloud topic filters` for details.\n')
    expr = self.backend.ExprHAS(['v'], self.backend.ExprOperand('pdq'))
    self.assertTrue(expr.Evaluate({'v': 'abcpdqxyz'}))
    self.AssertErrEquals(warning)
    self.assertTrue(expr.Evaluate({'v': 'abcpdqxyz'}))
    self.AssertErrEquals(warning)

  def testExprHASOneDeprecationWarningDoesntButWill(self):
    warning = ('WARNING: --filter : operator evaluation is changing for '
               'consistency across Google APIs.  v:pdq* currently does not '
               'match but will match in the near future.  Run '
               '`gcloud topic filters` for details.\n')
    expr = self.backend.ExprHAS(['v'], self.backend.ExprOperand('pdq*'))
    self.assertFalse(expr.Evaluate({'v': 'abc.pdq.xyz'}))
    self.AssertErrEquals(warning)
    self.assertFalse(expr.Evaluate({'v': 'abc.pdq.xyz'}))
    self.AssertErrEquals(warning)


class ExprHASAndEQTest(subtests.Base, sdk_test_base.WithLogCapture):
  """Pedantic combinatorial tests for notoriously underspecified : and =."""

  dict_data = {1: 'aa', 'bcd': 'bb', 3: 'cc', 3.14: 'pi', 'fgh': 'dd', 4: 'ee',
               'XYZ': 'ff'}
  list_data = R['l']
  tuple_data = R['t']

  def SetUp(self):
    self.backend = resource_expr.Backend()

  def RunSubTest(self, value, op, operand, deprecated=False):
    exprs = {
        ':': self.backend.ExprHAS,
        '=': self.backend.ExprEQ,
    }
    resource = {'v': value}
    self.backend._deprecated_eq_warned = False
    self.backend._deprecated_has_warned = False
    expr = exprs[op](['v'], self.backend.ExprOperand(operand))
    actual = expr.Evaluate(resource)
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

  def testExprHAS(self):

    def T(expected, value, op, operand, syntax=False, deprecated=False):
      exception = resource_exceptions.ExpressionSyntaxError if syntax else None
      self.Run(expected, value, op, operand, deprecated=deprecated, depth=2,
               exception=exception)

    # Empty exists.

    T(False, None, ':', '*')
    T(False, '', ':', '*')
    T(False, [], ':', '*')
    T(False, [None], ':', '*')
    T(False, [''], ':', '*')
    T(False, (None,), ':', '*')
    T(False, ('',), ':', '*')
    T(False, {}, ':', '*')
    T(False, {None: None}, ':', '*')
    T(False, {'': ''}, ':', '*')

    # Non-empty exists.

    T(True, 'x', ':', '*')
    T(True, False, ':', '*')
    T(True, True, ':', '*')
    T(True, 0, ':', '*')
    T(True, 1, ':', '*')
    T(True, ['x'], ':', '*')
    T(True, ('x',), ':', '*')
    T(True, {None: 'y'}, ':', '*')
    T(True, {'': 'y'}, ':', '*')
    T(True, {'x': None}, ':', '*')
    T(True, {'x': ''}, ':', '*')
    T(True, {'x': 'y'}, ':', '*')

    # Fringe atrifacts.

    T(True, None, ':', '')
    T(True, '', ':', '')
    T(True, None, ':', 'null')
    T(False, '', ':', 'null')
    T(True, '.', ':', '.')
    T(True, 'a.z', ':', '.')

    # No word boundaries.

    T(True, 'abcpdqxyz', ':', 'xyz', deprecated=True)
    T(False, 'abcpdqxyz', ':', 'xyz*')
    T(True, 'abcpdqxyz', ':', '*xyz', deprecated=True)
    T(True, 'abcpdqxyz', ':', '*xyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', 'pdq', deprecated=True)
    T(False, 'abcpdqxyz', ':', 'pdq*')
    T(True, 'abcpdqxyz', ':', 'pdqxyz', deprecated=True)
    T(False, 'abcpdqxyz', ':', 'pdqxyz*')
    T(False, 'abcpdqxyz', ':', 'pdq*')
    T(False, 'abcpdqxyz', ':', 'pdq*xyz')
    T(True, 'abcpdqxyz', ':', 'pdq*xyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*xyz', deprecated=True)
    T(True, 'abcpdqxyz', ':', '*xyz*', syntax=True)
    T(False, 'abcpdqxyz', ':', '*pdq')
    T(True, 'abcpdqxyz', ':', '*pdq*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*pdqxyz', deprecated=True)
    T(True, 'abcpdqxyz', ':', '*pdqxyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*pdq*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*pdq*xyz', syntax=True)
    T(True, 'abcpdqxyz', ':', '*pdq*xyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', 'abc', deprecated=True)
    T(True, 'abcpdqxyz', ':', 'abc*')
    T(False, 'abcpdqxyz', ':', 'abcxyz')
    T(False, 'abcpdqxyz', ':', 'abcxyz*')
    T(True, 'abcpdqxyz', ':', 'abc*')
    T(True, 'abcpdqxyz', ':', 'abc*xyz', deprecated=True)
    T(True, 'abcpdqxyz', ':', 'abc*xyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', 'abcpdq', deprecated=True)
    T(True, 'abcpdqxyz', ':', 'abcpdq*')
    T(True, 'abcpdqxyz', ':', 'abcpdqxyz')
    T(True, 'abcpdqxyz', ':', 'abcpdqxyz*')
    T(True, 'abcpdqxyz', ':', 'abcpdq*')
    T(True, 'abcpdqxyz', ':', 'abcpdq*xyz', deprecated=True)
    T(True, 'abcpdqxyz', ':', 'abcpdq*xyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', 'abc*')
    T(True, 'abcpdqxyz', ':', 'abc*xyz', deprecated=True)
    T(True, 'abcpdqxyz', ':', 'abc*xyz*', syntax=True)
    T(False, 'abcpdqxyz', ':', 'abc*pdq')
    T(True, 'abcpdqxyz', ':', 'abc*pdq*', syntax=True)
    T(True, 'abcpdqxyz', ':', 'abc*pdqxyz', deprecated=True)
    T(True, 'abcpdqxyz', ':', 'abc*pdqxyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', 'abc*pdq*', syntax=True)
    T(True, 'abcpdqxyz', ':', 'abc*pdq*xyz', syntax=True)
    T(True, 'abcpdqxyz', ':', 'abc*pdq*xyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*xyz', deprecated=True)
    T(True, 'abcpdqxyz', ':', '*xyz*', syntax=True)
    T(False, 'abcpdqxyz', ':', '*pdq')
    T(True, 'abcpdqxyz', ':', '*pdq*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*pdqxyz', deprecated=True)
    T(True, 'abcpdqxyz', ':', '*pdqxyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*pdq*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*pdq*xyz', syntax=True)
    T(True, 'abcpdqxyz', ':', '*pdq*xyz*', syntax=True)
    T(False, 'abcpdqxyz', ':', '*abc')
    T(True, 'abcpdqxyz', ':', '*abc*', syntax=True)
    T(False, 'abcpdqxyz', ':', '*abcxyz')
    T(True, 'abcpdqxyz', ':', '*abcxyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abc*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abc*xyz', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abc*xyz*', syntax=True)
    T(False, 'abcpdqxyz', ':', '*abcpdq')
    T(True, 'abcpdqxyz', ':', '*abcpdq*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abcpdqxyz', deprecated=True)
    T(True, 'abcpdqxyz', ':', '*abcpdqxyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abcpdq*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abcpdq*xyz', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abcpdq*xyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abc*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abc*xyz', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abc*xyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abc*pdq', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abc*pdq*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abc*pdqxyz', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abc*pdqxyz*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abc*pdq*', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abc*pdq*xyz', syntax=True)
    T(True, 'abcpdqxyz', ':', '*abc*pdq*xyz*', syntax=True)

    # Mixed case data no word boundaries.

    T(True, 'ABCPDQXYZ', ':', 'xyz', deprecated=True)
    T(False, 'ABCPDQXYZ', ':', 'xyz*')
    T(True, 'ABCPDQXYZ', ':', '*xyz', deprecated=True)
    T(True, 'ABCPDQXYZ', ':', 'pdq', deprecated=True)
    T(False, 'ABCPDQXYZ', ':', 'pdq*')
    T(True, 'ABCPDQXYZ', ':', 'pdqxyz', deprecated=True)
    T(False, 'ABCPDQXYZ', ':', 'pdqxyz*')
    T(False, 'ABCPDQXYZ', ':', 'pdq*')
    T(False, 'ABCPDQXYZ', ':', 'pdq*xyz')
    T(True, 'ABCPDQXYZ', ':', '*xyz', deprecated=True)
    T(False, 'ABCPDQXYZ', ':', '*pdq')
    T(True, 'ABCPDQXYZ', ':', '*pdqxyz', deprecated=True)
    T(True, 'ABCPDQXYZ', ':', 'abc', deprecated=True)
    T(True, 'ABCPDQXYZ', ':', 'abc*')
    T(False, 'ABCPDQXYZ', ':', 'abcxyz')
    T(False, 'ABCPDQXYZ', ':', 'abcxyz*')
    T(True, 'ABCPDQXYZ', ':', 'abc*')
    T(True, 'ABCPDQXYZ', ':', 'abc*xyz', deprecated=True)
    T(True, 'ABCPDQXYZ', ':', 'abcpdq', deprecated=True)
    T(True, 'ABCPDQXYZ', ':', 'abcpdq*')
    T(True, 'ABCPDQXYZ', ':', 'abcpdqxyz')
    T(True, 'ABCPDQXYZ', ':', 'abcpdqxyz*')
    T(True, 'ABCPDQXYZ', ':', 'abcpdq*')
    T(True, 'ABCPDQXYZ', ':', 'abcpdq*xyz', deprecated=True)
    T(True, 'ABCPDQXYZ', ':', 'abc*')
    T(True, 'ABCPDQXYZ', ':', 'abc*xyz', deprecated=True)
    T(False, 'ABCPDQXYZ', ':', 'abc*pdq')
    T(True, 'ABCPDQXYZ', ':', 'abc*pdqxyz', deprecated=True)
    T(True, 'ABCPDQXYZ', ':', '*xyz', deprecated=True)
    T(False, 'ABCPDQXYZ', ':', '*pdq')
    T(True, 'ABCPDQXYZ', ':', '*pdqxyz', deprecated=True)
    T(False, 'ABCPDQXYZ', ':', '*abc')
    T(False, 'ABCPDQXYZ', ':', '*abcxyz')
    T(False, 'ABCPDQXYZ', ':', '*abcpdq')
    T(True, 'ABCPDQXYZ', ':', '*abcpdqxyz', deprecated=True)

    # Mixed case operand no word boundaries.

    T(True, 'abcpdqxyz', ':', 'XYZ', deprecated=True)
    T(False, 'abcpdqxyz', ':', 'XYZ*')
    T(True, 'abcpdqxyz', ':', '*XYZ', deprecated=True)
    T(True, 'abcpdqxyz', ':', 'PDQ', deprecated=True)
    T(False, 'abcpdqxyz', ':', 'PDQ*')
    T(True, 'abcpdqxyz', ':', 'PDQXYZ', deprecated=True)
    T(False, 'abcpdqxyz', ':', 'PDQXYZ*')
    T(False, 'abcpdqxyz', ':', 'PDQ*')
    T(False, 'abcpdqxyz', ':', 'PDQ*XYZ')
    T(True, 'abcpdqxyz', ':', '*XYZ', deprecated=True)
    T(False, 'abcpdqxyz', ':', '*PDQ')
    T(True, 'abcpdqxyz', ':', '*PDQXYZ', deprecated=True)
    T(True, 'abcpdqxyz', ':', 'ABC', deprecated=True)
    T(True, 'abcpdqxyz', ':', 'ABC*')
    T(False, 'abcpdqxyz', ':', 'ABCXYZ')
    T(False, 'abcpdqxyz', ':', 'ABCXYZ*')
    T(True, 'abcpdqxyz', ':', 'ABC*')
    T(True, 'abcpdqxyz', ':', 'ABC*XYZ', deprecated=True)
    T(True, 'abcpdqxyz', ':', 'ABCPDQ', deprecated=True)
    T(True, 'abcpdqxyz', ':', 'ABCPDQ*')
    T(True, 'abcpdqxyz', ':', 'abcpdqxyz')
    T(True, 'abcpdqxyz', ':', 'abcpdqxyz*')
    T(True, 'abcpdqxyz', ':', 'ABCPDQ*')
    T(True, 'abcpdqxyz', ':', 'ABCPDQ*XYZ', deprecated=True)
    T(True, 'abcpdqxyz', ':', 'ABC*')
    T(True, 'abcpdqxyz', ':', 'ABC*XYZ', deprecated=True)
    T(False, 'abcpdqxyz', ':', 'ABC*PDQ')
    T(True, 'abcpdqxyz', ':', 'ABC*PDQXYZ', deprecated=True)
    T(True, 'abcpdqxyz', ':', '*XYZ', deprecated=True)
    T(False, 'abcpdqxyz', ':', '*PDQ')
    T(True, 'abcpdqxyz', ':', '*PDQXYZ', deprecated=True)
    T(False, 'abcpdqxyz', ':', '*ABC')
    T(False, 'abcpdqxyz', ':', '*abcxyz')
    T(False, 'abcpdqxyz', ':', '*ABCPDQ')
    T(True, 'abcpdqxyz', ':', '*ABCPDQXYZ', deprecated=True)

    # Word boundaries.

    T(True, 'abc.pdq.xyz', ':', 'xyz')
    T(False, 'abc.pdq.xyz', ':', 'xyz*', deprecated=True)
    T(False, 'abc.pdq.xyz', ':', 'xyz.')
    T(True, 'abc.pdq.xyz', ':', '*xyz', deprecated=True)
    T(True, 'abc.pdq.xyz', ':', '*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*xyz.')
    T(True, 'abc.pdq.xyz', ':', '.xyz')
    T(False, 'abc.pdq.xyz', ':', '.xyz*', deprecated=True)
    T(False, 'abc.pdq.xyz', ':', '.xyz.')
    T(True, 'abc.pdq.xyz', ':', 'pdq')
    T(False, 'abc.pdq.xyz', ':', 'pdq*', deprecated=True)
    T(True, 'abc.pdq.xyz', ':', 'pdq.')
    T(False, 'abc.pdq.xyz', ':', 'pdqxyz')
    T(False, 'abc.pdq.xyz', ':', 'pdqxyz*')
    T(False, 'abc.pdq.xyz', ':', 'pdqxyz.')
    T(False, 'abc.pdq.xyz', ':', 'pdq*', deprecated=True)
    T(False, 'abc.pdq.xyz', ':', 'pdq*xyz')
    T(True, 'abc.pdq.xyz', ':', 'pdq*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', 'pdq*xyz.')
    T(True, 'abc.pdq.xyz', ':', 'pdq.')
    T(True, 'abc.pdq.xyz', ':', 'pdq.xyz')
    T(False, 'abc.pdq.xyz', ':', 'pdq.xyz*', deprecated=True)
    T(False, 'abc.pdq.xyz', ':', 'pdq.xyz.')
    T(True, 'abc.pdq.xyz', ':', '*xyz', deprecated=True)
    T(True, 'abc.pdq.xyz', ':', '*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*xyz.')
    T(False, 'abc.pdq.xyz', ':', '*pdq')
    T(True, 'abc.pdq.xyz', ':', '*pdq*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*pdq.')
    T(False, 'abc.pdq.xyz', ':', '*pdqxyz')
    T(True, 'abc.pdq.xyz', ':', '*pdqxyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*pdqxyz.')
    T(True, 'abc.pdq.xyz', ':', '*pdq*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*pdq*xyz', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*pdq*xyz*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*pdq*xyz.', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*pdq.')
    T(True, 'abc.pdq.xyz', ':', '*pdq.xyz', deprecated=True)
    T(True, 'abc.pdq.xyz', ':', '*pdq.xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*pdq.xyz.')
    T(True, 'abc.pdq.xyz', ':', '.xyz')
    T(False, 'abc.pdq.xyz', ':', '.xyz*', deprecated=True)
    T(False, 'abc.pdq.xyz', ':', '.xyz.')
    T(True, 'abc.pdq.xyz', ':', '.pdq')
    T(False, 'abc.pdq.xyz', ':', '.pdq*', deprecated=True)
    T(True, 'abc.pdq.xyz', ':', '.pdq.')
    T(False, 'abc.pdq.xyz', ':', '.pdqxyz')
    T(False, 'abc.pdq.xyz', ':', '.pdqxyz*')
    T(False, 'abc.pdq.xyz', ':', '.pdqxyz.')
    T(False, 'abc.pdq.xyz', ':', '.pdq*', deprecated=True)
    T(False, 'abc.pdq.xyz', ':', '.pdq*xyz')
    T(True, 'abc.pdq.xyz', ':', '.pdq*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '.pdq*xyz.')
    T(True, 'abc.pdq.xyz', ':', '.pdq.')
    T(True, 'abc.pdq.xyz', ':', '.pdq.xyz')
    T(False, 'abc.pdq.xyz', ':', '.pdq.xyz*', deprecated=True)
    T(False, 'abc.pdq.xyz', ':', '.pdq.xyz.')
    T(True, 'abc.pdq.xyz', ':', 'abc')
    T(True, 'abc.pdq.xyz', ':', 'abc*')
    T(True, 'abc.pdq.xyz', ':', 'abc.')
    T(False, 'abc.pdq.xyz', ':', 'abcxyz')
    T(False, 'abc.pdq.xyz', ':', 'abcxyz*')
    T(False, 'abc.pdq.xyz', ':', 'abcxyz.')
    T(True, 'abc.pdq.xyz', ':', 'abc*')
    T(True, 'abc.pdq.xyz', ':', 'abc*xyz', deprecated=True)
    T(True, 'abc.pdq.xyz', ':', 'abc*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', 'abc*xyz.')
    T(True, 'abc.pdq.xyz', ':', 'abc.')
    T(False, 'abc.pdq.xyz', ':', 'abc.xyz')
    T(False, 'abc.pdq.xyz', ':', 'abc.xyz*')
    T(False, 'abc.pdq.xyz', ':', 'abc.xyz.')
    T(False, 'abc.pdq.xyz', ':', 'abcpdq')
    T(False, 'abc.pdq.xyz', ':', 'abcpdq*')
    T(False, 'abc.pdq.xyz', ':', 'abcpdq.')
    T(False, 'abc.pdq.xyz', ':', 'abcpdqxyz')
    T(False, 'abc.pdq.xyz', ':', 'abcpdqxyz*')
    T(False, 'abc.pdq.xyz', ':', 'abcpdqxyz.')
    T(False, 'abc.pdq.xyz', ':', 'abcpdq*')
    T(False, 'abc.pdq.xyz', ':', 'abcpdq*xyz')
    T(True, 'abc.pdq.xyz', ':', 'abcpdq*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', 'abcpdq*xyz.')
    T(False, 'abc.pdq.xyz', ':', 'abcpdq.')
    T(False, 'abc.pdq.xyz', ':', 'abcpdq.xyz')
    T(False, 'abc.pdq.xyz', ':', 'abcpdq.xyz*')
    T(False, 'abc.pdq.xyz', ':', 'abcpdq.xyz.')
    T(True, 'abc.pdq.xyz', ':', 'abc*')
    T(True, 'abc.pdq.xyz', ':', 'abc*xyz', deprecated=True)
    T(True, 'abc.pdq.xyz', ':', 'abc*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', 'abc*xyz.')
    T(False, 'abc.pdq.xyz', ':', 'abc*pdq')
    T(True, 'abc.pdq.xyz', ':', 'abc*pdq*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', 'abc*pdq.')
    T(False, 'abc.pdq.xyz', ':', 'abc*pdqxyz')
    T(True, 'abc.pdq.xyz', ':', 'abc*pdqxyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', 'abc*pdqxyz.')
    T(True, 'abc.pdq.xyz', ':', 'abc*pdq*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', 'abc*pdq*xyz', syntax=True)
    T(True, 'abc.pdq.xyz', ':', 'abc*pdq*xyz*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', 'abc*pdq*xyz.', syntax=True)
    T(False, 'abc.pdq.xyz', ':', 'abc*pdq.')
    T(True, 'abc.pdq.xyz', ':', 'abc*pdq.xyz', deprecated=True)
    T(True, 'abc.pdq.xyz', ':', 'abc*pdq.xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', 'abc*pdq.xyz.')
    T(True, 'abc.pdq.xyz', ':', 'abc.')
    T(False, 'abc.pdq.xyz', ':', 'abc.xyz')
    T(False, 'abc.pdq.xyz', ':', 'abc.xyz*')
    T(False, 'abc.pdq.xyz', ':', 'abc.xyz.')
    T(True, 'abc.pdq.xyz', ':', 'abc.pdq')
    T(True, 'abc.pdq.xyz', ':', 'abc.pdq*')
    T(True, 'abc.pdq.xyz', ':', 'abc.pdq.')
    T(False, 'abc.pdq.xyz', ':', 'abc.pdqxyz')
    T(False, 'abc.pdq.xyz', ':', 'abc.pdqxyz*')
    T(False, 'abc.pdq.xyz', ':', 'abc.pdqxyz.')
    T(True, 'abc.pdq.xyz', ':', 'abc.pdq*')
    T(True, 'abc.pdq.xyz', ':', 'abc.pdq*xyz', deprecated=True)
    T(True, 'abc.pdq.xyz', ':', 'abc.pdq*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', 'abc.pdq*xyz.')
    T(True, 'abc.pdq.xyz', ':', 'abc.pdq.')
    T(True, 'abc.pdq.xyz', ':', 'abc.pdq.xyz')
    T(True, 'abc.pdq.xyz', ':', 'abc.pdq.xyz*')
    T(False, 'abc.pdq.xyz', ':', 'abc.pdq.xyz.')
    T(True, 'abc.pdq.xyz', ':', '*xyz', deprecated=True)
    T(True, 'abc.pdq.xyz', ':', '*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*xyz.')
    T(False, 'abc.pdq.xyz', ':', '*pdq')
    T(True, 'abc.pdq.xyz', ':', '*pdq*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*pdq.')
    T(False, 'abc.pdq.xyz', ':', '*pdqxyz')
    T(True, 'abc.pdq.xyz', ':', '*pdqxyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*pdqxyz.')
    T(True, 'abc.pdq.xyz', ':', '*pdq*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*pdq*xyz', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*pdq*xyz*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*pdq*xyz.', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*pdq.')
    T(True, 'abc.pdq.xyz', ':', '*pdq.xyz', deprecated=True)
    T(True, 'abc.pdq.xyz', ':', '*pdq.xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*pdq.xyz.')
    T(False, 'abc.pdq.xyz', ':', '*abc')
    T(True, 'abc.pdq.xyz', ':', '*abc*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abc.')
    T(False, 'abc.pdq.xyz', ':', '*abcxyz')
    T(True, 'abc.pdq.xyz', ':', '*abcxyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abcxyz.')
    T(True, 'abc.pdq.xyz', ':', '*abc*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*xyz', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*xyz*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*xyz.', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abc.')
    T(False, 'abc.pdq.xyz', ':', '*abc.xyz')
    T(True, 'abc.pdq.xyz', ':', '*abc.xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abc.xyz.')
    T(False, 'abc.pdq.xyz', ':', '*abcpdq')
    T(True, 'abc.pdq.xyz', ':', '*abcpdq*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abcpdq.')
    T(False, 'abc.pdq.xyz', ':', '*abcpdqxyz')
    T(True, 'abc.pdq.xyz', ':', '*abcpdqxyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abcpdqxyz.')
    T(True, 'abc.pdq.xyz', ':', '*abcpdq*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abcpdq*xyz', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abcpdq*xyz*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abcpdq*xyz.', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abcpdq.')
    T(False, 'abc.pdq.xyz', ':', '*abcpdq.xyz')
    T(True, 'abc.pdq.xyz', ':', '*abcpdq.xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abcpdq.xyz.')
    T(True, 'abc.pdq.xyz', ':', '*abc*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*xyz', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*xyz*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*xyz.', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdq', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdq*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdq.', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdqxyz', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdqxyz*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdqxyz.', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdq*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdq*xyz', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdq*xyz*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdq*xyz.', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdq.', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdq.xyz', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdq.xyz*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc*pdq.xyz.', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abc.')
    T(False, 'abc.pdq.xyz', ':', '*abc.xyz')
    T(True, 'abc.pdq.xyz', ':', '*abc.xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abc.xyz.')
    T(False, 'abc.pdq.xyz', ':', '*abc.pdq')
    T(True, 'abc.pdq.xyz', ':', '*abc.pdq*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abc.pdq.')
    T(False, 'abc.pdq.xyz', ':', '*abc.pdqxyz')
    T(True, 'abc.pdq.xyz', ':', '*abc.pdqxyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abc.pdqxyz.')
    T(True, 'abc.pdq.xyz', ':', '*abc.pdq*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc.pdq*xyz', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc.pdq*xyz*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '*abc.pdq*xyz.', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abc.pdq.')
    T(True, 'abc.pdq.xyz', ':', '*abc.pdq.xyz', deprecated=True)
    T(True, 'abc.pdq.xyz', ':', '*abc.pdq.xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '*abc.pdq.xyz.')
    T(True, 'abc.pdq.xyz', ':', '.xyz')
    T(False, 'abc.pdq.xyz', ':', '.xyz*', deprecated=True)
    T(False, 'abc.pdq.xyz', ':', '.xyz.')
    T(True, 'abc.pdq.xyz', ':', '.pdq')
    T(False, 'abc.pdq.xyz', ':', '.pdq*', deprecated=True)
    T(True, 'abc.pdq.xyz', ':', '.pdq.')
    T(False, 'abc.pdq.xyz', ':', '.pdqxyz')
    T(False, 'abc.pdq.xyz', ':', '.pdqxyz*')
    T(False, 'abc.pdq.xyz', ':', '.pdqxyz.')
    T(False, 'abc.pdq.xyz', ':', '.pdq*', deprecated=True)
    T(False, 'abc.pdq.xyz', ':', '.pdq*xyz')
    T(True, 'abc.pdq.xyz', ':', '.pdq*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '.pdq*xyz.')
    T(True, 'abc.pdq.xyz', ':', '.pdq.')
    T(True, 'abc.pdq.xyz', ':', '.pdq.xyz')
    T(False, 'abc.pdq.xyz', ':', '.pdq.xyz*', deprecated=True)
    T(False, 'abc.pdq.xyz', ':', '.pdq.xyz.')
    T(False, 'abc.pdq.xyz', ':', '.abc')
    T(False, 'abc.pdq.xyz', ':', '.abc*')
    T(False, 'abc.pdq.xyz', ':', '.abc.')
    T(False, 'abc.pdq.xyz', ':', '.abcxyz')
    T(False, 'abc.pdq.xyz', ':', '.abcxyz*')
    T(False, 'abc.pdq.xyz', ':', '.abcxyz.')
    T(False, 'abc.pdq.xyz', ':', '.abc*')
    T(False, 'abc.pdq.xyz', ':', '.abc*xyz')
    T(True, 'abc.pdq.xyz', ':', '.abc*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '.abc*xyz.')
    T(False, 'abc.pdq.xyz', ':', '.abc.')
    T(False, 'abc.pdq.xyz', ':', '.abc.xyz')
    T(False, 'abc.pdq.xyz', ':', '.abc.xyz*')
    T(False, 'abc.pdq.xyz', ':', '.abc.xyz.')
    T(False, 'abc.pdq.xyz', ':', '.abcpdq')
    T(False, 'abc.pdq.xyz', ':', '.abcpdq*')
    T(False, 'abc.pdq.xyz', ':', '.abcpdq.')
    T(False, 'abc.pdq.xyz', ':', '.abcpdqxyz')
    T(False, 'abc.pdq.xyz', ':', '.abcpdqxyz*')
    T(False, 'abc.pdq.xyz', ':', '.abcpdqxyz.')
    T(False, 'abc.pdq.xyz', ':', '.abcpdq*')
    T(False, 'abc.pdq.xyz', ':', '.abcpdq*xyz')
    T(True, 'abc.pdq.xyz', ':', '.abcpdq*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '.abcpdq*xyz.')
    T(False, 'abc.pdq.xyz', ':', '.abcpdq.')
    T(False, 'abc.pdq.xyz', ':', '.abcpdq.xyz')
    T(False, 'abc.pdq.xyz', ':', '.abcpdq.xyz*')
    T(False, 'abc.pdq.xyz', ':', '.abcpdq.xyz.')
    T(False, 'abc.pdq.xyz', ':', '.abc*')
    T(False, 'abc.pdq.xyz', ':', '.abc*xyz')
    T(True, 'abc.pdq.xyz', ':', '.abc*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '.abc*xyz.')
    T(False, 'abc.pdq.xyz', ':', '.abc*pdq')
    T(True, 'abc.pdq.xyz', ':', '.abc*pdq*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '.abc*pdq.')
    T(False, 'abc.pdq.xyz', ':', '.abc*pdqxyz')
    T(True, 'abc.pdq.xyz', ':', '.abc*pdqxyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '.abc*pdqxyz.')
    T(True, 'abc.pdq.xyz', ':', '.abc*pdq*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '.abc*pdq*xyz', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '.abc*pdq*xyz*', syntax=True)
    T(True, 'abc.pdq.xyz', ':', '.abc*pdq*xyz.', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '.abc*pdq.')
    T(False, 'abc.pdq.xyz', ':', '.abc*pdq.xyz')
    T(True, 'abc.pdq.xyz', ':', '.abc*pdq.xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '.abc*pdq.xyz.')
    T(False, 'abc.pdq.xyz', ':', '.abc.')
    T(False, 'abc.pdq.xyz', ':', '.abc.xyz')
    T(False, 'abc.pdq.xyz', ':', '.abc.xyz*')
    T(False, 'abc.pdq.xyz', ':', '.abc.xyz.')
    T(False, 'abc.pdq.xyz', ':', '.abc.pdq')
    T(False, 'abc.pdq.xyz', ':', '.abc.pdq*')
    T(False, 'abc.pdq.xyz', ':', '.abc.pdq.')
    T(False, 'abc.pdq.xyz', ':', '.abc.pdqxyz')
    T(False, 'abc.pdq.xyz', ':', '.abc.pdqxyz*')
    T(False, 'abc.pdq.xyz', ':', '.abc.pdqxyz.')
    T(False, 'abc.pdq.xyz', ':', '.abc.pdq*')
    T(False, 'abc.pdq.xyz', ':', '.abc.pdq*xyz')
    T(True, 'abc.pdq.xyz', ':', '.abc.pdq*xyz*', syntax=True)
    T(False, 'abc.pdq.xyz', ':', '.abc.pdq*xyz.')
    T(False, 'abc.pdq.xyz', ':', '.abc.pdq.')
    T(False, 'abc.pdq.xyz', ':', '.abc.pdq.xyz')
    T(False, 'abc.pdq.xyz', ':', '.abc.pdq.xyz*')
    T(False, 'abc.pdq.xyz', ':', '.abc.pdq.xyz.')

    # Unicode accents and case ignored.

    T(True, 'and.pass.xyz', ':', 'äñ*')
    T(True, 'AND.pass.xyz', ':', 'äñ*')
    T(True, 'äñd.pass.xyz', ':', 'an*')
    T(True, 'äñD.pass.xyz', ':', 'an*')
    T(True, 'äñd.pass.xyz', ':', 'ĄN*')
    T(True, 'äñD.pass.xyz', ':', 'ĄN*')
    T(True, 'and.Päẞ.xyz', ':', 'Päẞ')
    T(True, 'and.Päẞ.xyz', ':', 'pÄß')

    # Some ligatures are typographic and decompose.

    T(True, 'and.puff.xyz', ':', 'Püﬀ')
    T(True, 'and.PUFF.xyz', ':', 'Püﬀ')
    T(False, 'and.puf.xyz', ':', 'Püﬀ')
    T(False, 'and.puF.xyz', ':', 'Püﬀ')
    T(True, 'and.puff.xyz', ':', 'pÜﬀ')
    T(True, 'and.puFf.xyz', ':', 'pÜﬀ')
    T(False, 'and.puF.xyz', ':', 'pÜﬀ')

    T(True, 'and.püﬀ.xyz', ':', 'puff')
    T(True, 'and.püﬀ.xyz', ':', 'PUFF')
    T(True, 'and.püﬀ.xyz', ':', 'puf', deprecated=True)
    T(False, 'and.püﬀ.xyz', ':', 'puf*', deprecated=True)
    T(True, 'and.PÜﬀ.xyz', ':', 'puf', deprecated=True)
    T(False, 'and.PÜﬀ.xyz', ':', 'puf*', deprecated=True)

    # Some ligatures are characters in their own right and don't decompose.

    T(False, 'and.pass.xyz', ':', 'Päẞ')
    T(False, 'and.PASS.xyz', ':', 'Päẞ')
    T(False, 'and.pas.xyz', ':', 'Päẞ')
    T(False, 'and.paS.xyz', ':', 'Päẞ')
    T(False, 'and.pass.xyz', ':', 'pÄß')
    T(False, 'and.paSs.xyz', ':', 'pÄß')
    T(False, 'and.pas.xyz', ':', 'pÄß')
    T(False, 'and.paS.xyz', ':', 'pÄß')

    T(False, 'and.paß.xyz', ':', 'pass')
    T(False, 'and.paß.xyz', ':', 'PASS')
    T(False, 'and.PAẞ.xyz', ':', 'pass')
    T(False, 'and.paß.xyz', ':', 'pas')
    T(False, 'and.paẞ.xyz', ':', 'paS')

    # Mixed types.

    T(False, 'abcpdqxyz', ':', '0')
    T(False, 'abcpdqxyz', ':', '1')
    T(False, 'abcpdqxyz', ':', 'az')
    T(True, 'abcpdqxyz', ':', 'ABC*xyz', deprecated=True)
    T(True, 3.14159265359, ':', '14159', deprecated=True)
    T(True, '3.14159265359', ':', '14159', deprecated=True)
    T(False, 'ABCPDQXYZ', ':', '3.14')
    T(True, 'abcpdqxyz', ':', ['ABC', 'xyz'], deprecated=True)
    T(True, 'abcpdqxyz', ':', ['ABC*', 'xyz'])
    T(True, 'abcpdqxyz', ':', ['ABC', '*xyz'], deprecated=True)
    T(True, 'abcpdqxyz', ':', ['ABC*', '*xyz'])
    T(True, 'abcpdqxyz', ':', ['BCD', 'xyz'], deprecated=True)
    T(True, 'abcpdqxyz', ':', ['*BCD', 'xyz'], deprecated=True)
    T(True, 'abcpdqxyz', ':', ['BCD', '*xyz'], deprecated=True)
    T(True, 'abcpdqxyz', ':', ['BCD', 'XYZ'], deprecated=True)
    T(True, 'abcpdqxyz', ':', ['*BCD', 'XYZ'], deprecated=True)
    T(True, 'abcpdqxyz', ':', ['BCD', '*XYZ'], deprecated=True)
    T(False, 'abcpdqxyz', ':', ['BCD', 'wxy'])
    T(False, None, ':', 'false')
    T(True, False, ':', 'false')
    T(False, True, ':', 'false')
    T(True, 0, ':', 'false')
    T(True, '0', ':', 'false')
    T(False, 1, ':', 'false')
    T(False, '1', ':', 'false')
    T(False, '', ':', 'false')
    T(True, 'False', ':', 'false')
    T(True, 'false', ':', 'false')
    T(False, None, ':', 'true')
    T(False, False, ':', 'true')
    T(True, True, ':', 'true')
    T(False, 0, ':', 'true')
    T(False, '0', ':', 'true')
    T(True, 1, ':', 'true')
    T(True, '1', ':', 'true')
    T(False, '', ':', 'true')
    T(False, False, ':', 'true')
    T(False, 'False', ':', 'true')
    T(False, 'false', ':', 'true')
    T(True, False, ':', '0')
    T(False, True, ':', '0')
    T(True, True, ':', '1')
    T(False, 1, ':', '0')
    T(True, 1, ':', '1')
    T(False, 1, ':', 'abc')
    T(False, 1, ':', 'bcd')
    T(False, 1, ':', 'ABC')
    T(False, 1, ':', 'BCD')
    T(False, 1, ':', 'xyz')
    T(False, 1, ':', 'XYZ')
    T(True, 2, ':', '*')
    T(False, 2, ':', 'abc*')
    T(False, 2, ':', '*xyz')
    T(False, 2, ':', 'abc*xyz')
    T(False, 2, ':', 'xyz*')
    T(False, 2, ':', '*abc')
    T(False, 2, ':', 'xyz*abc')
    T(False, 2, ':', 'def*')
    T(False, 2, ':', '*uvw')
    T(False, 2, ':', 'def*uvw')
    T(False, self.dict_data, ':', '0')
    T(True, self.dict_data, ':', '1')
    T(False, self.dict_data, ':', 'abc')
    T(True, self.dict_data, ':', 'bcd')
    T(False, self.dict_data, ':', 'ABC')
    T(True, self.dict_data, ':', 'BCD')
    T(True, self.dict_data, ':', 'xyz')
    T(True, self.dict_data, ':', 'XYZ')
    T(True, self.dict_data, ':', '3.14')
    T(True, self.dict_data, ':', ['0', '1'])
    T(False, self.dict_data, ':', ['0', '2'])
    T(False, self.list_data, ':', '0')
    T(True, self.list_data, ':', '1')
    T(False, self.list_data, ':', 'abc')
    T(True, self.list_data, ':', 'bcd')
    T(False, self.list_data, ':', 'ABC')
    T(True, self.list_data, ':', 'BCD')
    T(True, self.list_data, ':', 'xyz')
    T(True, self.list_data, ':', 'XYZ')
    T(True, self.list_data, ':', '3.14')
    T(False, self.tuple_data, ':', '0')
    T(True, self.tuple_data, ':', '1')
    T(False, self.tuple_data, ':', 'abc')
    T(True, self.tuple_data, ':', 'bcd')
    T(False, self.tuple_data, ':', 'ABC')
    T(True, self.tuple_data, ':', 'BCD')
    T(True, self.tuple_data, ':', 'xyz')
    T(True, self.tuple_data, ':', 'XYZ')
    T(True, self.tuple_data, ':', '3.14')
    T(True, _Truthiness(0), ':', 'nope')
    T(False, _Truthiness(1), ':', 'nope')
    T(False, _Truthiness(0), ':', 'yep')
    T(True, _Truthiness(1), ':', 'yep')

    # Don't match HTML tags.

    T(False, '<code>stuff</code>', ':', 'code')
    T(True, '(code)stuff(/code)', ':', 'code')
    T(True, '<code>stuff</code>', ':', 'stuff')
    T(True, '<code>stuff</code>ed', ':', 'stuff', deprecated=True)
    T(True, '<code>stuff</code>ed', ':', 'stuff*')
    T(True, '<code>stuff</code>ed', ':', 'stuffed')

  def testExprEQ(self):

    def T(expected, value, op, operand, syntax=False, deprecated=False):
      exception = resource_exceptions.ExpressionSyntaxError if syntax else None
      self.Run(expected, value, op, operand, deprecated=deprecated, depth=2,
               exception=exception)

    # Fringe atrifacts.

    T(True, None, '=', '')
    T(False, None, '=', '*')
    T(True, None, '=', 'null')
    T(True, '', '=', '')
    T(False, '', '=', '*')
    T(True, '*', '=', '*')
    T(False, 'x', '=', '*')
    T(True, '.', '=', '.')
    T(False, 'a.z', '=', '.', deprecated=True)

    # No word boundaries, no '*'.

    T(False, 'abcpdqxyz', '=', 'xyz')
    T(False, 'abcpdqxyz', '=', 'xyz*')
    T(False, 'abcpdqxyz', '=', '*xyz')
    T(False, 'abcpdqxyz', '=', '*xyz*')
    T(False, 'abcpdqxyz', '=', 'pdq')
    T(False, 'abcpdqxyz', '=', 'pdq*')
    T(False, 'abcpdqxyz', '=', 'pdqxyz')
    T(False, 'abcpdqxyz', '=', 'pdqxyz*')
    T(False, 'abcpdqxyz', '=', 'pdq*')
    T(False, 'abcpdqxyz', '=', 'pdq*xyz')
    T(False, 'abcpdqxyz', '=', 'pdq*xyz*')
    T(False, 'abcpdqxyz', '=', '*xyz')
    T(False, 'abcpdqxyz', '=', '*xyz*')
    T(False, 'abcpdqxyz', '=', '*pdq')
    T(False, 'abcpdqxyz', '=', '*pdq*')
    T(False, 'abcpdqxyz', '=', '*pdqxyz')
    T(False, 'abcpdqxyz', '=', '*pdqxyz*')
    T(False, 'abcpdqxyz', '=', '*pdq*')
    T(False, 'abcpdqxyz', '=', '*pdq*xyz')
    T(False, 'abcpdqxyz', '=', '*pdq*xyz*')
    T(False, 'abcpdqxyz', '=', 'abc')
    T(False, 'abcpdqxyz', '=', 'abc*')
    T(False, 'abcpdqxyz', '=', 'abcxyz')
    T(False, 'abcpdqxyz', '=', 'abcxyz*')
    T(False, 'abcpdqxyz', '=', 'abc*')
    T(False, 'abcpdqxyz', '=', 'abc*xyz')
    T(False, 'abcpdqxyz', '=', 'abc*xyz*')
    T(False, 'abcpdqxyz', '=', 'abcpdq')
    T(False, 'abcpdqxyz', '=', 'abcpdq*')
    T(True, 'abcpdqxyz', '=', 'abcpdqxyz')
    T(False, 'abcpdqxyz', '=', 'abcpdqxyz*')
    T(False, 'abcpdqxyz', '=', 'abcpdq*')
    T(False, 'abcpdqxyz', '=', 'abcpdq*xyz')
    T(False, 'abcpdqxyz', '=', 'abcpdq*xyz*')
    T(False, 'abcpdqxyz', '=', 'abc*')
    T(False, 'abcpdqxyz', '=', 'abc*xyz')
    T(False, 'abcpdqxyz', '=', 'abc*xyz*')
    T(False, 'abcpdqxyz', '=', 'abc*pdq')
    T(False, 'abcpdqxyz', '=', 'abc*pdq*')
    T(False, 'abcpdqxyz', '=', 'abc*pdqxyz')
    T(False, 'abcpdqxyz', '=', 'abc*pdqxyz*')
    T(False, 'abcpdqxyz', '=', 'abc*pdq*')
    T(False, 'abcpdqxyz', '=', 'abc*pdq*xyz')
    T(False, 'abcpdqxyz', '=', 'abc*pdq*xyz*')
    T(False, 'abcpdqxyz', '=', '*xyz')
    T(False, 'abcpdqxyz', '=', '*xyz*')
    T(False, 'abcpdqxyz', '=', '*pdq')
    T(False, 'abcpdqxyz', '=', '*pdq*')
    T(False, 'abcpdqxyz', '=', '*pdqxyz')
    T(False, 'abcpdqxyz', '=', '*pdqxyz*')
    T(False, 'abcpdqxyz', '=', '*pdq*')
    T(False, 'abcpdqxyz', '=', '*pdq*xyz')
    T(False, 'abcpdqxyz', '=', '*pdq*xyz*')
    T(False, 'abcpdqxyz', '=', '*abc')
    T(False, 'abcpdqxyz', '=', '*abc*')
    T(False, 'abcpdqxyz', '=', '*abcxyz')
    T(False, 'abcpdqxyz', '=', '*abcxyz*')
    T(False, 'abcpdqxyz', '=', '*abc*')
    T(False, 'abcpdqxyz', '=', '*abc*xyz')
    T(False, 'abcpdqxyz', '=', '*abc*xyz*')
    T(False, 'abcpdqxyz', '=', '*abcpdq')
    T(False, 'abcpdqxyz', '=', '*abcpdq*')
    T(False, 'abcpdqxyz', '=', '*abcpdqxyz')
    T(False, 'abcpdqxyz', '=', '*abcpdqxyz*')
    T(False, 'abcpdqxyz', '=', '*abcpdq*')
    T(False, 'abcpdqxyz', '=', '*abcpdq*xyz')
    T(False, 'abcpdqxyz', '=', '*abcpdq*xyz*')
    T(False, 'abcpdqxyz', '=', '*abc*')
    T(False, 'abcpdqxyz', '=', '*abc*xyz')
    T(False, 'abcpdqxyz', '=', '*abc*xyz*')
    T(False, 'abcpdqxyz', '=', '*abc*pdq')
    T(False, 'abcpdqxyz', '=', '*abc*pdq*')
    T(False, 'abcpdqxyz', '=', '*abc*pdqxyz')
    T(False, 'abcpdqxyz', '=', '*abc*pdqxyz*')
    T(False, 'abcpdqxyz', '=', '*abc*pdq*')
    T(False, 'abcpdqxyz', '=', '*abc*pdq*xyz')
    T(False, 'abcpdqxyz', '=', '*abc*pdq*xyz*')

    # Word boundaries, no '*'.

    T(False, 'abc.pdq.xyz', '=', 'xyz', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', 'xyz*')
    T(False, 'abc.pdq.xyz', '=', 'xyz.')
    T(False, 'abc.pdq.xyz', '=', '*xyz')
    T(False, 'abc.pdq.xyz', '=', '*xyz*')
    T(False, 'abc.pdq.xyz', '=', '*xyz.')
    T(False, 'abc.pdq.xyz', '=', '.xyz', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', '.xyz*')
    T(False, 'abc.pdq.xyz', '=', '.xyz.')
    T(False, 'abc.pdq.xyz', '=', 'pdq', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', 'pdq*')
    T(False, 'abc.pdq.xyz', '=', 'pdq.', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', 'pdqxyz')
    T(False, 'abc.pdq.xyz', '=', 'pdqxyz*')
    T(False, 'abc.pdq.xyz', '=', 'pdqxyz.')
    T(False, 'abc.pdq.xyz', '=', 'pdq*')
    T(False, 'abc.pdq.xyz', '=', 'pdq*xyz')
    T(False, 'abc.pdq.xyz', '=', 'pdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', 'pdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', 'pdq.', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', 'pdq.xyz', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', 'pdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', 'pdq.xyz.')
    T(False, 'abc.pdq.xyz', '=', '*xyz')
    T(False, 'abc.pdq.xyz', '=', '*xyz*')
    T(False, 'abc.pdq.xyz', '=', '*xyz.')
    T(False, 'abc.pdq.xyz', '=', '*pdq')
    T(False, 'abc.pdq.xyz', '=', '*pdq*')
    T(False, 'abc.pdq.xyz', '=', '*pdq.')
    T(False, 'abc.pdq.xyz', '=', '*pdqxyz')
    T(False, 'abc.pdq.xyz', '=', '*pdqxyz*')
    T(False, 'abc.pdq.xyz', '=', '*pdqxyz.')
    T(False, 'abc.pdq.xyz', '=', '*pdq*')
    T(False, 'abc.pdq.xyz', '=', '*pdq*xyz')
    T(False, 'abc.pdq.xyz', '=', '*pdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', '*pdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', '*pdq.')
    T(False, 'abc.pdq.xyz', '=', '*pdq.xyz')
    T(False, 'abc.pdq.xyz', '=', '*pdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', '*pdq.xyz.')
    T(False, 'abc.pdq.xyz', '=', '.xyz', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', '.xyz*')
    T(False, 'abc.pdq.xyz', '=', '.xyz.')
    T(False, 'abc.pdq.xyz', '=', '.pdq', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', '.pdq*')
    T(False, 'abc.pdq.xyz', '=', '.pdq.', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', '.pdqxyz')
    T(False, 'abc.pdq.xyz', '=', '.pdqxyz*')
    T(False, 'abc.pdq.xyz', '=', '.pdqxyz.')
    T(False, 'abc.pdq.xyz', '=', '.pdq*')
    T(False, 'abc.pdq.xyz', '=', '.pdq*xyz')
    T(False, 'abc.pdq.xyz', '=', '.pdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', '.pdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', '.pdq.', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', '.pdq.xyz', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', '.pdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', '.pdq.xyz.')
    T(False, 'abc.pdq.xyz', '=', 'abc', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', 'abc*')
    T(False, 'abc.pdq.xyz', '=', 'abc.', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', 'abcxyz')
    T(False, 'abc.pdq.xyz', '=', 'abcxyz*')
    T(False, 'abc.pdq.xyz', '=', 'abcxyz.')
    T(False, 'abc.pdq.xyz', '=', 'abc*')
    T(False, 'abc.pdq.xyz', '=', 'abc*xyz')
    T(False, 'abc.pdq.xyz', '=', 'abc*xyz*')
    T(False, 'abc.pdq.xyz', '=', 'abc*xyz.')
    T(False, 'abc.pdq.xyz', '=', 'abc.', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', 'abc.xyz')
    T(False, 'abc.pdq.xyz', '=', 'abc.xyz*')
    T(False, 'abc.pdq.xyz', '=', 'abc.xyz.')
    T(False, 'abc.pdq.xyz', '=', 'abcpdq')
    T(False, 'abc.pdq.xyz', '=', 'abcpdq*')
    T(False, 'abc.pdq.xyz', '=', 'abcpdq.')
    T(False, 'abc.pdq.xyz', '=', 'abcpdqxyz')
    T(False, 'abc.pdq.xyz', '=', 'abcpdqxyz*')
    T(False, 'abc.pdq.xyz', '=', 'abcpdqxyz.')
    T(False, 'abc.pdq.xyz', '=', 'abcpdq*')
    T(False, 'abc.pdq.xyz', '=', 'abcpdq*xyz')
    T(False, 'abc.pdq.xyz', '=', 'abcpdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', 'abcpdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', 'abcpdq.')
    T(False, 'abc.pdq.xyz', '=', 'abcpdq.xyz')
    T(False, 'abc.pdq.xyz', '=', 'abcpdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', 'abcpdq.xyz.')
    T(False, 'abc.pdq.xyz', '=', 'abc*')
    T(False, 'abc.pdq.xyz', '=', 'abc*xyz')
    T(False, 'abc.pdq.xyz', '=', 'abc*xyz*')
    T(False, 'abc.pdq.xyz', '=', 'abc*xyz.')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdq')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdq*')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdq.')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdqxyz')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdqxyz*')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdqxyz.')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdq*')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdq*xyz')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdq.')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdq.xyz')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', 'abc*pdq.xyz.')
    T(False, 'abc.pdq.xyz', '=', 'abc.', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', 'abc.xyz')
    T(False, 'abc.pdq.xyz', '=', 'abc.xyz*')
    T(False, 'abc.pdq.xyz', '=', 'abc.xyz.')
    T(False, 'abc.pdq.xyz', '=', 'abc.pdq', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', 'abc.pdq*')
    T(False, 'abc.pdq.xyz', '=', 'abc.pdq.', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', 'abc.pdqxyz')
    T(False, 'abc.pdq.xyz', '=', 'abc.pdqxyz*')
    T(False, 'abc.pdq.xyz', '=', 'abc.pdqxyz.')
    T(False, 'abc.pdq.xyz', '=', 'abc.pdq*')
    T(False, 'abc.pdq.xyz', '=', 'abc.pdq*xyz')
    T(False, 'abc.pdq.xyz', '=', 'abc.pdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', 'abc.pdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', 'abc.pdq.', deprecated=True)
    T(True, 'abc.pdq.xyz', '=', 'abc.pdq.xyz')
    T(False, 'abc.pdq.xyz', '=', 'abc.pdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', 'abc.pdq.xyz.')
    T(False, 'abc.pdq.xyz', '=', '*xyz')
    T(False, 'abc.pdq.xyz', '=', '*xyz*')
    T(False, 'abc.pdq.xyz', '=', '*xyz.')
    T(False, 'abc.pdq.xyz', '=', '*pdq')
    T(False, 'abc.pdq.xyz', '=', '*pdq*')
    T(False, 'abc.pdq.xyz', '=', '*pdq.')
    T(False, 'abc.pdq.xyz', '=', '*pdqxyz')
    T(False, 'abc.pdq.xyz', '=', '*pdqxyz*')
    T(False, 'abc.pdq.xyz', '=', '*pdqxyz.')
    T(False, 'abc.pdq.xyz', '=', '*pdq*')
    T(False, 'abc.pdq.xyz', '=', '*pdq*xyz')
    T(False, 'abc.pdq.xyz', '=', '*pdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', '*pdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', '*pdq.')
    T(False, 'abc.pdq.xyz', '=', '*pdq.xyz')
    T(False, 'abc.pdq.xyz', '=', '*pdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', '*pdq.xyz.')
    T(False, 'abc.pdq.xyz', '=', '*abc')
    T(False, 'abc.pdq.xyz', '=', '*abc*')
    T(False, 'abc.pdq.xyz', '=', '*abc.')
    T(False, 'abc.pdq.xyz', '=', '*abcxyz')
    T(False, 'abc.pdq.xyz', '=', '*abcxyz*')
    T(False, 'abc.pdq.xyz', '=', '*abcxyz.')
    T(False, 'abc.pdq.xyz', '=', '*abc*')
    T(False, 'abc.pdq.xyz', '=', '*abc*xyz')
    T(False, 'abc.pdq.xyz', '=', '*abc*xyz*')
    T(False, 'abc.pdq.xyz', '=', '*abc*xyz.')
    T(False, 'abc.pdq.xyz', '=', '*abc.')
    T(False, 'abc.pdq.xyz', '=', '*abc.xyz')
    T(False, 'abc.pdq.xyz', '=', '*abc.xyz*')
    T(False, 'abc.pdq.xyz', '=', '*abc.xyz.')
    T(False, 'abc.pdq.xyz', '=', '*abcpdq')
    T(False, 'abc.pdq.xyz', '=', '*abcpdq*')
    T(False, 'abc.pdq.xyz', '=', '*abcpdq.')
    T(False, 'abc.pdq.xyz', '=', '*abcpdqxyz')
    T(False, 'abc.pdq.xyz', '=', '*abcpdqxyz*')
    T(False, 'abc.pdq.xyz', '=', '*abcpdqxyz.')
    T(False, 'abc.pdq.xyz', '=', '*abcpdq*')
    T(False, 'abc.pdq.xyz', '=', '*abcpdq*xyz')
    T(False, 'abc.pdq.xyz', '=', '*abcpdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', '*abcpdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', '*abcpdq.')
    T(False, 'abc.pdq.xyz', '=', '*abcpdq.xyz')
    T(False, 'abc.pdq.xyz', '=', '*abcpdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', '*abcpdq.xyz.')
    T(False, 'abc.pdq.xyz', '=', '*abc*')
    T(False, 'abc.pdq.xyz', '=', '*abc*xyz')
    T(False, 'abc.pdq.xyz', '=', '*abc*xyz*')
    T(False, 'abc.pdq.xyz', '=', '*abc*xyz.')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdq')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdq*')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdq.')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdqxyz')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdqxyz*')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdqxyz.')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdq*')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdq*xyz')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdq.')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdq.xyz')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', '*abc*pdq.xyz.')
    T(False, 'abc.pdq.xyz', '=', '*abc.')
    T(False, 'abc.pdq.xyz', '=', '*abc.xyz')
    T(False, 'abc.pdq.xyz', '=', '*abc.xyz*')
    T(False, 'abc.pdq.xyz', '=', '*abc.xyz.')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdq')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdq*')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdq.')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdqxyz')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdqxyz*')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdqxyz.')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdq*')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdq*xyz')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdq.')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdq.xyz')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', '*abc.pdq.xyz.')
    T(False, 'abc.pdq.xyz', '=', '.xyz', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', '.xyz*')
    T(False, 'abc.pdq.xyz', '=', '.xyz.')
    T(False, 'abc.pdq.xyz', '=', '.pdq', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', '.pdq*')
    T(False, 'abc.pdq.xyz', '=', '.pdq.', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', '.pdqxyz')
    T(False, 'abc.pdq.xyz', '=', '.pdqxyz*')
    T(False, 'abc.pdq.xyz', '=', '.pdqxyz.')
    T(False, 'abc.pdq.xyz', '=', '.pdq*')
    T(False, 'abc.pdq.xyz', '=', '.pdq*xyz')
    T(False, 'abc.pdq.xyz', '=', '.pdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', '.pdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', '.pdq.', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', '.pdq.xyz', deprecated=True)
    T(False, 'abc.pdq.xyz', '=', '.pdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', '.pdq.xyz.')
    T(False, 'abc.pdq.xyz', '=', '.abc')
    T(False, 'abc.pdq.xyz', '=', '.abc*')
    T(False, 'abc.pdq.xyz', '=', '.abc.')
    T(False, 'abc.pdq.xyz', '=', '.abcxyz')
    T(False, 'abc.pdq.xyz', '=', '.abcxyz*')
    T(False, 'abc.pdq.xyz', '=', '.abcxyz.')
    T(False, 'abc.pdq.xyz', '=', '.abc*')
    T(False, 'abc.pdq.xyz', '=', '.abc*xyz')
    T(False, 'abc.pdq.xyz', '=', '.abc*xyz*')
    T(False, 'abc.pdq.xyz', '=', '.abc*xyz.')
    T(False, 'abc.pdq.xyz', '=', '.abc.')
    T(False, 'abc.pdq.xyz', '=', '.abc.xyz')
    T(False, 'abc.pdq.xyz', '=', '.abc.xyz*')
    T(False, 'abc.pdq.xyz', '=', '.abc.xyz.')
    T(False, 'abc.pdq.xyz', '=', '.abcpdq')
    T(False, 'abc.pdq.xyz', '=', '.abcpdq*')
    T(False, 'abc.pdq.xyz', '=', '.abcpdq.')
    T(False, 'abc.pdq.xyz', '=', '.abcpdqxyz')
    T(False, 'abc.pdq.xyz', '=', '.abcpdqxyz*')
    T(False, 'abc.pdq.xyz', '=', '.abcpdqxyz.')
    T(False, 'abc.pdq.xyz', '=', '.abcpdq*')
    T(False, 'abc.pdq.xyz', '=', '.abcpdq*xyz')
    T(False, 'abc.pdq.xyz', '=', '.abcpdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', '.abcpdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', '.abcpdq.')
    T(False, 'abc.pdq.xyz', '=', '.abcpdq.xyz')
    T(False, 'abc.pdq.xyz', '=', '.abcpdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', '.abcpdq.xyz.')
    T(False, 'abc.pdq.xyz', '=', '.abc*')
    T(False, 'abc.pdq.xyz', '=', '.abc*xyz')
    T(False, 'abc.pdq.xyz', '=', '.abc*xyz*')
    T(False, 'abc.pdq.xyz', '=', '.abc*xyz.')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdq')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdq*')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdq.')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdqxyz')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdqxyz*')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdqxyz.')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdq*')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdq*xyz')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdq.')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdq.xyz')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', '.abc*pdq.xyz.')
    T(False, 'abc.pdq.xyz', '=', '.abc.')
    T(False, 'abc.pdq.xyz', '=', '.abc.xyz')
    T(False, 'abc.pdq.xyz', '=', '.abc.xyz*')
    T(False, 'abc.pdq.xyz', '=', '.abc.xyz.')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdq')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdq*')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdq.')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdqxyz')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdqxyz*')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdqxyz.')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdq*')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdq*xyz')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdq*xyz*')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdq*xyz.')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdq.')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdq.xyz')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdq.xyz*')
    T(False, 'abc.pdq.xyz', '=', '.abc.pdq.xyz.')

    # Boolean values and operands.

    T(True, False, '=', 'false')
    T(True, False, '=', 'False')
    T(True, False, '=', 'false')
    T(True, False, '=', 'False')
    T(False, True, '=', 'false')
    T(False, True, '=', 'False')
    T(False, False, '=', 'true')
    T(False, False, '=', 'True')
    T(False, False, '=', 'true')
    T(False, False, '=', 'True')
    T(True, True, '=', 'true')
    T(True, True, '=', 'True')

    # Mixed types.

    T(True, _Truthiness(0), '=', 'nope')
    T(False, _Truthiness(1), '=', 'nope')
    T(False, _Truthiness(0), '=', 'yep')
    T(True, _Truthiness(1), '=', 'yep')

    # Don't match HTML tags.

    T(False, '<code>stuff</code>', '=', 'code')
    T(False, '(code)stuff(/code)', '=', 'code', deprecated=True)
    T(True, '<code>stuff</code>', '=', 'stuff')
    T(False, '<code>stuff</code>ed', '=', 'stuff')
    T(False, '<code>stuff</code>ed', '=', 'stuff*')
    T(True, '<code>stuff</code>ed', '=', 'stuffed')


class ResourceExprOPTest(subtests.Base):

  class _ExprOP(resource_expr._ExprOperator):

    def __init__(self, *args, **kwargs):
      super(ResourceExprOPTest._ExprOP, self).__init__(*args, **kwargs)
      self.actual = []

    def Apply(self, value, operand):
      self.actual += [(value, operand)]
      raise ValueError('Test value error')

  def SetUp(self):
    self.backend = resource_expr.Backend()

  def RunSubTest(self, key, operand, transform=None, args=None):
    if transform:
      call = resource_lex.MakeTransform('', transform, args=args)
    else:
      call = None
    expr = self.ExprOP(key, operand, call)
    expr.Evaluate(R)
    return expr.actual

  def Operand(self, value):
    """Returns an ExprOperand for value.

    Args:
      value: ExprOperand returned for this value.

    Returns:
      ExprOperand for value.
    """
    return self.backend.ExprOperand(value)

  def ExprOP(self, key, operand, transform):

    return ResourceExprOPTest._ExprOP(self.backend, key, operand, transform)

  def testResourceExprOP(self):

    def T(expected, key, operand, transform=None, args=None):
      """Runs one subtest.

      Calls ExprOP(key, operand, transform).Evaluate(R) and caputures
      (value, operand) tuples passed to ExprOP.Apply() by the Evaluate().
      Failures are collected and reported as a group.

      Args:
        expected: The list of (value, operand) tuples passed to Apply().
        key: A 'parsed' key where each element is a sub-resource name string or
          integer index.
        operand: The RHS operand string.
        transform: Optional transform function to apply.
        args: Optional arg list for the transform function.
      """
      self.Run(expected, key, operand, depth=2, transform=transform, args=args)

    T([({}, '1')], ['D'], self.Operand('1'))
    T([({}, 'abc')], ['D'], self.Operand('abc'))

    T([([], '1')], ['L'], self.Operand('1'))
    T([([], 'abc')], ['L'], self.Operand('abc'))

    T([(2.0, 1), (2, '1')], ['i'], self.Operand('1'))
    T([(2, 'abc')], ['i'], self.Operand('abc'))

    T([(1.0, 1), (1, '1'), ('bcd', '1'), (3.0, 1), (3, '1'), ('fgh', '1'),
       (3.14, 1), (3.14, '1'), ('pi', '1'), (4.0, 1), (4, '1'), ('XYZ', '1')],
      ['l'], self.Operand('1'))
    T([(1, 'abc'), ('bcd', 'abc'), (3, 'abc'), ('fgh', 'abc'),
       (3.14, 'abc'), ('pi', 'abc'), (4, 'abc'), ('XYZ', 'abc')],
      ['l'], self.Operand('abc'))

    T([('Joe', 'Jan'), ('Jan', 'Jan')], ['o', 'name'], self.Operand('Jan'))
    T([(50.0, 40), (50, '40'), (40.0, 40), (40, '40')],
      ['o', 'age'], self.Operand('40'))

    T([('string', '1')], ['s'], self.Operand('1'))
    T([('string', 'abc')], ['s'], self.Operand('abc'))

    T([(1.0, 1), (1, '1'), ('bcd', '1'), (3.0, 1), (3, '1'), ('fgh', '1'),
       (3.14, 1), (3.14, '1'), ('pi', '1'), (4.0, 1), (4, '1'), ('XYZ', '1')],
      ['t'], self.Operand('1'))
    T([(1, 'abc'), ('bcd', 'abc'), (3, 'abc'), ('fgh', 'abc'), (3.14, 'abc'),
       ('pi', 'abc'), (4, 'abc'), ('XYZ', 'abc')],
      ['t'], self.Operand('abc'))

    T([(0.0, 1), (0, '1')], ['i'], self.Operand('1'),
      transform=resource_transform.TransformLen)
    T([(0, 'abc')], ['i'], self.Operand('abc'),
      transform=resource_transform.TransformLen)


class NormalizeForSearchTest(subtests.Base):

  def RunSubTest(self, value, html=False):
    return resource_expr.NormalizeForSearch(value, html=html)

  def testNormalizeForSearch(self):

    def T(expected, value, html=False):
      self.Run(expected, value, html=html, depth=2)

    T('null', None)
    T('false', False)
    T('true', True)

    T('nope', _Truthiness(None))
    T('nope', _Truthiness(False))
    T('nope', _Truthiness(0))
    T('yep', _Truthiness(True))
    T('yep', _Truthiness(1))

    T('(code)stuff(/code)', '(code)stuff(/code)')
    T('<code>stuff</code>', '<code>stuff</code>')
    T('<code>stuff</code>ed', '<code>stuff</code>ed')
    T('st<code>uff</code>ed', 'st<code>uff</code>ed')

    T('(code)stuff(/code)', '(code)stuff(/code)', html=True)
    T('stuff', '<code>stuff</code>', html=True)
    T('stuffed', '<code>stuff</code>ed', html=True)
    T('stuffed', 'st<code>uff</code>ed', html=True)


if __name__ == '__main__':
  test_case.main()
