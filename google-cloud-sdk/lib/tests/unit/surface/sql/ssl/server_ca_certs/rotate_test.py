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
"""Tests for rotating Server CA Certs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.protorpclite import util as protorpc_util

from googlecloudsdk.api_lib.sql import exceptions
from tests.lib import test_case
from tests.lib.surface.sql import base
from tests.lib.surface.sql import data


class _BaseServerCaCertsRotateTest(object):

  def testRotateWithUpcomingCert(self):
    # The upcoming cert has fingerprint 'two'.
    active_cert_fingerprint = 'one'
    instance_name = 'integration-test'

    # The list endpoint is called to determine the upcoming certificate.
    self.mocked_client.instances.ListServerCas.Expect(
        self.messages.SqlInstancesListServerCasRequest(
            instance=instance_name,
            project=self.Project(),
        ),
        self.messages.InstancesListServerCasResponse(
            activeVersion=active_cert_fingerprint,
            certs=[
                data.GetSslCert(
                    instance_name, 'one',
                    datetime.datetime(
                        2024,
                        2,
                        2,
                        21,
                        10,
                        29,
                        402000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0)))),
                data.GetSslCert(
                    instance_name, 'two',
                    datetime.datetime(
                        2024,
                        4,
                        4,
                        21,
                        10,
                        29,
                        402000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))))
            ],
            kind='sql#sslCertsList',
        ))
    self.mocked_client.instances.RotateServerCa.Expect(
        self.messages.SqlInstancesRotateServerCaRequest(
            instance=instance_name,
            instancesRotateServerCaRequest=None,
            project=self.Project(),
        ),
        data.GetOperation(
            self.Project(),
            self.messages.DatabaseInstance(name=instance_name),
            'UPDATE',
            'PENDING'))
    self.mocked_client.operations.Get.Expect(
        data.GetOperationGetRequest(self.Project()),
        data.GetOperation(
            self.Project(),
            self.messages.DatabaseInstance(name=instance_name),
            'UPDATE',
            'DONE'))
    self.Run(
        'sql ssl server-ca-certs rotate --instance={}'.format(instance_name))
    self.AssertOutputContains(
        """\
SHA1_FINGERPRINT EXPIRATION
two              2024-04-04T21:10:29.402000+00:00
""",
        normalize_space=True)

  def testRotateWithNoUpcomingCert(self):
    active_cert_fingerprint = 'one'
    instance_name = 'integration-test'

    # The list endpoint is called to determine the upcoming certificate.
    self.mocked_client.instances.ListServerCas.Expect(
        self.messages.SqlInstancesListServerCasRequest(
            instance=instance_name,
            project=self.Project(),
        ),
        self.messages.InstancesListServerCasResponse(
            activeVersion=active_cert_fingerprint,
            certs=[
                data.GetSslCert(
                    instance_name, 'one',
                    datetime.datetime(
                        2024,
                        2,
                        2,
                        21,
                        10,
                        29,
                        402000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))))
            ],
            kind='sql#sslCertsList',
        ))

    with self.AssertRaisesExceptionRegexp(
        exceptions.ResourceNotFoundError,
        r'No upcoming Server CA Certificate exists.'):
      self.Run(
          'sql ssl server-ca-certs rotate --instance={}'.format(instance_name))


class ServerCaCertsRotateBetaTest(_BaseServerCaCertsRotateTest,
                                  base.SqlMockTestBeta):
  pass


class ServerCaCertsRotateAlphaTest(_BaseServerCaCertsRotateTest,
                                   base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
