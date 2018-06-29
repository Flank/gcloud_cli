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

"""Tests of the 'gcloud meta apis list' command."""

from __future__ import absolute_import
from __future__ import unicode_literals

from tests.lib import cli_test_base
from tests.lib.command_lib.util.apis import base


class ListTest(base.Base, cli_test_base.CliTestBase):

  def testList(self):
    self.Run('meta apis list')
    self.AssertOutputContains('appengine')
    self.AssertOutputContains('compute')

  def testListWithMockedAPIs(self):
    self.MockAPIs(
        ('foo', 'v1', False),
        ('foo', 'v2', True),
        ('bar', 'v1', True),
        ('baz', 'v1', True))
    self.Run('meta apis list')
    self.AssertOutputEquals("""\
NAME  VERSION  IS_DEFAULT  BASE_URL
bar   v1       *           https://bar.googleapis.com/
baz   v1       *           https://baz.googleapis.com/
foo   v1                   https://foo.googleapis.com/
foo   v2       *           https://foo.googleapis.com/
""")


if __name__ == '__main__':
  cli_test_base.main()
