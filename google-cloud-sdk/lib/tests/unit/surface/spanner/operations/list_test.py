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
"""Tests for Spanner operations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class OperationsListTest(base.SpannerTestBase):
  """Cloud Spanner operations list tests."""

  def testListDatabaseOp(self):
    response = self.msgs.ListOperationsResponse(operations=[
        self.msgs.Operation(name='op1'),
        self.msgs.Operation(name='op2')
    ])
    ref = resources.REGISTRY.Parse(
        'dbId',
        params={
            'projectsId': self.Project(),
            'instancesId': 'insId',
        },
        collection='spanner.projects.instances.databases')
    self.client.projects_instances_databases_operations.List.Expect(
        request=
        self.msgs.SpannerProjectsInstancesDatabasesOperationsListRequest(
            name=ref.RelativeName()+'/operations', pageSize=100),
        response=response)
    self.Run('spanner operations list --instance insId '
             '--database dbId')
    self.AssertOutputContains('op1')
    self.AssertOutputContains('op2')

  def testListInstanceOp(self):
    response = self.msgs.ListOperationsResponse(operations=[
        self.msgs.Operation(name='op1'),
        self.msgs.Operation(name='op2')
    ])
    ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')
    self.client.projects_instances_operations.List.Expect(
        request=
        self.msgs.SpannerProjectsInstancesOperationsListRequest(
            name=ref.RelativeName()+'/operations', pageSize=100),
        response=response)
    self.Run('spanner operations list --instance insId')
    self.AssertOutputContains('op1')
    self.AssertOutputContains('op2')
