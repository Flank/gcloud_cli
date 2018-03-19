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
"""Tests for Spanner instances list command."""

from tests.lib.surface.spanner import base


class InstancesListTest(base.SpannerTestBase):
  """Cloud Spanner instances list tests."""

  def testList(self):
    self.client.projects_instances.List.Expect(
        request=self.msgs.SpannerProjectsInstancesListRequest(
            parent='projects/'+self.Project(), pageSize=100),
        response=self.msgs.ListInstancesResponse(instances=[
            self.msgs.Instance(name='insA'),
            self.msgs.Instance(name='insB')
        ]))
    self.Run('spanner instances list')
    self.AssertOutputContains('insA')
    self.AssertOutputContains('insB')
