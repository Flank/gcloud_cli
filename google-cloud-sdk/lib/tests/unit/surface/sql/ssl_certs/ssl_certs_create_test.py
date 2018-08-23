# -*- coding: utf-8 -*- #
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
from __future__ import division
from __future__ import unicode_literals

import datetime
import os
import re

from apitools.base.protorpclite import util as protorpc_util

from googlecloudsdk.api_lib.sql import exceptions
from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseSslCertsCreateTest(object):

  def testSslCertsCreate(self):
    self.mocked_client.sslCerts.Insert.Expect(
        self.messages.SqlSslCertsInsertRequest(
            instance='integration-test',
            project=self.Project(),
            sslCertsInsertRequest=self.messages.SslCertsInsertRequest(
                commonName='newcert')),
        self.messages.SslCertsInsertResponse(
            clientCert=self.messages.SslCertDetail(
                certInfo=self.messages.SslCert(
                    cert='cert data client',
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
                    expirationTime=None,
                    instance='integration-test',
                    sha1Fingerprint='d926e1fb26e4dba2f73a14bea4ee9554577deda9',
                ),
                certPrivateKey='cert private key',
            ),
            serverCaCert=self.messages.SslCert(
                cert='cert data server',
                certSerialNumber='0',
                commonName='some nonsense',
                createTime=datetime.datetime(
                    2014,
                    1,
                    30,
                    1,
                    55,
                    28,
                    96000,
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
                expirationTime=datetime.datetime(
                    2024,
                    1,
                    28,
                    1,
                    55,
                    28,
                    96000,
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
                instance='integration-test',
                sha1Fingerprint='515917f85cf67be2912ca94c9f9bf8e35ee2aa47',
            ),
        ))
    cert_file = os.path.join(self.temp_path, 'cert')
    self.Run('sql ssl-certs create --instance=integration-test newcert {0}'
             .format(cert_file))
    self.AssertOutputContains("""\
NAME     SHA1_FINGERPRINT                          EXPIRATION
newcert  d926e1fb26e4dba2f73a14bea4ee9554577deda9  -
""", normalize_space=True)
    self.assertEqual(open(cert_file).read(), 'cert private key\n')

    # Checking for deprecation warning.
    self.AssertErrContains('`gcloud sql ssl-certs` is deprecated')

  def testSslCertsCreateBadDestination(self):
    with self.assertRaisesRegex(
        exceptions.ArgumentError,
        r'unable to write \[/foobar\]'):
      self.Run('sql ssl-certs create newcert /foobar '
               '--instance=integration-test')

  def testSslCertsCreateAlreadyExists(self):
    file_contents = 'arbitrary data\n'
    path = self.Touch(self.temp_path, 'arbitrary_file', file_contents)
    with self.assertRaisesRegex(
        exceptions.ArgumentError,
        r'file \[{file}\] already exists'.format(file=re.escape(path))):
      self.Run('sql ssl-certs create newcert {file} --instance=integration-test'
               .format(file=path))
    self.AssertFileExistsWithContents(file_contents, path)


class SslCertsCreateGATest(_BaseSslCertsCreateTest, base.SqlMockTestGA):
  pass


class SslCertsCreateBetaTest(_BaseSslCertsCreateTest, base.SqlMockTestBeta):
  pass


class SslCertsCreateAlphaTest(_BaseSslCertsCreateTest, base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
