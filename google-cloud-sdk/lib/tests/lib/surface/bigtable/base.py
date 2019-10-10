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

"""Base class for all bigtable tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error


class BigtableV2TestBase(sdk_test_base.WithFakeAuth,
                         sdk_test_base.WithLogCapture,
                         cli_test_base.CliTestBase):
  """Base class for Bigtable command unit tests hitting the v2 API."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    properties.VALUES.core.project.Set(self.Project())
    self.client = mock.Client(client_class=core_apis.GetClientClass(
        'bigtableadmin', 'v2'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.msgs = core_apis.GetMessagesModule('bigtableadmin', 'v2')

  @contextlib.contextmanager
  def AssertHttpResponseError(self, svc, msg):
    """Test uniform error handling for all commands."""
    svc.Expect(
        request=msg,
        exception=http_error.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches('Resource not found.'):
      yield
