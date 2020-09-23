# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for gcloud storage ls command used on buckets.

Primarily for listing buckets because since other test buckets are actively
being removed and added, special handling is needed.

Listing objects is done in the ls scenario test.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.storage import errors
from tests.lib import cli_test_base
from tests.lib import test_case


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class LsTestAlpha(cli_test_base.CliTestBase):
  """Test cases for features in Alpha.

  When a feature moves to beta, move the corresponding tests to a superclass of
  this one where self.track = calliope_base.ReleaseTrack.BETA, details here:
  go/gcloud-test-howto#how-to-test-multiple-release-tracks.

  This will ensure that tests from past releases run for the alpha release.
  """

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.messages = apis.GetMessagesModule('storage', 'v1')
    self.stdout_seek_position = 0

  def test_ls_filesystem_error(self):
    with self.assertRaises(ValueError):
      self.Run('storage ls file://hi.png')

  def test_ls_cloud_provider_error(self):
    with self.assertRaises(errors.InvalidUrlError):
      self.Run('storage ls ninjacloud://hi.png')


if __name__ == '__main__':
  test_case.main()
