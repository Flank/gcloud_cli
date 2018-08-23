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
"""Tests for Cloud Filestore operations list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.filestore import base


class CloudFilestoreOperationsListTest(base.CloudFilestoreUnitTestBase):

  def SetUp(self):
    self.SetUpTrack(calliope_base.ReleaseTrack.BETA)

  def RunList(self, *args):
    return self.Run(['filestore', 'operations', 'list'] + list(args))

  def testListNoOperation(self):
    parent = 'projects/{}/locations/-'.format(self.Project())
    self.mock_client.projects_locations_operations.List.Expect(
        self.messages.FileProjectsLocationsOperationsListRequest(
            name=parent, pageSize=100),
        self.messages.ListOperationsResponse(operations=[]))
    results = list(self.RunList())
    self.assertEquals(len(results), 0)

  def testListOneCloudFilestoreOperation(self):
    test_operation = self.GetTestCloudFilestoreOperation()
    parent = 'projects/{}/locations/-'.format(self.Project())
    self.mock_client.projects_locations_operations.List.Expect(
        self.messages.FileProjectsLocationsOperationsListRequest(
            name=parent, pageSize=100),
        self.messages.ListOperationsResponse(operations=[test_operation]))
    results = list(self.RunList())
    self.assertEquals([test_operation], results)

  def testListMultipleCloudFilestoreOperations(self):
    test_operations = self.GetTestCloudFilestoreOperationsList()
    parent = 'projects/{}/locations/-'.format(self.Project())
    self.mock_client.projects_locations_operations.List.Expect(
        self.messages.FileProjectsLocationsOperationsListRequest(
            name=parent, pageSize=100),
        self.messages.ListOperationsResponse(operations=test_operations))
    results = list(self.RunList())
    self.assertEquals(test_operations, results)

  def testListWithLocation(self):
    test_operation = self.GetTestCloudFilestoreOperation()
    parent = 'projects/{}/locations/us-central1-c'.format(self.Project())
    self.mock_client.projects_locations_operations.List.Expect(
        self.messages.FileProjectsLocationsOperationsListRequest(
            name=parent, pageSize=100),
        self.messages.ListOperationsResponse(operations=[test_operation]))
    results = list(self.RunList('--location=us-central1-c'))
    self.assertEquals([test_operation], results)

  def testListOutputUri(self):
    test_operations = self.GetTestCloudFilestoreOperationsList()
    parent = 'projects/{}/locations/-'.format(self.Project())
    self.mock_client.projects_locations_operations.List.Expect(
        self.messages.FileProjectsLocationsOperationsListRequest(
            name=parent, pageSize=100),
        self.messages.ListOperationsResponse(operations=test_operations))
    list(self.RunList('--uri'))
    # pylint: disable=line-too-long
    self.AssertOutputContains(
        """\
        https://file.googleapis.com/{0}/projects/{1}/locations/us-central1-c/operations/Operation1
        https://file.googleapis.com/{0}/projects/{1}/locations/us-central1-c/operations/Operation2
        """.format(self.api_version, self.Project()),
        normalize_space=True
    )
    # pylint: enable=line-too-long


class CloudFilestoreOperationsListAlphaTest(CloudFilestoreOperationsListTest):

  def SetUp(self):
    self.SetUpTrack(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
