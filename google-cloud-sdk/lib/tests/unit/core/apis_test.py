# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Tests for the apis module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.api_lib.util import apis_util
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case
from googlecloudsdk.third_party.apis import apis_map
from googlecloudsdk.third_party.apis.compute.alpha import compute_alpha_client
from googlecloudsdk.third_party.apis.compute.alpha import compute_alpha_messages
from googlecloudsdk.third_party.apis.compute.v1 import compute_v1_client
from googlecloudsdk.third_party.apis.compute.v1 import compute_v1_messages


class ApisTest(sdk_test_base.SdkBase):

  def SetUp(self):
    self.StartObjectPatch(apis_map, 'MAP', {})
    apis.AddToApisMap('compute', 'v1', True)
    apis.AddToApisMap('compute', 'alpha', False)
    apis.AddToApisMap('dns', 'v1', True)
    apis.AddToApisMap('dns', 'v1beta1', False)
    apis.AddToApisMap('sqladmin', 'v1beta3', True)
    apis.AddToApisMap('sqladmin', 'v1beta4', False)

    self.StartObjectPatch(apis_util, '_API_NAME_ALIASES', {
        'sql': 'sqladmin',
    })

  def testConstructAPIDef(self):
    expected_api_def = apis_map.APIDef(
        'googlecloudsdk.third_party.apis.dns.v1',
        'dns_v1_client.DnsV1',
        'dns_v1_messages', True)
    actual_api_def = apis.ConstructApiDef('dns', 'v1', True)
    self.assertEqual(expected_api_def, actual_api_def)

  def testAddToApisMap(self):
    with self.assertRaisesRegex(
        apis_util.UnknownAPIError,
        r'API named \[hello\] does not exist in the APIs map'):
      apis_internal._GetApiDef('hello', 'v1')

    expected_api_def = apis.ConstructApiDef('hello', 'v1', True)
    apis.AddToApisMap('hello', 'v1', True)
    self.assertEqual('v1', apis_internal._GetDefaultVersion('hello'))
    self.assertEqual(expected_api_def, apis_internal._GetApiDef('hello', 'v1'))

  def testAddToApisMap_NoDefault(self):
    apis.AddToApisMap('hello', 'v1')
    self.assertTrue(apis_internal._GetApiDef('hello', 'v1').default_version)
    apis.AddToApisMap('hello', 'v2')
    self.assertFalse(apis_internal._GetApiDef('hello', 'v2').default_version)
    self.assertTrue(apis_internal._GetApiDef('hello', 'v1').default_version)

  def testGetDefaultVersion(self):
    api_name = 'dns'
    default_api_def = apis_internal._GetApiDef(api_name, 'v1')

    default_version = apis_internal._GetDefaultVersion(api_name)
    also_default_api_def = apis_internal._GetApiDef(api_name, default_version)

    self.assertEqual(default_api_def, also_default_api_def)

  def testGetDefaultVersionUnknownAPI(self):
    self.assertEqual(None, apis_internal._GetDefaultVersion('something'))

  def testSetDefaultVersion(self):
    self.assertEqual('v1', apis_internal._GetDefaultVersion('dns'))
    apis.SetDefaultVersion('dns', 'v1beta1')
    self.assertEqual('v1beta1', apis_internal._GetDefaultVersion('dns'))

  def testSetDefaultVersionUnknownAPI(self):
    with self.assertRaises(apis_util.UnknownAPIError):
      apis.SetDefaultVersion('something', 'v1')

  def testSetDefaultVersionUnknownVersion(self):
    with self.assertRaises(apis_util.UnknownVersionError):
      apis.SetDefaultVersion('dns', 'v1something')

  def testResolveVersionWithOverride(self):
    overridden_version = 'alpha'
    properties.VALUES.api_client_overrides.compute.Set(overridden_version)
    resolved_version = apis.ResolveVersion('compute')
    self.assertEqual(overridden_version, resolved_version)

    overridden_version = 'v1beta4'
    properties.VALUES.api_client_overrides.sql.Set(overridden_version)
    resolved_version = apis.ResolveVersion('sql')
    self.assertEqual(overridden_version, resolved_version)

  def testResolveVersionWithoutOverride(self):
    resolved_version = apis.ResolveVersion('compute')
    self.assertEqual('v1', resolved_version)

  def testResolveVersionWithDefaultOverride(self):
    resolved_version = apis.ResolveVersion('compute', 'hello')
    self.assertEqual('hello', resolved_version)

  def testGetDefaultApiDef(self):
    expected_api_def = apis.ConstructApiDef('dns', 'v1', True)
    actual_api_def = apis_internal._GetApiDef('dns', 'v1')
    self.assertEqual(expected_api_def, actual_api_def)

  def testGetApiDefWithOverride(self):
    expected_api_def = apis.ConstructApiDef('compute', 'alpha', False)
    properties.VALUES.api_client_overrides.compute.Set('alpha')
    actual_api_def = apis_internal._GetApiDef('compute', 'v1')
    self.assertEqual(expected_api_def, actual_api_def)

    expected_api_def = apis.ConstructApiDef('sql', 'v1beta4', False)
    properties.VALUES.api_client_overrides.sql.Set('v1beta4')
    actual_api_def = apis_internal._GetApiDef('sql', 'v1beta3')
    self.assertEqual(expected_api_def, actual_api_def)

  def testGetApiDefWithAlias(self):
    sqladmin_api_def = apis_internal._GetApiDef('sqladmin', 'v1beta3')
    also_sqladmin_api_def = apis_internal._GetApiDef('sql', 'v1beta3')
    self.assertEqual(sqladmin_api_def, also_sqladmin_api_def)

  def testGetApiDefUnknownAPI(self):
    with self.assertRaisesRegex(
        apis_util.UnknownAPIError,
        r'API named \[hello\] does not exist in the APIs map'):
      apis_internal._GetApiDef('hello', 'v1')

  def testGetApiDefUnknownVersion(self):
    with self.assertRaisesRegex(
        apis_util.UnknownVersionError,
        r'The \[compute\] API does not have version \[hello\] in the APIs map'):
      apis_internal._GetApiDef('compute', 'hello')

  def testGetDefaultClient(self):
    client = apis.GetClientInstance('compute', 'v1', no_http=True)
    self.assertTrue(isinstance(client, compute_v1_client.ComputeV1))

  def testGetDefaultClientWithOverride(self):
    properties.VALUES.api_client_overrides.compute.Set('alpha')
    client = apis.GetClientInstance('compute', 'v1', no_http=True)
    self.assertTrue(isinstance(client, compute_alpha_client.ComputeAlpha))

  def testGetClientForSpecificVersion(self):
    client = apis.GetClientInstance('compute', 'alpha', no_http=True)
    self.assertTrue(isinstance(client, compute_alpha_client.ComputeAlpha))

  def testGetClientWithEndpointOverride(self):
    override = 'https://www-googleapis-test.sandbox.google.com/compute/v1/'
    properties.VALUES.api_endpoint_overrides.compute.Set(override)
    client = apis.GetClientInstance('compute', 'v1', no_http=True)
    self.assertEqual(override, client._url)

    override = 'http://localhost:1234/'
    properties.VALUES.api_endpoint_overrides.sql.Set(override)
    client = apis.GetClientInstance('sql', 'v1beta3', no_http=True)
    self.assertEqual(override, client._url)

  def testGetDefaultEndpointForUrl(self):
    url = 'https://www.googleapis.com/sql/v1beta3/path/to/resource'
    default_endpoint_url = apis_internal._GetDefaultEndpointUrl(url)
    self.assertEqual(url, default_endpoint_url)

  def testGetDefaultEndpointForUrl_Override(self):
    override = 'http://localhost:1234/'
    properties.VALUES.api_endpoint_overrides.sql.Set(override)
    endpoint = apis_internal._GetDefaultEndpointUrl(
        override + 'path/to/resource')
    self.assertEqual('https://www.googleapis.com/sql/v1beta3/path/to/resource',
                     endpoint)

  def testGetDefaultMessagesModule(self):
    messages_module = apis.GetMessagesModule('compute', 'v1')
    self.assertEqual(compute_v1_messages, messages_module)

  def testGetDefaultMessagesModuleWithOverride(self):
    properties.VALUES.api_client_overrides.compute.Set('alpha')
    messages_module = apis.GetMessagesModule('compute', 'v1')
    self.assertEqual(compute_alpha_messages, messages_module)

  def testGetMessagesModuleForSpecificVersion(self):
    messages_module = apis.GetMessagesModule('compute', 'alpha')
    self.assertEqual(compute_alpha_messages, messages_module)


if __name__ == '__main__':
  test_case.main()
