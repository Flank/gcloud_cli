# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Base class for all Cloud Game Services tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base


class _CloudGameServicesBase(cli_test_base.CliTestBase):
  """Base class for Cloud Game Services tests."""

  def SetUp(self):
    self.client = mock.Client(
        client_class=apis.GetClientClass('gameservices', 'v1alpha'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule('gameservices', 'v1alpha')


class CloudGameServicesUnitTestBase(sdk_test_base.WithFakeAuth,
                                    sdk_test_base.WithLogCapture,
                                    _CloudGameServicesBase):
  """Base class for Cloud Game Services unit tests."""

  pass


class CloudGameServicesE2ETestBase(e2e_base.WithServiceAuth,
                                   _CloudGameServicesBase):
  """base class for all Cloud Game Service e2e tests."""
  pass
