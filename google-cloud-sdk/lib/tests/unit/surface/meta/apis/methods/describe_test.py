# -*- coding: utf-8 -*- #
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

"""Tests of the 'gcloud meta apis methods describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.apis import registry
from tests.lib import cli_test_base
from tests.lib.command_lib.util.apis import base


class DescribeTest(base.Base, cli_test_base.CliTestBase):

  def testDescribe(self):
    self.Run(
        'meta apis methods describe --api-version=beta '
        '--collection=compute.disks get')
    self.AssertOutputContains(
        'path: projects/{project}/zones/{zone}/disks/{disk}')

  def testDescribeOnePlatform(self):
    self.Run(
        'meta apis methods describe --api-version=v1 '
        '--collection=pubsub.projects.topics get')
    self.AssertOutputContains("path: '{+topic}'")

  def testDescribeDefaultVersion(self):
    self.Run('meta apis methods describe --collection=compute.disks get')
    self.AssertOutputContains(
        'path: projects/{project}/zones/{zone}/disks/{disk}')

  def testDescribeMissingAPI(self):
    with self.assertRaisesRegex(registry.UnknownAPIError,
                                r'\[x\] does not exist'):
      self.Run('meta apis methods describe --api-version=v1 '
               '--collection=x.disks get')

  def testDescribeMissingVersion(self):
    with self.assertRaisesRegex(
        registry.UnknownAPIVersionError,
        r'Version \[v12345\] does not exist for API \[compute\].'):
      self.Run(
          'meta apis methods describe --api-version=v12345 '
          '--collection=compute.disks get ')

  def testDescribeMissingCollection(self):
    with self.assertRaisesRegex(registry.UnknownCollectionError,
                                r'\[x\] does not exist'):
      self.Run('meta apis methods describe --api-version=v1 '
               '--collection=compute.x get')

  def testDescribeMissingMethod(self):
    with self.assertRaisesRegex(
        registry.UnknownMethodError,
        r'Method \[x\] does not exist for collection \[compute.disks\].'):
      self.Run('meta apis methods describe --api-version=v1 '
               '--collection=compute.disks x')

  def testCollectionCompletion(self):
    self.MockCollections(('foo.projects.clusters', False),
                         ('foo.projects.clusters.instances', True))
    self.RunCompletion(
        'meta apis methods describe --collection f',
        ['foo.projects.clusters', 'foo.projects.clusters.instances'])

  def testMethodCompletion(self):
    self.MockCRUDMethods(('foo.projects.clusters', False),
                         ('bar.projects.clusters', True))
    self.RunCompletion(
        'meta apis methods describe --collection foo.projects.clusters ',
        ['get', 'patch', 'list', 'create'])
    self.RunCompletion(
        'meta apis methods describe --collection bar.projects.clusters ',
        ['get', 'patch', 'list', 'create'])


if __name__ == '__main__':
  cli_test_base.main()
