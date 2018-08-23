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
"""Tests for Spanner instance-configs list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib.surface.spanner import base


class InstanceConfigsListTest(base.SpannerTestBase):
  """Cloud Spanner instance-configs list tests."""

  def testList(self):
    self.client.projects_instanceConfigs.List.Expect(
        request=self.msgs.SpannerProjectsInstanceConfigsListRequest(
            parent='projects/'+self.Project(), pageSize=100),
        response=self.msgs.ListInstanceConfigsResponse(instanceConfigs=[
            self.msgs.InstanceConfig(name='cfgA'),
            self.msgs.InstanceConfig(name='cfgB')
        ]))
    self.Run('spanner instance-configs list')
    self.AssertOutputContains('cfgA')
    self.AssertOutputContains('cfgB')
