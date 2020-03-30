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
"""Base class for gcloud service directory tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

_API_NAME = 'servicedirectory'
_API_VERSION = 'v1beta1'


class _ServiceDirectoryBase(cli_test_base.CliTestBase):
  """Base class for all Service Directory tests."""
  pass


class ServiceDirectoryUnitTestBase(sdk_test_base.WithFakeAuth,
                                   _ServiceDirectoryBase):
  """Base class for all Service Directory unit tests."""

  def SetUp(self):
    """Creates mock client and adds Unmock on cleanup."""
    self.client = mock.Client(
        client_class=apis.GetClientClass(_API_NAME, _API_VERSION))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.msgs = apis.GetMessagesModule(_API_NAME, _API_VERSION)
