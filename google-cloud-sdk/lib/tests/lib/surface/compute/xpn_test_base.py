# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Base class for tests for `gcloud compute xpn` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.compute import xpn_api
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base

import mock


class XpnTestBase(cli_test_base.CliTestBase, parameterized.TestCase):
  """Base class for xpn tests."""

  def _SetUp(self, track):
    self.track = track
    self.StartPatch('googlecloudsdk.core.credentials.http.Http', autospec=True)
    self.xpn_client = mock.Mock(autospec=xpn_api.XpnClient)
    client = xpn_api.GetXpnClient(self.track)
    self.messages = client.messages
    self.xpn_client.messages = client.messages
    self.get_xpn_client_mock = self.StartObjectPatch(
        xpn_api, 'GetXpnClient', return_value=self.xpn_client)

  def _MakeProject(self):
    project_status_enum = self.messages.Project.XpnProjectStatusValueValuesEnum
    return self.messages.Project(
        name='xpn-host',
        creationTimestamp='2013-09-06T17:54:10.636-07:00',
        selfLink='https://www.googleapis.com/compute/alpha/projects/xpn-host/',
        xpnProjectStatus=project_status_enum.HOST
    )


class XpnApitoolsTestBase(sdk_test_base.WithFakeAuth,
                          cli_test_base.CliTestBase,
                          parameterized.TestCase):
  """Base class for xpn tests."""

  def _SetUp(self, track, api_version):
    self.track = track
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('compute', api_version),
        real_client=core_apis.GetClientInstance(
            'compute', api_version, no_http=True))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)
    self.messages = self.apitools_client.MESSAGES_MODULE
