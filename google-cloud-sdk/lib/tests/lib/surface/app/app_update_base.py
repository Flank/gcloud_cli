# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Base class for app update tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class AppUpdateBase(sdk_test_base.WithFakeAuth,
                    cli_test_base.CliTestBase):
  """Base class for all app update tests."""

  APPENGINE_API = 'appengine'
  APPENGINE_API_VERSION = 'v1beta'

  def _FormatApp(self):
    return 'apps/{0}'.format(self.Project())

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule(self.APPENGINE_API,
                                                self.APPENGINE_API_VERSION)
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass(self.APPENGINE_API,
                                 self.APPENGINE_API_VERSION),
        real_client=core_apis.GetClientInstance(
            self.APPENGINE_API, self.APPENGINE_API_VERSION, no_http=True))
    self.mock_client.Mock()
    # If any API calls were made but weren't expected, this will throw an error
    self.addCleanup(self.mock_client.Unmock)

  def ExpectPatchApplicationRequest(
      self, project, update_mask,
      split_health_checks=None):
    request = self.messages.AppengineAppsPatchRequest(
        name='apps/{0}'.format(project),
        application=self.messages.Application(
            featureSettings=self.messages.FeatureSettings(
                splitHealthChecks=split_health_checks)),
        updateMask=update_mask)
    self.mock_client.apps.Patch.Expect(
        request,
        response=self.messages.Operation(
            name='apps/{0}/operations'.format(project),
            done=True))
