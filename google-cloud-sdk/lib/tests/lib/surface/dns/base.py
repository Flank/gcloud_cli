# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Base classes for all gcloud dns tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base


class DnsMockMultiTrackTest(cli_test_base.CliTestBase,
                            sdk_test_base.WithFakeAuth,
                            sdk_test_base.WithTempCWD):
  """A base class for gcloud dns tests that need to use a mocked DNS client."""

  def SetUpForTrack(self, track, api_version):
    self.track = track
    self.api_version = api_version

    self.client = mock.Client(
        core_apis.GetClientClass('dns', self.api_version),
        real_client=core_apis.GetClientInstance(
            'dns', self.api_version, no_http=True))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = core_apis.GetMessagesModule('dns', self.api_version)


class DnsMockTest(DnsMockMultiTrackTest):
  """A base class for gcloud dns tests that need to use a mocked DNS client."""

  def SetUp(self):
    self.SetUpForTrack(calliope_base.ReleaseTrack.GA, 'v1')
    self.mocked_dns_v1 = self.client


class DnsMockBetaTest(DnsMockMultiTrackTest):
  """A base class for gcloud dns tests that need to use a mocked DNS client."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SetUpForTrack(self.track, 'v1beta2')
    self.mocked_dns_client = self.client
    self.messages_beta = self.messages


class DnsTest(e2e_base.WithServiceAuth, sdk_test_base.WithTempCWD):
  """A base class for gcloud dns tests that need to use a real DNS client."""

  def SetUp(self):
    self.ga_version = 'v1'
    self.beta_version = 'v1beta2'
