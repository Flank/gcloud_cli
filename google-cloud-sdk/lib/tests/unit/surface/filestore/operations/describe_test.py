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
"""Tests for Cloud Filestore operation describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.filestore import base


class CloudFilestoreOperationsDescribeTest(base.CloudFilestoreUnitTestBase):

  def SetUp(self):
    self.SetUpTrack(calliope_base.ReleaseTrack.GA)

  def RunDescribe(self, *args):
    return self.Run(['filestore', 'operations', 'describe'] + list(args))

  def testDescribeValidFilestoreOperation(self):
    test_operation = self.GetTestCloudFilestoreOperation()
    name = ('projects/{}/locations/us-central1-c/operations/'
            'operation_name'.format(self.Project()))
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.FileProjectsLocationsOperationsGetRequest(name=name),
        test_operation)
    result = self.RunDescribe('operation_name', '--zone=us-central1-c')
    self.assertEquals(result, test_operation)

  def testDescribeValidFilestoreOperationWithDeprecatedLocation(self):
    test_operation = self.GetTestCloudFilestoreOperation()
    name = ('projects/{}/locations/us-central1-c/operations/'
            'operation_name'.format(self.Project()))
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.FileProjectsLocationsOperationsGetRequest(name=name),
        test_operation)
    result = self.RunDescribe('operation_name', '--location=us-central1-c')
    self.assertEqual(result, test_operation)

  def testDescribeWithDefaultLocation(self):
    properties.VALUES.filestore.location.Set('us-central1-c')
    test_operation = self.GetTestCloudFilestoreOperation()
    name = ('projects/{}/locations/us-central1-c/operations/'
            'operation_name'.format(self.Project()))
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.FileProjectsLocationsOperationsGetRequest(name=name),
        test_operation)
    result = self.RunDescribe('operation_name')
    self.assertEquals(result, test_operation)

  def testMissingLocationWithoutDefault(self):
    with self.assertRaises(handlers.ParseError):
      self.RunDescribe('operation_name')

  def testMissingOperationName(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.RunDescribe()


class CloudFilestoreOperationsDescribeBetaTest(
    CloudFilestoreOperationsDescribeTest):

  def SetUp(self):
    self.SetUpTrack(calliope_base.ReleaseTrack.BETA)


class CloudFilestoreOperationsDescribeAlphaTest(
    CloudFilestoreOperationsDescribeTest):

  def SetUp(self):
    self.SetUpTrack(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
