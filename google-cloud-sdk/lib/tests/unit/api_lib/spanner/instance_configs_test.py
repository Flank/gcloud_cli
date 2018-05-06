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
"""Tests for Spanner instance configs library."""

from googlecloudsdk.api_lib.spanner import instance_configs
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class InstanceConfigsClientTest(base.SpannerTestBase):

  def testGet(self):
    response = self.msgs.InstanceConfig()
    ref = resources.REGISTRY.Parse(
        'cfgId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instanceConfigs')
    self.client.projects_instanceConfigs.Get.Expect(
        request=self.msgs.SpannerProjectsInstanceConfigsGetRequest(
            name=ref.RelativeName()),
        response=response)
    self.assertEqual(instance_configs.Get('cfgId'), response)

  def testList(self):
    config_list = [self.msgs.InstanceConfig()]
    response = self.msgs.ListInstanceConfigsResponse(
        instanceConfigs=config_list)
    self.client.projects_instanceConfigs.List.Expect(
        request=self.msgs.SpannerProjectsInstanceConfigsListRequest(
            parent='projects/'+self.Project(), pageSize=100),
        response=response)
    self.assertItemsEqual(instance_configs.List(), config_list)
