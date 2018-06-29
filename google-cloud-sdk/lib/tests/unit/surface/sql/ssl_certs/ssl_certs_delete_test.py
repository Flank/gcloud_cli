# Copyright 2015 Google Inc. All Rights Reserved.
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
from __future__ import unicode_literals
import datetime

from apitools.base.protorpclite import util as protorpc_util

from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.sql import base


class SslCertsDeleteTest(base.SqlMockTestBeta):
  # pylint:disable=g-tzinfo-datetime

  def testSslCertsDelete(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)

    self.mocked_client.sslCerts.List.Expect(
        self.messages.SqlSslCertsListRequest(
            instance='integration-test', project=self.Project()),
        self.messages.SslCertsListResponse(
            items=[
                self.messages.SslCert(
                    cert='cert data',
                    certSerialNumber='1264712781',
                    commonName='cert',
                    createTime=datetime.datetime(
                        2014,
                        2,
                        4,
                        21,
                        10,
                        29,
                        402000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    expirationTime=datetime.datetime(
                        2024,
                        2,
                        2,
                        21,
                        10,
                        29,
                        402000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    instance='integration-test',
                    kind='sql#sslCert',
                    sha1Fingerprint='77299aad4c8136911c1f0b07dd9802a9a72124e8',
                ),
                self.messages.SslCert(
                    cert='cert data',
                    certSerialNumber='976069575',
                    commonName='newcert',
                    createTime=datetime.datetime(
                        2014,
                        7,
                        17,
                        19,
                        56,
                        52,
                        170000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    expirationTime=datetime.datetime(
                        2024,
                        7,
                        14,
                        19,
                        56,
                        52,
                        170000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    instance='integration-test',
                    kind='sql#sslCert',
                    sha1Fingerprint='d926e1fb26e4dba2f73a14bea4ee9554577deda9',
                ),
            ],
            kind='sql#sslCertsList',
        ))
    self.mocked_client.sslCerts.Delete.Expect(
        self.messages.SqlSslCertsDeleteRequest(
            instance='integration-test',
            project=self.Project(),
            sha1Fingerprint='d926e1fb26e4dba2f73a14bea4ee9554577deda9'),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                7,
                17,
                20,
                51,
                57,
                293000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                7,
                17,
                20,
                51,
                57,
                353000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                7,
                17,
                20,
                51,
                57,
                353000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='integration-test',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/integration-test'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='0163a566-7103-4ebf-98a9-64673b60359b',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/0163a566-7103-4ebf-98a9-64673b60359b'.
            format(self.Project()),
            operationType='UPDATE',
            status='RUNNING',
            user='170350250316@developer.gserviceaccount.com',
        ))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='0163a566-7103-4ebf-98a9-64673b60359b',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                7,
                17,
                20,
                51,
                57,
                293000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                7,
                17,
                20,
                51,
                57,
                353000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                7,
                17,
                20,
                51,
                57,
                353000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='integration-test',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/integration-test'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='0163a566-7103-4ebf-98a9-64673b60359b',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/0163a566-7103-4ebf-98a9-64673b60359b'.
            format(self.Project()),
            operationType='UPDATE',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com',
        ))

    self.Run('sql ssl-certs delete --instance=integration-test newcert')
    self.AssertErrContains(
        'Deleted [https://www.googleapis.com/sql/v1beta4/projects/'
        '{0}/instances/integration-test/sslCerts'
        '/d926e1fb26e4dba2f73a14bea4ee9554577deda9].'.format(self.Project()))
    self.assertEqual(prompt_mock.call_count, 1)

    # Checking for deprecation warning.
    self.AssertErrContains('`gcloud sql ssl-certs` is deprecated')

  def testSslCertsBadDelete(self):
    self.mocked_client.sslCerts.List.Expect(
        self.messages.SqlSslCertsListRequest(
            instance='integration-test',
            project=self.Project(),
        ),
        self.messages.SslCertsListResponse(
            items=[
                self.messages.SslCert(
                    cert='cert data',
                    certSerialNumber='1264712781',
                    commonName='cert',
                    createTime=datetime.datetime(
                        2014,
                        2,
                        4,
                        21,
                        10,
                        29,
                        402000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    expirationTime=datetime.datetime(
                        2024,
                        2,
                        2,
                        21,
                        10,
                        29,
                        402000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    instance='integration-test',
                    kind='sql#sslCert',
                    sha1Fingerprint='77299aad4c8136911c1f0b07dd9802a9a72124e8',
                ),
                self.messages.SslCert(
                    cert='cert data',
                    certSerialNumber='976069575',
                    commonName='newcert',
                    createTime=datetime.datetime(
                        2014,
                        7,
                        17,
                        19,
                        56,
                        52,
                        170000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    expirationTime=datetime.datetime(
                        2024,
                        7,
                        14,
                        19,
                        56,
                        52,
                        170000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))),
                    instance='integration-test',
                    kind='sql#sslCert',
                    sha1Fingerprint='d926e1fb26e4dba2f73a14bea4ee9554577deda9',
                ),
            ],
            kind='sql#sslCertsList',
        ))
    with self.assertRaisesRegex(
        exceptions.ResourceNotFoundError,
        r'no ssl cert named \[noncert\] for instance \[https://'
        r'www.googleapis.com/sql/v1beta4/projects/{0}/'
        r'instances/integration-test\]'.format(self.Project())):
      self.Run('sql ssl-certs delete --instance=integration-test noncert')

  def testSslCertsDeleteNoConfirmCancels(self):
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('sql ssl-certs delete --instance=integration-test noncert')

if __name__ == '__main__':
  test_case.main()
