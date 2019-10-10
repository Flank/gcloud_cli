# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Base for Runtime Config surface unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.app.api import appengine_api_client_base
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class SchedulerTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for Runtime Config unit tests."""

  def SetUp(self):
    self.client = mock.Client(client_class=apis.GetClientClass('cloudscheduler',
                                                               'v1beta1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule('cloudscheduler', 'v1beta1')
    app_engine_api_version = (
        appengine_api_client_base.AppengineApiClientBase.ApiVersion())
    self.app_engine_client = mock.Client(
        apis.GetClientClass('appengine', app_engine_api_version))
    self.app_engine_client.Mock()
    self.app_engine_messages = apis.GetMessagesModule('appengine',
                                                      app_engine_api_version)
    self.addCleanup(self.app_engine_client.Unmock)
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectGetApp(self):
    name = 'apps/' + self.Project()
    self.app_engine_client.apps.Get.Expect(
        self.app_engine_messages.AppengineAppsGetRequest(name=name),
        self.app_engine_messages.Application(name=name,
                                             locationId='us-central1'))
