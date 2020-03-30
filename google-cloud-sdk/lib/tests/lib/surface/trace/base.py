# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Base class for all Cloud Trace tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base

import mock as mock1

NO_PROJECT_REGEXP = (r'.*(required property|unknown field) \[project.*')

NO_AUTH_REGEXP = (r'Your current active account \[.*\] does not have any valid '
                  'credentials')

# The import string for the Projects Api, used for mocking its methods.
_PROJECTS_API_IMPORT = ('googlecloudsdk.api_lib.cloudresourcemanager.'
                        'projects_api')
# The mock project number for each test to use
_PROJECT_NUM = 12345


class TraceTestBase(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):
  """Base class for unit tests in trace package."""

  def Project(self):
    return 'my-project'

  def SetUp(self):
    self.mock_client_v2 = mock.Client(
        core_apis.GetClientClass('cloudtrace', 'v2beta1'))
    self.mock_client_v2.Mock()
    self.addCleanup(self.mock_client_v2.Unmock)

    resource_messages = core_apis.GetMessagesModule('cloudresourcemanager',
                                                    'v1')

    project_number = mock1.patch(
        _PROJECTS_API_IMPORT + '.Get',
        return_value=resource_messages.Project(projectNumber=_PROJECT_NUM),
        autospec=True)
    self.addCleanup(project_number.stop)
    project_number.start()

    self.msgs = core_apis.GetMessagesModule('cloudtrace', 'v2beta1')

  def RunTrace(self, cmd, track=None):
    return self.Run('trace ' + cmd, track)

  def RunWithoutPerms(self, cmd, track=None):
    """Test the command without valid permissions."""
    # Disable user output, this way we can check error handling from all
    # formatters Display() method, not only the default one.
    properties.VALUES.core.user_output_enabled.Set(False)
    # This is simulated by the API call returning a 403 http error.
    with self.AssertRaisesHttpExceptionMatches('Permission denied.'):
      result = self.RunTrace(cmd, track)
      # In case the command returns a generator, force its expansion.
      result = list(result)

  def RunWithoutProject(self, cmd, track=None):
    """Test the command without a set project."""
    # Remove project.
    properties.PersistProperty(properties.VALUES.core.project, None)
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegex(Exception, NO_PROJECT_REGEXP):
      self.RunTrace(cmd, track)

  def RunWithoutAuth(self, cmd, track=None):
    """Test the command without authentication."""
    # Remove credentials.
    self.FakeAuthSetCredentialsPresent(False)
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegex(Exception, NO_AUTH_REGEXP):
      self.RunTrace(cmd, track)


class TraceIntegrationTestBase(e2e_base.WithServiceAuth):
  """Base class for integration tests."""

  def RunTrace(self, cmd):
    return self.Run('trace ' + cmd)
