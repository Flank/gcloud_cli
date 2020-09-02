# Lint as: python3
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
"""Base class for all SecurityCenterSettings tests."""

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from googlecloudsdk.calliope import base


class SecurityCenterSettingsTestBase(cli_test_base.CliTestBase):
  """Base class for all SecurityCenter Settings tests."""

  def RunSccSettings(self, *command):
    self.track = base.ReleaseTrack.ALPHA
    return self.Run(['scc'] + list(command))


class SecurityCenterSettingsUnitTestBase(sdk_test_base.WithFakeAuth,
                                         sdk_test_base.WithLogCapture,
                                         SecurityCenterSettingsTestBase):
  """Base class for all SecurityCenter Settings unit tests."""

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('securitycenter', 'v1beta2')
    self.mocked_client = mock.Client(
        core_apis.GetClientClass('securitycenter', 'v1beta2'),
        real_client=core_apis.GetClientInstance(
            'securitycenter', 'v1beta2', no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)


class SecurityCenterSettingsE2ETestBase(e2e_base.WithServiceAuth,
                                        SecurityCenterSettingsTestBase):
  pass
