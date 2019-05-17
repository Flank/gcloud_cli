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

"""Tests for googlecloudsdk.calliope.command_release_tracks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import command_release_tracks
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case


class CommandReleaseTracksTest(sdk_test_base.SdkBase, parameterized.TestCase):

  @parameterized.parameters([
      ([{'prop': 'val'}],
       [{'prop': 'val'}]),
      ({'prop': 'val'},
       [{'prop': 'val'}]),
      ([{'release_tracks': ['ALPHA', 'BETA']}],
       [{'release_tracks': ['ALPHA']},
        {'release_tracks': ['BETA']}]),
      ([{'release_tracks': ['ALPHA', 'BETA'], 'ALPHA': {'prop': 'val'}}],
       [{'release_tracks': ['ALPHA'], 'prop': 'val'},
        {'release_tracks': ['BETA']}]),
  ])
  def testSeparateDeclarativeCommandTracks(self, impls, expected):
    actual = list(
        command_release_tracks.SeparateDeclarativeCommandTracks(impls))
    self.assertEqual(expected, actual)


if __name__ == '__main__':
  test_case.main()
