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
"""Unit tests for `gcloud redis operatios list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import extra_types
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import redis_test_base
from six.moves import range  # pylint: disable=redefined-builtin


class ListTestGA(redis_test_base.OperationsUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testList(self):
    expected_operations = self._MakeOperations(3)
    self._ExpectList(expected_operations)

    # Disable output so can capture returned lists instead of printing.
    properties.VALUES.core.user_output_enabled.Set(False)
    actual_operations = self.Run('redis operations list --region {}'
                                 .format(self.region_id))

    self.assertEqual(actual_operations, expected_operations)

  def testList_UsingRegionProperty(self):
    expected_operations = self._MakeOperations(3)
    self._ExpectList(expected_operations)

    properties.VALUES.redis.region.Set(self.region_id)
    # Disable output so can capture returned lists instead of printing.
    properties.VALUES.core.user_output_enabled.Set(False)
    actual_operations = self.Run('redis operations list')

    self.assertEqual(actual_operations, expected_operations)

  def testList_Uri(self):
    expected_operations = self._MakeOperations(3)
    self._ExpectList(expected_operations)

    self.Run('redis operations list --region {} --uri'.format(self.region_id))

    self.AssertOutputEquals(
        """\
        https://redis.googleapis.com/{api_version}/{operation_name}_0
        https://redis.googleapis.com/{api_version}/{operation_name}_1
        https://redis.googleapis.com/{api_version}/{operation_name}_2
        """.format(api_version=self.api_version,
                   operation_name=self.operation_relative_name),
        normalize_space=True)

  def testList_CheckFormat(self):
    expected_operations = self._MakeOperations(3)
    self._ExpectList(expected_operations)

    self.Run('redis operations list --region {}'.format(self.region_id))

    # pylint: disable=line-too-long
    self.AssertOutputEquals(
        """\
        OPERATION_NAME    REGION       TYPE    TARGET       DONE  CREATE_TIME          DURATION
        {operation_id}_0  {region_id}          my-instance  True  2018-01-01T00:00:00  2M15S
        {operation_id}_1  {region_id}          my-instance  True  2018-01-01T00:00:00  2M15S
        {operation_id}_2  {region_id}          my-instance  True  2018-01-01T00:00:00  2M15S
        """.format(operation_id=self.operation_id, region_id=self.region_id), normalize_space=True)
    # pylint: enable=line-too-long

  def _ExpectList(self, expected_operations):
    self.operations_service.List.Expect(
        request=self.messages.RedisProjectsLocationsOperationsListRequest(
            name=self.region_relative_name),
        response=self.messages.ListOperationsResponse(
            operations=expected_operations))

  def _MakeOperations(self, n):
    def EncodeJsonValue(value):
      return encoding.PyValueToMessage(extra_types.JsonValue, value)
    metadata_dict = {
        'createTime': EncodeJsonValue('2018-01-01T00:00:00'),
        'startTime': EncodeJsonValue('2018-01-01T00:00:10'),
        'endTime': EncodeJsonValue('2018-01-01T00:02:15'),
        'target': EncodeJsonValue('my-instance')}
    metadata = encoding.DictToAdditionalPropertyMessage(
        metadata_dict, self.messages.Operation.MetadataValue)
    operations = []
    for i in range(n):
      name = '{}_{}'.format(self.operation_relative_name, i)
      operation = self.messages.Operation(name=name, metadata=metadata,
                                          done=True)
      operations.append(operation)
    return operations


class ListTestBeta(ListTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ListTestAlpha(ListTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
