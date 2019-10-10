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

"""Unit tests for the resource_expr_rewrite module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_expr_rewrite
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_projection_parser
from tests.lib import subtests
from tests.lib import test_case
from tests.lib.core.resource import s_expr

import six


class ResourceFilterExpressionBackendRewriteTest(subtests.Base):
  """Tests the filter expression rewrite backends.

  The s_expr backend Rewrite() method returns an S-expression
  (lisp style expression) equivalent string of the filter expression.
  """

  def SetUp(self):
    symbols = {'len': len, 'test_transform': lambda x: 'test'}
    aliases = {'y': resource_lex.Lexer('a.b.c').KeyWithAttribute()}
    self.defaults = resource_projection_parser.Parse(
        '(compound.string:alias=s, floating:alias=z)',
        aliases=aliases,
        symbols=symbols)

  def SetBackend(self, backend):
    self.rewrite = backend.Rewrite

  def RunSubTest(self, expression):
    return self.rewrite(expression, defaults=self.defaults)

  def testResourceFilterBackendBaseRewrite(self):
    """Rewrite backend base tests -- all expressions should collapse to None."""

    def T(expected, expression, exception=None):
      self.Run(expected, expression, exception=exception, depth=2)

    self.SetBackend(resource_expr_rewrite.BackendBase())

    T((None, None),
      None)
    T((None, None),
      '')
    T(('a:3', None),
      'a:3')
    T(('s:xyz', None),
      's:xyz')
    T(('-a:3', None),
      '-a:3')
    T(('NOT a:3', None),
      'NOT a:3')
    T(('x<3', None),
      'x<3')
    T(('x<=3', None),
      'x<=3')
    T(('x>=3', None),
      'x>=3')
    T(('x>3', None),
      'x>3')
    T(('x!=3', None),
      'x!=3')
    T(('-x!=3', None),
      '-x!=3')
    T(('NOT x!=3', None),
      'NOT x!=3')
    T(('s=ing', None),
      's=ing')
    T(('s:S*ing', None),
      's:S*ing')
    T(('s:str*', None),
      's:str*')
    T(('s~[a-z]', None),
      's~[a-z]')
    T(('s!~^s.*g$', None),
      's!~^s.*g$')
    T(('s:"STRING"', None),
      's:"STRING"')

    T(('a.b.c:"c*g"', None),
      'a.b.c:"c*g"')
    T(('x:1 AND (y:2 OR z:3)', None),
      'x:1 AND (y:2 OR z:3)')
    T(('NOT x:1 AND ( y:2 OR z:3 )', None),
      'NOT x:1 AND ( y:2 OR z:3 )')
    T(('(x>0 OR y>0) AND z>0', None),
      '(x>0 OR y>0) AND z>0')
    T(('( x:1 OR y:2 ) AND ( w:3 OR z:4 )', None),
      '( x:1 OR y:2 ) AND ( w:3 OR z:4 )')
    T(('( x:1 OR y:2 ) AND ( x:3 OR z:4 )', None),
      '( x:1 OR y:2 ) AND ( x:3 OR z:4 )')

    T(('a.b.c.test_transform():1', None),
      'a.b.c.test_transform():1')
    T(('a.b.c.test_transform():1 AND z:3', None),
      'a.b.c.test_transform():1 AND z:3')

    T(('a.b.c.unknown():1', None),
      'a.b.c.unknown():1')
    T(('a.b.c.unknown():1 AND z:3', None),
      'a.b.c.unknown():1 AND z:3')

  def testResourceFilterRewriteBackend(self):
    """Rewrite backend tests -- RE  & transform terms should rewrite to None."""

    def T(expected, expression, exception=None):
      self.Run(expected, expression, exception=exception, depth=2)

    self.SetBackend(resource_expr_rewrite.Backend())

    T((None, None),
      '')
    T((None, None),
      ' ')
    T((None, 'a:3'),
      'a:3')
    T((None, 'compound.string:xyz'),
      's:xyz')
    T((None, 'NOT a:3'),
      '-a:3')
    T((None, 'NOT a:3'),
      'NOT a:3')
    T((None, 'x<3'),
      'x<3')
    T((None, 'x<=3'),
      'x<=3')
    T((None, 'x>=3'),
      'x>=3')
    T((None, 'x>3'),
      'x>3')
    T((None, 'x!=3'),
      'x!=3')
    T((None, 'NOT x!=3'),
      '-x!=3')
    T((None, 'NOT x!=3'),
      'NOT x!=3')
    T((None, 'compound.string=ing'),
      's=ing')
    T((None, 'compound.string:S*ing'),
      's:S*ing')
    T((None, 'compound.string:str*'),
      's:str*')
    T(('s~[a-z]', None),
      's~[a-z]')
    T(('s!~^s.*g$', None),
      's!~^s.*g$')
    T((None, 'compound.string:STRING'),
      's:"STRING"')

    T((None, 'a.b.c:c*g'),
      'a.b.c:"c*g"')
    T((None, 'x:1 AND (a.b.c:2 OR floating:3)'),
      'x:1 AND (y:2 OR z:3)')
    T((None, 'NOT x:1 AND (a.b.c:2 OR floating:3)'),
      'NOT x:1 AND ( y:2 OR z:3 )')
    T((None, '(x>0 OR a.b.c>0) AND floating>0'),
      '(x>0 OR y>0) AND z>0')
    T((None, '(x:1 OR a.b.c:2) AND (w:3 OR floating:4)'),
      '( x:1 OR y:2 ) AND ( w:3 OR z:4 )')
    T((None, '(x:1 OR a.b.c:2) AND (x:3 OR floating:4)'),
      '( x:1 OR y:2 ) AND ( x:3 OR z:4 )')

    T((None, 'x:("a b",q,"y z")'),
      'x:("a b", q, "y z")')
    T((None, 'x:(a,b,q,y,z)'),
      'x:(a, b, q, y, z)')

    T(('a.b.c.test_transform():1', None),
      'a.b.c.test_transform():1')
    T(('a.b.c.test_transform():1 AND z:3', 'floating:3'),
      'a.b.c.test_transform():1 AND z:3')
    T(('a.b.c.unknown():1', None),
      'a.b.c.unknown():1')
    T(('a.b.c.unknown():1 AND z:3', 'floating:3'),
      'a.b.c.unknown():1 AND z:3')

  def testResourceFilterRewriteBackendWithSupportedOperand(self):

    def T(expected, expression):
      self.Run(expected, expression, depth=2)

    class BackendWithSupportedOperands(resource_expr_rewrite.Backend):

      def __init__(self, **kwargs):
        self._super = super(BackendWithSupportedOperands, self)
        self._super.__init__(**kwargs)

      def IsSupportedOperand(self, operand):
        return ' ' not in operand

      def RewriteOperand(self, operand):
        if (isinstance(operand, list) and
            any([x for x in operand if not self.IsSupportedOperand(x)])):
          return None
        return self._super.RewriteOperand(operand)

    self.SetBackend(BackendWithSupportedOperands())

    T((None, 'a:3'),
      'a:3')
    T((None, 'compound.string:xyz'),
      's:xyz')

    T(('x:("a b", q, "y z")', None),
      'x:("a b", q, "y z")')
    T((None, 'x:(a,b,q,y,z)'),
      'x:(a, b, q, y, z)')

  def testResourceFilterRewriteSExpressionBackend(self):
    """S-expression tests."""

    def T(expected, expression):
      self.Run(expected, expression, depth=2)

    self.SetBackend(s_expr.Backend())

    T((None, None),
      '')
    T((None, '(IN (GET "a") 3)'),
      'a:3')
    T((None, '(IN (GET "compound.string") "xyz")'),
      's:xyz')
    T((None, '(NOT (IN (GET "a") 3))'),
      '-a:3')
    T((None, '(NOT (IN (GET "a") 3))'),
      'NOT a:3')
    T((None, '(LT (GET "x") 3)'),
      'x<3')
    T((None, '(LE (GET "x") 3)'),
      'x<=3')
    T((None, '(GE (GET "x") 3)'),
      'x>=3')
    T((None, '(GT (GET "x") 3)'),
      'x>3')
    T((None, '(NE (GET "x") 3)'),
      'x!=3')
    T((None, '(NOT (NE (GET "x") 3))'),
      '-x!=3')
    T((None, '(NOT (NE (GET "x") 3))'),
      'NOT x!=3')
    T((None, '(EQ (GET "compound.string") "ing")'),
      's=ing')
    T((None, '(IN (GET "compound.string") "S*ing")'),
      's:S*ing')
    T((None, '(IN (GET "compound.string") "str*")'),
      's:str*')
    T((None, '(RE (GET "compound.string") "[a-z]")'),
      's~[a-z]')
    T((None, '(NRE (GET "compound.string") "^s.*g$")'),
      's!~^s.*g$')
    T((None, '(IN (GET "compound.string") "STRING")'),
      's:"STRING"')

    # These tests are repeated below with SupportedKey().

    T((None, '(IN (GET "a.b.c") "c*g")'),
      'a.b.c:"c*g"')
    T((None,
       '(AND (IN (GET "x") 1)'
       ' (OR (IN (GET "a.b.c") 2) (IN (GET "floating") 3)))'),
      'x:1 AND (y:2 OR z:3)')
    T((None,
       '(AND (NOT (IN (GET "x") 1))'
       ' (OR (IN (GET "a.b.c") 2) (IN (GET "floating") 3)))'),
      'NOT x:1 AND ( y:2 OR z:3 )')
    T((None,
       '(AND (OR (GT (GET "x") 0) (GT (GET "a.b.c") 0))'
       ' (GT (GET "floating") 0))'),
      '(x>0 OR y>0) AND z>0')
    T((None,
       '(AND (OR (IN (GET "x") 1) (IN (GET "a.b.c") 2))'
       ' (OR (IN (GET "w") 3) (IN (GET "floating") 4)))'),
      '( x:1 OR y:2 ) AND ( w:3 OR z:4 )')
    T((None,
       '(AND (OR (IN (GET "x") 1) (IN (GET "a.b.c") 2))'
       ' (OR (IN (GET "x") 3) (IN (GET "floating") 4)))'),
      '( x:1 OR y:2 ) AND ( x:3 OR z:4 )')

  def testResourceFilterBackendSExpressionsWithSupportedKey(self):
    """S-expression tests with supported key restrictions."""

    def T(expected, expression):
      self.Run(expected, expression, depth=2)

    def SupportedKey(name):
      return name in ['a.b.c', 'x', 'z']

    self.SetBackend(s_expr.SupportedKeyBackend(supported_key=SupportedKey))

    T((None, '(IN (GET "a.b.c") "c*g")'),
      'a.b.c:"c*g"')
    T(('x:1 AND (y:2 OR z:3)', '(IN (GET "x") 1)'),
      'x:1 AND (y:2 OR z:3)')
    T(('NOT x:1 AND ( y:2 OR z:3 )', '(NOT (IN (GET "x") 1))'),
      'NOT x:1 AND ( y:2 OR z:3 )')
    T((None, '(AND (NOT (IN (GET "x") 1)) (NOT (IN (GET "a.b.c") 1)))'),
      'NOT x:1 AND NOT y:1')
    T(('(x>1 AND y>2) OR z>3', None),
      '(x>1 AND y>2) OR z>3')
    T(('(x>0 OR y>0) AND z>0', '(OR (GT (GET "x") 0) (GT (GET "a.b.c") 0))'),
      '(x>0 OR y>0) AND z>0')
    T(('( x:1 OR y:2 ) AND ( w:3 OR z:4 )',
       '(OR (IN (GET "x") 1) (IN (GET "a.b.c") 2))'),
      '( x:1 OR y:2 ) AND ( w:3 OR z:4 )')
    T(('( x:1 OR a:2 ) AND ( b:3 OR c:4 )', None),
      '( x:1 OR a:2 ) AND ( b:3 OR c:4 )')
    T(('( x:1 OR y:2 ) AND ( x:3 OR z:4 )',
       '(OR (IN (GET "x") 1) (IN (GET "a.b.c") 2))'),
      '( x:1 OR y:2 ) AND ( x:3 OR z:4 )')
    T(('len() AND a=2', None),
      'len() AND a=2')
    T(('len() AND x=2', '(EQ (GET "x") 2)'),
      'len() AND x=2')
    T(('len() AND z=2', None),
      'len() AND z=2')


class ResourceExprRewriteQuoteTest(subtests.Base):
  """Tests for resource_expr_rewrite.BackendBase Quote."""

  def SetUp(self):
    self.backend = resource_expr_rewrite.BackendBase()

  def RunSubTest(self, string, always=False):
    return self.backend.Quote(string, always=always)

  def testResourceExprRewriteQuote(self):

    def T(expected, string, always=False):
      self.Run(expected, string, always=always, depth=2)

    T('abc', 'abc')
    T('"abc"', 'abc', always=True)
    T('"a b c"', 'a b c')
    T('"a b c"', 'a b c', always=True)

    T('"a\'b\'c"', 'a\'b\'c')
    T(r'"a\"b\"c"', 'a"b"c')
    T(r'"a\\\tb\\\nc"', r'a\tb\nc')
    T(r'"a\\\"b\\\"c"', r'a\"b\"c')


class ResourceExprRewriteQuoteOperandTest(subtests.Base):
  """Tests for resource_expr_rewrite.BackendBase QuoteOperand."""

  def SetUp(self):
    self.backend = resource_expr_rewrite.BackendBase()

  def RunSubTest(self, operand, always=False):
    return self.backend.QuoteOperand(operand, always=always)

  def testResourceExprRewriteQuote(self):

    def T(expected, operand, always=False):
      self.Run(expected, operand, always=always, depth=2)

    T('abc', 'abc')
    T('"abc"', 'abc', always=True)
    T('"a b c"', 'a b c')
    T('"a b c"', 'a b c', always=True)

    T('"a\'b\'c"', 'a\'b\'c')
    T(r'"a\"b\"c"', 'a"b"c')
    T(r'"a\\\tb\\\nc"', r'a\tb\nc')
    T(r'"a\\\"b\\\"c"', r'a\"b\"c')

    T('(abc,xyz)', ['abc', 'xyz'])
    T('("abc","xyz")', ['abc', 'xyz'], always=True)
    T('("a b c",xyz)', ['a b c', 'xyz'])
    T('("a b c","xyz")', ['a b c', 'xyz'], always=True)

    T('("a\'b\'c",xyz)', ['a\'b\'c', 'xyz'])
    T('("a\'b\'c","xyz")', ['a\'b\'c', 'xyz'], always=True)
    T(r'("a\"b\"c",xyz)', ['a"b"c', 'xyz'])
    T(r'("a\"b\"c","xyz")', ['a"b"c', 'xyz'], always=True)
    T(r'("a\\\tb\\\nc",xyz)', [r'a\tb\nc', 'xyz'])
    T(r'("a\\\tb\\\nc","xyz")', [r'a\tb\nc', 'xyz'], always=True)
    T(r'("a\\\"b\\\"c",xyz)', [r'a\"b\"c', 'xyz'])
    T(r'("a\\\"b\\\"c","xyz")', [r'a\"b\"c', 'xyz'], always=True)


class _Rewriter(resource_expr_rewrite.BackendBase):

  def RewriteTerm(self, key, op, operand, key_type):
    return '{key_type}::({key} {op} {operand})'.format(
        key_type=key_type.__name__,
        key=key,
        op=op,
        operand=operand,
    )


class MessageRewriteResourceTest(subtests.Base):

  def RunSubTest(self, expression, message, frontend_fields):
    rewriter = _Rewriter(message=message, frontend_fields=frontend_fields)
    return rewriter.Rewrite(expression)

  def testResourceFilterRewriter(self):

    # In InstanceGroups, name, kind and zone are string fields, and size is a
    # numeric field. The InstanceGroup message overrides the heuristic that
    # uses the operand value as a hint.
    message = apis.GetMessagesModule('compute', 'v1').InstanceGroup
    # Only using type names in this test.
    text = 'str' if six.PY3 else 'unicode'

    def T(expected, expression, frontend_fields=None, exception=None):
      self.Run(expected, expression, message, frontend_fields=frontend_fields,
               depth=2, exception=exception)

    T((None, text + '::(name = foo*bar)'),
      'name=foo*bar')
    T((None, text + '::(name != foo*bar)'),
      'name!=foo*bar')
    T((None, text + '::(name : foo*bar)'),
      'name:foo*bar')

    T((None, text + '::(kind : bar)'),
      'kind:bar')
    T((None, 'int::(size = 987)'),
      'size=987')

    T((None, text + '::(namedPorts.name : foo)'),
      'namedPorts.name:foo')
    T((None, text + '::(namedPorts.name : foo)'),
      'named_ports.name:foo')
    T((None, 'int::(namedPorts.port : 80)'),
      'namedPorts.port:80')
    T((None, 'int::(namedPorts.port : 1024)'),
      'named_ports.port:1024')

    T(('namedPorts.unknown=abc', None),
      'namedPorts.unknown=abc')
    T(('named_ports.unknown=xyz', None),
      'named_ports.unknown=xyz')

    T(None,
      'namedPorts.unknown=abc',
      frontend_fields={},
      exception=resource_exceptions.UnknownFieldError)
    T(None,
      'named_ports.unknown=xyz',
      frontend_fields={},
      exception=resource_exceptions.UnknownFieldError)

    T(('unknown:bar', None),
      'unknown:bar')
    T(None,
      'unknown:bar',
      frontend_fields={},
      exception=resource_exceptions.UnknownFieldError)
    T(None,
      'unknown:bar',
      frontend_fields={'name'},
      exception=resource_exceptions.UnknownFieldError)

    T(('thisIs.aTest:bar', None),
      'thisIs.aTest:bar',
      frontend_fields={'thisIs.aTest'})
    T(('this_is.a_test:bar', None),
      'this_is.a_test:bar',
      frontend_fields={'thisIs.aTest'})

    T(('thisIs[].aTest:bar', None),
      'thisIs[].aTest:bar',
      frontend_fields={'thisIs.aTest'})
    T(('this_is[1].a_test:bar', None),
      'this_is[1].a_test:bar',
      frontend_fields={'thisIs.aTest'})


if __name__ == '__main__':
  test_case.main()
