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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import endpoints
from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.firebase.test import unit_base
import six

PROD_TESTING = 'https://testing.googleapis.com/'
TEST_TESTING = 'https://test-testing.sandbox.googleapis.com/'
PROD_RESULTS = 'https://www.googleapis.com/toolresults/v1beta3/'
TEST_RESULTS = 'https://staging-toolresults.sandbox.googleapis.com/toolresults/v1beta3/'


class EndpointTests(unit_base.TestMockClientTest):
  """Unit tests for api_lib.test.endpoints."""

  def testDefaultEndpoints(self):
    properties.VALUES.api_endpoint_overrides.testing.Set(None)
    properties.VALUES.api_endpoint_overrides.toolresults.Set(None)
    endpoints.ValidateTestServiceEndpoints()

  def testProdEndpointCompatibleWithDefaultEndpoint(self):
    properties.VALUES.api_endpoint_overrides.testing.Set(None)
    properties.VALUES.api_endpoint_overrides.toolresults.Set(PROD_RESULTS)
    endpoints.ValidateTestServiceEndpoints()

    properties.VALUES.api_endpoint_overrides.testing.Set(PROD_TESTING)
    properties.VALUES.api_endpoint_overrides.toolresults.Set(None)
    endpoints.ValidateTestServiceEndpoints()

  def testProdEndpointsAreCompatible(self):
    properties.VALUES.api_endpoint_overrides.testing.Set(PROD_TESTING)
    properties.VALUES.api_endpoint_overrides.toolresults.Set(PROD_RESULTS)
    endpoints.ValidateTestServiceEndpoints()

  def testTestEndpointsAreCompatible(self):
    properties.VALUES.api_endpoint_overrides.testing.Set(TEST_TESTING)
    properties.VALUES.api_endpoint_overrides.toolresults.Set(TEST_RESULTS)
    endpoints.ValidateTestServiceEndpoints()

  def testLocalEndpointCompatibleWithTestEndpoint(self):
    properties.VALUES.api_endpoint_overrides.testing.Set('https://localhost/')
    properties.VALUES.api_endpoint_overrides.toolresults.Set(TEST_RESULTS)
    endpoints.ValidateTestServiceEndpoints()

  def testProdEndpointIsIncompatibleWithTestEndpoint(self):
    properties.VALUES.api_endpoint_overrides.testing.Set(PROD_TESTING)
    properties.VALUES.api_endpoint_overrides.toolresults.Set(TEST_RESULTS)

    with self.assertRaises(exceptions.IncompatibleApiEndpointsError) as ex_ctx:
      endpoints.ValidateTestServiceEndpoints()
    self.assertIn('not compatible', six.text_type(ex_ctx.exception))

  def testEmptyEndpointsAreInvalid(self):
    with self.assertRaises(properties.InvalidValueError) as ex_ctx:
      properties.VALUES.api_endpoint_overrides.testing.Set('')
    self.assertIn('not a valid endpoint', six.text_type(ex_ctx.exception))

    with self.assertRaises(properties.InvalidValueError) as ex_ctx:
      properties.VALUES.api_endpoint_overrides.toolresults.Set('')
    self.assertIn('not a valid endpoint', six.text_type(ex_ctx.exception))


if __name__ == '__main__':
  test_case.main()
