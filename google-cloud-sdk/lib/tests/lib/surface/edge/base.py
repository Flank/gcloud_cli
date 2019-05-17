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
"""Base class for all Cloud IoT Edge tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class CloudIotEdgeBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase,
                       sdk_test_base.WithLogCapture):
  """Base class for Cloud IoT Edge unit tests."""

  def SetUp(self):
    """Creates mock client and adds Unmock on cleanup."""
    self.client = mock.Client(
        client_class=apis.GetClientClass('edge', 'v1alpha1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule('edge', 'v1alpha1')

    self.edgeml_client = mock.Client(
        client_class=apis.GetClientClass('edgeml', 'v1beta1'))
    self.edgeml_client.Mock()
    self.addCleanup(self.edgeml_client.Unmock)
    self.edgeml_messages = apis.GetMessagesModule('edgeml', 'v1beta1')

    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('edge', 'v1alpha1')
    self.resources.RegisterApiByName('edgeml', 'v1beta1')
