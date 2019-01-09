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
"""Tests that exercise workerpool describe."""

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
class DescribeTest(e2e_base.WithMockHttp, sdk_test_base.WithFakeAuth):

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

  def testDescribe(self):
    wp_in = self.msg.WorkerPool()
    wp_in.workerConfig = self.msg.WorkerConfig()
    wp_in.name = 'fake_name'
    wp_in.workerCount = 3
    wp_in.regions = [
        self.msg.WorkerPool.RegionsValueListEntryValuesEnum.us_central1,
        self.msg.WorkerPool.RegionsValueListEntryValuesEnum.us_east1
    ]
    wp_in.workerConfig.machineType = 'fakemachine'
    wp_in.workerConfig.diskSizeGb = 123
    wp_in.workerConfig.network = self.msg.Network()
    wp_in.workerConfig.network.network = 'networkname'
    wp_in.workerConfig.network.subnetwork = 'subnetname'
    wp_in.workerConfig.network.projectId = 'project'
    wp_in.workerConfig.tag = 'faketag'

    wp_out = copy.deepcopy(wp_in)
    wp_out.createTime = self.frozen_time_str
    wp_out.status = self.msg.WorkerPool.StatusValueValuesEnum.RUNNING

    self.mocked_cloudbuild_v1alpha1.projects_workerPools.Get.Expect(
        self.msg.CloudbuildProjectsWorkerPoolsGetRequest(
            name=u'projects/{}/workerPools/{}'.format(self.project_id,
                                                      wp_in.name)),
        response=wp_out)

    self._Run(['alpha', 'builds', 'worker-pools', 'describe', wp_in.name])
    self.AssertOutputContains(
        """\
createTime: '{}'
name: fake_name
regions:
- us-central1
- us-east1
status: RUNNING
workerConfig:
diskSizeGb: '123'
machineType: fakemachine
network:
network: networkname
projectId: project
subnetwork: subnetname
tag: faketag
workerCount: '3'
""".format(self.frozen_time_str),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
