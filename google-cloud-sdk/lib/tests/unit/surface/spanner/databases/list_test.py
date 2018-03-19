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
"""Tests for Spanner databases list command."""

from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class DatabasesListTest(base.SpannerTestBase):
  """Cloud Spanner databases list tests."""

  def SetUp(self):
    self.ins_ref = resources.REGISTRY.Parse(
        'myins',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')

  def testList(self):
    self.client.projects_instances_databases.List.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesListRequest(
            parent=self.ins_ref.RelativeName(), pageSize=100),
        response=self.msgs.ListDatabasesResponse(databases=[
            self.msgs.Database(name='db1'),
            self.msgs.Database(name='db2')
        ]))
    self.Run('spanner databases list --instance myins')
    self.AssertOutputContains('db1')
    self.AssertOutputContains('db2')
