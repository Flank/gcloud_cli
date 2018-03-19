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
"""Unit tests for the command_lib.meta.debug module."""
from tests.lib import test_case


class DebugTest(test_case.TestCase):

  def testImport(self):
    # If it imports, it's probably okay. This command isn't critical for users.
    # pylint: disable=g-import-not-at-top
    from googlecloudsdk.command_lib.meta import debug  # pylint: disable=unused-variable


if __name__ == '__main__':
  test_case.main()
