# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""ai-platform jobs list tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.parameters('ml-engine', 'ai-platform')
class ListTestBase(object):

  def SetUp(self):
    self.statuses = self.short_msgs.Job.StateValueValuesEnum
    self.client.projects_jobs.List.Expect(
        self.msgs.MlProjectsJobsListRequest(
            pageSize=100,
            parent='projects/{}'.format(self.Project())
        ),
        self.short_msgs.ListJobsResponse(
            jobs=[
                self.short_msgs.Job(
                    jobId='opName1',
                    state=self.statuses.STATE_UNSPECIFIED,
                    createTime='2016-01-01T00:00:00Z'),
                self.short_msgs.Job(
                    jobId='opName2',
                    state=self.statuses.SUCCEEDED,
                    createTime='2016-01-02T00:00:00Z')
            ]))
    # So Run() returns resources
    properties.VALUES.core.user_output_enabled.Set(False)

  def testList(self, module_name):
    self.assertEqual(
        list(self.Run('{} jobs list'.format(module_name))), [
            self.short_msgs.Job(
                jobId='opName1', state=self.statuses.STATE_UNSPECIFIED,
                createTime='2016-01-01T00:00:00Z'),
            self.short_msgs.Job(
                jobId='opName2', state=self.statuses.SUCCEEDED,
                createTime='2016-01-02T00:00:00Z')
        ])

  def testList_TestFormat(self, module_name):
    properties.VALUES.core.user_output_enabled.Set(True)  # So we see the output
    self.StartObjectPatch(times, 'LOCAL', times.GetTimeZone('PST'))

    self.Run('{} jobs list'.format(module_name))

    self.AssertOutputEquals("""\
        JOB_ID   STATUS             CREATED
        opName1  STATE_UNSPECIFIED  2015-12-31T16:00:00
        opName2  SUCCEEDED          2016-01-01T16:00:00
        """, normalize_space=True)


class ListGaTest(ListTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(ListGaTest, self).SetUp()


class ListBetaTest(ListTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(ListBetaTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()
