# -*- coding: utf-8 -*- #
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

"""Base class for all Cloud Logging tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base

NO_PROJECT_REGEXP = (r'.*(required property|unknown field) \[project.*')

NO_AUTH_REGEXP = (r'Your current active account \[.*\] does not have any valid '
                  'credentials')


class LoggingTestBase(cli_test_base.CliTestBase,
                      sdk_test_base.WithFakeAuth):
  """Base class for unit tests in logging package."""

  def Project(self):
    return 'my-project'

  def SetUp(self):
    self.mock_client_v2 = mock.Client(
        core_apis.GetClientClass('logging', 'v2'))
    self.mock_client_v2.Mock()
    self.addCleanup(self.mock_client_v2.Unmock)

    self.msgs = core_apis.GetMessagesModule('logging', 'v2')

  def RunLogging(self, cmd):
    return self.Run('logging ' + cmd)

  def RunWithoutPerms(self, cmd):
    """Test the command without valid permissions."""
    # Disable user output, this way we can check error handling from all
    # formatters Display() method, not only the default one.
    properties.VALUES.core.user_output_enabled.Set(False)
    # This is simulated by the API call returning a 403 http error.
    with self.AssertRaisesHttpExceptionMatches('Permission denied.'):
      result = self.RunLogging(cmd)
      # In case the command returns a generator, force its expansion.
      result = list(result)

  def RunWithoutProject(self, cmd):
    """Test the command without a set project."""
    # Remove project.
    properties.PersistProperty(properties.VALUES.core.project, None)
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegex(Exception, NO_PROJECT_REGEXP):
      self.RunLogging(cmd)

  def RunWithoutAuth(self, cmd):
    """Test the command without authentication."""
    # Remove credentials.
    self.FakeAuthSetCredentialsPresent(False)
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegex(Exception, NO_AUTH_REGEXP):
      self.RunLogging(cmd)


class LoggingIntegrationTestBase(e2e_base.WithServiceAuth):
  """Base class for integration tests."""

  def RunLogging(self, cmd):
    return self.Run('logging ' + cmd)
