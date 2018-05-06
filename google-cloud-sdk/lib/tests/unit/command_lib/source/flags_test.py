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
"""Tests for command_lib.source.flags."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.source import flags
from tests.lib import subtests
from tests.lib import test_case


class RepoNameValidatorTest(subtests.Base):

  def Good(self, name):
    self.Run(name, name, depth=2)

  def Bad(self, name):
    self.Run(None, name, depth=2, exception=arg_parsers.ArgumentTypeError)

  def RunSubTest(self, name):
    return flags.REPO_NAME_VALIDATOR(name)

  def testInvalidNames(self):
    self.Bad('-startswithhyphen')  # May not start with a hyphen
    self.Bad('a' * 129)  # Limit of 128

  def testValidNames(self):
    self.Good('a' * 3)  # May have 3 characters
    self.Good('a' * 128)  # May have 128 characters
    self.Good('a-aa-a')  # May have hyphens in the middle
    self.Good('aaaaa1')  # May end with a number
    self.Good('_')       # May be just an underscore

    self.Good('may_have_underscores')  # May have underscores
    self.Good('to/be/or/not/to/be')  # May have slashes


if __name__ == '__main__':
  test_case.main()
