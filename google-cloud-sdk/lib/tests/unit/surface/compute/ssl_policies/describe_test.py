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
"""Tests for the SSL policies describe alpha command."""

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import ssl_policies_test_base


class SslPolicyDescribeBetaTest(ssl_policies_test_base.SslPoliciesTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)

  def testDescribeNonCustomProfile(self):
    name = 'my-ssl-policy'
    description = 'My Description'
    profile = 'MODERN'
    profile_enum = self.messages.SslPolicy.ProfileValueValuesEnum(profile)
    min_tls_version_enum = self.messages.SslPolicy.MinTlsVersionValueValuesEnum(
        'TLS_1_0')

    ssl_policy_ref = self.GetSslPolicyRef(name)
    result_ssl_policy = self.messages.SslPolicy(
        name=name,
        description=description,
        profile=profile_enum,
        minTlsVersion=min_tls_version_enum,
        customFeatures=[],
        fingerprint='SOME_FINGERPRINT',
        selfLink=ssl_policy_ref.SelfLink())

    self.ExpectGetRequest(ssl_policy_ref, result_ssl_policy)

    response = self.Run('compute ssl-policies describe {}'.format(name))
    self.assertEqual(response, result_ssl_policy)

  def testDescribeCustomProfile(self):
    name = 'my-ssl-policy'
    profile = 'CUSTOM'
    profile_enum = self.messages.SslPolicy.ProfileValueValuesEnum(profile)
    min_tls_version_enum = self.messages.SslPolicy.MinTlsVersionValueValuesEnum(
        'TLS_1_2')
    custom_features = [
        'TLS_RSA_WITH_AES_128_CBC_SHA', 'TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384',
        'TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256'
    ]

    ssl_policy_ref = self.GetSslPolicyRef(name)
    result_ssl_policy = self.messages.SslPolicy(
        name=name,
        profile=profile_enum,
        minTlsVersion=min_tls_version_enum,
        customFeatures=custom_features,
        fingerprint='SOME_FINGERPRINT',
        selfLink=ssl_policy_ref.SelfLink())

    self.ExpectGetRequest(ssl_policy_ref, result_ssl_policy)

    response = self.Run('compute ssl-policies describe {}'.format(name))
    self.assertEqual(response, result_ssl_policy)


class SslPolicyDescribeAlphaTest(SslPolicyDescribeBetaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
