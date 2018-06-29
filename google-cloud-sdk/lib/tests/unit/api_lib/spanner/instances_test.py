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
"""Tests for Spanner instances library."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.spanner import instances
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class InstancesClientTest(base.SpannerTestBase):

  def testCreate(self):
    response = self.msgs.Operation()
    ref = resources.REGISTRY.Parse(
        'cfgId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instanceConfigs')
    self.client.projects_instances.Create.Expect(
        request=self.msgs.SpannerProjectsInstancesCreateRequest(
            parent='projects/'+self.Project(),
            createInstanceRequest=self.msgs.CreateInstanceRequest(
                instanceId='insId',
                instance=self.msgs.Instance(
                    config=ref.RelativeName(),
                    displayName='name',
                    nodeCount=3))),
        response=response)
    self.assertEqual(
        instances.Create('insId', 'cfgId', 'name', 3), response)

  def testDelete(self):
    response = self.msgs.Empty()
    ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')
    self.client.projects_instances.Delete.Expect(
        request=self.msgs.SpannerProjectsInstancesDeleteRequest(
            name=ref.RelativeName()),
        response=response)
    self.assertEqual(instances.Delete('insId'), response)

  def testGet(self):
    response = self.msgs.Instance()
    ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')
    self.client.projects_instances.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesGetRequest(
            name=ref.RelativeName()),
        response=response)
    self.assertEqual(instances.Get('insId'), response)

  def testList(self):
    instance_list = [self.msgs.Instance()]
    response = self.msgs.ListInstancesResponse(instances=instance_list)
    self.client.projects_instances.List.Expect(
        request=self.msgs.SpannerProjectsInstancesListRequest(
            parent='projects/'+self.Project(), pageSize=100),
        response=response)
    self.assertCountEqual(instances.List(), instance_list)

  def testPatch(self):
    response = self.msgs.Operation()
    ref = resources.REGISTRY.Parse(
        'insId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instances')
    self.client.projects_instances.Patch.Expect(
        request=self.msgs.SpannerProjectsInstancesPatchRequest(
            name=ref.RelativeName(),
            updateInstanceRequest=self.msgs.UpdateInstanceRequest(
                fieldMask='displayName,nodeCount',
                instance=self.msgs.Instance(
                    displayName='name', nodeCount=3))),
        response=response)
    self.assertEqual(
        instances.Patch('insId', description='name', nodes=3), response)
