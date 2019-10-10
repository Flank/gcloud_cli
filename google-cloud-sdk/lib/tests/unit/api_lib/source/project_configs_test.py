# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for sourcerepo project API wrapper module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.source import project_configs
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib.surface.source import base


class ProjectConfigApiTest(base.SourceTestBase):
  """Sourcerepo project-config api tests."""

  def SetUp(self):
    properties.VALUES.core.project.Set(self.Project())
    self.api_client = project_configs.ProjectConfig()
    self.project_ref = self._GetProjectRef()
    self.project_name = self.project_ref.RelativeName()

  def testUpdate_pushblock(self):
    project_config = self.messages.ProjectConfig(
        name=self.project_name, enablePrivateKeyCheck=True)
    self._ExpectUpdateProjectConfig(project_config, 'enablePrivateKeyCheck')
    self.assertEqual(
        project_config,
        self.api_client.Update(project_config, 'enablePrivateKeyCheck'))

  def testUpdate_topic(self):
    topic_name = 'projects/my-project/topics/aa'
    project_config = self.messages.ProjectConfig(
        name=self.project_name,
        pubsubConfigs=self.messages.ProjectConfig.
        PubsubConfigsValue(additionalProperties=[
            self.messages.ProjectConfig.PubsubConfigsValue.AdditionalProperty(
                key=topic_name, value=self._CreatePubsubConfig(topic_name))
        ]))
    self._ExpectUpdateProjectConfig(project_config, 'pubsubConfigs')
    self.assertEqual(project_config,
                     self.api_client.Update(project_config, 'pubsubConfigs'))

  def testGet(self):
    project_config = self.messages.ProjectConfig(name=self.project_name)
    self._ExpectGetProjectConfig(self.project_ref, project_config)
    self.assertEqual(project_config, self.api_client.Get(self.project_ref))


if __name__ == '__main__':
  sdk_test_base.main()
