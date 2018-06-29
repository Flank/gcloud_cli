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

"""Tests of the 'gcloud meta apis messages describe' command."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.util.apis import registry
from tests.lib import cli_test_base
from tests.lib.command_lib.util.apis import base


class DescribeTest(base.Base, cli_test_base.CliTestBase):

  def testDescribe(self):
    self.Run(
        'meta apis messages describe --api compute --api-version v1 Instance')
    self.AssertOutputContains('canIpForward:')

  def testDescribeDefaultVersion(self):
    self.Run('meta apis messages describe --api compute Instance')
    self.AssertOutputContains('canIpForward:')

  def testDescribeMissingVersion(self):
    with self.assertRaisesRegex(
        registry.UnknownAPIVersionError,
        r'Version \[v0\] does not exist for API \[compute\].'):
      self.Run(
          'meta apis messages describe --api compute --api-version v0 Instance')

  def testDescribeInvalidCollection(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[message\]: Message \[asdf\] does not exist for '
        r'API \[compute\]'):
      self.Run(
          'meta apis messages describe --api compute asdf')

  def testCompletion(self):
    self.MockCollections(('foo.projects.clusters', False))
    self.RunCompletion('meta apis messages describe --api f', ['foo'])


if __name__ == '__main__':
  cli_test_base.main()
