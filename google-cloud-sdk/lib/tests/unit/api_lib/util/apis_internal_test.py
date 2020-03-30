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
"""Tests for googlecloudsdk.api_lib.util.apis_internal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from googlecloudsdk.third_party.apis import apis_map


class EffectiveApiEndpointTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.compute_v1_mtls_endpoint = 'https://compute.mtls.googleapis.com/compute/v1/'
    self.compute_v1_endpoint = 'https://compute.googleapis.com/compute/v1/'
    self.compute_v1_api_def = apis_map.APIDef(
        class_path='googlecloudsdk.third_party.apis.compute.v1',
        client_classpath='compute_v1_client.ComputeV1',
        messages_modulepath='compute_v1_messages',
        default_version=True,
        enable_mtls=True,
        mtls_endpoint_override=self.compute_v1_mtls_endpoint)

    self.spanner_v1_endpoint = 'https://spanner.googleapis.com/'
    self.spanner_v1_mtls_endpoint = 'https://spanner.mtls.googleapis.com/'
    self.spanner_v1_api_def = apis_map.APIDef(
        class_path='googlecloudsdk.third_party.apis.spanner.v1',
        client_classpath='spanner_v1_client.SpannerV1',
        messages_modulepath='spanner_v1_messages',
        default_version=True,
        enable_mtls=True,
        mtls_endpoint_override='')

    self.redis_v1_endpoint = 'https://redis.googleapis.com/'
    self.redis_v1_api_def = apis_map.APIDef(
        class_path='googlecloudsdk.third_party.apis.redis.v1',
        client_classpath='redis_v1_client.RedisV1',
        messages_modulepath='redis_v1_messages',
        default_version=True,
        enable_mtls=False,
        mtls_endpoint_override='')

  def testClientCertPropertyOff_DisableMTLS(self):
    self.StartObjectPatch(
        properties.VALUES.context_aware.use_client_certificate,
        'GetBool').return_value = False
    self.StartObjectPatch(apis_internal,
                          '_GetApiDef').return_value = self.redis_v1_api_def
    endpoint = apis_internal._GetEffectiveApiEndpoint('redis', 'v1')
    self.assertEqual(endpoint, self.redis_v1_endpoint)
    self.AssertErrEquals('')

  def testClientCertPropertyOff_EnableMTLS(self):
    self.StartObjectPatch(
        properties.VALUES.context_aware.use_client_certificate,
        'GetBool').return_value = False
    self.StartObjectPatch(apis_internal,
                          '_GetApiDef').return_value = self.spanner_v1_api_def
    endpoint = apis_internal._GetEffectiveApiEndpoint('spanner', 'v1')
    self.assertEqual(endpoint, self.spanner_v1_endpoint)
    self.AssertErrEquals('')

  def testClientCertPropertyOff_EnableMTLS_OverrideMtlsEndpoint(self):
    self.StartObjectPatch(
        properties.VALUES.context_aware.use_client_certificate,
        'GetBool').return_value = False
    self.StartObjectPatch(apis_internal,
                          '_GetApiDef').return_value = self.compute_v1_api_def
    endpoint = apis_internal._GetEffectiveApiEndpoint('compute', 'v1')
    self.assertEqual(endpoint, self.compute_v1_endpoint)
    self.AssertErrEquals('')

  def testClientCertPropertyOn_DisableMTLS(self):
    self.StartObjectPatch(
        properties.VALUES.context_aware.use_client_certificate,
        'GetBool').return_value = True
    self.StartObjectPatch(apis_internal,
                          '_GetApiDef').return_value = self.redis_v1_api_def
    endpoint = apis_internal._GetEffectiveApiEndpoint('redis', 'v1')
    self.assertEqual(endpoint, self.redis_v1_endpoint)
    self.AssertErrContains(
        'redis_v1 does not support client certificate authorization on this '
        'version of gcloud. The request will be executed without using a '
        'client certificate. '
        'Please run $ gcloud topic client-certificate for more information.')

  def testClientCertPropertyOn_EnableMTLS(self):
    self.StartObjectPatch(
        properties.VALUES.context_aware.use_client_certificate,
        'GetBool').return_value = True
    self.StartObjectPatch(apis_internal,
                          '_GetApiDef').return_value = self.spanner_v1_api_def
    endpoint = apis_internal._GetEffectiveApiEndpoint('spanner', 'v1')
    self.assertEqual(endpoint, self.spanner_v1_mtls_endpoint)
    self.AssertErrEquals('')

  def testClientCertPropertyOn_EnableMTLS_OverrideMtlsEndpoint(self):
    self.StartObjectPatch(
        properties.VALUES.context_aware.use_client_certificate,
        'GetBool').return_value = True
    self.StartObjectPatch(apis_internal,
                          '_GetApiDef').return_value = self.compute_v1_api_def
    endpoint = apis_internal._GetEffectiveApiEndpoint('compute', 'v1')
    self.assertEqual(endpoint, self.compute_v1_mtls_endpoint)
    self.AssertErrEquals('')

  def testAllMtlsEnabledServicesHaveMtlsEndpoints(self):
    """Makes sure all services enabling mTLS in gcloud have mTLS endpoints."""
    self.StartObjectPatch(
        properties.VALUES.context_aware.use_client_certificate,
        'GetBool').return_value = True
    failures = []
    for service, versions in apis_map.MAP.items():
      for version, api_def in versions.items():
        if api_def.enable_mtls:
          mtls_endpoint = apis_internal._GetEffectiveApiEndpoint(
              service, version)
          if '.mtls.' not in mtls_endpoint:
            failures.append((service, version))
    if failures:
      self.fail('These APIs have mTLS enabled but do not have mTLS endpoint: {}'
                .format(failures))


if __name__ == '__main__':
  test_case.main()
