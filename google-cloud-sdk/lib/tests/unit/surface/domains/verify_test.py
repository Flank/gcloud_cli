# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for `gcloud domains verify` command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.app import api_test_util


class VerifyTest(api_test_util.ApiTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.open_mock = self.StartPatch('webbrowser.open_new_tab')

  def testVerify(self):
    """Test verify command directs user to browser."""
    self.Run('domains verify example.com')
    self.open_mock.assert_called_once_with(
        'https://www.google.com/webmasters/verification/'
        'verification?authuser=0&domain=example.com&pli=1')
