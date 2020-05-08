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
"""Tests for the SSL certificates describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class SslCertificatesDescribeTest(test_base.BaseTest,
                                  test_case.WithOutputCapture):

  @property
  def _api(self):
    return 'v1'

  def SetUp(self):
    self.SelectApi(self._api)
    self.SetEncoding('utf8')
    self._resources = test_resources.MakeSslCertificates(
        self.messages, self.api)

  def RunVersioned(self, command):
    prefix = '' if self.api == 'v1' else self.api
    return self.Run('{prefix} {command}'.format(prefix=prefix, command=command))

  def testSelfManagedCase(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._resources[0]],
    ])

    self.RunVersioned("""
        compute ssl-certificates describe my-cert
        """)

    self.CheckRequests(
        [(self.compute.sslCertificates,
          'Get',
          messages.ComputeSslCertificatesGetRequest(
              sslCertificate='my-cert',
              project='my-project'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            creationTimestamp: '2017-12-18T11:11:11.000-07:00'
            description: Self-managed certificate.
            expireTime: '2018-12-18T11:11:11.000-07:00'
            name: ssl-cert-1
            selfLink: {compute_uri}/projects/my-project/global/sslCertificates/ssl-cert-1
            selfManaged:
              certificate: |-
                -----BEGIN CERTIFICATE-----
                MIICZzCCAdACCQDjYQHCnQOiTDANBgkqhkiG9w0BAQsFADB4MQswCQYDVQQGEwJV
                UzETMBEGA1UECAwKV2FzaGluZ3RvbjEQMA4GA1UEBwwHU2VhdHRsZTEPMA0GA1UE
                CgwGR29vZ2xlMRgwFgYDVQQLDA9DbG91ZCBQbGF0Zm9ybXMxFzAVBgNVBAMMDmdj
                bG91ZCBjb21wdXRlMB4XDTE0MTAxMzIwMTcxMloXDTE1MTAxMzIwMTcxMloweDEL
                MAkGA1UEBhMCVVMxEzARBgNVBAgMCldhc2hpbmd0b24xEDAOBgNVBAcMB1NlYXR0
                bGUxDzANBgNVBAoMBkdvb2dsZTEYMBYGA1UECwwPQ2xvdWQgUGxhdGZvcm1zMRcw
                FQYDVQQDDA5nY2xvdWQgY29tcHV0ZTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkC
                gYEAw3JXUCTn8J2VeWqHuc9zJxdy1WfQJtbDxQUUy4nsqU6QPGso3HYXlI/eozg6
                bGhkJNtDVV4AAPQVv01aoFMt3T6MKLzAkjfse7zKQmQ399vQaE7lbLAV9M4FSV9s
                wksSvT7cOW9ddcdKdyV3NTbptW5PeUE8Zk/aCFLPLqOg800CAwEAATANBgkqhkiG
                9w0BAQsFAAOBgQCKMIRiThp2O+wg7M8wcNSdPzAZ61UMeisQKS5OEY90OsekWYUT
                zMkUznRtycTdTBxEqKQoJKeAXq16SezJaZYE48FpoObQc2ZLMvje7F82tOwC2kob
                v83LejX3zZnirv2PZVcFgvUE0k3a8/14enHi7j6jZu+Pl5ZM9BZ+vkBO8g==
                -----END CERTIFICATE-----
            type: SELF_MANAGED
           """.format(compute_uri=self.compute_uri)))

  def testManagedCase(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._resources[2]],
    ])

    self.RunVersioned("""
        compute ssl-certificates describe --global ssl-cert-3
        """)

    self.CheckRequests(
        [(self.compute.sslCertificates, 'Get',
          messages.ComputeSslCertificatesGetRequest(
              sslCertificate='ssl-cert-3', project='my-project'))],)
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
                creationTimestamp: '2017-12-17T10:00:00.000-07:00'
                description: Managed certificate.
                expireTime: '2018-12-17T10:00:00.000-07:00'
                managed:
                  domainStatus:
                    test1.certsbridge.com: ACTIVE
                    xn--8a342mzfam5b18csni3w.certsbridge.com: FAILED_CAA_FORBIDDEN
                  domains:
                  - test1.certsbridge.com
                  - xn--8a342mzfam5b18csni3w.certsbridge.com
                  status: ACTIVE
                name: ssl-cert-3
                selfLink: {compute_uri}/projects/my-project/global/sslCertificates/ssl-cert-3
                type: MANAGED
            """.format(compute_uri=self.compute_uri)))


class SslCertificatesDescribeBetaTest(SslCertificatesDescribeTest):

  @property
  def _api(self):
    return 'beta'


class SslCertificatesDescribeAlphaTest(SslCertificatesDescribeTest):

  @property
  def _api(self):
    return 'alpha'


if __name__ == '__main__':
  test_case.main()
