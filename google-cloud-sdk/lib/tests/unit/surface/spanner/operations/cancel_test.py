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
"""Tests for Spanner operations cancel command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class OperationsCancelTest(base.SpannerTestBase):
  """Cloud Spanner operations cancel tests."""

  def testCancelDatabaseOp(self):
    response = self.msgs.Empty()
    ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'projectsId': self.Project(),
            'instancesId': 'insId',
            'databasesId': 'dbId',
        },
        collection='spanner.projects.instances.databases.operations')
    self.client.projects_instances_databases_operations.Cancel.Expect(
        request=
        self.msgs.SpannerProjectsInstancesDatabasesOperationsCancelRequest(
            name=ref.RelativeName()),
        response=response)
    self.Run('spanner operations cancel opId --instance insId '
             '--database dbId')

  def testCancelInstanceOp(self):
    response = self.msgs.Empty()
    ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'projectsId': self.Project(),
            'instancesId': 'insId',
        },
        collection='spanner.projects.instances.operations')
    self.client.projects_instances_operations.Cancel.Expect(
        request=self.msgs.SpannerProjectsInstancesOperationsCancelRequest(
            name=ref.RelativeName()),
        response=response)
    self.Run('spanner operations cancel opId --instance insId')
