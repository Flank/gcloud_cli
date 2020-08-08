# Lint as: python3
# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for google3.third_party.py.googlecloudsdk.command_lib.privateca.pem_utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import pem_utils
from tests.lib import cli_test_base
from tests.lib import test_case

CERT1 = """-----BEGIN CERTIFICATE-----
MIIEiDCCAnACFBIqqUoIQUU5RgXxiua8ISTU9YMcMA0GCSqGSIb3DQEBCwUAMIGM
MQswCQYDVQQGEwJVUzETMBEGA1UECAwKV2FzaGluZ3RvbjERMA8GA1UEBwwIS2ly
a2xhbmQxHTAbBgNVBAoMFEludGVybWVkaWF0ZSBDQSBJbmMuMRswGQYDVQQLDBJT
dGlsbCBVbml0IFRlc3RpbmcxGTAXBgNVBAMMEGludGVybWVkaWF0ZS5jb20wHhcN
MTkwOTA0MjMwNTE1WhcNNDcwMTIwMjMwNTE1WjB0MQswCQYDVQQGEwJDQTETMBEG
A1UECAwKU29tZS1TdGF0ZTENMAsGA1UEBwwETGVhZjEfMB0GA1UECgwWTGVhZiBD
ZXJ0IGluIFVuaXQgVGVzdDENMAsGA1UECwwETGVhZjERMA8GA1UEAwwIbGVhZi5j
b20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCwgxbW4gZypGqAHVer
aMbHsig7A29xb8FllK2uT0kTIIu869qMsLWVyBVr0TVB+8ubycTQzR49bNQ5QuUL
-----END CERTIFICATE-----
"""

CERT2 = """-----BEGIN CERTIFICATE-----
MIIEiDCCAnACFBIqqUoIQUU5RgXxiua8ISTU9YMcMA0GCSqGSIb3DQEBCwUAMIGM
MQswCQYDVQQGEwJVUzETMBEGA1UECAwKV2FzaGluZ3RvbjERMA8GA1UEBwwIS2ly
a2xhbmQxHTAbBgNVBAoMFEludGVybWVkaWF0ZSBDQSBJbmMuMRswGQYDVQQLDBJT
dGlsbCBVbsdsdsdsdsdpbmcxGTAXBgNVBAMMEGludGVybWVkaWF0ZS5jb20wHhcN
MTkwOTA0MjMwNTE1WhcNNDcwMTIwMjMwNTE1WjB0MQswCQYDVQQGEwJDQTETMBEG
A1UECAwKU29tZS1TdGF0ZTENMAsGA1UEBwwETGVhZjEfMB0GA1UECgwWTGVhZiBD
ZXJ0IGluIFVuaXQgVGVzdDENMAsGA1UECwwETGVhZjERMA8GA1UEAwwIbGVhZi5j
b20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCwgxbW4gZypGqAHVer
aMbHsig7A29xb8FllK2uT0kTIIu869qMsLWVyBVr0TVB+8ubycTQzR49bNQ5QuUL
-----END CERTIFICATE-----
"""

CERT3 = """-----BEGIN CERTIFICATE-----
MIIEiDCCAnACFBIqqUoIQUU5RgXxiua8ISTU9YMcMA0GCSqGSIb3DQEBCwUAMIGM
MQswCQYDVQQGEwJVUzETMBEGA1UECAwKV2FzaGluZ3RvbjERMA8GA1UEBwwIS2ly
a2xhbmQxHTAbBgNVBAoMFEludGVybWVkaWF0ZSBDQSBJbmMuMRswGQYDVQQLDBJT
dGlsbCBVbsdsdsdsdsdpbmcxGTAXBgNVBAMMEGludGVybWVkaWF0ZS5jb20wHhcN
MTkwOTA0MjMwNTE1WhcNNDcwMTIwMjMwNTE1WjB0MQswCQYDVQQGEwJDQTETMBEG
A1UECAwKU29asdasdF0asdsdsdsdA1UEBwwETGVhZjEfMB0GA1UECgwWTGVhZiBD
ZXJ0IGluIFVuaXQgVGVzdDENMAsGA1UECwwETGVhZjERMA8GA1UEAwwIbGVhZi5j
b20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCwgxbW4gZypGqAHVer
aMbHsig7A29xb8FllK2uT0kTIIu869qMsLWVyBVr0TVB+8ubycTQzR49bNQ5QuUL
-----END CERTIFICATE-----
"""


class PemUtilsTest(cli_test_base.CliTestBase):

  def testValidateAndParseCAChain(self):
    pem_chain = CERT1 + '\n' + CERT2 + '\n' + CERT3
    chain = pem_utils.ValidateAndParsePemChain(pem_chain)
    self.assertEqual(chain, [CERT1, CERT2, CERT3])

  def testInvalidPemChain(self):
    pem_chain = CERT1 + '\n' + CERT2 + '-----END CERTIFICATE-----'
    with self.AssertRaisesExceptionMatches(exceptions.InvalidArgumentException,
                                           'pem-chain'):
      pem_utils.ValidateAndParsePemChain(pem_chain)

  def testInvalidPemChainGarbage(self):
    pem_chain = 'asdadsasd'
    with self.AssertRaisesExceptionMatches(exceptions.InvalidArgumentException,
                                           'pem-chain'):
      pem_utils.ValidateAndParsePemChain(pem_chain)


if __name__ == '__main__':
  test_case.main()
