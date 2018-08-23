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

"""Base class for all Error Reporting tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base


class ErrorReportingTestBase(cli_test_base.CliTestBase,
                             sdk_test_base.WithFakeAuth):
  """Base class for unit tests in error_reporting package."""

  FAKE_PROJECT = 'my-errors'

  NO_PROJECT_REGEXP = (r'.*(required property|unknown field) \[project.*')

  NO_AUTH_REGEXP = (r'Your current active account \[.*\] does not have any '
                    'valid credentials')

  def Project(self):
    return self.FAKE_PROJECT

  def SetUp(self):
    self.mock_client = mock.Client(
        core_apis.GetClientClass('clouderrorreporting', 'v1beta1'))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def RunCmd(self, cmd):
    return self.Run('beta error-reporting ' + cmd)

  def RunWithoutProject(self, cmd):
    """Test the command without a set project."""
    properties.PersistProperty(properties.VALUES.core.project, None)
    with self.assertRaisesRegex(Exception, self.NO_PROJECT_REGEXP):
      self.RunCmd(cmd)

  def RunWithoutAuth(self, cmd):
    """Test the command without authentication."""
    self.FakeAuthSetCredentialsPresent(False)
    with self.assertRaisesRegex(Exception, self.NO_AUTH_REGEXP):
      self.RunCmd(cmd)


class ErrorReportingIntegrationTestBase(e2e_base.WithServiceAuth):
  """Base class for integration tests."""

  def PreSetUp(self):
    # This is required to disable the use of service account. Service accounts
    # do not have OWNER permission, which some tested commands require.
    self.requires_refresh_token = True

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(True)

  def RunCmd(self, cmd):
    return self.Run('beta error-reporting ' + cmd)
