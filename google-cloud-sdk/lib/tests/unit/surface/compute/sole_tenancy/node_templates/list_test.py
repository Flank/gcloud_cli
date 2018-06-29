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
"""Tests for the sole-tenancy node-templates list subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class NodeTemplatesListTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def testTableOutput(self):
    self.list_json.side_effect = iter([test_resources.NODE_TEMPLATES])
    self.Run('compute sole-tenancy node-templates list')
    self.list_json.assert_called_once_with(
        requests=[(self.compute.nodeTemplates,
                   'AggregatedList',
                   self.messages.ComputeNodeTemplatesAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals("""\
NAME        REGION    DESCRIPTION      NODE_TYPE       NODE_AFFINITY_LABELS   STATUS
template-1  region-1  a cool template  iAPX-286        environment=prod       READY
                                                       nodeGrouping=frontend
template-2  region-1  a cold template  n1-node-96-624  environment=prod       CREATING
                                                       nodeGrouping=backend
""", normalize_space=True)


if __name__ == '__main__':
  test_case.main()
