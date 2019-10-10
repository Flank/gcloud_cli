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
"""Base class for spanner tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class SpannerTestBase(sdk_test_base.WithFakeAuth,
                      cli_test_base.CliTestBase):
  """Base class for Cloud Spanner unit tests."""

  def SetUp(self):
    """Creates mock client and adds Unmock on cleanup."""
    self.client = mock.Client(client_class=apis.GetClientClass('spanner', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.msgs = apis.GetMessagesModule('spanner', 'v1')
    self.track = calliope_base.ReleaseTrack.GA


class SpannerTestBeta(SpannerTestBase):
  """Base class for Cloud Spanner BETA unit tests."""

  def Run(self, cmd, track=None):
    return super(SpannerTestBeta, self).Run(
        cmd, track=calliope_base.ReleaseTrack.BETA)


class SpannerTestAlpha(SpannerTestBase):
  """Base class for Cloud Spanner ALPHA unit tests."""

  def Run(self, cmd, track=None):
    return super(SpannerTestAlpha, self).Run(
        cmd, track=calliope_base.ReleaseTrack.ALPHA)
