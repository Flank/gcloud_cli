# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import ssl_policies_test_base


class SslPolicyListGATest(ssl_policies_test_base.SslPoliciesTestBase):

  def SetUp(self):
    self._SetUpReleaseTrack()
    # Since list command returns a generator, we do not want the items to
    # go to STDOUT (which will cause the test to fail otherwise).
    properties.VALUES.core.user_output_enabled.Set(False)

  def _SetUpReleaseTrack(self):
    self._SetUp(calliope_base.ReleaseTrack.GA)

  def _MakeSslPolicy(self,
                     name,
                     profile,
                     min_tls_version,
                     fingerprint,
                     custom_features=None,
                     description=None):
    ssl_policy_ref = self.GetSslPolicyRef(name)
    return self.messages.SslPolicy(
        name=name,
        description=description,
        profile=self.messages.SslPolicy.ProfileValueValuesEnum(profile),
        minTlsVersion=self.messages.SslPolicy.MinTlsVersionValueValuesEnum(
            min_tls_version),
        customFeatures=custom_features or [],
        fingerprint=fingerprint,
        selfLink=ssl_policy_ref.SelfLink())

  def testList(self):
    ssl_policies = [
        self._MakeSslPolicy(
            'policy1',
            'COMPATIBLE',
            'TLS_1_1',
            b'f1',
            description='Some description.'),
        self._MakeSslPolicy(
            'policy2',
            'CUSTOM',
            'TLS_1_2',
            b'f2',
            custom_features=[
                'TLS_RSA_WITH_AES_128_CBC_SHA', 'TLS_RSA_WITH_AES_256_CBC_SHA',
                'TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256',
                'TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256'
            ]),
        self._MakeSslPolicy('policy3', 'RESTRICTED', 'TLS_1_0', b'f3')
    ]

    self.ExpectListRequest(ssl_policies)

    results = self.Run('compute ssl-policies list')
    self.assertEqual(results, ssl_policies)


class SslPolicyListBetaTest(SslPolicyListGATest):

  def _SetUpReleaseTrack(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)


class SslPolicyListAlphaTest(SslPolicyListBetaTest):

  def _SetUpReleaseTrack(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
