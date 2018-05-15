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

"""Cloud resource filter expression S-expression rewrite backend.

This class is an alternate resource_filter.Compile backend that rewrites
expressions instead of evaluating them. To rewrite a filter expression string
to an S-expression string:

  rewriter = s_expr.Backend()
  frontend_expr, backend_expr = rewriter.Rewrite(filter_expression_string)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_expr_rewrite


class Backend(resource_expr_rewrite.BackendBase):
  """Cloud resource filter expression S-expression test rewrite backend."""

  _OPERATORS = {'<': 'LT', '<=': 'LE', ':': 'IN', '=': 'EQ', '!=': 'NE',
                '>=': 'GE', '>': 'GT', '~': 'RE', '!~': 'NRE'}

  def RewriteAND(self, left, right):
    """Rewrites <left AND right>."""
    return '(AND {left} {right})'.format(left=left, right=right)

  def RewriteOR(self, left, right):
    """Rewrites <left OR right>."""
    return '(OR {left} {right})'.format(left=left, right=right)

  def RewriteNOT(self, expr):
    """Rewrites <NOT expr>."""
    return '(NOT {expr})'.format(expr=expr)

  def RewriteTerm(self, key, op, operand, key_type):
    """Rewrites <key op operand>."""
    del key_type  # unused in RewriteTerm
    op = self._OPERATORS.get(op)
    if not op:
      return None
    return '({op} {key} {operand})'.format(
        op=op,
        key='(GET {key})'.format(key=self.Quote(key, always=True)),
        operand=self.QuoteOperand(operand, always=True))


class SupportedKeyBackend(Backend):
  """S-expression backend with supported key check."""

  def __init__(self, supported_key=None, **kwargs):
    self._super = super(SupportedKeyBackend, self)
    self._super.__init__(**kwargs)
    self.supported_key = supported_key or (lambda x: True)

  def RewriteTerm(self, key, op, operand, key_type):
    """Checks if key is supported before doing rewrite."""
    if not self.supported_key(key):
      return None
    return self._super.RewriteTerm(key, op, operand, key_type)
