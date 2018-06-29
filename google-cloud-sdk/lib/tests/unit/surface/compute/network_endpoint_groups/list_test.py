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
"""Tests for the network-endpoint-groups list subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class NetworkEndpointGroupsListTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def testTableOutput(self):
    self.list_json.side_effect = iter([test_resources.NETWORK_ENDPOINT_GROUPS])
    self.Run('compute network-endpoint-groups list')
    self.list_json.assert_called_once_with(
        requests=[(
            self.compute.networkEndpointGroups,
            'AggregatedList',
            self.messages.ComputeNetworkEndpointGroupsAggregatedListRequest(
                project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals("""\
NAME     LOCATION  TYPE            ENDPOINT_TYPE   SIZE
my-neg1  zone-1    LOAD_BALANCING  GCE_VM_IP_PORT  5
my-neg2  zone-2    LOAD_BALANCING  GCE_VM_IP_PORT  2
""", normalize_space=True)

  def testCommandOuput(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    self.list_json.side_effect = iter([test_resources.NETWORK_ENDPOINT_GROUPS])
    result = list(self.Run('compute network-endpoint-groups list'))
    self.list_json.assert_called_once_with(
        requests=[(
            self.compute.networkEndpointGroups,
            'AggregatedList',
            self.messages.ComputeNetworkEndpointGroupsAggregatedListRequest(
                project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.assertEqual(test_resources.NETWORK_ENDPOINT_GROUPS, result)


if __name__ == '__main__':
  test_case.main()
