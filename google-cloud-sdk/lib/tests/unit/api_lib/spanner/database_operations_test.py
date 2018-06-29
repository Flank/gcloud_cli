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
"""Tests for Spanner database operations library."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.spanner import database_operations
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class DatabaseOperationsClientTest(base.SpannerTestBase):

  def testAwait(self):
    result = self.msgs.Operation.ResponseValue()
    ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'instancesId': 'insId',
            'databasesId': 'dbId',
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.databases.operations')
    not_done = self.msgs.Operation(name=ref.RelativeName())
    done = self.msgs.Operation(
        name=ref.RelativeName(), done=True, response=result)
    self.client.projects_instances_databases_operations.Get.Expect(
        request=
        self.msgs.SpannerProjectsInstancesDatabasesOperationsGetRequest(
            name=ref.RelativeName()),
        response=not_done)
    self.client.projects_instances_databases_operations.Get.Expect(
        request=
        self.msgs.SpannerProjectsInstancesDatabasesOperationsGetRequest(
            name=ref.RelativeName()),
        response=done)
    self.assertEqual(
        database_operations.Await(not_done, ''), result)

  def testCancel(self):
    response = self.msgs.Empty()
    ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'instancesId': 'insId',
            'databasesId': 'dbId',
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.databases.operations')
    self.client.projects_instances_databases_operations.Cancel.Expect(
        request=
        self.msgs.SpannerProjectsInstancesDatabasesOperationsCancelRequest(
            name=ref.RelativeName()),
        response=response)
    self.assertEqual(
        database_operations.Cancel('insId', 'dbId', 'opId'), response)

  def testGet(self):
    response = self.msgs.Operation()
    ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'instancesId': 'insId',
            'databasesId': 'dbId',
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.databases.operations')
    self.client.projects_instances_databases_operations.Get.Expect(
        request=
        self.msgs.SpannerProjectsInstancesDatabasesOperationsGetRequest(
            name=ref.RelativeName()),
        response=response)
    self.assertEqual(
        database_operations.Get('insId', 'dbId', 'opId'), response)

  def testList(self):
    operation = self.msgs.Operation()
    response = self.msgs.ListOperationsResponse(
        operations=[operation])
    ref = resources.REGISTRY.Parse(
        'dbId',
        params={
            'instancesId': 'insId',
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.databases')
    self.client.projects_instances_databases_operations.List.Expect(
        request=
        self.msgs.SpannerProjectsInstancesDatabasesOperationsListRequest(
            name=ref.RelativeName()+'/operations', pageSize=100),
        response=response)
    self.assertCountEqual(
        database_operations.List('insId', 'dbId'), [operation])
