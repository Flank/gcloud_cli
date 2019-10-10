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
"""Tests for googlecloudsdk.api_lib.app.api.appengine_app_update_api_client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.app.api import appengine_app_update_api_client
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case


class ErrorTest(sdk_test_base.SdkBase):

  def SetUp(self):
    properties.VALUES.core.project.Set('fakeproject')
    api_name = 'appengine'

    api_version = appengine_app_update_api_client.DEFAULT_VERSION
    self.mocked_client = mock.Client(
        apis.GetClientClass(api_name, api_version),
        real_client=apis.GetClientInstance(
            api_name, api_version, no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

    self.messages = apis.GetMessagesModule(api_name, api_version)

    self.client = (appengine_app_update_api_client.
                   AppengineAppUpdateApiClient(self.mocked_client))

  def ExpectPatchApplication(self, update_mask,
                             split_health_checks=None,
                             use_container_optimized_os=None):
    self.mocked_client.apps.Patch.Expect(
        request=self.messages.AppengineAppsPatchRequest(
            name='apps/fakeproject',
            application=self.messages.Application(
                featureSettings=self.messages.FeatureSettings(
                    splitHealthChecks=split_health_checks,
                    useContainerOptimizedOs=use_container_optimized_os)),
            updateMask=update_mask),
        response=self.messages.Operation(done=True))

  def testPatchApplication_splitHealthChecks(self):
    self.ExpectPatchApplication('featureSettings.splitHealthChecks,',
                                split_health_checks=True)

    self.client.PatchApplication(split_health_checks=True)

  def testPatchApplication_useContainerOptimizedOs(self):
    self.ExpectPatchApplication('featureSettings.useContainerOptimizedOs,',
                                use_container_optimized_os=True)

    self.client.PatchApplication(use_container_optimized_os=True)

  def testPatchApplication_multipleFeatureChanges(self):
    self.ExpectPatchApplication('featureSettings.splitHealthChecks,'
                                'featureSettings.useContainerOptimizedOs,',
                                split_health_checks=False,
                                use_container_optimized_os=True)

    self.client.PatchApplication(split_health_checks=False,
                                 use_container_optimized_os=True)


if __name__ == '__main__':
  test_case.main()
