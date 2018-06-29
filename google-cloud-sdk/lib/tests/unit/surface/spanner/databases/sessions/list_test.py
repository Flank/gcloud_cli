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
"""Tests for Spanner databases sessions list command."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class DatabasesListSessionsTest(base.SpannerTestBase):
  """Cloud Spanner databases sessions list tests."""

  def SetUp(self):
    self.db_ref = resources.REGISTRY.Parse(
        'mydb',
        params={
            'projectsId': self.Project(),
            'instancesId': 'myins',
        },
        collection='spanner.projects.instances.databases')

  def testList(self):
    self.client.projects_instances_databases_sessions.List.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesSessionsListRequest(
            database=self.db_ref.RelativeName()),
        response=self.msgs.ListSessionsResponse(sessions=[
            self.msgs.Session(
                approximateLastUseTime='2017-08-29T15:37:56.325712Z',
                createTime='2017-08-29T15:37:58.325712Z',
                name='sdfk002jkjlkj4R')
        ]))
    self.Run(
        'spanner databases sessions list --database {} --instance myins'.format(
            self.db_ref.Name()))
    self.AssertOutputEquals(r"""---
approximateLastUseTime: '2017-08-29T15:37:56.325712Z'
createTime: '2017-08-29T15:37:58.325712Z'
name: sdfk002jkjlkj4R
""")

  def testListWithFilter(self):
    server_filter = 'labels.aLabel:*'

    self.client.projects_instances_databases_sessions.List.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesSessionsListRequest(
            database=self.db_ref.RelativeName(), filter=server_filter),
        response=self.msgs.ListSessionsResponse(sessions=[
            self.msgs.Session(
                approximateLastUseTime='2017-08-29T15:37:56.325712Z',
                createTime='2017-08-29T15:37:58.325712Z',
                name='sdfk002jkjlkj4R',
                labels=self.msgs.Session.LabelsValue(additionalProperties=[
                    self.msgs.Session.LabelsValue.AdditionalProperty(
                        key='aLabel', value='stuff')
                ]))
        ]))
    self.Run('spanner databases sessions list --database {} --instance myins'
             ' --server-filter {}'.format(self.db_ref.Name(), server_filter))
    self.AssertOutputEquals(r"""---
approximateLastUseTime: '2017-08-29T15:37:56.325712Z'
createTime: '2017-08-29T15:37:58.325712Z'
labels:
  aLabel: stuff
name: sdfk002jkjlkj4R
""")
