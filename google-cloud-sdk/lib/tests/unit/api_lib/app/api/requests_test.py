# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for googlecloudsdk.api_lib.app.api.requests."""

from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error


class ErrorTest(sdk_test_base.SdkBase):

  def SetUp(self):
    properties.VALUES.core.project.Set('fakeproject')
    api_name = 'appengine'
    api_version = appengine_api_client.AppengineApiClient.ApiVersion()
    self.mocked_client = mock.Client(
        apis.GetClientClass(api_name, api_version),
        real_client=apis.GetClientInstance(
            api_name, api_version, no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

    self.messages = apis.GetMessagesModule(api_name, api_version)

    self.client = appengine_api_client.AppengineApiClient(
        self.mocked_client)

  def testRaisesHttpError(self):
    """Test that http errors are raised directly from api client method."""
    message = self.messages.AppengineAppsGetRequest(
        name='apps/fakeproject')
    error = http_error.MakeHttpError()
    self.mocked_client.apps.Get.Expect(message, exception=error)
    with self.assertRaises(apitools_exceptions.HttpError):
      self.client.GetApplication()


if __name__ == '__main__':
  test_case.main()
