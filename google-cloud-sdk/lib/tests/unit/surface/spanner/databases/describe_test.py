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
"""Tests for Spanner databases describe command."""

from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class DatabasesDescribeTest(base.SpannerTestBase):
  """Cloud Spanner databases describe tests."""

  def SetUp(self):
    self.db_ref = resources.REGISTRY.Parse(
        'mydb',
        params={
            'projectsId': self.Project(),
            'instancesId': 'myins',
        },
        collection='spanner.projects.instances.databases')

  def testDescribe(self):
    self.client.projects_instances_databases.Get.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesGetRequest(
            name=self.db_ref.RelativeName()),
        response=self.msgs.Database(name='reallymydb'))
    self.Run('spanner databases describe mydb --instance myins')
    self.AssertOutputContains('reallymydb')
