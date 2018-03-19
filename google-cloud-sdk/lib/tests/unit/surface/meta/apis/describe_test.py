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

"""Tests of the 'gcloud meta apis describe' command."""

from googlecloudsdk.command_lib.util.apis import registry
from tests.lib import cli_test_base
from tests.lib.command_lib.util.apis import base


class DescribeTest(base.Base, cli_test_base.CliTestBase):

  def testDescribe(self):
    self.Run('meta apis describe compute --api-version=beta')
    self.AssertOutputContains('name: compute')
    self.AssertOutputContains('version: beta')

  def testDescribeDefaultVersion(self):
    self.Run('meta apis describe compute')
    self.AssertOutputContains('name: compute')
    self.AssertOutputContains('version: v1')

  def testDescribeMissingAPI(self):
    with self.assertRaisesRegexp(registry.UnknownAPIError,
                                 r'\[asdfasdf\] does not exist'):
      self.Run('meta apis describe asdfasdf --api-version=v1')

  def testDescribeMissingVersion(self):
    with self.assertRaisesRegexp(
        registry.UnknownAPIVersionError,
        r'Version \[v12345\] does not exist for API \[compute\].'):
      self.Run('meta apis describe compute --api-version=v12345')

  def testCompletion(self):
    self.MockAPIs(
        ('foo', 'v1', True),
        ('bar', 'v1', True),
        ('baz', 'v1', True))
    self.RunCompletion('meta apis describe b', ['bar', 'baz'])


if __name__ == '__main__':
  cli_test_base.main()
