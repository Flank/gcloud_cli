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
"""Tests for Spanner operations describe command."""

from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class OperationsDescribeTest(base.SpannerTestBase):
  """Cloud Spanner operations describe tests."""

  def testDescribeDatabaseOp(self):
    response = self.msgs.Operation(name='testop')
    ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'projectsId': self.Project(),
            'instancesId': 'insId',
            'databasesId': 'dbId',
        },
        collection='spanner.projects.instances.databases.operations')
    self.client.projects_instances_databases_operations.Get.Expect(
        request=
        self.msgs.SpannerProjectsInstancesDatabasesOperationsGetRequest(
            name=ref.RelativeName()),
        response=response)
    self.Run('spanner operations describe opId --instance insId '
             '--database dbId')
    self.AssertOutputContains('testop')

  def testDescribeInstanceOp(self):
    response = self.msgs.Operation(name='testop')
    ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'projectsId': self.Project(),
            'instancesId': 'insId',
        },
        collection='spanner.projects.instances.operations')
    self.client.projects_instances_operations.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesOperationsGetRequest(
            name=ref.RelativeName()),
        response=response)
    self.Run('spanner operations describe opId --instance insId')
    self.AssertOutputContains('testop')
