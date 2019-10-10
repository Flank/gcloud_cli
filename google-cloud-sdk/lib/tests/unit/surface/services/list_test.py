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

"""Unit tests for services list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import http
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.services import unit_test_base

import httplib2


class ListTestGA(unit_test_base.SUUnitTestBase):
  """Unit tests for services list command."""
  OPERATION_NAME = 'operations/abc.0000000000'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testList(self):
    self.ExpectListServicesCall()

    self.Run('services list --available')
    self.AssertOutputEquals(
        """\
NAME TITLE
service-name-1.googleapis.com
service-name.googleapis.com
""",
        normalize_space=True)


class ListTestBeta(ListTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ListTestAlpha(ListTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


# DO NOT REMOVE THIS TEST.
# The services API should always use gcloud's shared quota.
class QuotaHeaderTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth,
                      parameterized.TestCase):
  """Make sure user project quota is disabled for this API."""

  def SetUp(self):
    properties.VALUES.core.project.Set('foo')
    mock_http_client = self.StartObjectPatch(http, 'Http')
    mock_http_client.return_value.request.return_value = \
      (httplib2.Response({
          'status': 200
      }), b'')
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
    self.Run(track + ' services list')
    header = self.request_mock.call_args[0][3].get(b'X-Goog-User-Project', None)
    self.assertEqual(header, header_value)


if __name__ == '__main__':
  test_case.main()
