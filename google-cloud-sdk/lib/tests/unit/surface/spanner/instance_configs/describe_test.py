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
"""Tests for Spanner instance-configs describe command."""

from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class InstanceConfigsDescribeTest(base.SpannerTestBase):
  """Cloud Spanner instance-configs describe tests."""

  def SetUp(self):
    self.cfg_ref = resources.REGISTRY.Parse(
        'cfgId',
        params={'projectsId': self.Project()},
        collection='spanner.projects.instanceConfigs')

  def testDescribe(self):
    self.client.projects_instanceConfigs.Get.Expect(
        request=self.msgs.SpannerProjectsInstanceConfigsGetRequest(
            name=self.cfg_ref.RelativeName()),
        response=self.msgs.InstanceConfig(name='testconfig'))
    self.Run('spanner instance-configs describe cfgId')
    self.AssertOutputContains('testconfig')
