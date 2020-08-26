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
"""Tests for On-Demand Scanning request hooks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container.images import request_hooks
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case


class FormatScanRequestParentTest(test_case.TestCase, parameterized.TestCase):

  def SetUp(self):
    properties.VALUES.core.project.Set('fake-project')
    self.msgs = apis.GetMessagesModule('ondemandscanning', 'v1beta1')

  class ArgsMock(object):
    """Mock arguments."""
    resource_url = None

  @parameterized.named_parameters([
      {
          'testcase_name': '_global',
          'resource_url':
              'https://gcr.io/fake-project/debian@sha256:6ea10209bda9af3c1260950b947715d6a3825d21d89e39889f4b9dc5dc24a763',
          'want_parent': 'projects/fake-project/locations/us',
      },
      {
          'testcase_name': '_global_no_https',
          'resource_url':
              'gcr.io/fake-project/debian@sha256:6ea10209bda9af3c1260950b947715d6a3825d21d89e39889f4b9dc5dc24a763',
          'want_parent': 'projects/fake-project/locations/us',
      },
      {
          'testcase_name': '_us',
          'resource_url':
              'https://us.gcr.io/fake-project/debian@sha256:6ea10209bda9af3c1260950b947715d6a3825d21d89e39889f4b9dc5dc24a763',
          'want_parent': 'projects/fake-project/locations/us',
      },
      {
          'testcase_name': '_us_no_https',
          'resource_url':
              'us.gcr.io/fake-project/debian@sha256:6ea10209bda9af3c1260950b947715d6a3825d21d89e39889f4b9dc5dc24a763',
          'want_parent': 'projects/fake-project/locations/us',
      },
      {
          'testcase_name': '_eu',
          'resource_url':
              'https://eu.gcr.io/fake-project/debian@sha256:6ea10209bda9af3c1260950b947715d6a3825d21d89e39889f4b9dc5dc24a763',
          'want_parent': 'projects/fake-project/locations/europe',
      },
      {
          'testcase_name': '_eu_no_https',
          'resource_url':
              'eu.gcr.io/fake-project/debian@sha256:6ea10209bda9af3c1260950b947715d6a3825d21d89e39889f4b9dc5dc24a763',
          'want_parent': 'projects/fake-project/locations/europe',
      },
      {
          'testcase_name': '_asia',
          'resource_url':
              'https://asia.gcr.io/fake-project/debian@sha256:6ea10209bda9af3c1260950b947715d6a3825d21d89e39889f4b9dc5dc24a763',
          'want_parent': 'projects/fake-project/locations/asia',
      },
      {
          'testcase_name': '_asia_no_https',
          'resource_url':
              'asia.gcr.io/fake-project/debian@sha256:6ea10209bda9af3c1260950b947715d6a3825d21d89e39889f4b9dc5dc24a763',
          'want_parent': 'projects/fake-project/locations/asia',
      },
  ])
  def test_format_scan_request_parent(self, resource_url, want_parent):
    req = (self.msgs
           .OndemandscanningProjectsLocationsScansScanContainerImageRequest())
    args = self.ArgsMock()
    args.resource_url = resource_url

    parent = request_hooks.FormatScanRequestParent(None, args, req).parent

    self.assertEqual(parent, want_parent, 'Got: "{}", want: "{}"'.format(
        parent, want_parent))

  @parameterized.named_parameters([
      {
          'testcase_name': '_missing_region',
          'resource_url':
              'https://fake-project/debian@sha256:6ea10209bda9af3c1260950b947715d6a3825d21d89e39889f4b9dc5dc24a763',
      },
      {
          'testcase_name': '_http_instead_of_https',
          'resource_url':
              'http://gcr.io/fake-project/debian@sha256:6ea10209bda9af3c1260950b947715d6a3825d21d89e39889f4b9dc5dc24a763',
      },
      {
          'testcase_name': '_invalid_region',
          'resource_url':
              'https://aisa.gcr.io/fake-project/debian@sha256:6ea10209bda9af3c1260950b947715d6a3825d21d89e39889f4b9dc5dc24a763',
      },
  ])
  def test_format_scan_request_parent_errors(self, resource_url):
    req = (self.msgs
           .OndemandscanningProjectsLocationsScansScanContainerImageRequest())
    args = self.ArgsMock()
    args.resource_url = resource_url

    self.assertRaises(exceptions.InvalidArgumentException,
                      request_hooks.FormatScanRequestParent, None, args, req)
