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

"""Tests for gcloud app regions."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import http
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.app import api_test_util

import httplib2


class RegionsListTest(api_test_util.ApiTestBase):
  """Tests for `gcloud app regions list` commands."""

  REGIONS = {'us-central': [('standardEnvironmentAvailable', True),
                            ('flexibleEnvironmentAvailable', True)],
             'us-east1': [('standardEnvironmentAvailable', True),
                          ('flexibleEnvironmentAvailable', True)],
             'europe-west': [('standardEnvironmentAvailable', True),
                             ('flexibleEnvironmentAvailable', False)]}

  def testList(self):
    """Test output of `gcloud app regions list` command."""
    self.ExpectListRegionsRequest(self.REGIONS, self.Project())
    self.Run('app regions list')
    self.AssertOutputContains("""\
        REGION      SUPPORTS STANDARD  SUPPORTS FLEXIBLE
        europe-west YES                NO
        us-central  YES                YES
        us-east1    YES                YES""", normalize_space=True)


class QuotaHeaderTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth,
                      parameterized.TestCase):
  """Make sure user project quota is disabled for this API."""

  def SetUp(self):
    properties.VALUES.core.project.Set('foo')
    mock_http_client = self.StartObjectPatch(http, 'Http')
    mock_http_client.return_value.request.return_value = \
        (httplib2.Response({'status': 200}), b'')
    self.request_mock = mock_http_client.return_value.request

  @parameterized.parameters(
      (None, 'beta', None),
      (None, '', None),
      (properties.VALUES.billing.LEGACY, 'beta', None),
      (properties.VALUES.billing.LEGACY, '', None),
      (properties.VALUES.billing.CURRENT_PROJECT, 'beta', b'foo'),
      (properties.VALUES.billing.CURRENT_PROJECT, '', b'foo'),
      ('bar', 'beta', b'bar'),
      ('bar', '', b'bar'),
  )
  def testQuotaHeader(self, prop_value, track, header_value):
    properties.VALUES.billing.quota_project.Set(prop_value)
    self.Run(track + ' app regions list')
    header = self.request_mock.call_args[0][3].get(b'X-Goog-User-Project', None)
    self.assertEqual(header, header_value)


if __name__ == '__main__':
  test_case.main()
