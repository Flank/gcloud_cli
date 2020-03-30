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
"""Tests for the SSL policies describe alpha command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import ssl_policies_test_base


class SslPolicyUpdateGATest(ssl_policies_test_base.SslPoliciesTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.GA)

  def testSwitchFromModernToRestrictedProfile(self):
    name = 'my-ssl-policy'
    new_profile = 'RESTRICTED'
    new_profile_enum = (
        self.messages.SslPolicy.ProfileValueValuesEnum(new_profile))

    ssl_policy_ref = self.GetSslPolicyRef(name)
    existing_ssl_policy = self.messages.SslPolicy(
        name=name,
        description='My Description.',
        profile=self.messages.SslPolicy.ProfileValueValuesEnum('MODERN'),
        minTlsVersion=self.messages.SslPolicy.MinTlsVersionValueValuesEnum(
            'TLS_1_0'),
        customFeatures=[],
        fingerprint=b'f1',
        selfLink=ssl_policy_ref.SelfLink())
    patch_ssl_policy = self.messages.SslPolicy(
        profile=new_profile_enum, customFeatures=[], fingerprint=b'f1')
    updated_ssl_policy = copy.deepcopy(existing_ssl_policy)
    updated_ssl_policy.profile = new_profile_enum
    updated_ssl_policy.fingerprint = b'f2'

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=ssl_policy_ref)

    self.ExpectGetRequest(ssl_policy_ref, existing_ssl_policy)
    self.ExpectPatchRequest(ssl_policy_ref, patch_ssl_policy, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(ssl_policy_ref, updated_ssl_policy)

    response = self.Run('compute ssl-policies update {} --profile {}'.format(
        name, new_profile))
    self.assertEqual(response, updated_ssl_policy)

  def testSwitchFromCompatibleToCustomProfile(self):
    name = 'my-ssl-policy'
    new_profile = 'CUSTOM'
    new_profile_enum = (
        self.messages.SslPolicy.ProfileValueValuesEnum(new_profile))
    custom_features = [
        'TLS_RSA_WITH_AES_128_CBC_SHA', 'TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384',
        'TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256'
    ]

    ssl_policy_ref = self.GetSslPolicyRef(name)
    existing_ssl_policy = self.messages.SslPolicy(
        name=name,
        profile=self.messages.SslPolicy.ProfileValueValuesEnum('COMPATIBLE'),
        minTlsVersion=self.messages.SslPolicy.MinTlsVersionValueValuesEnum(
            'TLS_1_0'),
        customFeatures=[],
        fingerprint=b'f1',
        selfLink=ssl_policy_ref.SelfLink())
    patch_ssl_policy = self.messages.SslPolicy(
        profile=new_profile_enum,
        customFeatures=custom_features,
        fingerprint=b'f1')
    updated_ssl_policy = copy.deepcopy(existing_ssl_policy)
    updated_ssl_policy.profile = new_profile_enum
    updated_ssl_policy.customFeatures = custom_features
    updated_ssl_policy.fingerprint = b'f2'

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=ssl_policy_ref)

    self.ExpectGetRequest(ssl_policy_ref, existing_ssl_policy)
    self.ExpectPatchRequest(ssl_policy_ref, patch_ssl_policy, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(ssl_policy_ref, updated_ssl_policy)

    response = self.Run('compute ssl-policies update {} --profile {} '
                        '--custom-features {}'.format(
                            name, new_profile, ','.join(custom_features)))
    self.assertEqual(response, updated_ssl_policy)

  def testSwitchFromCustomToModernProfile(self):
    name = 'my-ssl-policy'
    new_profile = 'MODERN'
    new_profile_enum = (
        self.messages.SslPolicy.ProfileValueValuesEnum(new_profile))

    ssl_policy_ref = self.GetSslPolicyRef(name)
    existing_ssl_policy = self.messages.SslPolicy(
        name=name,
        profile=self.messages.SslPolicy.ProfileValueValuesEnum('CUSTOM'),
        minTlsVersion=self.messages.SslPolicy.MinTlsVersionValueValuesEnum(
            'TLS_1_0'),
        customFeatures=[
            'TLS_RSA_WITH_AES_128_CBC_SHA',
            'TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384',
            'TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256'
        ],
        fingerprint=b'f1',
        selfLink=ssl_policy_ref.SelfLink())
    patch_ssl_policy = self.messages.SslPolicy(
        profile=new_profile_enum, customFeatures=[], fingerprint=b'f1')
    updated_ssl_policy = copy.deepcopy(existing_ssl_policy)
    updated_ssl_policy.profile = new_profile_enum
    updated_ssl_policy.customFeatures = []
    updated_ssl_policy.fingerprint = b'f2'

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=ssl_policy_ref)

    self.ExpectGetRequest(ssl_policy_ref, existing_ssl_policy)
    self.ExpectPatchRequest(ssl_policy_ref, patch_ssl_policy, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(ssl_policy_ref, updated_ssl_policy)

    response = self.Run('compute ssl-policies update {} --profile {}'.format(
        name, new_profile))
    self.assertEqual(response, updated_ssl_policy)

  def testUpdateMinTlsVersion(self):
    name = 'my-ssl-policy'
    new_min_tls_version_enum = (
        self.messages.SslPolicy.MinTlsVersionValueValuesEnum('TLS_1_2'))

    ssl_policy_ref = self.GetSslPolicyRef(name)
    existing_ssl_policy = self.messages.SslPolicy(
        name=name,
        profile=self.messages.SslPolicy.ProfileValueValuesEnum('COMPATIBLE'),
        minTlsVersion=self.messages.SslPolicy.MinTlsVersionValueValuesEnum(
            'TLS_1_1'),
        customFeatures=[],
        fingerprint=b'f1',
        selfLink=ssl_policy_ref.SelfLink())
    patch_ssl_policy = self.messages.SslPolicy(
        minTlsVersion=new_min_tls_version_enum, fingerprint=b'f1')
    updated_ssl_policy = copy.deepcopy(existing_ssl_policy)
    updated_ssl_policy.minTlsVersion = new_min_tls_version_enum
    updated_ssl_policy.fingerprint = b'f2'

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=ssl_policy_ref)

    self.ExpectGetRequest(ssl_policy_ref, existing_ssl_policy)
    self.ExpectPatchRequest(ssl_policy_ref, patch_ssl_policy, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(ssl_policy_ref, updated_ssl_policy)

    response = self.Run('compute ssl-policies update {} '
                        '--min-tls-version {}'.format(name, '1.2'))
    self.assertEqual(response, updated_ssl_policy)

  def testCustomFeaturesWithNonCustomProfile(self):
    name = 'my-ssl-policy'
    custom_features = [
        'TLS_RSA_WITH_AES_128_CBC_SHA', 'TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384',
        'TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256'
    ]
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--custom-features\]: Custom features cannot be '
        r'specified when using non-CUSTOM profiles.'):
      self.Run('compute ssl-policies update {} --profile {} '
               '--custom-features {}'.format(name, 'MODERN',
                                             ','.join(custom_features)))


class SslPolicyUpdateBetaTest(SslPolicyUpdateGATest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)


class SslPolicyUpdateAlphaTest(SslPolicyUpdateBetaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
