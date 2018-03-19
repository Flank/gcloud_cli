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
"""Tests for Spanner databases sessions delete command."""
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class DatabasesListSessionsTest(base.SpannerTestBase):
  """Cloud Spanner databases list sessions tests."""

  def SetUp(self):
    self.session_ref = resources.REGISTRY.Parse(
        'mysession',
        params={
            'projectsId': self.Project(),
            'instancesId': 'myins',
            'databasesId': 'mydb',
        },
        collection='spanner.projects.instances.databases.sessions')

  def testDelete(self):
    self.client.projects_instances_databases_sessions.Delete.Expect(
        request=self.msgs.
        SpannerProjectsInstancesDatabasesSessionsDeleteRequest(
            name=self.session_ref.RelativeName()),
        response=self.msgs.Empty())
    self.Run('spanner databases sessions delete mysession --database mydb '
             '--instance myins')

  def testDeleteWithDefaultInstance(self):
    self.client.projects_instances_databases_sessions.Delete.Expect(
        request=self.msgs.
        SpannerProjectsInstancesDatabasesSessionsDeleteRequest(
            name=self.session_ref.RelativeName()),
        response=self.msgs.Empty())
    self.Run('config set spanner/instance myins')
    self.Run('spanner databases sessions delete mysession --database mydb')
