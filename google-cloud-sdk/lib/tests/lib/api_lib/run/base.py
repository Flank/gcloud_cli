# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Base class for Google Serverless Engine API unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
import mock


class ServerlessApiBase(cli_test_base.CliTestBase):
  """Base class for Serverless API tests."""

  def SetUp(self):
    self.mock_serverless_client = mock.Mock()
    self.serverless_messages = core_apis.GetMessagesModule(
        'run', 'v1alpha1')
    self.mock_serverless_client._VERSION = 'v1alpha1'  # pylint: disable=protected-access
    self.mock_serverless_client.MESSAGES_MODULE = self.serverless_messages
