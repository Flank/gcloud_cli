# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Cloud SDK parameterized test line number label support.

A simple example:

  from tests.lib import parameterized
  from tests.lib import parameterized_line_no

  T = parameterized_line_no.LineNo

  class AdditionExample(parameterized.TestCase):
    @parameterized.named_parameters(
       T(1, 2, 3),
       T(4, 5, 9),
       T(1, 1, 3))
    def testAddition(self, op1, op2, result):
      self.assertEqual(result, op1 + op2)

Each invocation is a separate test case and properly isolated just
like a normal test method, with its own setUp/tearDown cycle. The test
case names will have the string :<line-no>: appended, where <line-no>
is the test module source line number of the test case parameters
(the line number of the closing paren if the parameters span multiple lines).

If a parameterized test fails, the error message will show the original test
name plus :<line-no>:, and the arguments for the specific invocation.

These tests also have the benefit that they can be run individually
from the command line:

  $ testmodule.py AdditionExample.testAddition:23:

runs the subtests for the parameters on line 23.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import inspect


def LineNo(*args):
  """Inserts the current line number into the parameters name field."""
  lineno = inspect.currentframe().f_back.f_lineno
  name = ':{}:'.format(lineno)
  return [name] + list(args)
