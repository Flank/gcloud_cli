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
"""Tests for googlecloudsdk.api_lib.sql.instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import json
import sys

from googlecloudsdk.api_lib.sql import api_util as common_api_util
from googlecloudsdk.api_lib.sql import exceptions as sql_exceptions
from googlecloudsdk.api_lib.sql import instance_prop_reducers as reducers_util
from googlecloudsdk.api_lib.sql import instances as instances_util
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.sql import base
from tests.lib.surface.sql import data
import mock


class DatabaseInstancesTest(base.SqlMockTestBeta):

  def testGetDatabaseInstances(self):
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            maxResults=100,
            project=self.Project(),
        ),
        self.messages.InstancesListResponse(
            items=data.GetDatabaseInstancesListOfOne(),
            kind='sql#instancesList',
            nextPageToken='100',
        ))
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            pageToken='100',
            project=self.Project(),
            maxResults=100,
        ),
        self.messages.InstancesListResponse(
            items=data.GetDatabaseInstancesListOfTwo(),
            kind='sql#instancesList',
            nextPageToken=None,
        ))

    expected_instance_list = data.GetDatabaseInstancesListOfOne(
    ) + data.GetDatabaseInstancesListOfTwo()
    expected_instance_list[0].state = 'STOPPED'

    self.assertEqual(expected_instance_list,
                     list(instances_util._BaseInstances.GetDatabaseInstances()))

  def testGetDatabaseInstancesWithLimit(self):
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            maxResults=2,
            project=self.Project(),
        ),
        self.messages.InstancesListResponse(
            items=data.GetDatabaseInstancesListOfOne(),
            kind='sql#instancesList',
            nextPageToken='100',
        ))
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            pageToken='100',
            project=self.Project(),
            maxResults=1,
        ),
        self.messages.InstancesListResponse(
            items=data.GetDatabaseInstancesListOfTwo(),
            kind='sql#instancesList',
            nextPageToken=None,
        ))

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
            project=self.Project(),
        ),
        self.messages.InstancesListResponse(
            items=data.GetDatabaseInstancesListOfOne(),
            kind='sql#instancesList',
            nextPageToken='10',
        ))
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            pageToken='10',
            project=self.Project(),
            maxResults=10,
        ),
        self.messages.InstancesListResponse(
            items=data.GetDatabaseInstancesListOfTwo(),
            kind='sql#instancesList',
            nextPageToken=None,
        ))

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


class PrintAndConfirmAuthorizedNetworksOverwriteTest(base.SqlMockTestBeta):

  def testPrintAndConfirmAuthorizedNetworksOverwrite(self):
    captured_prompt = io.StringIO()
    sys.stderr = captured_prompt
    instances_util.InstancesV1Beta4.PrintAndConfirmAuthorizedNetworksOverwrite()
    sys.stderr = sys.__stdout__

    self.assertEqual(json.loads(captured_prompt.getvalue())['message'],
                     'When adding a new IP address to authorized networks, '
                     'make sure to also include any IP addresses that have '
                     'already been authorized. Otherwise, they will be '
                     'overwritten and de-authorized.')


class InstanceV1Beta4Test(base.SqlMockTestBeta):

  def testSetProjectAndInstanceFromRef(self):
    instance_resource = self.messages.DatabaseInstance()
    instance_ref = common_api_util.SqlClient('v1beta4').resource_parser.Parse(
        'test_instance_id',
        params={'project': 'test_project_name'},
        collection='sql.instances')
    instances_util.InstancesV1Beta4.\
      SetProjectAndInstanceFromRef(instance_resource, instance_ref)
    self.assertEqual((instance_resource.project, instance_resource.name),
                     (instance_ref.project, instance_ref.instance))

  def testAddBackupConfigToSettings(self):
    settings = self.messages.Settings(
        activationPolicy=None,
        authorizedGaeApplications=[],
        backupConfiguration=None,
        databaseFlags=[],
        ipConfiguration=None,
        kind='sql#settings',
        locationPreference=None,
        pricingPlan='PER_USE',
        replicationType='SYNCHRONOUS',
        settingsVersion=None,
        tier='D1',
    )

    backup_configuration = (reducers_util.BackupConfiguration(
        self.messages, enable_bin_log=True))
    instances_util.InstancesV1Beta4.AddBackupConfigToSettings(
        settings, backup_configuration)

    self.assertEqual(settings.backupConfiguration, backup_configuration)


class StartCloudSqlProxyTest(base.SqlMockTestBeta):
  """Tests instances_util.StartCloudSqlProxy."""
  paths_mock = mock.Mock()
  proxy_process = mock.Mock()

  def SetUp(self):
    self.instance = self.messages.DatabaseInstance(
        name='some-instance', connectionName='storage:some-instance')
    self.proxy_process.stderr = mock.Mock()

    # Mock out calls to get the SDK path.
    self.paths_mock.sdk_bin_path = '/some/sdk/path'
    self.StartPatch(
        'googlecloudsdk.core.config.Paths', return_value=self.paths_mock)

    # Mock out calls to get the credentials.
    self.StartPatch(
        'googlecloudsdk.core.properties.VALUES.core.account.Get',
        return_value='test@google.com')
    self.paths_mock.LegacyCredentialsAdcPath = mock.Mock(
        return_value='wherever/adc.json')

    # Mock out calls to get the proxy command line args.
    self.StartPatch(
        'googlecloudsdk.core.execution_utils',
        return_value=['cloud_sql_proxy', 'wtv'])
    self.proxy_process.poll = mock.Mock(return_value=None)
    self.StartPatch('subprocess.Popen', return_value=self.proxy_process)

  def testStartProxyFromBinPath(self):
    find_exec_mock = self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath')
    self.proxy_process.stderr.readline = mock.Mock(
        return_value=b'Ready for new connections')
    process = instances_util.StartCloudSqlProxy(self.instance, 9470)

    # Ensure that FindExecutableOnPath was not called.
    self.assertEqual(find_exec_mock.call_count, 0)
    self.assertEqual(process, self.proxy_process)

  def testStartProxyFromPath(self):
    find_exec_mock = self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value='/other/sdk/path')
    self.paths_mock.sdk_bin_path = None
    self.proxy_process.stderr.readline = mock.Mock(
        return_value=b'Ready for new connections')
    process = instances_util.StartCloudSqlProxy(self.instance, 9470)

    # Ensure that FindExecutableOnPath was called.
    self.assertEqual(find_exec_mock.call_count, 1)
    self.assertEqual(process, self.proxy_process)

  def testFailToFindProxyPath(self):
    find_exec_mock = self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value=None)
    self.paths_mock.sdk_bin_path = None
    with self.assertRaises(exceptions.ToolException):
      instances_util.StartCloudSqlProxy(self.instance, 9470)

    # Ensure that FindExecutableOnPath was called.
    self.assertEqual(find_exec_mock.call_count, 1)

  def testProxyTimeout(self):
    sleep_mock = self.StartPatch('time.sleep')
    self.proxy_process.stderr.readline = mock.Mock(return_value=b'')
    seconds_to_timeout = 10

    with self.assertRaises(sql_exceptions.CloudSqlProxyError):
      instances_util.StartCloudSqlProxy(self.instance, 9470, seconds_to_timeout)

    # Polling happens every 0.2 seconds, so timeout should happen after
    # the seconds to timeout have elapsed.
    iterations_to_timeout = (seconds_to_timeout / 0.2) + 1
    self.assertEqual(sleep_mock.call_count, iterations_to_timeout)

  def testProxyAddressInUse(self):
    sleep_mock = self.StartPatch('time.sleep')
    self.proxy_process.stderr.readline = mock.Mock(
        return_value=b'bind: address already in use')

    with self.assertRaises(sql_exceptions.CloudSqlProxyError):
      instances_util.StartCloudSqlProxy(self.instance, 9470)

    # The error was thrown on the first iteration, so no sleep calls were made.
    self.assertEqual(sleep_mock.call_count, 0)

  def testProxyUnknownError(self):
    # Polling will stop if the proxy process poll method does not return None.
    self.proxy_process.poll = mock.Mock(return_value=1)

    with self.AssertRaisesExceptionRegexp(
        sql_exceptions.CloudSqlProxyError,
        'Failed to start the Cloud SQL Proxy.'):
      instances_util.StartCloudSqlProxy(self.instance, 9470)


class IsInstanceV2Test(base.SqlMockTestBeta):
  """Tests instances_util.IsInstanceV2."""
  project = 'some-project'
  instance = 'some-instance'

  def testV2MySqlInstance(self):
    self.assertTrue(
        instances_util.IsInstanceV2(
            data.GetV2Instance(self.project, self.instance)))

  def testPostgresInstance(self):
    self.assertTrue(
        instances_util.IsInstanceV2(
            data.GetPostgresInstance(self.project, self.instance)))

  def testV1MySqlInstance(self):
    self.assertFalse(
        instances_util.IsInstanceV2(
            data.GetV1Instance(self.project, self.instance)))


class IsInstanceV1Test(base.SqlMockTestBeta):
  """Tests instances_util.IsInstanceV1."""
  project = 'some-project'
  instance = 'some-instance'

  def testV1MySqlInstance(self):
    self.assertTrue(
        instances_util.IsInstanceV1(
            data.GetV1Instance(self.project, self.instance)))

  def testV2MySqlInstance(self):
    self.assertFalse(
        instances_util.IsInstanceV1(
            data.GetV2Instance(self.project, self.instance)))

  def testPostgresInstance(self):
    self.assertFalse(
        instances_util.IsInstanceV1(
            data.GetPostgresInstance(self.project, self.instance)))

  def testV1TierInstance(self):
    instance = data.GetV1Instance(self.project, self.instance)
    instance.backendType = ''
    instance.settings.tier = 'D0'
    self.assertTrue(instances_util.IsInstanceV1(instance))

  def testNonV1TierInstance(self):
    instance = data.GetV2Instance(self.project, self.instance)
    instance.backendType = ''
    instance.settings.tier = 'db-n1-standard-1'
    self.assertFalse(instances_util.IsInstanceV1(instance))

  def testBlankTierInstance(self):
    instance = data.GetV2Instance(self.project, self.instance)
    instance.settings.tier = None
    self.assertFalse(instances_util.IsInstanceV1(instance))


class GetInstanceStateTest(base.SqlMockTestBeta):
  """Tests instances_util.GetInstanceState."""
  project = 'some-project'
  instance = 'some-instance'

  def testRunnableInstance(self):
    instance = data.GetV2Instance(self.project, self.instance)
    instance.settings.activationPolicy = 'ON_DEMAND'
    instance.state = 'RUNNABLE'
    self.assertEqual('RUNNABLE', instances_util.GetInstanceState(instance))

  def testStoppedInstance(self):
    instance = data.GetV2Instance(self.project, self.instance)
    instance.settings.activationPolicy = 'NEVER'
    instance.state = 'RUNNABLE'
    self.assertEqual('STOPPED', instances_util.GetInstanceState(instance))


if __name__ == '__main__':
  test_case.main()
