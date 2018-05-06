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
"""Tests for common App Engine flags."""
from __future__ import absolute_import
import string

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.app import flags
from tests.lib import subtests
from tests.lib import test_case


class VersionValidationTest(subtests.Base):
  """Tests for the VERESION_TYPE flag validation.

  - May only contain lowercase letters, digits, and hyphens.
  - Must begin and end with a letter or digit.
  - Must not exceed 63 characters.
  """

  _VALID_CHARS = set(string.ascii_lowercase + string.digits + '-')
  _INVALID_CHARS = set(string.printable) - _VALID_CHARS

  def RunSubTest(self, value, **kwargs):
    del kwargs  # Unused by RunSubTest
    return flags.VERSION_TYPE(value)

  def testVersionType_Valid(self):
    """Test that valid flag values are accepted."""
    def T(value):
      self.Run(value, value, depth=2)

    T('a')  # Minimum length
    T('a' * 63)  # Maximum length

    for char in self._VALID_CHARS:  # All valid characters
      T('a{}a'.format(char))

    for char in self._VALID_CHARS - set('-'):  # Valid start/end characters
      T('{0}a{0}'.format(char))

  def testVersionType_Invalid(self):
    """Test that invalid flag values are not accepted."""
    def T(value):
      self.Run(value, value, depth=2, exception=arg_parsers.ArgumentTypeError)

    T('')  # Empty string
    T('a' * 64)  # String exceeding maximum length

    for s in self._INVALID_CHARS:  # Any invalid characters
      T('a{}a'.format(s))

    for s in self._INVALID_CHARS | set('-'):  # Invalid start/end characters
      T('{0}a{0}'.format(s))


if __name__ == '__main__':
  test_case.main()
