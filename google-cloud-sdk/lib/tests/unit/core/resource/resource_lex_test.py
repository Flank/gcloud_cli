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

"""Unit tests for the resource_lex module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_projection_spec
from tests.lib import subtests
from tests.lib import test_case


class ResourceLexTest(subtests.Base):

  def RunSubTest(self, fun, expression, aliases=None, annotate=None, **kwargs):
    if aliases:
      defaults = resource_projection_spec.ProjectionSpec(None, aliases=aliases)
    else:
      defaults = None
    lex = resource_lex.Lexer(expression, defaults=defaults)
    try:
      actual = getattr(lex, fun)(**kwargs)
    finally:
      if annotate is not None:
        self.AddFollowOnTest('annotate', annotate, lex.Annotate)
    return actual

  def testLexToken(self):

    def T(expected, expression, aliases=None, annotate=None,
          exception=None, **kwargs):
      self.Run(expected, 'Token', expression, aliases=aliases,
               annotate=annotate, depth=2, exception=exception, **kwargs)

    # empty expression

    T(None, None, annotate='*HERE*')
    T(None, '', annotate='*HERE*')

    # numbers

    T('123', '123  junk', annotate='123  *HERE* junk')
    T(123, '123  junk', annotate='123  *HERE* junk', convert=True)
    T('1.3', '1.3  junk', annotate='1.3  *HERE* junk')
    T(1.3, '1.3  junk', annotate='1.3  *HERE* junk', convert=True)
    T('1.3.5', '1.3.5  junk', annotate='1.3.5  *HERE* junk')
    T('1.3.5', '1.3.5  junk', annotate='1.3.5  *HERE* junk', convert=True)

    T('123', '123  junk', annotate='123 *HERE*  junk', space=False)
    T(123, '123  junk', annotate='123  *HERE* junk', convert=True)
    T('1.3', '1.3  junk', annotate='1.3 *HERE*  junk', space=False)
    T(1.3, '1.3  junk', annotate='1.3 *HERE*  junk', convert=True, space=False)
    T('1.3.5', '1.3.5  junk', annotate='1.3.5 *HERE*  junk', space=False)
    T('1.3.5', '1.3.5  junk', annotate='1.3.5 *HERE*  junk', convert=True,
      space=False)

    # default terminators

    T('abc', '  abc  def  ', annotate='  abc  *HERE* def  ')
    T(123, '  123  def  ', annotate='  123  *HERE* def  ', convert=True)

    # explicit terminators

    T('abc', ' abc()', annotate=' abc *HERE* ()', terminators='(){}=!<>+*/%')
    T('abc', ' abc<1', annotate=' abc *HERE* <1', terminators='(){}=!<>+*/%')
    T('abc', ' abc>1', annotate=' abc *HERE* >1', terminators='(){}=!<>+*/%')
    T('abc', ' abc=1', annotate=' abc *HERE* =1', terminators='(){}=!<>+*/%')
    T('abc', ' abc!1', annotate=' abc *HERE* !1', terminators='(){}=!<>+*/%')
    T('abc', ' abc+1', annotate=' abc *HERE* +1', terminators='(){}=!<>+*/%')
    T('abc', ' abc*1', annotate=' abc *HERE* *1', terminators='(){}=!<>+*/%')
    T('abc', ' abc/1', annotate=' abc *HERE* /1', terminators='(){}=!<>+*/%')
    T('abc', ' abc%1', annotate=' abc *HERE* %1', terminators='(){}=!<>+*/%')

    # different terminators types

    T('abc', ' abc()', annotate=' abc *HERE* ()',
      terminators=('(', ')', '{', '}', '=', '!', '<', '>', '+', '*', '/', '%'))
    T('abc', ' abc()', annotate=' abc *HERE* ()',
      terminators=['(', ')', '{', '}', '=', '!', '<', '>', '+', '*', '/', '%'])
    T('abc', ' abc()', annotate=' abc *HERE* ()',
      terminators=set(['(', ')', '{', '}', '=', '!', '<', '>', '+', '*', '/',
                       '%']))

    # quotes and escapes

    T('one two', '   "one two" three ', annotate='   "one two" *HERE* three ')
    T('123', ' "123" ', annotate=' "123" *HERE*')
    T('123', ' "123" ', annotate=' "123" *HERE*', convert=True)
    T('a"z', r' a\"z ', annotate=r' a\"z *HERE*')
    T('a"z', r' "a\"z" ', annotate=r' "a\"z" *HERE*')
    T(r'a\z', r' "a\\z" ', annotate=r' "a\\z" *HERE*')

    T('abc', r'"abc"', annotate=r'"abc" *HERE*')
    T(r'abc\$xyz', r'abc\$xyz', annotate=r'abc\$xyz *HERE*')
    T(r'"abc', r'\"abc xyz\"', annotate=r'\"abc *HERE* xyz\"')

    # exceptions

    T(None, ' a"b cd', annotate='*HERE* a"b cd',
      exception=resource_exceptions.ExpressionSyntaxError)

  def testLexKey(self):

    def T(expected, expression, aliases=None, annotate=None,
          exception=None, **kwargs):
      self.Run(expected, 'Key', expression, aliases=aliases,
               annotate=annotate, depth=2, exception=exception, **kwargs)

    aliases = {
        'r': resource_lex.Lexer('r.r').Key(),
        'x': resource_lex.Lexer('a.b.c').Key(),
        'y': resource_lex.Lexer('a.b[].c').Key(),
        'z': resource_lex.Lexer('a[123].b.c').Key(),
        }

    # empty expression

    T([], '')

    # top level resource expressions

    T([], '.', annotate='. *HERE*')
    T([], '.:abc', annotate='. *HERE* :abc')

    # valid keys

    T(['a', 'b', 'c'], ' a.b.c next ', annotate=' a.b.c *HERE* next ')
    T(['a', 'b'], ' a. b next ', annotate=' a. b *HERE* next ')
    T(['a', 'b', None, 'c'], ' a.b[].c next ', annotate=' a.b[].c *HERE* next ')
    T(['a', 123, 'b', 'c'], ' a[123].b.c next ',
      annotate=' a[123].b.c *HERE* next ')
    T(['a', 'b', 'c'], ' a.b.c .d next ', annotate=' a.b.c *HERE* .d next ')
    T(['@type'], '@type:a', annotate='@type *HERE* :a')

    # [x] and x. or .x are equivalent in all combinations

    T(['a', 'b', 'c'], ' a.b[c] next ', annotate=' a.b[c] *HERE* next ')
    T(['a', 'b', 'c'], ' a[b].c next ', annotate=' a[b].c *HERE* next ')
    T(['a', 'b', 'c'], ' a[b][c] next ', annotate=' a[b][c] *HERE* next ')
    T(['a', 'b', 'c'], ' [a].b.c next ', annotate=' [a].b.c *HERE* next ')
    T(['a', 'b', 'c'], ' [a].b[c] next ', annotate=' [a].b[c] *HERE* next ')
    T(['a', 'b', 'c'], ' [a][b].c next ', annotate=' [a][b].c *HERE* next ')
    T(['a', 'b', 'c'], ' [a][b][c] next ', annotate=' [a][b][c] *HERE* next ')

    # aliases

    T(['r', 'r'], ' r next ', aliases=aliases, annotate=' r *HERE* next ')
    T(['r'], ' r() next ', aliases=aliases, annotate=' r *HERE* () next ')
    T(['a', 'b', 'c'], ' x next ', aliases=aliases, annotate=' x *HERE* next ')
    T(['a', 'b', 'c', 'b'], ' x. b next ', aliases=aliases,
      annotate=' x. b *HERE* next ')
    T(['a', 'b', None, 'c'], ' y next ', aliases=aliases,
      annotate=' y *HERE* next ')
    T(['a', 123, 'b', 'c'], ' z next ', aliases=aliases,
      annotate=' z *HERE* next ')
    T(['a', 'b', 'c'], ' x .d next ', aliases=aliases,
      annotate=' x *HERE* .d next ')

    # terminators

    T(['a', 'b'], ' a.b(c ', annotate=' a.b *HERE* (c ')
    T(['a', 'b'], ' a.b)c ', annotate=' a.b *HERE* )c ')
    T(['a', 'b'], ' a.b{c ', annotate=' a.b *HERE* {c ')
    T(['a', 'b'], ' a.b}c ', annotate=' a.b *HERE* }c ')
    T(['a', 'b'], ' a.b<c ', annotate=' a.b *HERE* <c ')
    T(['a', 'b'], ' a.b>c ', annotate=' a.b *HERE* >c ')
    T(['a', 'b'], ' a.b=c ', annotate=' a.b *HERE* =c ')
    T(['a', 'b'], ' a.b!c ', annotate=' a.b *HERE* !c ')
    T(['a', 'b'], ' a.b+c ', annotate=' a.b *HERE* +c ')
    T(['a', 'b'], ' a.b*c ', annotate=' a.b *HERE* *c ')
    T(['a', 'b'], ' a.b/c ', annotate=' a.b *HERE* /c ')
    T(['a', 'b'], ' a.b%c ', annotate=' a.b *HERE* %c ')
    T(['a', 'b_c'], ' a.b_c ', annotate=' a.b_c *HERE* ')
    T([None], ' []a cd', annotate=' [] *HERE* a cd')
    T([1, 'a'], ' [1].a cd', annotate=' [1].a *HERE* cd')

    # end of input

    T(['a'], 'a', annotate='a *HERE*')
    T(['a', None], 'a[]', annotate='a[] *HERE*')

    # exceptions

    T(None, '..', exception=resource_exceptions.ExpressionSyntaxError,
      annotate='. *HERE* .')
    T(None, ' a"b cd', exception=resource_exceptions.ExpressionSyntaxError,
      annotate='*HERE* a"b cd')
    T(None, ' a.', exception=resource_exceptions.ExpressionSyntaxError,
      annotate=' a. *HERE*')
    T(None, ' .a cd', exception=resource_exceptions.ExpressionSyntaxError,
      annotate=' . *HERE* a cd')
    T(None, ' a..b cd', exception=resource_exceptions.ExpressionSyntaxError,
      annotate=' a. *HERE* .b cd')
    T(None, ' a[ cd', exception=resource_exceptions.ExpressionSyntaxError,
      annotate=' a[ cd *HERE*')
    T(None, ' a] cd', exception=resource_exceptions.ExpressionSyntaxError,
      annotate=' a] *HERE* cd')
    T(None, '#type:a', exception=resource_exceptions.ExpressionSyntaxError,
      annotate='*HERE* #type:a')

  def testLexIsCharacter(self):

    def T(expected, expression, aliases=None, annotate=None,
          exception=None, **kwargs):
      self.Run(expected, 'IsCharacter', expression, aliases=aliases,
               annotate=annotate, depth=2, exception=exception, **kwargs)

    # empty expression

    T(None, '', exception=resource_exceptions.ExpressionSyntaxError,
      characters='ax')
    T(None, '', annotate='*HERE*', characters='ax', peek=True)
    T(None, '', annotate='*HERE*', characters='ax', peek=True, eoi_ok=True)
    T(None, '', annotate='*HERE*', characters='ax', eoi_ok=True)

    # non-empty match

    T('x', 'xyz', annotate='x *HERE* yz', characters='ax')
    T('x', 'xyz', annotate='*HERE* xyz', characters='ax', peek=True)
    T('x', 'xyz', annotate='x *HERE* yz', characters='ax', eoi_ok=True)

    # different characters types

    T('x', 'xyz', annotate='x *HERE* yz', characters=('a', 'x'))
    T('x', 'xyz', annotate='x *HERE* yz', characters=['a', 'x'])
    T('x', 'xyz', annotate='x *HERE* yz', characters=set(['a', 'x']))

  def testLexIsString(self):

    def T(expected, expression, aliases=None, annotate=None,
          exception=None, **kwargs):
      self.Run(expected, 'IsString', expression, aliases=aliases,
               annotate=annotate, depth=2, exception=exception, **kwargs)

    # empty expression

    T(False, '', annotate='*HERE*', name='AND')
    T(False, '', annotate='*HERE*', name='AND', peek=True)

    # non-empty match

    T(False, 'ANDOR', annotate='*HERE* ANDOR', name='AND')
    T(False, 'ANDOR', annotate='*HERE* ANDOR', name='AND', peek=True)

    T(False, 'ORAND', annotate='*HERE* ORAND', name='AND')
    T(False, 'ORAND', annotate='*HERE* ORAND', name='AND', peek=True)

    T(True, 'AND OR', annotate='AND *HERE* OR', name='AND')
    T(True, 'AND OR', annotate='*HERE* AND OR', name='AND', peek=True)

  def testLexSkipSpace(self):

    def T(expected, expression, aliases=None, annotate=None,
          exception=None, **kwargs):
      self.Run(expected, 'SkipSpace', expression, aliases=aliases,
               annotate=annotate, depth=2, exception=exception, **kwargs)

    # empty expression

    T(False, '', annotate='*HERE*')
    T(False, '   ', annotate='   *HERE*')
    T(False, '', annotate='*HERE*')
    T(False, '   ', annotate='   *HERE*',
      exception=resource_exceptions.ExpressionSyntaxError, token='Op')

  def testLexArgs(self):

    def T(expected, expression, aliases=None, annotate=None,
          exception=None, **kwargs):
      self.Run(expected, 'Args', expression, aliases=aliases,
               annotate=annotate, depth=2, exception=exception, **kwargs)

    # empty expression

    T(['a', '1', 'z'], 'a, 1, z) x', annotate='a, 1, z) *HERE* x')
    T(['a', 1, 'z'], 'a, 1, z) x', convert=True, annotate='a, 1, z) *HERE* x')
    T(['a b'], 'a b) x', annotate='a b) *HERE* x')
    T(['(a, 1)', 'z'], '(a, 1), z)', annotate='(a, 1), z) *HERE*')

    # syntax errors

    T(None, 'a, 1, z', exception=resource_exceptions.ExpressionSyntaxError,
      annotate='a, 1, z *HERE*')
    T(None, 'a,', exception=resource_exceptions.ExpressionSyntaxError,
      annotate='a, *HERE*')
    T(None, 'a', exception=resource_exceptions.ExpressionSyntaxError,
      annotate='a *HERE*')
    T(None, 'a', exception=resource_exceptions.ExpressionSyntaxError,
      annotate='a *HERE*')
    T(None, '', exception=resource_exceptions.ExpressionSyntaxError,
      annotate='*HERE*')
    T(None, ',', exception=resource_exceptions.ExpressionSyntaxError,
      annotate=', *HERE*')
    T(None, '(a, 1), z', exception=resource_exceptions.ExpressionSyntaxError,
      annotate='(a, 1), z *HERE*')


class ParseKeyTest(subtests.Base):

  def RunSubTest(self, name):
    return resource_lex.ParseKey(name)

  def testParseKey(self):
    """These are the inverse of the testGetKeyName subtests below."""

    def T(expected, name, exception=None):
      self.Run(expected, name, exception=exception, depth=2)

    T([], '.')
    T([None], '[]')
    T([123], '[123]')
    T([-1], '[-1]')
    T(['a', None], 'a[]')
    T(['a', 123], 'a[123]')
    T(['a', -1], 'a[-1]')
    T([None, 'a'], '[].a')
    T([123, 'a'], '[123].a')
    T([-1, 'a'], '[-1].a')
    T(['a', None, 'z'], 'a[].z')
    T(['a', 123, 'z'], 'a[123].z')
    T(['a', -1, 'z'], 'a[-1].z')
    T(['a', 'b', 'c', 'd'], 'a.b.c.d')
    T(['x', 'y'], 'x.y')
    T(['x', None, 'y'], 'x[].y')
    T(['x', 123, 'y'], 'x[123].y')
    T(['x', -1, 'y'], 'x[-1].y')
    T(['x', 'a&b', 'y'], 'x."a&b".y')
    T(['x', 'a "2" b', 'y'], 'x."a \\"2\\" b".y')
    T(['a.b', 'y.z'], '"a.b"."y.z"')
    T(['@a', 'z'], '@a.z')
    T(None, 'a:b', exception=resource_exceptions.ExpressionSyntaxError)


class GetKeyNameTest(subtests.Base):

  def RunSubTest(self, key):
    return resource_lex.GetKeyName(key)

  def testGetKeyName(self):
    """These are the inverse of the testParseKey subtests above."""

    def T(expected, key):
      self.Run(expected, key, depth=2)

    T('.', [])
    T('[]', [None])
    T('[123]', [123])
    T('[-1]', [-1])
    T('a[]', ['a', None])
    T('a[123]', ['a', 123])
    T('a[-1]', ['a', -1])
    T('[].a', [None, 'a'])
    T('[123].a', [123, 'a'])
    T('[-1].a', [-1, 'a'])
    T('a[].z', ['a', None, 'z'])
    T('a[123].z', ['a', 123, 'z'])
    T('a[-1].z', ['a', -1, 'z'])
    T('a.b.c.d', ['a', 'b', 'c', 'd'])
    T('x.y', ['x', 'y'])
    T('x[].y', ['x', None, 'y'])
    T('x[123].y', ['x', 123, 'y'])
    T('x[-1].y', ['x', -1, 'y'])
    T('x."a&b".y', ['x', 'a&b', 'y'])
    T('x."a \\"2\\" b".y', ['x', 'a "2" b', 'y'])
    T('"a.b"."y.z"', ['a.b', 'y.z'])
    T('@a.z', ['@a', 'z'])
    T('labels.a-z', ['labels', 'a-z'])
    T('foo."abc+xyz"', ['foo', 'abc+xyz'])


if __name__ == '__main__':
  test_case.main()
