# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests that exercise workerpool list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case


# TODO(b/29358031): Move WithMockHttp somewhere more appropriate for unit tests.
class ListTest(e2e_base.WithMockHttp, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.StartPatch('time.sleep')  # To speed up tests with polling

    self.mocked_cloudbuild_v1alpha1 = mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1alpha1'))
    self.mocked_cloudbuild_v1alpha1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1alpha1.Unmock)
    self.msg = core_apis.GetMessagesModule('cloudbuild', 'v1alpha1')

    self.project_id = 'my-project'
    properties.VALUES.core.project.Set(self.project_id)

    self.frozen_time_str = '2018-11-12T00:10:00+00:00'

  def _Run(self, args):
    self.Run(args)

  def testList(self):
    wp_1_in = self.msg.WorkerPool()
    wp_1_in.workerConfig = self.msg.WorkerConfig()
    wp_1_in.name = 'fake_name_1'

    wp_2_in = self.msg.WorkerPool()
    wp_2_in.workerConfig = self.msg.WorkerConfig()
    wp_2_in.name = 'fake_name_2'

    wp_1_out = copy.deepcopy(wp_1_in)
    wp_1_out.createTime = self.frozen_time_str
    wp_1_out.status = self.msg.WorkerPool.StatusValueValuesEnum.RUNNING

    wp_2_out = copy.deepcopy(wp_2_in)
    wp_2_out.createTime = self.frozen_time_str
    wp_2_out.status = self.msg.WorkerPool.StatusValueValuesEnum.RUNNING

    response = self.msg.ListWorkerPoolsResponse()
    response.workerPools = [wp_1_out, wp_2_out]

    self.mocked_cloudbuild_v1alpha1.projects_workerPools.List.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsListRequest(
            parent=u'projects/{}'.format(self.project_id)),
        response=response)

    self._Run(['alpha', 'builds', 'worker-pools', 'list'])
    self.AssertOutputContains(
        """\
NAME CREATE_TIME STATUS
fake_name_1 {} RUNNING
fake_name_2 {} RUNNING
""".format(self.frozen_time_str, self.frozen_time_str),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
