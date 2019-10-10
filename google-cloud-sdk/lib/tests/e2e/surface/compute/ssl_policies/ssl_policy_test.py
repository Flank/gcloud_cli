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
"""Integration tests for SSL policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base

_CUSTOM_FEATURES_1 = [
    'TLS_RSA_WITH_AES_128_CBC_SHA', 'TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA',
    'TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA'
]
_CUSTOM_FEATURES_2 = [
    'TLS_RSA_WITH_AES_256_CBC_SHA', 'TLS_RSA_WITH_AES_256_GCM_SHA384',
    'TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256',
    'TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384'
]


class SslPolicyTestBase(e2e_test_base.BaseTest):

  def UniqueName(self, name):
    return next(e2e_utils.GetResourceNameGenerator(
        prefix='compute-ssl-policy-test-' + name))

  def _SetUp(self, api_version, release_track):
    """Setup common test components.

    Args:
      api_version: Compute Engine API version to use for requests.
      release_track: Release track the test is targeting.
    """
    self.track = release_track
    self._messages = apis.GetMessagesModule('compute', api_version)
    properties.VALUES.core.user_output_enabled.Set(False)
    self._ssl_policy_names = []

  def _CreateSslPolicy(self,
                       name,
                       profile=None,
                       min_tls_version=None,
                       description=None,
                       custom_features=None):
    result = self.Run(
        'compute ssl-policies create {name}'
        ' {description} {profile} {min_tls_version} {custom_features}'.format(
            name=name,
            description=('--description {}'.format(description)
                         if description else ''),
            profile=('--profile {}'.format(profile) if profile else ''),
            min_tls_version=('--min-tls-version {}'.format(min_tls_version)
                             if min_tls_version else ''),
            custom_features=('--custom-features {}'.format(
                ','.join(custom_features)) if custom_features else '')))
    self._ssl_policy_names.append(name)
    return result

  def _UpdateSslPolicy(self,
                       name,
                       profile=None,
                       min_tls_version=None,
                       custom_features=None):
    return self.Run(
        'compute ssl-policies update {name}'
        ' {profile} {min_tls_version} {custom_features}'.format(
            name=name,
            profile=('--profile {}'.format(profile) if profile else ''),
            min_tls_version=('--min-tls-version {}'.format(min_tls_version)
                             if min_tls_version else ''),
            custom_features=('--custom-features {}'.format(
                ','.join(custom_features)) if custom_features else '')))

  def _DescribeSslPolicy(self, name):
    return self.Run('compute ssl-policies describe {}'.format(name))

  def _ListSslPolicies(self):
    return self.Run('compute ssl-policies list')

  def _DeleteSslPolicy(self, name):
    self.Run('compute ssl-policies delete {}'.format(name))
    self._ssl_policy_names.remove(name)

  def _VerifySslPolicy(self,
                       actual_ssl_policy,
                       expected_name,
                       expected_profile,
                       expected_min_tls_version,
                       expected_description=None,
                       expected_custom_features=None):
    self.assertEqual(expected_name, actual_ssl_policy.name)
    self.assertEqual(
        self._messages.SslPolicy.ProfileValueValuesEnum(expected_profile),
        actual_ssl_policy.profile)
    self.assertEqual(
        self._messages.SslPolicy.MinTlsVersionValueValuesEnum(
            expected_min_tls_version), actual_ssl_policy.minTlsVersion)
    if expected_description:
      self.assertEqual(expected_description, actual_ssl_policy.description)
    if expected_custom_features:
      self.assertEqual(
          set(expected_custom_features), set(actual_ssl_policy.customFeatures))

  def _VerifyListSslPoliciesContains(self, expected_names_set):
    results = list(self._ListSslPolicies())
    actual_names_set = {result.name for result in results}
    # Verify only that the expected SSL policy resources is a subset of
    # the list of SSL policy resources. We do not perform exact match because
    # the previous iteration of the test might have not properly cleaned up
    # the resources or more than one instance of this test runs
    # concurrently causing resources from the other test run to be also
    # part of the output.
    self.assertEqual(set(), expected_names_set.difference(actual_names_set))

  def SslPolicyTest(self,
                    profile=None,
                    min_tls_version=None,
                    custom_features=None):
    """Creates and verifies the SSL policy resource."""

    # Create an SSL policy using COMPATIBLE profile, min TLS version 1.0 and
    # verify the result.
    name1 = self.UniqueName('pol1')
    create_result1 = self._CreateSslPolicy(
        name1,
        profile='COMPATIBLE',
        min_tls_version='1.0',
        description='description')
    self._VerifySslPolicy(
        create_result1,
        expected_name=name1,
        expected_description='description',
        expected_profile='COMPATIBLE',
        expected_min_tls_version='TLS_1_0')
    self._VerifySslPolicy(
        self._DescribeSslPolicy(name1),
        expected_name=name1,
        expected_description='description',
        expected_profile='COMPATIBLE',
        expected_min_tls_version='TLS_1_0')

    # Create an SSL policy using CUSTOM profile, min TLS version 1.1 and
    # verify the result.
    name2 = self.UniqueName('pol2')
    create_result2 = self._CreateSslPolicy(
        name2,
        profile='CUSTOM',
        min_tls_version='1.1',
        custom_features=_CUSTOM_FEATURES_1)
    self._VerifySslPolicy(
        create_result2,
        expected_name=name2,
        expected_profile='CUSTOM',
        expected_min_tls_version='TLS_1_1',
        expected_custom_features=_CUSTOM_FEATURES_1)
    self._VerifySslPolicy(
        self._DescribeSslPolicy(name2),
        expected_name=name2,
        expected_profile='CUSTOM',
        expected_min_tls_version='TLS_1_1',
        expected_custom_features=_CUSTOM_FEATURES_1)

    # Create 3 more SSL policies, relying on 1 or more default values.
    name3 = self.UniqueName('pol3')
    self._CreateSslPolicy(name3, min_tls_version='1.2')
    name4 = self.UniqueName('pol4')
    self._CreateSslPolicy(name4, profile='MODERN')
    name5 = self.UniqueName('pol5')
    self._CreateSslPolicy(name5)

    # Verify listing SSL policies shows the 5 SSL policies
    # which have been created so far.
    self._VerifyListSslPoliciesContains({name1, name2, name3, name4, name5})

    # Update the first SSL policy's profile from COMPATIBLE to CUSTOM,
    # min TLS version from 1.0 to 1.2, and verify the result.
    update_result1 = self._UpdateSslPolicy(
        name1,
        profile='CUSTOM',
        min_tls_version='1.2',
        custom_features=_CUSTOM_FEATURES_2)
    self._VerifySslPolicy(
        update_result1,
        expected_name=name1,
        expected_description='description',
        expected_profile='CUSTOM',
        expected_min_tls_version='TLS_1_2',
        expected_custom_features=_CUSTOM_FEATURES_2)
    self._VerifySslPolicy(
        self._DescribeSslPolicy(name1),
        expected_name=name1,
        expected_description='description',
        expected_profile='CUSTOM',
        expected_min_tls_version='TLS_1_2',
        expected_custom_features=_CUSTOM_FEATURES_2)

    # Update the second SSL policy's profile from CUSTOM to RESTRICTED,
    # and verify the result.
    update_result2 = self._UpdateSslPolicy(name2, profile='RESTRICTED')
    self._VerifySslPolicy(
        update_result2,
        expected_name=name2,
        expected_profile='RESTRICTED',
        expected_min_tls_version='TLS_1_1')
    self._VerifySslPolicy(
        self._DescribeSslPolicy(name2),
        expected_name=name2,
        expected_profile='RESTRICTED',
        expected_min_tls_version='TLS_1_1')

    # Delete the SSL policies
    self._DeleteSslPolicy(name1)
    self._DeleteSslPolicy(name2)
    self._DeleteSslPolicy(name3)
    self._DeleteSslPolicy(name4)
    self._DeleteSslPolicy(name5)

  def TearDown(self):
    # Delete the SslPolicy
    self.DeleteResources(self._ssl_policy_names, self.DeleteSslPolicy,
                         'ssl policy')


class SslPolicyTestAlpha(SslPolicyTestBase):

  def SetUp(self):
    super(SslPolicyTestAlpha, self)._SetUp('alpha',
                                           calliope_base.ReleaseTrack.ALPHA)

  def testSslPolicy(self):
    """Tests SSL policy operations using the Alpha release track."""
    self.SslPolicyTest()


class SslPolicyTestBeta(SslPolicyTestBase):

  def SetUp(self):
    super(SslPolicyTestBeta, self)._SetUp('beta',
                                          calliope_base.ReleaseTrack.BETA)

  def testSslPolicy(self):
    """Tests SSL policy operations using the Beta release track."""
    self.SslPolicyTest()


class SslPolicyTestGA(SslPolicyTestBase):

  def SetUp(self):
    super(SslPolicyTestGA, self)._SetUp('v1', calliope_base.ReleaseTrack.GA)

  def testSslPolicy(self):
    """Tests SSL policy operations using the GA release track."""
    self.SslPolicyTest()


if __name__ == '__main__':
  e2e_test_base.main()
