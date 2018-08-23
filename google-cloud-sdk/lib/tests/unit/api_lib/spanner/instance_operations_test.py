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
"""Tests for Spanner instance operations library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types
from googlecloudsdk.api_lib.spanner import instance_operations
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class InstanceOperationsClientTest(base.SpannerTestBase):

  def testAwait(self):
    instance = self.msgs.Instance()
    result = self.msgs.Operation.ResponseValue(
        additionalProperties=[
            self.msgs.Operation.ResponseValue.AdditionalProperty(
                key='name',
                value=extra_types.JsonValue(string_value='resultname'))])
    ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'instancesId': 'insId',
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.operations')
    not_done = self.msgs.Operation(name=ref.RelativeName())
    done = self.msgs.Operation(
        name=ref.RelativeName(), done=True, response=result)
    self.client.projects_instances_operations.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesOperationsGetRequest(
            name=ref.RelativeName()),
        response=not_done)
    self.client.projects_instances_operations.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesOperationsGetRequest(
            name=ref.RelativeName()),
        response=done)
    self.client.projects_instances.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesOperationsGetRequest(
            name='resultname'),
        response=instance)
    self.assertEqual(
        instance_operations.Await(not_done, ''), instance)

  def testCancel(self):
    response = self.msgs.Empty()
    ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'instancesId': 'insId',
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.operations')
    self.client.projects_instances_operations.Cancel.Expect(
        request=self.msgs.SpannerProjectsInstancesOperationsCancelRequest(
            name=ref.RelativeName()),
        response=response)
    self.assertEqual(
        instance_operations.Cancel('insId', 'opId'), response)

  def testGet(self):
    response = self.msgs.Operation()
    ref = resources.REGISTRY.Parse(
        'opId',
        params={
            'instancesId': 'insId',
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.operations')
    self.client.projects_instances_operations.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesOperationsGetRequest(
            name=ref.RelativeName()),
        response=response)
    self.assertEqual(
        instance_operations.Get('insId', 'opId'), response)

  def testList(self):
    operation = self.msgs.Operation()
    response = self.msgs.ListOperationsResponse(
        operations=[operation])
    ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')
    self.client.projects_instances_operations.List.Expect(
        request=
        self.msgs.SpannerProjectsInstancesOperationsListRequest(
            name=ref.RelativeName()+'/operations', pageSize=100),
        response=response)
    self.assertCountEqual(
        instance_operations.List('insId'), [operation])
