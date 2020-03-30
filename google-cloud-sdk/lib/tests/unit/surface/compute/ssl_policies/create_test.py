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
"""Tests for the SSL policies create alpha command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import ssl_policies_test_base


class SslPolicyCreateGATest(ssl_policies_test_base.SslPoliciesTestBase):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.GA)

  def testNonCustomProfile(self):
    name = 'my-ssl-policy'
    description = 'My Description'
    profile = 'MODERN'
    profile_enum = self.messages.SslPolicy.ProfileValueValuesEnum(profile)
    min_tls_version_enum = self.messages.SslPolicy.MinTlsVersionValueValuesEnum(
        'TLS_1_0')

    ssl_policy_ref = self.GetSslPolicyRef(name)
    ssl_policy_to_insert = self.messages.SslPolicy(
        name=name,
        description=description,
        profile=profile_enum,
        minTlsVersion=min_tls_version_enum,
        customFeatures=[])
    created_ssl_policy = copy.deepcopy(ssl_policy_to_insert)
    created_ssl_policy.fingerprint = b'SOME_FINGERPRINT'
    created_ssl_policy.selfLink = ssl_policy_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=ssl_policy_ref)

    self.ExpectInsertRequest(ssl_policy_ref, ssl_policy_to_insert, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(ssl_policy_ref, created_ssl_policy)

    response = self.Run('compute ssl-policies create {} --description "{}" '
                        '--profile {} --min-tls-version {} '
                        '--format=disable'.format(
                            name, description, profile, '1.0'))
    resources = list(response)
    self.assertEqual(resources[0], created_ssl_policy)

  def testCustomProfile(self):
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
    ssl_policy_to_insert = self.messages.SslPolicy(
        name=name,
        profile=profile_enum,
        minTlsVersion=min_tls_version_enum,
        customFeatures=custom_features)
    created_ssl_policy = copy.deepcopy(ssl_policy_to_insert)
    created_ssl_policy.fingerprint = b'SOME_FINGERPRINT'
    created_ssl_policy.selfLink = ssl_policy_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=ssl_policy_ref)

    self.ExpectInsertRequest(ssl_policy_ref, ssl_policy_to_insert, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(ssl_policy_ref, created_ssl_policy)

    response = self.Run('compute ssl-policies create {} --profile {} '
                        '--min-tls-version {} --custom-features {} '
                        '--format=disable'.format(
                            name, profile, '1.2', ','.join(custom_features)))
    resources = list(response)
    self.assertEqual(resources[0], created_ssl_policy)

  def testDefaultProfile(self):
    name = 'my-ssl-policy'
    profile = 'COMPATIBLE'
    profile_enum = self.messages.SslPolicy.ProfileValueValuesEnum(profile)
    min_tls_version_enum = self.messages.SslPolicy.MinTlsVersionValueValuesEnum(
        'TLS_1_1')

    ssl_policy_ref = self.GetSslPolicyRef(name)
    ssl_policy_to_insert = self.messages.SslPolicy(
        name=name,
        profile=profile_enum,
        minTlsVersion=min_tls_version_enum,
        customFeatures=[])
    created_ssl_policy = copy.deepcopy(ssl_policy_to_insert)
    created_ssl_policy.fingerprint = b'SOME_FINGERPRINT'
    created_ssl_policy.selfLink = ssl_policy_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=ssl_policy_ref)

    self.ExpectInsertRequest(ssl_policy_ref, ssl_policy_to_insert, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(ssl_policy_ref, created_ssl_policy)

    response = self.Run('compute ssl-policies create {} '
                        '--min-tls-version {} --format=disable'.format(
                            name, '1.1'))
    resources = list(response)
    self.assertEqual(resources[0], created_ssl_policy)

  def testDefaultMinTlsVersion(self):
    name = 'my-ssl-policy'
    profile = 'RESTRICTED'
    profile_enum = self.messages.SslPolicy.ProfileValueValuesEnum(profile)
    min_tls_version_enum = self.messages.SslPolicy.MinTlsVersionValueValuesEnum(
        'TLS_1_0')

    ssl_policy_ref = self.GetSslPolicyRef(name)
    ssl_policy_to_insert = self.messages.SslPolicy(
        name=name,
        profile=profile_enum,
        minTlsVersion=min_tls_version_enum,
        customFeatures=[])
    created_ssl_policy = copy.deepcopy(ssl_policy_to_insert)
    created_ssl_policy.fingerprint = b'SOME_FINGERPRINT'
    created_ssl_policy.selfLink = ssl_policy_ref.SelfLink()

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=ssl_policy_ref)

    self.ExpectInsertRequest(ssl_policy_ref, ssl_policy_to_insert, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(ssl_policy_ref, created_ssl_policy)

    response = self.Run('compute ssl-policies create {} '
                        '--profile {} --format=disable'.format(name, profile))
    resources = list(response)
    self.assertEqual(resources[0], created_ssl_policy)

  def testInvalidProfile(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --profile: Invalid choice: \'FOO\''):
      self.Run('compute ssl-policies create my-ssl-policy ' '--profile FOO')

  def testInvalidMinTlsVersion(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --min-tls-version: Invalid choice: \'2.0\''):
      self.Run('compute ssl-policies create my-ssl-policy '
               '--min-tls-version 2.0')


class SslPolicyCreateBetaTest(SslPolicyCreateGATest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)


class SslPolicyCreateAlphaTest(SslPolicyCreateBetaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
