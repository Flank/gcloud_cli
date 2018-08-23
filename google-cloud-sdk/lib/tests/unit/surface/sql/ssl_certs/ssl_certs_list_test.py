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

from apitools.base.protorpclite import util as protorpc_util

from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseSslCertsListTest(object):

  def testSslCertsList(self):
    self.mocked_client.sslCerts.List.Expect(
        self.messages.SqlSslCertsListRequest(
            instance='integration-test',
            project=self.Project(),
        ),
        self.messages.SslCertsListResponse(
            items=[
                self.messages.SslCert(
                    cert='-----BEGIN CERTIFICATE-----\nMIIC/zCCAeegAwIBA',
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
            ],
            kind='sql#sslCertsList',
        ))
    self.Run('sql ssl-certs list --instance=integration-test')
    self.AssertOutputContains("""\
NAME  SHA1_FINGERPRINT                          EXPIRATION
cert  77299aad4c8136911c1f0b07dd9802a9a72124e8  2024-02-02T21:10:29.402000+00:00
""", normalize_space=True)

    # Checking for deprecation warning.
    self.AssertErrContains('`gcloud sql ssl-certs` is deprecated')


class SslCertsListGATest(_BaseSslCertsListTest, base.SqlMockTestGA):
  pass


class SslCertsListBetaTest(_BaseSslCertsListTest, base.SqlMockTestBeta):
  pass


class SslCertsListAlphaTest(_BaseSslCertsListTest, base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
