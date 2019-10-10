# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Base class for remote build execution unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class RemoteBuildExecutionUnitTestBase(cli_test_base.CliTestBase,
                                       sdk_test_base.WithFakeAuth):
  """Base class for Remote Build Execution Unit Tests.

  Contains some common setup code as well as helper functions for dealing with
  LROs.
  """

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'v1alpha'

  def SetUp(self):
    self.mocked_rbe_v1alpha = mock.Client(
        core_apis.GetClientClass('remotebuildexecution', 'v1alpha'),
        real_client=core_apis.GetClientInstance('remotebuildexecution',
                                                'v1alpha',
                                                no_http=True))
    self.mocked_rbe_v1alpha.Mock()
    self.addCleanup(self.mocked_rbe_v1alpha.Unmock)

    properties.VALUES.core.project.Set('test-project')
    self.rbe_v1alpha_messages = core_apis.GetMessagesModule(
        'remotebuildexecution', 'v1alpha')

  def _GetOperationResponse(self, name, response=None,
                            error_json=None):
    """Helper function to build GoogleLongRunningOperation response."""
    if response:
      result = {
          'name': name,
          'done': True,
          'response': response
      }
      return encoding.PyValueToMessage(
          self.rbe_v1alpha_messages.GoogleLongrunningOperation,
          result)
    if error_json:
      result = {
          'name': name,
          'done': True,
          'error': error_json
      }
      return encoding.PyValueToMessage(
          self.rbe_v1alpha_messages.GoogleLongrunningOperation,
          result)
    return self.rbe_v1alpha_messages.GoogleLongrunningOperation(name=name)
