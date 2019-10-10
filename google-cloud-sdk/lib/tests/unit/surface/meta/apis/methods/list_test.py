# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Tests of the 'gcloud meta apis methods list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.apis import registry
from tests.lib import cli_test_base
from tests.lib.command_lib.util.apis import base


class ListTest(base.Base, cli_test_base.CliTestBase):

  def testList(self):
    self.Run('meta apis methods list --api-version=beta '
             '--collection=compute.instances')
    self.AssertOutputContains('aggregatedList')
    self.AssertOutputContains('get')

  def testListDefaultVersion(self):
    self.Run('meta apis methods list --collection=compute.instances')
    self.AssertOutputContains('aggregatedList')
    self.AssertOutputContains('get')

  def testListMissingAPI(self):
    with self.assertRaisesRegex(registry.UnknownAPIError,
                                r'\[x\] does not exist'):
      self.Run('meta apis methods list --api-version=v1 '
               '--collection=x.instances')

  def testListMissingVersion(self):
    with self.assertRaisesRegex(
        registry.UnknownAPIVersionError,
        r'Version \[v12345\] does not exist for API \[compute\].'):
      self.Run(
          'meta apis methods list --api-version=v12345 '
          '--collection=compute.instances')

  def testListNoDefault(self):
    self.MockAPIs(('something', 'v1', False))
    with self.assertRaisesRegex(
        registry.NoDefaultVersionError,
        r'API \[something\] does not have a default version.'):
      self.Run('meta apis methods list --collection=something.projects.foo')

  def testCompletion(self):
    self.MockCollections(('foo.projects.clusters', False),
                         ('foo.projects.clusters.instances', True))
    self.RunCompletion(
        'meta apis methods list --collection f',
        ['foo.projects.clusters', 'foo.projects.clusters.instances'])


if __name__ == '__main__':
  cli_test_base.main()
