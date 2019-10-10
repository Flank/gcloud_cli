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

"""Tests of the 'gcloud meta apis collections list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.util.apis import registry
from tests.lib import cli_test_base
from tests.lib.command_lib.util.apis import base


class ListTest(base.Base, cli_test_base.CliTestBase):

  def testList(self):
    self.Run('meta apis collections list --api=compute --api-version=beta')
    self.AssertOutputContains('addresses')
    self.AssertOutputContains('disks')

  def testListDefaultVersion(self):
    self.Run('meta apis collections list --api=compute')
    self.AssertOutputContains('addresses')
    self.AssertOutputContains('disks')

  def testListAll(self):
    self.Run('meta apis collections list')
    self.AssertOutputContains('compute.')
    self.AssertOutputContains('appengine.')

  def testListMissingAPI(self):
    with self.assertRaisesRegex(registry.UnknownAPIError,
                                r'\[x\] does not exist'):
      self.Run('meta apis collections list --api=x --api-version=v1')

  def testListMissingVersion(self):
    with self.assertRaisesRegex(
        registry.UnknownAPIVersionError,
        r'Version \[v12345\] does not exist for API \[compute\].'):
      self.Run('meta apis collections list --api=compute --api-version=v12345')

  def testListVersionNoAPI(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [--api]: The --api-version flag can only be '
        'specified when using the --api flag.'):
      self.Run('meta apis collections list --api-version=v12345')

  def testListWithMockedCollections(self):
    self.MockCollections(('foo.projects.clusters', False),
                         ('foo.projects.clusters.instances', True))
    self.Run('meta apis collections list --api=foo --api-version=v1')
    self.AssertOutputEquals("""\
COLLECTION_NAME                  DETAILED_PATH
foo.projects.clusters            projects/{projectsId}/clusters/{clustersId}
foo.projects.clusters.instances  projects/{projectsId}/clusters/{clustersId}/instances/{instancesId}
""")

  def testNoDefault(self):
    self.MockAPIs(('foo', 'v1', False))
    with self.AssertRaisesExceptionMatches(
        registry.NoDefaultVersionError,
        'API [foo] does not have a default version.'):
      self.Run('meta apis collections list --api=foo')

  def testCompletion(self):
    self.MockAPIs(
        ('foo', 'v1', True),
        ('bar', 'v1', True),
        ('baz', 'v1', True))
    self.RunCompletion('meta apis collections list --api b', ['bar', 'baz'])


if __name__ == '__main__':
  cli_test_base.main()
