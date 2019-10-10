# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Unit tests for the intance_groups_utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import test_case
from six.moves import range  # pylint: disable=redefined-builtin


class InstanceGroupUtilsTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'v1')

  def testSplitInstancesInRequest(self):
    requests = instance_groups_utils.SplitInstancesInRequest(
        self.messages.ComputeInstanceGroupManagersAbandonInstancesRequest(
            instanceGroupManager='name',
            instanceGroupManagersAbandonInstancesRequest=self.messages.
            InstanceGroupManagersAbandonInstancesRequest(
                instances=['a', 'b', 'c', 'd', 'e']),
            project='project',
            zone='zone'), 'instanceGroupManagersAbandonInstancesRequest', 2)
    self.assertEqual(
        requests[0],
        self.messages.ComputeInstanceGroupManagersAbandonInstancesRequest(
            instanceGroupManager='name',
            instanceGroupManagersAbandonInstancesRequest=self.messages.
            InstanceGroupManagersAbandonInstancesRequest(
                instances=['a', 'b'],),
            project='project',
            zone='zone',))
    self.assertEqual(
        requests[1],
        self.messages.ComputeInstanceGroupManagersAbandonInstancesRequest(
            instanceGroupManager='name',
            instanceGroupManagersAbandonInstancesRequest=self.messages.
            InstanceGroupManagersAbandonInstancesRequest(
                instances=['c', 'd'],),
            project='project',
            zone='zone',))
    self.assertEqual(
        requests[2],
        self.messages.ComputeInstanceGroupManagersAbandonInstancesRequest(
            instanceGroupManager='name',
            instanceGroupManagersAbandonInstancesRequest=self.messages.
            InstanceGroupManagersAbandonInstancesRequest(
                instances=['e'],),
            project='project',
            zone='zone',))

  def testLiftRequestsList(self):
    a = object()
    b = object()
    c = [object(), object(), object()]
    result = list(instance_groups_utils.GenerateRequestTuples(a, b, c))
    for i in range(3):
      self.assertIs(result[i][0], a)
      self.assertIs(result[i][1], b)
      self.assertIs(result[i][2], c[i])


if __name__ == '__main__':
  test_case.main()
