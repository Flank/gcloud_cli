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
"""Tests of 'gcloud compute networks vpc-access operations list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import extra_types
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.networks.vpc_access import base


class OperationsListTestBeta(base.VpcAccessUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'v1beta1'

  def _ExpectList(self, expected_operations):
    self.client.projects_locations_operations.List.Expect(
        request=self.messages.VpcaccessProjectsLocationsOperationsListRequest(
            name=self.region_relative_name),
        response=self.messages.ListOperationsResponse(
            operations=expected_operations))

  def _MakeOperations(self):
    operations = []
    operation_prefix = 'projects/{}/locations/{}/operations/'.format(
        self.project_id, self.region_id)

    # An operation is inserted but not done.
    operations.append(
        self.messages.Operation(
            name=operation_prefix + 'my-operation-0',
            metadata=self._MakeMetadata('my-connector-0', 'create', True,
                                        '2018-01-01T00:00:10'),
            done=False))
    # An operation is done.
    operations.append(
        self.messages.Operation(
            name=operation_prefix + 'my-operation-1',
            metadata=self._MakeMetadata('my-connector-1', 'delete', False,
                                        '2018-01-01T00:00:10',
                                        '2018-01-01T00:02:15'),
            done=True))
    return operations

  def _MakeMetadata(self, target, method, is_alpha, create_time='',
                    end_time=''):

    def EncodeJsonValue(value):
      return encoding.PyValueToMessage(extra_types.JsonValue, value)

    metadata_dict = {
        'target': EncodeJsonValue(target),
        'method': EncodeJsonValue(method),
    }
    if is_alpha:
      metadata_dict['insertTime'] = EncodeJsonValue(create_time)
    else:
      metadata_dict['createTime'] = EncodeJsonValue(create_time)
    if end_time:
      metadata_dict['endTime'] = EncodeJsonValue(end_time)

    return encoding.DictToAdditionalPropertyMessage(
        metadata_dict, self.messages.Operation.MetadataValue)

  def testZeroOperationsList(self):
    self.client.projects_locations_operations.List.Expect(
        self.messages.VpcaccessProjectsLocationsOperationsListRequest(
            name=self.region_relative_name),
        self.messages.ListOperationsResponse(operations=[]))
    self.Run('compute networks vpc-access operations list --region={}'.format(
        self.region_id))
    self.AssertErrContains('Listed 0 items.')

  def testOperationsList(self):
    expected_operations = self._MakeOperations()
    self._ExpectList(expected_operations)

    self.Run('compute networks vpc-access operations list --region={}'.format(
        self.region_id))

    # pylint: disable=line-too-long
    self.AssertOutputEquals(
        """\
        OPERATION_ID REGION TARGET METHOD DONE START_TIME END_TIME
        my-operation-0 us-central1 my-connector-0 create False 2018-01-01T00:00:10 -
        my-operation-1 us-central1 my-connector-1 delete True 2018-01-01T00:00:10 2018-01-01T00:02:15
        """,
        normalize_space=True)
    # pylint: enable=line-too-long

  def testOperationsListUri(self):
    expected_operations = self._MakeOperations()
    self._ExpectList(expected_operations)

    self.Run(
        'compute networks vpc-access operations list --region={} --uri'.format(
            self.region_id))

    # pylint: disable=line-too-long
    self.AssertOutputEquals(
        """\
        https://vpcaccess.googleapis.com/{api_version}/projects/{project}/locations/{location}/operations/my-operation-0
        https://vpcaccess.googleapis.com/{api_version}/projects/{project}/locations/{location}/operations/my-operation-1
        """.format(
            api_version=self.api_version,
            project=self.project_id,
            location=self.region_id),
        normalize_space=True)
    # pylint: enable=line-too-long


class OperationsListTestAlpha(OperationsListTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'v1alpha1'


if __name__ == '__main__':
  test_case.main()
