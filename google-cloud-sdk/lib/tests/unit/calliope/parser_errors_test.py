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

"""Unit tests for the parser_errors module."""

from googlecloudsdk.calliope import parser_errors
from tests.lib import test_case


class ArgumentErrorTest(test_case.Base):

  def testArgumentErrorOK(self):
    e = parser_errors.ArgumentError('abc [{info}] xyz', info='TEST INFO')
    self.assertEquals('abc [TEST INFO] xyz', str(e))

  def testArgumentErrorUnknownKey(self):
    e = parser_errors.ArgumentError('abc [{info}] xyz', data='TEST INFO')
    self.assertEquals('abc [{info}] xyz', str(e))

  def testArgumentErrorBadSpec(self):
    e = parser_errors.ArgumentError('abc [{:3}] xyz')
    self.assertEquals('abc [{:3}] xyz', str(e))

  def testArgumentErrorUnbalanced(self):
    e = parser_errors.ArgumentError('abc [{info] xyz', info='TEST INFO')
    self.assertEquals('abc [{info] xyz', str(e))


if __name__ == '__main__':
  test_case.main()
