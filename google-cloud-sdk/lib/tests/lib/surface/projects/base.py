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
"""Base class for all projects tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class ProjectsTestBase(cli_test_base.CliTestBase):
  """Base class for all Projects tests."""

  def Project(self):
    return None

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('cloudresourcemanager', 'v1')

  def RunProjectsAlpha(self, *command):
    return self.Run(['alpha', 'projects'] + list(command))

  def RunProjectsBeta(self, *command):
    return self.Run(['beta', 'projects'] + list(command))

  def RunProjects(self, *command):
    return self.Run(['projects'] + list(command))


class ProjectsUnitTestBase(ProjectsTestBase, sdk_test_base.WithFakeAuth):
  """Base class for all Projects unit tests that use fake auth and mocks."""

  def SetUp(self):
    self.mock_client = mock.Client(
        core_apis.GetClientClass('cloudresourcemanager', 'v1'),
        real_client=core_apis.GetClientInstance(
            'cloudresourcemanager', 'v1', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.StartPatch('time.sleep')
