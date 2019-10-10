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
"""Test of the 'source project-configs describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.source import base


class ProjectConfigDescribeTestGA(base.SourceTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def _ExpectGetProjectConfig(self, project_name=None):
    project = project_name or self.Project()
    self.client.projects.GetConfig.Expect(
        request=self.messages.SourcerepoProjectsGetConfigRequest(
            name='projects/{}'.format(project)),
        response=self.messages.ProjectConfig())

  def testDescribe(self):
    self._ExpectGetProjectConfig()
    self.Run('source project-configs describe')

  def testDescribe_ProjectName(self):
    self._ExpectGetProjectConfig('my-project')
    self.Run('source project-configs describe --project my-project')


class ProjectConfigDescribeTestBeta(ProjectConfigDescribeTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ProjectConfigDescribeTestAlpha(ProjectConfigDescribeTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
