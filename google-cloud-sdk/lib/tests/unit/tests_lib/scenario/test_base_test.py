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

"""Tests for the scenario test_base."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib.scenario import test_base

import six


class TestBaseTests(test_base.ScenarioTestBase, parameterized.TestCase):

  def SetUp(self):
    self.run_mock = self.StartObjectPatch(self.cli, 'Execute')
    data = """\
title: my scenario
release_tracks: [ALPHA, BETA]
actions:
  - set_property:
      core/project: myproj
  - execute_command:
      command: iot registries create my-registry --region us-central1
      events:
        - expect_exit_code: 0
  - set_property:
      core/project: otherproj
  - execute_command:
      command: iot registries describe my-registry --region us-central1
      events:
        - expect_exit_code: 0
"""
    self.spec_path = self.Touch(self.temp_path, contents=data)

  def _Check(self, data):
    def _Inner(command):
      expected_command, props = data.pop(0)
      self.assertEqual(expected_command, command)
      for p, v in six.iteritems(props):
        self.assertEqual(v, properties.FromString(p).Get())
    return _Inner

  @parameterized.named_parameters(
      ('Alpha', calliope_base.ReleaseTrack.ALPHA),
      ('Beta', calliope_base.ReleaseTrack.BETA),
  )
  def testScenario(self, track):
    data = [
        ([track.prefix, 'iot', 'registries', 'create', 'my-registry',
          '--region', 'us-central1'],
         {'core/project': 'myproj'}),

        ([track.prefix, 'iot', 'registries', 'describe', 'my-registry',
          '--region', 'us-central1'],
         {'core/project': 'otherproj'}),
    ]
    self.run_mock.side_effect = self._Check(data)
    self.RunScenario(self.spec_path, track, update_modes=[])
    self.assertEquals(2, len(self.run_mock.mock_calls))


if __name__ == '__main__':
  test_base.main()
