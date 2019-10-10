# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests that exercise operations listing and executing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.sql import base


class _BaseInstancesDescribeTest(object):

  def testSimpleDescribe(self):
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='testinstance',
            project=self.Project(),
        ),
        self.messages.DatabaseInstance(
            currentDiskSize=52690837,
            databaseVersion='MYSQL_5_5',
            etag='"DExdZ69FktjWMJ-ohD1vLZW9pnk/MQ"',
            name='testinstance',
            ipAddresses=[],
            ipv6Address='2001:4860:4864:1:df7c:6a7a:d107:ab9d',
            kind='sql#instance',
            maxDiskSize=268435456000,
            project=self.Project(),
            region='us-central',
            serverCaCert=None,
            settings=self.messages.Settings(
                activationPolicy='NEVER',
                authorizedGaeApplications=[],
                backupConfiguration=self.messages.BackupConfiguration(
                    binaryLogEnabled=False,
                    enabled=True,
                    kind='sql#backupConfiguration',
                    startTime='11:54'),
                databaseFlags=[],
                ipConfiguration=self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=False,
                    requireSsl=None,
                ),
                kind='sql#settings',
                locationPreference=None,
                pricingPlan='PER_USE',
                replicationType='SYNCHRONOUS',
                settingsVersion=1,
                tier='D0',
            ),
            state='RUNNABLE',
            instanceType='CLOUD_SQL_INSTANCE',
        ))

    self.Run('sql instances describe testinstance')
    self.AssertOutputContains(
        """\
currentDiskSize: '52690837'
databaseVersion: MYSQL_5_5
etag: '"DExdZ69FktjWMJ-ohD1vLZW9pnk/MQ"'
instanceType: CLOUD_SQL_INSTANCE
ipv6Address: 2001:4860:4864:1:df7c:6a7a:d107:ab9d
kind: sql#instance
maxDiskSize: '268435456000'
name: testinstance
project: {0}
region: us-central
settings:
  activationPolicy: NEVER
  backupConfiguration:
    binaryLogEnabled: false
    enabled: true
    kind: sql#backupConfiguration
    startTime: 11:54
  ipConfiguration:
    ipv4Enabled: false
  kind: sql#settings
  pricingPlan: PER_USE
  replicationType: SYNCHRONOUS
  settingsVersion: '1'
  tier: D0
state: STOPPED
""".format(self.Project()),
        normalize_space=True)

    # This is a V1 instance, so check that the deprecation message is shown.
    self.AssertErrContains(
        'Upgrade your First Generation instance to Second Generation')

  def testDescribeLabels(self):
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='testinstance',
            project=self.Project(),
        ),
        self.messages.DatabaseInstance(
            currentDiskSize=52690837,
            databaseVersion='MYSQL_5_5',
            etag='"DExdZ69FktjWMJ-ohD1vLZW9pnk/MQ"',
            name='testinstance',
            ipAddresses=[],
            ipv6Address='2001:4860:4864:1:df7c:6a7a:d107:ab9d',
            kind='sql#instance',
            maxDiskSize=268435456000,
            project=self.Project(),
            region='us-central',
            serverCaCert=None,
            settings=self.messages.Settings(
                activationPolicy='ON_DEMAND',
                authorizedGaeApplications=[],
                backupConfiguration=self.messages.BackupConfiguration(
                    binaryLogEnabled=False,
                    enabled=True,
                    kind='sql#backupConfiguration',
                    startTime='11:54'),
                databaseFlags=[],
                ipConfiguration=self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=False,
                    requireSsl=None,
                ),
                kind='sql#settings',
                userLabels=self.messages.Settings.UserLabelsValue(
                    additionalProperties=[
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='bar',
                            value='value',
                        ),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='baz',
                            value='qux',
                        ),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='foo',
                            value='bar',
                        ),
                    ],),
                locationPreference=None,
                pricingPlan='PER_USE',
                replicationType='SYNCHRONOUS',
                settingsVersion=1,
                tier='D0',
            ),
            state='RUNNABLE',
            instanceType='CLOUD_SQL_INSTANCE',
        ))

    self.Run('sql instances describe testinstance --format="default(labels)"')
    self.AssertOutputContains(
        """\
settings:
  userLabels:
    bar: value
    baz: qux
    foo: bar
""",
        normalize_space=True)

  def testInstanceNotFound(self):
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='nosuchinstance',
            project=self.Project(),),
        exception=http_error.MakeHttpError(
            403,
            'The client is not authorized to make this request.',
            url=('https://www.googleapis.com/sql/v1beta4/projects'
                 '/google.com%3Acloudsdktest/instances/noinstance?alt=json')))

    with self.assertRaises(exceptions.ResourceNotFoundError):
      self.Run('sql instances describe nosuchinstance')

  # TODO(b/122660263): Remove when V1 instances are no longer supported.
  def testNoV2DeprecationWarning(self):
    diff = {
        'name': 'v2-instance',
    }
    self.ExpectInstanceGet(self.GetV2Instance(), diff)

    self.Run('sql instances describe v2-instance')

    # This is a V2 instance, so check that the deprecation message is not shown.
    self.AssertErrNotContains(
        'Upgrade your First Generation instance to Second Generation')


class InstancesDescribeGATest(_BaseInstancesDescribeTest, base.SqlMockTestGA):
  pass


class InstancesDescribeBetaTest(_BaseInstancesDescribeTest,
                                base.SqlMockTestBeta):
  pass


class InstancesDescribeAlphaTest(_BaseInstancesDescribeTest,
                                 base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
