# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Base class for all ml translate tests."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

TRANSLATE_API = 'translate'


class MlTranslateTestBase(sdk_test_base.WithFakeAuth,
                          cli_test_base.CliTestBase):
  """Base class for gcloud ml speech command unit tests."""

  _VERSIONS_FOR_RELEASE_TRACKS = {
      calliope_base.ReleaseTrack.ALPHA: 'v3beta1',
      calliope_base.ReleaseTrack.BETA: 'v3',
  }

  def SetUp(self):
    """Basic SetUp."""
    self.track = None
    self.version = None
    self.client = None
    self.messages = None

  def SetUpForTrack(self, track):
    """Creates mock client and adds Unmock on cleanup."""
    self.track = track
    self.version = self._VERSIONS_FOR_RELEASE_TRACKS[track]
    self.client = mock.Client(
        client_class=apis.GetClientClass(TRANSLATE_API, self.version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule(TRANSLATE_API, self.version)
