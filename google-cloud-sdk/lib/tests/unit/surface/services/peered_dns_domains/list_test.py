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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.services import unit_test_base
import mock

_NETWORK = 'hello'
_GOOGLEAPIS_NAME = 'googleapis-com'
_GOOGLEAPIS_SUFFIX = 'googleapis.com.'
_GCR_NAME = 'gcr-io'
_GCR_SUFFIX = 'gcr.io.'


class ListPeeredDnsDomainsTest(unit_test_base.SNUnitTestBase):
  """Unit tests for services peered-dns-domains list command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  @mock.patch.object(projects_api, 'Get', autospec=True)
  def testListPeeredDnsDomains_Success(self, mock_get):
    mock_get.return_value.projectNumber = self.PROJECT_NUMBER
    domains = [
        self.services_messages.PeeredDnsDomain(
            name=_GOOGLEAPIS_NAME,
            dnsSuffix=_GOOGLEAPIS_SUFFIX,
        ),
        self.services_messages.PeeredDnsDomain(
            name=_GCR_NAME,
            dnsSuffix=_GCR_SUFFIX,
        ),
    ]

    self.ExpectListPeeredDnsDomains(_NETWORK, domains)

    self.Run(
        ('services peered-dns-domains list --service={} --network={}').format(
            self.service,
            _NETWORK,
        ))

    expected_output = textwrap.dedent("""\
        NAME           DNS_SUFFIX
        gcr-io         gcr.io.
        googleapis-com googleapis.com.
        """)

    self.AssertOutputEquals(expected_output, normalize_space=True)

  @mock.patch.object(projects_api, 'Get', autospec=True)
  def testListPeeredDnsDomains_WithDefaultService(self, mock_get):
    mock_get.return_value.projectNumber = self.PROJECT_NUMBER
    self.service = 'servicenetworking.googleapis.com'
    domains = [
        self.services_messages.PeeredDnsDomain(
            name=_GOOGLEAPIS_NAME,
            dnsSuffix=_GOOGLEAPIS_SUFFIX,
        ),
        self.services_messages.PeeredDnsDomain(
            name=_GCR_NAME,
            dnsSuffix=_GCR_SUFFIX,
        ),
    ]

    self.ExpectListPeeredDnsDomains(_NETWORK, domains)

    self.Run(('services peered-dns-domains list --network={}').format(_NETWORK))

    expected_output = textwrap.dedent("""\
        NAME           DNS_SUFFIX
        gcr-io         gcr.io.
        googleapis-com googleapis.com.
        """)

    self.AssertOutputEquals(expected_output, normalize_space=True)

  @mock.patch.object(projects_api, 'Get', autospec=True)
  def testListPeeredDnsDomains_PermissionDenied(self, mock_get):
    mock_get.return_value.projectNumber = self.PROJECT_NUMBER
    server_error = http_error.MakeDetailedHttpError(code=403, message='Error.')
    self.ExpectListPeeredDnsDomains(_NETWORK, domains=None, error=server_error)

    with self.assertRaisesRegex(
        exceptions.ListPeeredDnsDomainsPermissionDeniedException,
        r'Error.',
    ):
      self.Run(
          ('services peered-dns-domains list --service={} --network={}').format(
              self.service,
              _NETWORK,
          ))


if __name__ == '__main__':
  test_case.main()
