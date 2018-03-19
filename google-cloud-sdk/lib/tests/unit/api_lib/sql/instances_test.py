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
"""Tests for googlecloudsdk.api_lib.sql.instances."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from googlecloudsdk.api_lib.sql import instances as instances_util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.sql import base
from tests.lib.surface.sql import data


class DatabaseInstancesTest(base.SqlMockTestBeta):

  def testGetDatabaseInstances(self):
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            maxResults=100,
            project=self.Project(),),
        self.messages.InstancesListResponse(
            items=data.GetDatabaseInstancesListOfOne(),
            kind=u'sql#instancesList',
            nextPageToken='100',))
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            pageToken=u'100',
            project=self.Project(),
            maxResults=100,),
        self.messages.InstancesListResponse(
            items=data.GetDatabaseInstancesListOfTwo(),
            kind=u'sql#instancesList',
            nextPageToken=None,))

    expected_instance_list = data.GetDatabaseInstancesListOfOne(
    ) + data.GetDatabaseInstancesListOfTwo()
    expected_instance_list[0].state = 'STOPPED'

    self.assertEqual(expected_instance_list,
                     list(instances_util._BaseInstances.GetDatabaseInstances()))

  def testGetDatabaseInstancesWithLimit(self):
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            maxResults=2,
            project=self.Project(),),
        self.messages.InstancesListResponse(
            items=data.GetDatabaseInstancesListOfOne(),
            kind=u'sql#instancesList',
            nextPageToken='100',))
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            pageToken=u'100',
            project=self.Project(),
            maxResults=1,),
        self.messages.InstancesListResponse(
            items=data.GetDatabaseInstancesListOfTwo(),
            kind=u'sql#instancesList',
            nextPageToken=None,))

    expected_instance_list = data.GetDatabaseInstancesListOfOne(
    ) + data.GetDatabaseInstancesListOfTwo()
    expected_instance_list[0].state = 'STOPPED'

    self.assertEqual(
        expected_instance_list[:2],
        list(instances_util._BaseInstances.GetDatabaseInstances(limit=2)))

  def testGetDatabaseInstancesWithBatchSize(self):
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            maxResults=10,
            project=self.Project(),),
        self.messages.InstancesListResponse(
            items=data.GetDatabaseInstancesListOfOne(),
            kind=u'sql#instancesList',
            nextPageToken='10',))
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            pageToken=u'10',
            project=self.Project(),
            maxResults=10,),
        self.messages.InstancesListResponse(
            items=data.GetDatabaseInstancesListOfTwo(),
            kind=u'sql#instancesList',
            nextPageToken=None,))

    expected_instance_list = data.GetDatabaseInstancesListOfOne(
    ) + data.GetDatabaseInstancesListOfTwo()
    expected_instance_list[0].state = 'STOPPED'

    self.assertEqual(
        expected_instance_list,
        list(instances_util._BaseInstances.GetDatabaseInstances(batch_size=10)))


class IsPostgresDatabaseVersionTest(base.SqlMockTestBeta):
  """Tests instances_util.InstancesV1Beta4.IsPostgresDatabaseVersion."""

  def testPostgresInstance(self):
    postgres_instance = self.messages.DatabaseInstance(
        databaseVersion='POSTGRES_9_6')
    self.assertTrue(
        instances_util._BaseInstances.IsPostgresDatabaseVersion(
            postgres_instance.databaseVersion))

  def testMySQLInstance(self):
    mysql_instance = self.messages.DatabaseInstance(databaseVersion='MYSQL_5_7')
    self.assertFalse(
        instances_util._BaseInstances.IsPostgresDatabaseVersion(
            mysql_instance.databaseVersion))


class GetRegionFromZoneTest(base.SqlMockTestBeta, parameterized.TestCase):
  """Tests instances_util.GetRegionFromZone."""

  @parameterized.parameters(
      ('asia-northeast1-b', 'asia-northeast1'),
      ('us-east4-b', 'us-east4'),
      ('europe-west2-a', 'europe-west2'),
      # Edge cases: 1-, 2-, or many-component zones.
      ('europe', 'europe'),
      ('europe-west2', 'europe-west2'),
      ('europe-west2-a-etc', 'europe-west2'))
  def testGetRegionFromZone(self, zone, derived_region):
    self.assertEqual(instances_util.GetRegionFromZone(zone), derived_region)


if __name__ == '__main__':
  test_case.main()
