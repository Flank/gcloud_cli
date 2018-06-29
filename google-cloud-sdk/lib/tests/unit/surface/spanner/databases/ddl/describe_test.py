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
"""Tests for Spanner databases ddl describe command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class DatabasesDdlDescribeTest(base.SpannerTestBase):
  """Cloud Spanner databases ddl describe tests."""

  def SetUp(self):
    self.db_ref = resources.REGISTRY.Parse(
        'mydb',
        params={
            'projectsId': self.Project(),
            'instancesId': 'myins',
        },
        collection='spanner.projects.instances.databases')

  def testDescribe(self):
    self.client.projects_instances_databases.GetDdl.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesGetDdlRequest(
            database=self.db_ref.RelativeName()),
        response=self.msgs.GetDatabaseDdlResponse(
            statements=['CREATE TABLE foo', 'CREATE TABLE bar']))
    self.Run('spanner databases ddl describe mydb --instance myins')
    self.AssertOutputContains('CREATE TABLE foo')
    self.AssertOutputContains('CREATE TABLE bar')

  def testDescribeWithDefaultInstance(self):
    self.client.projects_instances_databases.GetDdl.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesGetDdlRequest(
            database=self.db_ref.RelativeName()),
        response=self.msgs.GetDatabaseDdlResponse(
            statements=['CREATE TABLE foo']))
    self.Run('config set spanner/instance myins')
    self.Run('spanner databases ddl describe mydb')
    self.AssertOutputContains('CREATE TABLE foo')
