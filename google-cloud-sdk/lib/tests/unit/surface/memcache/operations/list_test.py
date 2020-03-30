# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Unit tests for `gcloud memcache operations list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import extra_types
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.memcache import memcache_test_base
from six.moves import range  # pylint: disable=redefined-builtin


class ListTest(memcache_test_base.OperationsUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectList(self, expected_operations):
    self.operations_service.List.Expect(
        request=self.messages.MemcacheProjectsLocationsOperationsListRequest(
            name=self.region_relative_name),
        response=self.messages.ListOperationsResponse(
            operations=expected_operations))

  def _MakeOperations(self, n):

    def EncodeJsonValue(value):
      return encoding.PyValueToMessage(extra_types.JsonValue, value)

    metadata_dict = {
        'createTime': EncodeJsonValue('2020-01-01T00:00:00'),
        'startTime': EncodeJsonValue('2020-01-01T00:00:10'),
        'endTime': EncodeJsonValue('2020-01-01T00:02:15'),
        'target': EncodeJsonValue('my-instance'),
        'verb': EncodeJsonValue('create')
    }
    metadata = encoding.DictToAdditionalPropertyMessage(
        metadata_dict, self.messages.Operation.MetadataValue)
    operations = []
    for i in range(n):
      name = '{}_{}'.format(self.operation_relative_name, i)
      operation = self.messages.Operation(
          name=name, metadata=metadata, done=True)
      operations.append(operation)
    return operations

  def testList(self):
    self.SetUpForTrack()
    self.SetUpOperations()
    expected_operations = self._MakeOperations(3)
    self._ExpectList(expected_operations)

    # Disable output so can capture returned lists instead of printing.
    properties.VALUES.core.user_output_enabled.Set(False)
    actual_operations = self.Run(
        'memcache operations list --region {}'.format(self.region_id))

    self.assertEqual(actual_operations, expected_operations)

  def testList_Uri(self):
    self.SetUpForTrack()
    self.SetUpOperations()
    expected_operations = self._MakeOperations(3)
    self._ExpectList(expected_operations)

    self.Run('memcache operations list --region {} --uri'.format(
        self.region_id))

    self.AssertOutputEquals(
        """\
        https://memcache.googleapis.com/{api_version}/{operation_name}_0
        https://memcache.googleapis.com/{api_version}/{operation_name}_1
        https://memcache.googleapis.com/{api_version}/{operation_name}_2
        """.format(
            api_version=self.api_version,
            operation_name=self.operation_relative_name),
        normalize_space=True)

  def testList_CheckFormat(self):
    self.SetUpForTrack()
    self.SetUpOperations()
    expected_operations = self._MakeOperations(3)
    self._ExpectList(expected_operations)

    self.Run('memcache operations list --region {}'.format(self.region_id))

    # pylint: disable=line-too-long
    self.AssertOutputEquals(
        """\
        OPERATION_NAME    LOCATION       TYPE    TARGET       DONE  CREATE_TIME          DURATION
        {operation_id}_0  {region_id} create  my-instance  True  2020-01-01T00:00:00  2M15S
        {operation_id}_1  {region_id} create  my-instance  True  2020-01-01T00:00:00  2M15S
        {operation_id}_2  {region_id} create  my-instance  True  2020-01-01T00:00:00  2M15S
        """.format(operation_id=self.operation_id, region_id=self.region_id),
        normalize_space=True)
    # pylint: enable=line-too-long


if __name__ == '__main__':
  test_case.main()
