# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Unit tests for the resource_filter_scrub module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core.resource import resource_filter_scrub
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_projection_parser
from tests.lib import subtests
from tests.lib import test_case


class ResourceFilterTest(subtests.Base):

  def SetUp(self):
    aliases = {
        'i': resource_lex.Lexer('integer').Key(),
        'v': resource_lex.Lexer('compound.string.value').Key(),
    }
    self.defaults = resource_projection_parser.Parse(
        '(compound.string:alias=s, floating:alias=f)',
        aliases=aliases)
    self.rewrite = resource_filter_scrub.Backend().Rewrite

  def RunSubTest(self, expression):
    """Only interested in the rewrite backend_expression (the scrubbed one)."""
    _, scrubbed_expression = self.rewrite(expression, defaults=self.defaults)
    return scrubbed_expression

  def testResourceFilter(self):

    def T(expected, expression):
      self.Run(expected, expression, depth=2)

    # empty expression

    T(None, '')

    T('x:X', 'x:3')
    T('NOT x:X', '-x:3')
    T('NOT x:X', 'NOT x:3')

    T('x<X', 'x<2')
    T('x<=X', 'x<=2')
    T('x=X', 'x=2')
    T('x!=X', 'x!=2')
    T('x>=X', 'x>=2')
    T('x>X', 'x>2')
    T(None, 'x~xyz')
    T(None, 'x!~xyz')

    T('x:X', 'x:(a,b,c)')
    T('x:X', 'x:(a OR b OR c)')
    T('x=X', 'x=(a,b,c)')
    T('x=X', 'x=(a OR b OR c)')

    T('x=X', 'x="compound string"')
    T('x=X', 'x="compound \"quoted\" string"')

    # OR precedence over adjacent conjunction

    T('x:X AND (x:X OR x:X)', 'x:0 x:0 OR x:0')
    T('(x:X AND x:X) OR x:X', '(x:0 x:0) OR x:0')
    T('x:X AND (x:X OR x:X)', 'x:0 AND (x:0 OR x:0)')

    T('(x:X OR x:X) AND x:X', 'x:0 OR x:0 x:0')
    T('x:X OR (x:X AND x:X)', 'x:0 OR (x:0 x:0)')
    T('(x:X OR x:X) AND x:X', '(x:0 OR x:0) AND x:0')

    T('x=X OR y=X', 'x=2 OR y=3.14')
    T('x=X AND y=X', 'x=2 y=3.14')
    T('x=X AND y=X', 'x=2 ( y=3.14 )')
    T('x=X AND y=X', '( x=2 ) y=3.14')
    T('x=X AND y=X', '( x=2 y=3.14 )')

    # AND, NOT OR and (...) combinations

    T('x:X AND (x:X OR x:X)', 'x:1 AND ( x:1 OR x:1 )')
    T('(x:X OR x:X) AND x:X', '( x:1 OR x:1 ) AND x:1')
    T('NOT x:X AND (x:X OR x:X)', 'NOT x:1 AND ( x:1 OR x:1 )')
    T('NOT (x:X OR x:X) AND x:X', 'NOT ( x:1 OR x:1 ) AND x:1')

    # OnePlatform queries have non-standard OR >>> AND precedence. Cloud SDK
    # requires parentheses when AND and OR are combined to clarify user intent.

    # This group adds (...) to achieve standard AND/OR precedence.

    T('(x>X AND y>X) OR x>X', '(x>0 AND y>0) OR x>0')
    T('x>X OR (x>X AND y>X)', 'x>0 OR (x>0 AND y>0)')
    T('(NOT x>X AND y>X) OR x>X', '(NOT x>0 AND y>0) OR x>0')
    T('NOT x>X OR (x>X AND y>X)', 'NOT x>0 OR (x>0 AND y>0)')
    T('(x:X AND x:X) OR x:X', '(x:0 AND x:0) OR x:0')
    T('(x:X AND x:X) OR x:X', '(x:2 AND x:0) OR x:2')
    T('x:X OR (x:X AND x:X)', 'x:0 OR (x:0 AND x:0)')
    T('x:X OR (x:X AND x:X)', 'x:0 OR (x:2 AND x:2)')

    # (...) nesting

    T('(x:X OR x:X) AND (x:X OR x:X)', '( x:0 OR x:0 ) AND ( x:0 OR x:0 )')

    # global restrctions

    T('X AND (NOT X AND X)', 'moe -larry curly')


if __name__ == '__main__':
  test_case.main()
