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

"""General unit tests for endpoints."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties

from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base


class EndpointsTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for endpoints."""

  def testServicesTestEnvironment(self):
    # Set an environment override
    endpoint_override = 'https://foo.org/'
    properties.VALUES.api_endpoint_overrides.servicemanagement.Set(
        endpoint_override)

    # Get an instance of the servicemanagement client
    services_client = apis.GetClientInstance('servicemanagement', 'v1')
    self.assertIn(endpoint_override, services_client._url)


if __name__ == '__main__':
  test_case.main()
